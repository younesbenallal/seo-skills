#!/usr/bin/env python3
"""Convert a sitemap or sitemap index into a compact URL inventory."""

import argparse
import csv
import gzip
import json
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


COMMERCIAL = {
    "alternative",
    "alternatives",
    "compare",
    "comparison",
    "demo",
    "pricing",
    "product",
    "products",
    "solution",
    "solutions",
    "use-case",
    "use-cases",
    "vs",
}
CONTENT = {"article", "articles", "blog", "guide", "guides", "learn", "news", "resources"}
TOOLS = {"calculator", "calculators", "examples", "template", "templates", "tool", "tools"}
DOCS = {"api", "changelog", "developer", "developers", "docs", "documentation", "help", "support"}
COMPANY = {"about", "careers", "company", "contact", "legal", "partners", "privacy", "terms"}


def local_name(tag):
    return tag.rsplit("}", 1)[-1]


def read_source(source, timeout):
    parsed = urllib.parse.urlparse(source)
    if parsed.scheme in {"http", "https"}:
        request = urllib.request.Request(
            source,
            headers={"User-Agent": "Mozilla/5.0 (compatible; CompetitorIntelligence/1.0)"},
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = response.read()
            encoding = response.headers.get("Content-Encoding", "")
        if source.lower().endswith(".gz") or "gzip" in encoding.lower():
            data = gzip.decompress(data)
        return data

    path = Path(source).expanduser()
    data = path.read_bytes()
    if path.suffix.lower() == ".gz":
        data = gzip.decompress(data)
    return data


def resolve_child(parent, child):
    if urllib.parse.urlparse(child).scheme in {"http", "https"}:
        return child
    if urllib.parse.urlparse(parent).scheme in {"http", "https"}:
        return urllib.parse.urljoin(parent, child)
    return str((Path(parent).expanduser().parent / child).resolve())


def parse_xml(data):
    root = ET.fromstring(data)
    kind = local_name(root.tag)
    if kind not in {"sitemapindex", "urlset"}:
        raise ValueError(f"unsupported root element: {kind}")

    records = []
    item_name = "sitemap" if kind == "sitemapindex" else "url"
    for item in root:
        if local_name(item.tag) != item_name:
            continue
        values = {}
        for child in item:
            name = local_name(child.tag)
            if name in {"loc", "lastmod", "changefreq", "priority"}:
                values[name] = (child.text or "").strip()
        if values.get("loc"):
            records.append(values)
    return kind, records


def page_type(segments):
    terms = set(segments)
    if terms & COMMERCIAL:
        return "commercial"
    if terms & TOOLS:
        return "tool-or-template"
    if terms & DOCS:
        return "docs-or-support"
    if terms & CONTENT:
        return "editorial"
    if terms & COMPANY:
        return "company"
    if not segments:
        return "homepage"
    return "other"


def url_row(url, lastmod, changefreq, priority, source_sitemap):
    parsed = urllib.parse.urlparse(url)
    raw_segments = [urllib.parse.unquote(part) for part in parsed.path.split("/") if part]
    segments = [part.lower() for part in raw_segments]
    slug = raw_segments[-1] if raw_segments else ""
    slug_terms = slug.lower().replace("_", "-").split("-") if slug else []
    combined = segments[:-1] + slug_terms
    return {
        "url": url,
        "host": parsed.netloc.lower(),
        "path": parsed.path or "/",
        "first_segment": raw_segments[0] if raw_segments else "",
        "depth": len(raw_segments),
        "slug": slug,
        "slug_terms": " ".join(term for term in slug_terms if term),
        "page_type": page_type(combined),
        "lastmod": lastmod,
        "changefreq": changefreq,
        "priority": priority,
        "source_sitemap": source_sitemap,
    }


def summarize(rows, sources, errors):
    page_types = Counter(row["page_type"] for row in rows)
    segments = Counter(row["first_segment"] or "/" for row in rows)
    hosts = Counter(row["host"] for row in rows)
    dated = [row for row in rows if row["lastmod"]]
    months = Counter(row["lastmod"][:7] for row in dated if len(row["lastmod"]) >= 7)
    newest = sorted(dated, key=lambda row: row["lastmod"], reverse=True)[:20]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "totals": {
            "urls": len(rows),
            "sitemaps_processed": len(sources),
            "errors": len(errors),
        },
        "hosts": dict(hosts.most_common(20)),
        "page_types": dict(page_types.most_common()),
        "top_first_segments": dict(segments.most_common(50)),
        "lastmod": {
            "urls_with_lastmod": len(dated),
            "coverage_percent": round((len(dated) / len(rows) * 100), 2) if rows else 0,
            "oldest": min((row["lastmod"] for row in dated), default=None),
            "newest": max((row["lastmod"] for row in dated), default=None),
            "top_months": dict(months.most_common(36)),
        },
        "newest_samples": [
            {"url": row["url"], "lastmod": row["lastmod"], "page_type": row["page_type"]}
            for row in newest
        ],
        "notes": [
            "page_type is a URL-based heuristic and requires sampling before strategic claims",
            "lastmod may reflect publishing, editing, or deployment behavior",
        ],
    }


def main():
    parser = argparse.ArgumentParser(
        description="Flatten a sitemap tree into pages.csv and a bounded summary.json."
    )
    parser.add_argument("source", help="Sitemap URL or local XML/XML.GZ file")
    parser.add_argument("--output-dir", required=True, help="Directory for generated artifacts")
    parser.add_argument("--max-sitemaps", type=int, default=500)
    parser.add_argument("--max-urls", type=int, default=1_000_000)
    parser.add_argument("--timeout", type=float, default=30)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    queue = [args.source]
    queued = {args.source}
    processed = []
    errors = []
    pages = {}

    while queue:
        source = queue.pop(0)
        if len(processed) >= args.max_sitemaps:
            errors.append({"source": source, "error": "max sitemap limit reached"})
            break
        try:
            data = read_source(source, args.timeout)
            kind, records = parse_xml(data)
            processed.append(source)
            if kind == "sitemapindex":
                for record in records:
                    child = resolve_child(source, record["loc"])
                    if child not in queued:
                        queued.add(child)
                        queue.append(child)
                continue

            for record in records:
                url = record["loc"]
                pages[url] = url_row(
                    url,
                    record.get("lastmod", ""),
                    record.get("changefreq", ""),
                    record.get("priority", ""),
                    source,
                )
                if len(pages) >= args.max_urls:
                    errors.append({"source": source, "error": "max URL limit reached"})
                    queue.clear()
                    break
        except Exception as exc:
            errors.append({"source": source, "error": str(exc)})

    rows = sorted(pages.values(), key=lambda row: row["url"])
    fieldnames = [
        "url",
        "host",
        "path",
        "first_segment",
        "depth",
        "slug",
        "slug_terms",
        "page_type",
        "lastmod",
        "changefreq",
        "priority",
        "source_sitemap",
    ]
    with (output_dir / "pages.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    summary = summarize(rows, processed, errors)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    errors_path = output_dir / "errors.csv"
    if errors:
        with errors_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["source", "error"])
            writer.writeheader()
            writer.writerows(errors)
    elif errors_path.exists():
        errors_path.unlink()

    print(f"URLs: {len(rows)}")
    print(f"Sitemaps: {len(processed)}")
    print(f"Errors: {len(errors)}")
    print(f"Inventory: {output_dir / 'pages.csv'}")
    print(f"Summary: {output_dir / 'summary.json'}")
    return 1 if not rows and errors else 0


if __name__ == "__main__":
    sys.exit(main())
