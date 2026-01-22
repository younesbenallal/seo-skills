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
  python geo-state-report/scripts/brightdata-geo.py \
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
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple


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
    for _ in range(poll_attempts):
        url = build_url(base_url, f"/datasets/v3/progress/{snapshot_id}")
        resp = http_json(url, "GET", api_key, timeout_sec=60)
        status = (resp or {}).get("status") or ""
        if status in ("ready", "failed"):
            return str(status)
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


@dataclass
class PromptResult:
    chatbot: str
    prompt: str
    mentions: int
    cited: bool
    first_citation_rank: Optional[int]
    fan_out_count: int
    used_web_search: bool
    sources_count: int
    ugc_sources_count: int
    youtube_sources_count: int
    competitor_domains: List[str]
    sources: List[Dict[str, Any]]


def analyze_record(
    chatbot: str,
    record: Dict[str, Any],
    *,
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
        prompt=prompt,
        mentions=mentions,
        cited=cited,
        first_citation_rank=first_rank,
        fan_out_count=fan_out_count,
        used_web_search=used_web_search,
        sources_count=len(sources),
        ugc_sources_count=ugc,
        youtube_sources_count=yt,
        competitor_domains=competitors_found,
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
            rows.append({**base, "web_search": False, "additional_prompt": ""})
        else:
            rows.append(base)
    return rows


def write_json(path: str, data: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


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
    parser.add_argument("--poll-attempts", type=int, default=90)

    parser.add_argument("--target-domains", default="", help="Comma-separated target domains (your site)")
    parser.add_argument("--brand-terms", default="", help="Comma-separated brand terms")
    parser.add_argument("--competitor-domains", default="", help="Comma-separated competitor domains (optional)")

    parser.add_argument("--out-dir", default="geo-state-run")
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

    run_at = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    base_out_dir = str(args.out_dir).strip()
    out_dir = os.path.join(base_out_dir, date_str)
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
    for chatbot, dataset_id in jobs:
        inputs = build_inputs(prompts, args.check_url, args.country, chatbot=chatbot)
        custom_fields = get_custom_output_fields(chatbot)
        snapshot_id = trigger_dataset(
            base_url=args.base_url,
            api_key=api_key,
            dataset_id=dataset_id,
            input_rows=inputs,
            custom_output_fields=custom_fields,
        )
        status = poll_progress(
            base_url=args.base_url,
            api_key=api_key,
            snapshot_id=snapshot_id,
            poll_delay_sec=args.poll_delay_sec,
            poll_attempts=args.poll_attempts,
        )
        snapshots.append({"chatbot": chatbot, "dataset_id": dataset_id, "snapshot_id": snapshot_id, "status": status})
        write_json(os.path.join(out_dir, "snapshots", f"{chatbot}.json"), snapshots[-1])

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
        raw = download_snapshot(base_url=args.base_url, api_key=api_key, snapshot_id=snapshot_id, fmt="json")
        
        # Clean unwanted fields from raw data before saving
        if isinstance(raw, list):
            cleaned_raw = [clean_record(record) if isinstance(record, dict) else record for record in raw]
        elif isinstance(raw, dict):
            cleaned_raw = clean_record(raw)
        else:
            cleaned_raw = raw
        
        write_json(os.path.join(out_dir, "raw", f"{chatbot}-{snapshot_id}.json"), cleaned_raw)

        if not isinstance(raw, list):
            continue
        for record in raw:
            if not isinstance(record, dict):
                continue
            analyzed = analyze_record(
                chatbot=chatbot,
                record=record,
                target_domains=target_domains,
                brand_terms=brand_terms,
                competitor_domains=competitor_domains,
            )
            if analyzed.prompt:
                all_results.append(analyzed)

    write_json(
        os.path.join(out_dir, "results.json"),
        {
            "run_at": run_at,
            "check_url": args.check_url,
            "target_domains": target_domains,
            "brand_terms": brand_terms,
            "snapshots": snapshots,
            "results": [r.__dict__ for r in all_results],
        },
    )

    results_path = os.path.join(out_dir, "results.json")
    print(f"Wrote results to {results_path}")
    print("Note: AI will generate customized HTML report after analyzing results.json")


if __name__ == "__main__":
    main()
