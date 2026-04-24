#!/usr/bin/env python3
"""
Bright Data GEO / LLM visibility collector.

This script mirrors the Bright Data "datasets/v3" workflow:
1) Trigger dataset run (returns snapshot_id)
2) Poll progress until ready/failed
3) Download snapshot results
4) Save results to results.json

Note: HTML report generation is handled by AI after analyzing results.json.

Requirements:
- Python 3.10+
- BRIGHTDATA_API_KEY env var (or --api-key)

Example:
  export BRIGHTDATA_API_KEY="..."
  python geo-audit-report/scripts/brightdata-geo.py \
    --check-url "https://example.com" \
    --prompts-file prompts.txt \
    --chatgpt-dataset-id "gd_..." \
    --perplexity-dataset-id "gd_..." \
    --gemini-dataset-id "gd_..." \
    --target-domains "example.com" \
    --brand-terms "Example,Example Product" \
    --out-dir ./geo-run
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


DEFAULT_BASE_URL = "https://api.brightdata.com"


CHATGPT_OUTPUT_FIELDS = [
    "url",
    "prompt",
    "links_attached",
    "citations",
    "recommendations",
    "country",
    "is_map",
    "references",
    "shopping",
    "shopping_visible",
    "index",
    "answer_text_markdown",
    "web_search_triggered",
    "additional_prompt",
    "additional_answer_text",
    "map",
    "search_sources",
    "model",
    "web_search_query",
]

PERPLEXITY_OUTPUT_FIELDS = [
    "url",
    "prompt",
    "answer_text_markdown",
    "sources",
    "is_shopping_data",
    "shopping_data",
    "index",
    "exported_markdown",
    "related_prompts",
    "citations",
    "web_search_query",
]

GEMINI_OUTPUT_FIELDS = [
    "url",
    "prompt",
    "answer_text_markdown",
    "sources",
    "citations",
    "index",
    "web_search_query",
]


def get_custom_output_fields(chatbot: str) -> str:
    if chatbot == "chatgpt":
        return "|".join(CHATGPT_OUTPUT_FIELDS)
    if chatbot == "perplexity":
        return "|".join(PERPLEXITY_OUTPUT_FIELDS)
    if chatbot == "gemini":
        return "|".join(GEMINI_OUTPUT_FIELDS)
    return ""


def http_json(
    url: str,
    method: str,
    api_key: str,
    payload: Optional[Any] = None,
    timeout_sec: int = 60,
) -> Any:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data_bytes = None
    if payload is not None:
        data_bytes = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(url=url, method=method, headers=headers, data=data_bytes)
    with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
        body = resp.read().decode("utf-8", errors="replace")
        if not body.strip():
            return None
        return json.loads(body)


def build_url(base_url: str, path: str, query: Optional[Dict[str, str]] = None) -> str:
    base = base_url.rstrip("/")
    full = f"{base}{path}"
    if not query:
        return full
    q = {k: v for k, v in query.items() if v}
    return f"{full}?{urllib.parse.urlencode(q)}"


def trigger_dataset(
    *,
    base_url: str,
    api_key: str,
    dataset_id: str,
    input_rows: List[Dict[str, Any]],
    custom_output_fields: str,
) -> str:
    url = build_url(
        base_url,
        "/datasets/v3/trigger",
        {
            "dataset_id": dataset_id,
            "custom_output_fields": custom_output_fields,
            "include_errors": "true",
        },
    )
    resp = http_json(url, "POST", api_key, payload=input_rows, timeout_sec=120)
    snapshot_id = (resp or {}).get("snapshot_id")
    if not snapshot_id:
        raise RuntimeError(f"Bright Data trigger returned no snapshot_id: {resp}")
    return str(snapshot_id)


def poll_progress(
    *,
    base_url: str,
    api_key: str,
    snapshot_id: str,
    poll_delay_sec: int,
    poll_attempts: int,
) -> str:
    for attempt in range(poll_attempts):
        url = build_url(base_url, f"/datasets/v3/progress/{snapshot_id}")
        resp = http_json(url, "GET", api_key, timeout_sec=60)
        status = (resp or {}).get("status") or ""
        if status in ("ready", "failed"):
            return str(status)
        if attempt % 6 == 0:  # Print every 30 seconds (6 * 5 sec)
            print(f"  Polling... attempt {attempt + 1}/{poll_attempts}, status: {status or 'processing'}")
        time.sleep(poll_delay_sec)
    return "timeout"


def download_snapshot(
    *,
    base_url: str,
    api_key: str,
    snapshot_id: str,
    fmt: str = "json",
) -> Any:
    url = build_url(
        base_url,
        f"/datasets/v3/snapshot/{snapshot_id}",
        {"format": fmt},
    )
    return http_json(url, "GET", api_key, timeout_sec=120)


def load_prompts(path: str) -> List[str]:
    raw = open(path, "r", encoding="utf-8").read().strip()
    if not raw:
        return []
    if path.lower().endswith(".json"):
        obj = json.loads(raw)
        if isinstance(obj, list):
            return [str(x).strip() for x in obj if str(x).strip()]
        if isinstance(obj, dict) and isinstance(obj.get("prompts"), list):
            return [str(x).strip() for x in obj["prompts"] if str(x).strip()]
        return []
    prompts = [line.strip() for line in raw.splitlines() if line.strip()]
    return prompts


def normalize_domain(value: str) -> str:
    v = value.strip().lower()
    v = v.replace("https://", "").replace("http://", "")
    v = v.split("/")[0]
    return v


def classify_domain(domain: str) -> str:
    d = normalize_domain(domain)
    if any(d.endswith(x) for x in ["reddit.com", "quora.com", "medium.com", "stackoverflow.com", "stackexchange.com"]):
        return "ugc"
    if d.endswith("youtube.com") or d.endswith("youtu.be"):
        return "youtube"
    return "web"


def count_mentions(text: str, brand_terms: List[str], target_domains: List[str]) -> int:
    if not text:
        return 0
    hay = text.lower()
    count = 0
    for term in brand_terms:
        t = term.strip().lower()
        if not t:
            continue
        count += len(re.findall(re.escape(t), hay))
    for dom in target_domains:
        d = normalize_domain(dom)
        if not d:
            continue
        count += len(re.findall(re.escape(d), hay))
    return count


def to_sources(record: Dict[str, Any]) -> List[Dict[str, Any]]:
    citations = record.get("citations") or []
    sources = record.get("sources") or []
    combined = []
    if isinstance(citations, list):
        combined.extend([c for c in citations if isinstance(c, dict)])
    if isinstance(sources, list):
        combined.extend([s for s in sources if isinstance(s, dict)])
    out = []
    for item in combined:
        url = item.get("url") if isinstance(item.get("url"), str) else ""
        title = item.get("title") if isinstance(item.get("title"), str) else ""
        domain = item.get("domain") if isinstance(item.get("domain"), str) else ""
        if not domain and url:
            try:
                domain = urllib.parse.urlparse(url).netloc
            except Exception:
                domain = ""
        out.append(
            {
                "title": title or None,
                "url": url or None,
                "domain": normalize_domain(domain) if domain else None,
                "type": classify_domain(domain or url),
            }
        )
    return [x for x in out if x.get("url") or x.get("title")]


def compute_first_citation_rank(sources: List[Dict[str, Any]], target_domains: List[str]) -> Optional[int]:
    targets = [normalize_domain(d) for d in target_domains if normalize_domain(d)]
    for index, source in enumerate(sources):
        dom = normalize_domain(str(source.get("domain") or source.get("url") or ""))
        if not dom:
            continue
        for t in targets:
            if dom == t or dom.endswith(f".{t}"):
                return index + 1
    return None


def compute_used_web_search(record: Dict[str, Any]) -> bool:
    web_search_query = record.get("web_search_query") or []
    if isinstance(web_search_query, list) and len(web_search_query) > 0:
        return True
    if record.get("web_search_triggered") is True:
        return True
    citations = record.get("citations") or []
    if isinstance(citations, list):
        for c in citations:
            if not isinstance(c, dict):
                continue
            url = str(c.get("url") or "")
            if "utm_source=chatgpt.com" in url:
                return True
    return False


def domain_matches_target(domain_or_url: str, target_domains: List[str]) -> Optional[str]:
    current = normalize_domain(domain_or_url)
    if not current:
        return None
    for target in target_domains:
        normalized_target = normalize_domain(target)
        if not normalized_target:
            continue
        if current == normalized_target or current.endswith(f".{normalized_target}"):
            return normalized_target
    return None


def to_search_results(record: Dict[str, Any]) -> List[Dict[str, Any]]:
    search_sources = record.get("search_sources") or []
    if not isinstance(search_sources, list):
        return []

    out: List[Dict[str, Any]] = []
    for item in search_sources:
        if not isinstance(item, dict):
            continue
        url = item.get("url") if isinstance(item.get("url"), str) else ""
        title = item.get("title") if isinstance(item.get("title"), str) else ""
        rank = item.get("rank")
        domain = ""
        if url:
            try:
                domain = urllib.parse.urlparse(url).netloc
            except Exception:
                domain = ""
        out.append(
            {
                "title": title or None,
                "url": url or None,
                "domain": normalize_domain(domain) if domain else None,
                "rank": rank if isinstance(rank, int) else None,
            }
        )

    return [item for item in out if item.get("url") or item.get("title")]


def build_fan_out_details(
    *,
    record: Dict[str, Any],
    target_domains: List[str],
    mentions: int,
    cited: bool,
) -> List[Dict[str, Any]]:
    raw_queries = record.get("web_search_query") or []
    if not isinstance(raw_queries, list):
        return []

    queries = [str(item).strip() for item in raw_queries if str(item).strip()]
    if len(queries) == 0:
        return []

    search_results = to_search_results(record)
    matched_domains = sorted(
        {
            match
            for result in search_results
            for match in [domain_matches_target(str(result.get("domain") or result.get("url") or ""), target_domains)]
            if match
        }
    )

    return [
        {
            "query": query,
            "brand_appeared_in_response": mentions > 0,
            "brand_cited_in_response": cited,
            "brand_found_in_search_results": len(matched_domains) > 0,
            "matched_target_domains": matched_domains,
            "search_results_count": len(search_results),
            "search_results": search_results,
        }
        for query in queries
    ]


def aggregate_fan_out_queries(results: List["PromptResult"]) -> List[Dict[str, Any]]:
    aggregates: Dict[str, Dict[str, Any]] = {}

    for result in results:
        for detail in result.fan_out_details:
            query = str(detail.get("query") or "").strip()
            if not query:
                continue

            key = query.lower()
            entry = aggregates.setdefault(
                key,
                {
                    "query": query,
                    "count": 0,
                    "appeared_in_responses": 0,
                    "not_appeared_in_responses": 0,
                    "cited_in_responses": 0,
                    "found_in_search_results": 0,
                    "prompts": set(),
                    "chatbots": set(),
                    "matched_target_domains": set(),
                },
            )

            entry["count"] += 1
            if detail.get("brand_appeared_in_response"):
                entry["appeared_in_responses"] += 1
            else:
                entry["not_appeared_in_responses"] += 1
            if detail.get("brand_cited_in_response"):
                entry["cited_in_responses"] += 1
            if detail.get("brand_found_in_search_results"):
                entry["found_in_search_results"] += 1

            entry["prompts"].add(result.prompt)
            entry["chatbots"].add(result.chatbot)
            for domain in detail.get("matched_target_domains") or []:
                entry["matched_target_domains"].add(domain)

    summary = []
    for item in aggregates.values():
        summary.append(
            {
                "query": item["query"],
                "count": item["count"],
                "appeared_in_responses": item["appeared_in_responses"],
                "not_appeared_in_responses": item["not_appeared_in_responses"],
                "cited_in_responses": item["cited_in_responses"],
                "found_in_search_results": item["found_in_search_results"],
                "prompts": sorted(item["prompts"]),
                "chatbots": sorted(item["chatbots"]),
                "matched_target_domains": sorted(item["matched_target_domains"]),
            }
        )

    summary.sort(
        key=lambda item: (
            -int(item["count"]),
            -int(item["appeared_in_responses"]),
            str(item["query"]).lower(),
        )
    )
    return summary


@dataclass
class PromptResult:
    chatbot: str
    model: Optional[str]
    prompt: str
    captured_at: str
    answer_text_markdown: str
    mentions: int
    cited: bool
    first_citation_rank: Optional[int]
    citations_count: int
    fan_out_queries: List[str]
    fan_out_details: List[Dict[str, Any]]
    fan_out_count: int
    used_web_search: bool
    sources_count: int
    ugc_sources_count: int
    youtube_sources_count: int
    competitor_domains: List[str]
    brands_mentioned: List[str]
    sources: List[Dict[str, Any]]


def analyze_record(
    chatbot: str,
    record: Dict[str, Any],
    *,
    run_at: str,
    target_domains: List[str],
    brand_terms: List[str],
    competitor_domains: List[str],
) -> PromptResult:
    prompt = str(record.get("prompt") or "").strip()
    markdown = str(record.get("answer_text_markdown") or "")
    sources = to_sources(record)
    first_rank = compute_first_citation_rank(sources, target_domains)
    cited = first_rank is not None
    mentions = count_mentions(markdown, brand_terms, target_domains)
    used_web_search = compute_used_web_search(record)
    fan_out = record.get("web_search_query") or []
    fan_out_count = len(fan_out) if isinstance(fan_out, list) else 0
    citations = record.get("citations") or []
    brands_mentioned = record.get("recommendations") or []
    fan_out_details = build_fan_out_details(
        record=record,
        target_domains=target_domains,
        mentions=mentions,
        cited=cited,
    )

    ugc = sum(1 for s in sources if s.get("type") == "ugc")
    yt = sum(1 for s in sources if s.get("type") == "youtube")

    competitors_found: List[str] = []
    answer_lower = markdown.lower()
    for dom in competitor_domains:
        d = normalize_domain(dom)
        if d and d in answer_lower:
            competitors_found.append(d)
    competitors_found = sorted(set(competitors_found))

    return PromptResult(
        chatbot=chatbot,
        model=str(record.get("model") or "").strip() or None,
        prompt=prompt,
        captured_at=run_at,
        answer_text_markdown=markdown,
        mentions=mentions,
        cited=cited,
        first_citation_rank=first_rank,
        citations_count=len(citations) if isinstance(citations, list) else 0,
        fan_out_queries=[str(item).strip() for item in fan_out if str(item).strip()]
        if isinstance(fan_out, list)
        else [],
        fan_out_details=fan_out_details,
        fan_out_count=fan_out_count,
        used_web_search=used_web_search,
        sources_count=len(sources),
        ugc_sources_count=ugc,
        youtube_sources_count=yt,
        competitor_domains=competitors_found,
        brands_mentioned=[str(item).strip() for item in brands_mentioned if str(item).strip()]
        if isinstance(brands_mentioned, list)
        else [],
        sources=sources,
    )


def clean_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Remove unwanted properties from BrightData response."""
    unwanted_fields = ["source_html", "response_raw", "answer_html", "answer_text"]
    cleaned = {k: v for k, v in record.items() if k not in unwanted_fields}
    return cleaned


def build_inputs(prompts: List[str], check_url: str, country: str, chatbot: str) -> List[Dict[str, Any]]:
    rows = []
    for idx, p in enumerate(prompts):
        base = {"url": check_url, "prompt": p, "country": country, "index": idx + 1}
        if chatbot == "chatgpt":
            rows.append({**base, "additional_prompt": ""})
        else:
            rows.append(base)
    return rows


def write_json(path: str, data: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def read_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def snapshot_meta_path(out_dir: str, chatbot: str) -> str:
    return os.path.join(out_dir, "snapshots", f"{chatbot}.json")


def raw_snapshot_path(out_dir: str, chatbot: str, snapshot_id: str) -> str:
    return os.path.join(out_dir, "raw", f"{chatbot}-{snapshot_id}.json")


def build_results_payload(
    *,
    run_at: str,
    check_url: str,
    target_domains: List[str],
    brand_terms: List[str],
    snapshots: List[Dict[str, str]],
    all_results: List["PromptResult"],
) -> Dict[str, Any]:
    return {
        "schema_version": "geo-audit-v2",
        "run_at": run_at,
        "check_url": check_url,
        "target_domains": target_domains,
        "brand_terms": brand_terms,
        "snapshots": snapshots,
        "manual_recommendations": [],
        "fan_out_summary": aggregate_fan_out_queries(all_results),
        "results": [r.__dict__ for r in all_results],
        "responses": [r.__dict__ for r in all_results],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", default=os.environ.get("BRIGHTDATA_API_KEY", ""), help="Bright Data API key (or BRIGHTDATA_API_KEY)")
    parser.add_argument("--base-url", default=os.environ.get("BRIGHTDATA_API_URL", DEFAULT_BASE_URL))
    parser.add_argument("--check-url", required=True, help="URL to check in the dataset input (often your site or a root page)")
    parser.add_argument("--prompts-file", required=True, help="Text file (one prompt per line) or JSON array")

    parser.add_argument("--chatgpt-dataset-id", default="", help="Bright Data dataset id for ChatGPT")
    parser.add_argument("--perplexity-dataset-id", default="", help="Bright Data dataset id for Perplexity")
    parser.add_argument("--gemini-dataset-id", default="", help="Bright Data dataset id for Gemini")

    parser.add_argument("--country", default="US")
    parser.add_argument("--poll-delay-sec", type=int, default=5)
    parser.add_argument("--poll-attempts", type=int, default=180)  # Increased to 15 minutes (180 * 5 sec)

    parser.add_argument("--target-domains", default="", help="Comma-separated target domains (your site)")
    parser.add_argument("--brand-terms", default="", help="Comma-separated brand terms")
    parser.add_argument("--competitor-domains", default="", help="Comma-separated competitor domains (optional)")

    parser.add_argument("--out-dir", default="geo-audit-run")
    parser.add_argument("--resume-from", default="", help="Resume from an existing dated run directory")
    parser.add_argument("--force", action="store_true", help="Force re-download of raw snapshots when resuming")
    parser.add_argument("--skip-download", action="store_true", help="Only trigger+poll (no snapshot download)")

    args = parser.parse_args()

    api_key = str(args.api_key).strip()
    if not api_key:
        raise SystemExit("Missing BRIGHTDATA_API_KEY (env) or --api-key")

    prompts = load_prompts(args.prompts_file)
    if len(prompts) == 0:
        raise SystemExit("No prompts found in --prompts-file")

    target_domains = [normalize_domain(x) for x in str(args.target_domains).split(",") if normalize_domain(x)]
    brand_terms = [x.strip() for x in str(args.brand_terms).split(",") if x.strip()]
    competitor_domains = [normalize_domain(x) for x in str(args.competitor_domains).split(",") if normalize_domain(x)]

    run_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    resume_from = str(args.resume_from).strip()
    base_out_dir = str(args.out_dir).strip()
    out_dir = resume_from if resume_from else os.path.join(base_out_dir, date_str)
    os.makedirs(out_dir, exist_ok=True)

    jobs: List[Tuple[str, str]] = []
    if args.chatgpt_dataset_id:
        jobs.append(("chatgpt", str(args.chatgpt_dataset_id)))
    if args.perplexity_dataset_id:
        jobs.append(("perplexity", str(args.perplexity_dataset_id)))
    if args.gemini_dataset_id:
        jobs.append(("gemini", str(args.gemini_dataset_id)))

    if not jobs:
        raise SystemExit("No dataset ids provided. Set at least --chatgpt-dataset-id or --perplexity-dataset-id.")

    snapshots: List[Dict[str, str]] = []
    pending_indices: List[int] = []
    for chatbot, dataset_id in jobs:
        meta_path = snapshot_meta_path(out_dir, chatbot)
        existing_snapshot = None
        if resume_from and os.path.exists(meta_path):
            try:
                loaded = read_json(meta_path)
                if isinstance(loaded, dict) and loaded.get("snapshot_id"):
                    existing_snapshot = {
                        "chatbot": chatbot,
                        "dataset_id": str(loaded.get("dataset_id") or dataset_id),
                        "snapshot_id": str(loaded.get("snapshot_id") or ""),
                        "status": str(loaded.get("status") or ""),
                    }
            except Exception:
                existing_snapshot = None

        if existing_snapshot:
            print(
                f"Resuming existing {chatbot} snapshot {existing_snapshot['snapshot_id']} "
                f"({existing_snapshot.get('status') or 'unknown'})"
            )
            snapshots.append(existing_snapshot)
        else:
            print(f"Triggering {chatbot} dataset...")
            inputs = build_inputs(prompts, args.check_url, args.country, chatbot=chatbot)
            custom_fields = get_custom_output_fields(chatbot)
            snapshot_id = trigger_dataset(
                base_url=args.base_url,
                api_key=api_key,
                dataset_id=dataset_id,
                input_rows=inputs,
                custom_output_fields=custom_fields,
            )
            snapshots.append(
                {
                    "chatbot": chatbot,
                    "dataset_id": dataset_id,
                    "snapshot_id": snapshot_id,
                    "status": "triggered",
                }
            )
            write_json(meta_path, snapshots[-1])

        if snapshots[-1]["status"] != "ready":
            pending_indices.append(len(snapshots) - 1)

    if pending_indices:
        print(f"Polling {len(pending_indices)} snapshot(s) together (this may take 1-5 minutes)...")
        for attempt in range(args.poll_attempts):
            next_pending: List[int] = []
            for index in pending_indices:
                snapshot = snapshots[index]
                url = build_url(args.base_url, f"/datasets/v3/progress/{snapshot['snapshot_id']}")
                resp = http_json(url, "GET", api_key, timeout_sec=60)
                status = str((resp or {}).get("status") or "")

                if status in ("ready", "failed"):
                    snapshot["status"] = status
                    print(f"{snapshot['chatbot']} status: {status}")
                    write_json(snapshot_meta_path(out_dir, snapshot["chatbot"]), snapshot)
                else:
                    snapshot["status"] = status or snapshot["status"]
                    next_pending.append(index)

            if not next_pending:
                break

            if attempt % 6 == 0:
                joined = ", ".join(
                    f"{snapshots[index]['chatbot']}={snapshots[index].get('status') or 'processing'}"
                    for index in next_pending
                )
                print(f"  Polling... attempt {attempt + 1}/{args.poll_attempts}, {joined}")

            pending_indices = next_pending
            time.sleep(args.poll_delay_sec)

        for index in pending_indices:
            snapshots[index]["status"] = "timeout"
            print(f"{snapshots[index]['chatbot']} status: timeout")
            write_json(snapshot_meta_path(out_dir, snapshots[index]["chatbot"]), snapshots[index])

    if args.skip_download:
        print(json.dumps({"run_at": run_at, "snapshots": snapshots}, indent=2))
        return

    all_results: List[PromptResult] = []
    for snap in snapshots:
        chatbot = snap["chatbot"]
        snapshot_id = snap["snapshot_id"]
        status = snap["status"]
        if status != "ready":
            continue
        raw_path = raw_snapshot_path(out_dir, chatbot, snapshot_id)

        if os.path.exists(raw_path) and not args.force:
            print(f"Using existing raw snapshot for {chatbot}: {raw_path}")
            raw = read_json(raw_path)
        else:
            raw = download_snapshot(base_url=args.base_url, api_key=api_key, snapshot_id=snapshot_id, fmt="json")

            if isinstance(raw, list):
                cleaned_raw = [clean_record(record) if isinstance(record, dict) else record for record in raw]
            elif isinstance(raw, dict):
                cleaned_raw = clean_record(raw)
            else:
                cleaned_raw = raw

            write_json(raw_path, cleaned_raw)

        if not isinstance(raw, list):
            continue
        for record in raw:
            if not isinstance(record, dict):
                continue
            analyzed = analyze_record(
                chatbot=chatbot,
                record=record,
                run_at=run_at,
                target_domains=target_domains,
                brand_terms=brand_terms,
                competitor_domains=competitor_domains,
            )
            if analyzed.prompt:
                all_results.append(analyzed)

        write_json(
            os.path.join(out_dir, "results.partial.json"),
            build_results_payload(
                run_at=run_at,
                check_url=args.check_url,
                target_domains=target_domains,
                brand_terms=brand_terms,
                snapshots=snapshots,
                all_results=all_results,
            ),
        )

    write_json(
        os.path.join(out_dir, "results.json"),
        build_results_payload(
            run_at=run_at,
            check_url=args.check_url,
            target_domains=target_domains,
            brand_terms=brand_terms,
            snapshots=snapshots,
            all_results=all_results,
        ),
    )

    results_path = os.path.join(out_dir, "results.json")
    print(f"Wrote results to {results_path}")
    print("Note: AI will generate customized HTML report after analyzing results.json")


if __name__ == "__main__":
    main()
