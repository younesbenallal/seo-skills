#!/usr/bin/env python3
"""Aggregate, compare, and score Google Search Console rows saved from any GSC MCP.

Accepted inputs (one or more files per argument, e.g. several paginated pages):
- JSON returned by a GSC MCP: {"rows": [...]}, {"data": {"rows": [...]}}, or a bare list
- rows shaped either {"query": ..., "page": ..., "clicks": ...} or {"keys": [...], "clicks": ...}
- tool-result files with text before the JSON, or MCP content blocks [{"type": "text", "text": "..."}]
- CSV exports from the Search Console UI or an API export

CTR is always recomputed from clicks / impressions, because MCPs disagree on percent vs fraction.
Positions are always averaged weighted by impressions.
"""

import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

METRICS = ("clicks", "impressions", "ctr", "position")
DIMENSIONS = ("date", "query", "page", "country", "device", "searchAppearance")
CSV_HEADERS = {
    "top queries": "query",
    "queries": "query",
    "query": "query",
    "top pages": "page",
    "pages": "page",
    "page": "page",
    "url": "page",
    "date": "date",
    "country": "country",
    "device": "device",
    "clicks": "clicks",
    "impressions": "impressions",
    "position": "position",
    # French Search Console UI exports
    "requêtes les plus fréquentes": "query",
    "requêtes": "query",
    "pages les plus populaires": "page",
    "pays": "country",
    "appareil": "device",
    "clics": "clicks",
}
# Organic CTR by position 1-10 (same curve as common public benchmarks); decays linearly after 10.
CTR_CURVE = [0.285, 0.157, 0.110, 0.080, 0.072, 0.051, 0.040, 0.032, 0.028, 0.025]


def expected_ctr(position):
    if position < 1:
        return CTR_CURVE[0]
    if position <= 10:
        return CTR_CURVE[int(position) - 1]
    return max(0.005, 0.025 - (position - 10) * 0.002)


# ---------- loading ----------


def parse_json_text(text):
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = min((i for i in (text.find("{"), text.find("[")) if i >= 0), default=-1)
        if start < 0:
            raise ValueError("no JSON found")
        return json.JSONDecoder().raw_decode(text[start:])[0]


def find_rows(payload):
    """Return (rows, dimension names) from any supported JSON shape."""
    if isinstance(payload, list):
        if payload and isinstance(payload[0], dict) and payload[0].get("type") == "text":
            return find_rows(parse_json_text("".join(block.get("text", "") for block in payload)))
        if payload and isinstance(payload[0], dict) and "impressions" in payload[0]:
            return payload, None
        for item in payload:
            if isinstance(item, (dict, list)):
                rows, dimensions = find_rows(item)
                if rows:
                    return rows, dimensions
        return [], None
    if isinstance(payload, dict):
        dimensions = payload.get("dimensions")
        if isinstance(payload.get("rows"), list):
            return payload["rows"], dimensions
        for value in payload.values():
            if isinstance(value, (dict, list)):
                rows, nested_dimensions = find_rows(value)
                if rows:
                    return rows, nested_dimensions or dimensions
    return [], None


def to_number(value):
    """Parse API numbers and UI exports: "1,210", "3 000", "9,2", "1.8%", "0,17 %"."""
    if isinstance(value, (int, float)):
        return float(value)
    text = re.sub(r"[\s%]", "", str(value))
    if "," in text and "." in text or re.fullmatch(r"\d{1,3}(,\d{3})+", text):
        text = text.replace(",", "")
    else:
        text = text.replace(",", ".")
    return float(text or 0)


def normalize(raw, dimensions, source):
    row = {}
    keys = raw.get("keys")
    if keys is not None:
        if not dimensions:
            raise ValueError(f"{source}: rows use 'keys' but the payload has no 'dimensions'; pass --dims")
        row.update(zip(dimensions, keys))
    for name in DIMENSIONS:
        if name in raw:
            row[name] = raw[name]
    row["clicks"] = to_number(raw.get("clicks", 0))
    row["impressions"] = to_number(raw.get("impressions", 0))
    row["position"] = to_number(raw.get("position", 0))
    return row


def load_file(path, dims_override):
    text = Path(path).read_text(encoding="utf-8-sig")
    if path.lower().endswith(".csv"):
        reader = csv.DictReader(text.splitlines())
        rows = []
        for raw in reader:
            mapped = {CSV_HEADERS[k.strip().lower()]: v for k, v in raw.items() if k and k.strip().lower() in CSV_HEADERS}
            rows.append(normalize(mapped, None, path))
        return rows
    rows, dimensions = find_rows(parse_json_text(text))
    return [normalize(raw, dims_override or dimensions, path) for raw in rows]


def load(paths, dims_override=None):
    rows = []
    for path in paths:
        rows.extend(load_file(path, dims_override))
    if not rows:
        sys.exit(f"No rows found in {', '.join(paths)}")
    return rows


# ---------- aggregation ----------


def bucket(row, key):
    if key in ("month", "week", "year"):
        if "date" not in row:
            sys.exit(f"--by {key} needs rows with a 'date' dimension")
        day = date.fromisoformat(row["date"][:10])
        if key == "month":
            return day.strftime("%Y-%m")
        if key == "year":
            return str(day.year)
        iso = day.isocalendar()
        return f"{iso[0]}-W{iso[1]:02d}"
    if key not in row:
        sys.exit(f"Rows have no '{key}' dimension (available: {', '.join(k for k in row if k not in METRICS)})")
    return row[key]


def aggregate(rows, keys):
    groups = defaultdict(lambda: {"clicks": 0.0, "impressions": 0.0, "weighted": 0.0})
    for row in rows:
        group = groups[tuple(bucket(row, key) for key in keys)]
        group["clicks"] += row["clicks"]
        group["impressions"] += row["impressions"]
        group["weighted"] += row["position"] * row["impressions"]
    result = {}
    for group_key, g in groups.items():
        impressions = g["impressions"]
        result[group_key] = {
            "clicks": g["clicks"],
            "impressions": impressions,
            "ctr": g["clicks"] / impressions if impressions else 0.0,
            "position": g["weighted"] / impressions if impressions else 0.0,
        }
    return result


# ---------- output ----------


def fmt(value, column):
    if isinstance(value, float):
        if column in ("ctr", "ctr_before", "ctr_after", "expected_ctr") or "share" in column:
            return f"{value * 100:.2f}%"
        if "position" in column:
            return f"{value:.1f}"
        if column == "click_change":
            return f"{value:+.0f}"
        return f"{value:.0f}"
    return "" if value is None else str(value)


def emit(records, columns, args):
    if args.limit:
        records = records[: args.limit]
    if args.format == "json":
        print(json.dumps(records, ensure_ascii=False, indent=2))
        return
    if args.format == "csv":
        writer = csv.DictWriter(sys.stdout, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)
        return
    print("| " + " | ".join(columns) + " |")
    print("|" + "|".join("---" for _ in columns) + "|")
    for record in records:
        print("| " + " | ".join(fmt(record.get(c), c).replace("|", "\\|") for c in columns) + " |")


def with_keys(keys, group_key, stats):
    return {**dict(zip(keys, group_key)), **stats}


# ---------- commands ----------


def cmd_aggregate(args):
    keys = args.by.split(",")
    rows = load(args.files, args.dims)
    grouped = aggregate(rows, keys)
    records = [with_keys(keys, k, v) for k, v in grouped.items()]
    time_keys = {"date", "month", "week", "year"}
    if set(keys) <= time_keys:
        records.sort(key=lambda r: tuple(r[k] for k in keys))
    else:
        records.sort(key=lambda r: r[args.sort], reverse=args.sort != "position")
    total = aggregate(rows, [])[()]
    print(f"Total: {total['clicks']:.0f} clicks, {total['impressions']:.0f} impressions, "
          f"CTR {total['ctr'] * 100:.2f}%, weighted position {total['position']:.1f}\n", file=sys.stderr)
    emit(records, keys + list(METRICS), args)


def classify(before, after, args):
    if after is None:
        return "disappeared" if before["clicks"] >= args.min_prior_clicks else "gone (low volume)"
    position_change = after["position"] - before["position"]
    if position_change > args.position_threshold:
        return "ranking drop"
    if position_change < -args.position_threshold:
        return "ranking gain"
    if before["impressions"] and after["impressions"] < before["impressions"] * args.ratio:
        return "impressions loss, position stable"
    if before["ctr"] and after["ctr"] < before["ctr"] * args.ratio:
        return "CTR collapse, position stable"
    return "stable / demand"


def cmd_compare(args):
    keys = args.by.split(",")
    before = aggregate(load(args.before, args.dims), keys)
    after = aggregate(load(args.after, args.dims), keys)
    total_before = sum(v["clicks"] for v in before.values())
    total_after = sum(v["clicks"] for v in after.values())
    total_change = total_after - total_before
    records = []
    for group_key in set(before) | set(after):
        b = before.get(group_key)
        a = after.get(group_key)
        b_stats = b or {"clicks": 0.0, "impressions": 0.0, "ctr": 0.0, "position": 0.0}
        a_stats = a or {"clicks": 0.0, "impressions": 0.0, "ctr": 0.0, "position": 0.0}
        click_change = a_stats["clicks"] - b_stats["clicks"]
        records.append({
            **dict(zip(keys, group_key)),
            "clicks_before": b_stats["clicks"],
            "clicks_after": a_stats["clicks"],
            "click_change": click_change,
            "share_of_total_change": click_change / total_change if total_change else 0.0,
            "impressions_before": b_stats["impressions"],
            "impressions_after": a_stats["impressions"],
            "ctr_before": b_stats["ctr"],
            "ctr_after": a_stats["ctr"],
            "position_before": b_stats["position"] if b else None,
            "position_after": a_stats["position"] if a else None,
            "diagnosis": "new" if b is None else classify(b, a, args),
        })
    records.sort(key=lambda r: r["click_change"], reverse=args.gains)
    print(f"Total clicks: {total_before:.0f} -> {total_after:.0f} ({total_change:+.0f})\n", file=sys.stderr)
    emit(records, keys + ["clicks_before", "clicks_after", "click_change", "share_of_total_change",
                          "impressions_before", "impressions_after", "ctr_before", "ctr_after",
                          "position_before", "position_after", "diagnosis"], args)


def cmd_decay(args):
    keys = [args.by]
    periods = [aggregate(load([path], args.dims), keys) for path in args.periods]
    oldest, middle, newest = periods
    records = []
    for group_key, p1 in oldest.items():
        p2 = middle.get(group_key)
        p3 = newest.get(group_key, {"clicks": 0.0, "position": None})
        if not p2 or p1["clicks"] < args.min_clicks:
            continue
        if not (p1["clicks"] > p2["clicks"] > p3["clicks"]):
            continue
        if p3["position"] is None:
            trend = "dropped out"
        elif p3["position"] - p1["position"] > 2:
            trend = "rankings declining"
        elif p3["position"] - p1["position"] < -2:
            trend = "rankings improving (CTR or demand issue)"
        else:
            trend = "rankings stable (CTR or demand decline)"
        records.append({
            args.by: group_key[0],
            "clicks_p1": p1["clicks"],
            "clicks_p2": p2["clicks"],
            "clicks_p3": p3["clicks"],
            "click_loss": p1["clicks"] - p3["clicks"],
            "position_p1": p1["position"],
            "position_p3": p3["position"],
            "trend": trend,
        })
    records.sort(key=lambda r: r["click_loss"], reverse=True)
    emit(records, [args.by, "clicks_p1", "clicks_p2", "clicks_p3", "click_loss", "position_p1", "position_p3", "trend"], args)


OPPORTUNITY_DEFAULTS = {
    "quick-wins": {"min_impressions": 100, "min_position": 4, "max_position": 15},
    "ctr-gap": {"min_impressions": 500, "min_position": 0, "max_position": 20},
    "content-gaps": {"min_impressions": 50, "min_position": 20, "max_position": 0},
}


def cmd_opportunities(args):
    for name, value in OPPORTUNITY_DEFAULTS[args.kind].items():
        if getattr(args, name) is None:
            setattr(args, name, value)
    keys = args.by.split(",")
    records = []
    for group_key, s in aggregate(load(args.files, args.dims), keys).items():
        if s["impressions"] < args.min_impressions:
            continue
        position = s["position"]
        record = with_keys(keys, group_key, s)
        if args.kind == "quick-wins":
            if not (args.min_position <= position <= args.max_position):
                continue
            record["potential_extra_clicks"] = s["impressions"] * max(0.0, expected_ctr(args.target_position) - s["ctr"])
        elif args.kind == "ctr-gap":
            if position > args.max_position:
                continue
            record["expected_ctr"] = expected_ctr(position)
            gap = record["expected_ctr"] - s["ctr"]
            if gap <= args.min_gap:
                continue
            record["potential_extra_clicks"] = s["impressions"] * gap
            record["note"] = "top 3 with CTR < 1%: answer likely shown in the SERP" if position <= 3 and s["ctr"] < 0.01 else ""
        else:  # content-gaps
            if position <= args.min_position:
                continue
            record["potential_extra_clicks"] = s["impressions"] * expected_ctr(args.target_position)
        records.append(record)
    records.sort(key=lambda r: r["potential_extra_clicks"], reverse=True)
    extra = ["expected_ctr", "potential_extra_clicks", "note"] if args.kind == "ctr-gap" else ["potential_extra_clicks"]
    emit(records, keys + list(METRICS) + extra, args)


def cmd_cannibalization(args):
    grouped = aggregate(load(args.files, args.dims), ["query", "page"])
    by_query = defaultdict(list)
    for (query, page), s in grouped.items():
        by_query[query].append({"page": page, **s})
    records = []
    for query, pages in by_query.items():
        total = sum(p["impressions"] for p in pages)
        if total < args.min_impressions:
            continue
        competing = [p for p in pages if p["impressions"] / total >= args.min_share]
        if len(competing) < 2:
            continue
        competing.sort(key=lambda p: p["position"])
        records.append({
            "query": query,
            "total_impressions": total,
            "pages": len(competing),
            "position_gap": competing[-1]["position"] - competing[0]["position"],
            "detail": "; ".join(
                f"{p['page']} (pos {p['position']:.1f}, {p['impressions']:.0f} impr, {p['clicks']:.0f} clicks)"
                for p in competing
            ),
        })
    records.sort(key=lambda r: r["total_impressions"], reverse=True)
    emit(records, ["query", "total_impressions", "pages", "position_gap", "detail"], args)


def cmd_segment(args):
    patterns = []
    for spec in args.segment:
        name, _, regex = spec.partition("=")
        patterns.append((name, re.compile(regex, re.IGNORECASE)))
    rows = load(args.files, args.dims)
    for row in rows:
        value = str(row.get(args.dim, ""))
        row["segment"] = next((name for name, pattern in patterns if pattern.search(value)), "other")
    grouped = aggregate(rows, ["segment"])
    total_clicks = sum(v["clicks"] for v in grouped.values()) or 1
    total_impressions = sum(v["impressions"] for v in grouped.values()) or 1
    records = []
    for (name,), s in grouped.items():
        records.append({
            "segment": name,
            "rows": sum(1 for r in rows if r["segment"] == name),
            **s,
            "click_share": s["clicks"] / total_clicks,
            "impression_share": s["impressions"] / total_impressions,
        })
    records.sort(key=lambda r: r["impressions"], reverse=True)
    emit(records, ["segment", "rows", "clicks", "impressions", "ctr", "position", "click_share", "impression_share"], args)


# ---------- CLI ----------


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--dims", type=lambda v: v.split(","), help="Dimension order when rows only carry 'keys'")
    common.add_argument("--format", choices=("md", "csv", "json"), default="md")
    common.add_argument("--limit", type=int, default=50, help="Max rows printed (0 = all)")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("aggregate", parents=[common], help="Group rows by dimensions or by month/week/year")
    p.add_argument("files", nargs="+")
    p.add_argument("--by", required=True, help="Comma list, e.g. month | page | page,month | query")
    p.add_argument("--sort", choices=METRICS, default="clicks")
    p.set_defaults(func=cmd_aggregate)

    p = sub.add_parser("compare", parents=[common], help="Compare two periods and classify each change")
    p.add_argument("--before", nargs="+", required=True)
    p.add_argument("--after", nargs="+", required=True)
    p.add_argument("--by", default="page")
    p.add_argument("--position-threshold", type=float, default=2.0)
    p.add_argument("--ratio", type=float, default=0.7, help="Impressions/CTR below ratio x before = loss")
    p.add_argument("--min-prior-clicks", type=float, default=5)
    p.add_argument("--gains", action="store_true", help="Sort biggest gains first")
    p.set_defaults(func=cmd_compare)

    p = sub.add_parser("decay", parents=[common], help="Three consecutive declining periods")
    p.add_argument("--periods", nargs=3, required=True, metavar=("OLDEST", "MIDDLE", "NEWEST"))
    p.add_argument("--by", default="page")
    p.add_argument("--min-clicks", type=float, default=10)
    p.set_defaults(func=cmd_decay)

    p = sub.add_parser("opportunities", parents=[common], help="quick-wins | ctr-gap | content-gaps")
    p.add_argument("kind", choices=("quick-wins", "ctr-gap", "content-gaps"))
    p.add_argument("files", nargs="+")
    p.add_argument("--by", default="query")
    p.add_argument("--min-impressions", type=float, help="Default: 100 quick-wins, 500 ctr-gap, 50 content-gaps")
    p.add_argument("--min-position", type=float, help="quick-wins lower bound (4); content-gaps: rank worse than this (20)")
    p.add_argument("--max-position", type=float, help="quick-wins upper bound (15); ctr-gap upper bound (20)")
    p.add_argument("--target-position", type=float, default=3)
    p.add_argument("--min-gap", type=float, default=0.01, help="ctr-gap: minimum CTR gap vs curve")
    p.set_defaults(func=cmd_opportunities)

    p = sub.add_parser("cannibalization", parents=[common], help="Queries split across several pages")
    p.add_argument("files", nargs="+", help="Rows with both query and page dimensions")
    p.add_argument("--min-impressions", type=float, default=50)
    p.add_argument("--min-share", type=float, default=0.1, help="Ignore pages under this share of the query's impressions")
    p.set_defaults(func=cmd_cannibalization)

    p = sub.add_parser("segment", parents=[common], help="Split traffic with regex segments")
    p.add_argument("files", nargs="+")
    p.add_argument("--dim", default="query")
    p.add_argument("--segment", action="append", required=True, metavar="NAME=REGEX", help="First match wins; repeatable")
    p.set_defaults(func=cmd_segment)

    args = parser.parse_args()
    args.limit = args.limit or None
    args.func(args)


if __name__ == "__main__":
    main()
