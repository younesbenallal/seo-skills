#!/usr/bin/env python3
"""
DataForSEO GEO / LLM visibility collector.

This script uses DataForSEO AI Optimization LLM Scraper Live endpoints and
produces the same results.json shape as the Bright Data collector so the
existing HTML renderer and dashboard keep working.

Requirements:
- Python 3.10+
- DATA_FOR_SEO_LOGIN env var (or --login)
- DATA_FOR_SEO_PASSWORD env var (or --password)

Example:
  export DATA_FOR_SEO_LOGIN="..."
  export DATA_FOR_SEO_PASSWORD="..."
  python geo-audit-report/scripts/dataforseo-geo.py \
    --check-url "https://example.com" \
    --prompts-file prompts.txt \
    --chatbots "chatgpt,gemini" \
    --target-domains "example.com" \
    --brand-terms "Example,Example Product" \
    --out-dir ./geo-run
"""

from __future__ import annotations

import argparse
import base64
import csv
import json
import os
import re
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


DEFAULT_BASE_URL = "https://api.dataforseo.com"

CHATBOT_SPECS = {
    "chatgpt": {
        "endpoint": "/v3/ai_optimization/chat_gpt/llm_scraper/live/advanced",
        "mode": "scraper",
    },
    "gemini": {
        "endpoint": "/v3/ai_optimization/gemini/llm_scraper/live/advanced",
        "mode": "scraper",
    },
    "perplexity": {
        "endpoint": "/v3/ai_optimization/perplexity/llm_responses/live",
        "mode": "responses",
    },
}

COUNTRY_TO_LOCATION = {
    "us": "United States",
    "gb": "United Kingdom",
    "uk": "United Kingdom",
    "ca": "Canada",
    "au": "Australia",
    "fr": "France",
    "de": "Germany",
    "es": "Spain",
    "it": "Italy",
    "nl": "Netherlands",
}

LANGUAGE_TO_NAME = {
    "en": "English",
    "fr": "French",
    "de": "German",
    "es": "Spanish",
    "it": "Italian",
    "nl": "Dutch",
}

DEFAULT_LOCATIONS_CSV = os.environ.get("DATA_FOR_SEO_LOCATIONS_CSV", "")


def build_basic_auth(login: str, password: str) -> str:
    raw = f"{login}:{password}".encode("utf-8")
    return base64.b64encode(raw).decode("ascii")


def http_json(
    url: str,
    method: str,
    auth_header: str,
    payload: Optional[Any] = None,
    timeout_sec: int = 180,
) -> Any:
    headers = {
        "Authorization": f"Basic {auth_header}",
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
    return [line.strip() for line in raw.splitlines() if line.strip()]


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
    sources = record.get("sources") or []
    if not isinstance(sources, list):
        return []

    out = []
    for item in sources:
        if not isinstance(item, dict):
            continue
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

    return [item for item in out if item.get("url") or item.get("title")]


def compute_first_citation_rank(sources: List[Dict[str, Any]], target_domains: List[str]) -> Optional[int]:
    targets = [normalize_domain(d) for d in target_domains if normalize_domain(d)]
    for index, source in enumerate(sources):
        dom = normalize_domain(str(source.get("domain") or source.get("url") or ""))
        if not dom:
            continue
        for target in targets:
            if dom == target or dom.endswith(f".{target}"):
                return index + 1
    return None


def compute_used_web_search(record: Dict[str, Any]) -> bool:
    if record.get("web_search_used") is True:
        return True
    fan_out = record.get("fan_out_queries") or []
    if isinstance(fan_out, list) and len(fan_out) > 0:
        return True
    search_results = record.get("search_results") or []
    if isinstance(search_results, list) and len(search_results) > 0:
        return True
    sources = record.get("sources") or []
    return isinstance(sources, list) and len(sources) > 0


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
    raw_results = record.get("search_results") or []
    if not isinstance(raw_results, list):
        return []

    out: List[Dict[str, Any]] = []
    for item in raw_results:
        if not isinstance(item, dict):
            continue
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

    return [item for item in out if item.get("url") or item.get("title")]


def build_fan_out_details(
    *,
    record: Dict[str, Any],
    target_domains: List[str],
    mentions: int,
    cited: bool,
) -> List[Dict[str, Any]]:
    raw_queries = record.get("fan_out_queries") or []
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


def write_json(path: str, data: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def read_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


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


@dataclass
class LocaleTarget:
    location_code: Optional[int]
    location_name: str
    language_code: Optional[str]
    language_name: str
    country_iso_code: str


def extract_brand_entities(record: Dict[str, Any]) -> List[str]:
    brand_entities = record.get("brand_entities") or []
    if not isinstance(brand_entities, list):
        return []
    names = []
    for item in brand_entities:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()
        if title:
            names.append(title)
    return sorted(set(names))


def analyze_record(
    chatbot: str,
    record: Dict[str, Any],
    *,
    prompt: str,
    run_at: str,
    target_domains: List[str],
    brand_terms: List[str],
    competitor_domains: List[str],
) -> PromptResult:
    markdown = str(record.get("markdown") or "")
    sources = to_sources(record)
    first_rank = compute_first_citation_rank(sources, target_domains)
    cited = first_rank is not None
    mentions = count_mentions(markdown, brand_terms, target_domains)
    used_web_search = compute_used_web_search(record)
    fan_out = record.get("fan_out_queries") or []
    fan_out_count = len(fan_out) if isinstance(fan_out, list) else 0
    fan_out_details = build_fan_out_details(
        record=record,
        target_domains=target_domains,
        mentions=mentions,
        cited=cited,
    )

    ugc = sum(1 for source in sources if source.get("type") == "ugc")
    yt = sum(1 for source in sources if source.get("type") == "youtube")

    competitors_found: List[str] = []
    answer_lower = markdown.lower()
    for dom in competitor_domains:
        normalized = normalize_domain(dom)
        if normalized and normalized in answer_lower:
            competitors_found.append(normalized)

    return PromptResult(
        chatbot=chatbot,
        model=str(record.get("model") or "").strip() or None,
        prompt=prompt,
        captured_at=str(record.get("datetime") or run_at),
        answer_text_markdown=markdown,
        mentions=mentions,
        cited=cited,
        first_citation_rank=first_rank,
        citations_count=len(sources),
        fan_out_queries=[str(item).strip() for item in fan_out if str(item).strip()]
        if isinstance(fan_out, list)
        else [],
        fan_out_details=fan_out_details,
        fan_out_count=fan_out_count,
        used_web_search=used_web_search,
        sources_count=len(sources),
        ugc_sources_count=ugc,
        youtube_sources_count=yt,
        competitor_domains=sorted(set(competitors_found)),
        brands_mentioned=extract_brand_entities(record),
        sources=sources,
    )


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
        "provider": "dataforseo",
        "provider_method": "ai_optimization_live",
        "run_at": run_at,
        "check_url": check_url,
        "target_domains": target_domains,
        "brand_terms": brand_terms,
        "snapshots": snapshots,
        "manual_recommendations": [],
        "fan_out_summary": aggregate_fan_out_queries(all_results),
        "results": [result.__dict__ for result in all_results],
        "responses": [result.__dict__ for result in all_results],
    }


def load_csv_rows(path: str) -> List[Dict[str, str]]:
    with open(path, "r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [row for row in reader if isinstance(row, dict)]


def looks_like_language_code(value: str) -> bool:
    return bool(re.fullmatch(r"[a-z]{2,3}(?:-[a-z]{2})?", value.strip().lower()))


def resolve_locale_from_csv(
    csv_path: str,
    country: str,
    language: str,
    location_name: str,
    language_name: str,
) -> Optional[LocaleTarget]:
    if not csv_path or not os.path.exists(csv_path):
        return None

    rows = load_csv_rows(csv_path)
    country_value = country.strip()
    language_value = language.strip()
    explicit_location_name = location_name.strip().lower()
    explicit_language_name = language_name.strip().lower()

    for row in rows:
        row_country = str(row.get("country_iso_code") or "").strip().lower()
        row_language_code = str(row.get("language_code") or "").strip().lower()
        row_location_name = str(row.get("location_name") or "").strip().lower()
        row_language_name = str(row.get("language_name") or "").strip().lower()

        country_matches = False
        if explicit_location_name:
            country_matches = row_location_name == explicit_location_name
        elif country_value:
            country_matches = (
                row_country == country_value.lower()
                if len(country_value) == 2
                else row_location_name == country_value.lower()
            )

        language_matches = False
        if explicit_language_name:
            language_matches = row_language_name == explicit_language_name
        elif language_value:
            language_matches = (
                row_language_code == language_value.lower()
                if looks_like_language_code(language_value)
                else row_language_name == language_value.lower()
            )

        if not country_matches or not language_matches:
            continue

        location_code_text = str(row.get("location_code") or "").strip()
        return LocaleTarget(
            location_code=int(location_code_text) if location_code_text.isdigit() else None,
            location_name=str(row.get("location_name") or "").strip() or country_value or "United States",
            language_code=str(row.get("language_code") or "").strip() or None,
            language_name=str(row.get("language_name") or "").strip() or language_value or "English",
            country_iso_code=str(row.get("country_iso_code") or "").strip().upper(),
        )

    return None


def build_locale_target(
    country: str,
    language: str,
    location_name: str,
    language_name: str,
    csv_path: str,
) -> LocaleTarget:
    resolved = resolve_locale_from_csv(csv_path, country, language, location_name, language_name)
    if resolved:
        return resolved

    country_value = country.strip()
    language_value = language.strip()
    fallback_location_name = (
        location_name.strip()
        or (
            COUNTRY_TO_LOCATION.get(country_value.lower(), "United States")
            if len(country_value) == 2
            else country_value
        )
        or "United States"
    )
    fallback_language_name = (
        language_name.strip()
        or (
            LANGUAGE_TO_NAME.get(language_value.lower(), "English")
            if looks_like_language_code(language_value)
            else language_value
        )
        or "English"
    )
    fallback_country_code = country.strip().upper() if len(country.strip()) == 2 else ""
    fallback_language_code = language.strip().lower() if looks_like_language_code(language) else None
    return LocaleTarget(
        location_code=None,
        location_name=fallback_location_name,
        language_code=fallback_language_code,
        language_name=fallback_language_name,
        country_iso_code=fallback_country_code,
    )


def parse_chatbots(value: str) -> List[str]:
    requested = []
    for item in value.split(","):
        chatbot = item.strip().lower()
        if not chatbot:
            continue
        if chatbot not in CHATBOT_SPECS:
            raise SystemExit(f"Unsupported DataForSEO chatbot '{chatbot}'. Supported: chatgpt, gemini, perplexity")
        requested.append(chatbot)
    return requested


def to_annotation_sources(annotations: Any) -> List[Dict[str, Any]]:
    if not isinstance(annotations, list):
        return []

    out = []
    for item in annotations:
        if not isinstance(item, dict):
            continue
        url = item.get("url") if isinstance(item.get("url"), str) else ""
        title = item.get("title") if isinstance(item.get("title"), str) else ""
        domain = ""
        if url:
            try:
                domain = urllib.parse.urlparse(url).netloc
            except Exception:
                domain = ""
        if not domain and "." in title:
            domain = title
        out.append(
            {
                "title": title or None,
                "url": url or None,
                "domain": normalize_domain(domain) if domain else None,
                "type": classify_domain(domain or url),
            }
        )

    deduped: List[Dict[str, Any]] = []
    seen = set()
    for item in out:
        key = (item.get("url"), item.get("title"))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return [item for item in deduped if item.get("url") or item.get("title")]


def normalize_responses_record(result_record: Dict[str, Any]) -> Dict[str, Any]:
    items = result_record.get("items") or []
    text_parts: List[str] = []
    collected_sources: List[Dict[str, Any]] = []

    if isinstance(items, list):
        for item in items:
            if not isinstance(item, dict):
                continue
            if str(item.get("type") or "") != "message":
                continue
            message = item.get("message") or {}
            if not isinstance(message, dict):
                continue
            sections = message.get("sections") or []
            if not isinstance(sections, list):
                continue
            for section in sections:
                if not isinstance(section, dict):
                    continue
                if str(section.get("type") or "") != "text":
                    continue
                text = str(section.get("text") or "").strip()
                if text:
                    text_parts.append(text)
                collected_sources.extend(to_annotation_sources(section.get("annotations")))

    fan_out = result_record.get("fan_out_queries") or []
    normalized = {
        "markdown": "\n\n".join(text_parts).strip(),
        "sources": collected_sources,
        "fan_out_queries": fan_out if isinstance(fan_out, list) else [],
        "datetime": result_record.get("datetime"),
        "model": str(result_record.get("model_name") or result_record.get("model") or "").strip() or None,
        "web_search_used": bool(result_record.get("web_search")),
    }
    return normalized


def post_prompt(
    *,
    base_url: str,
    auth_header: str,
    chatbot: str,
    prompt: str,
    locale: LocaleTarget,
    force_web_search: bool,
    tag: str,
    perplexity_model: str,
) -> Dict[str, Any]:
    spec = CHATBOT_SPECS[chatbot]
    endpoint = str(spec["endpoint"])
    mode = str(spec["mode"])
    if mode == "scraper":
        payload = [
            {
                "keyword": prompt,
                **({"location_code": locale.location_code} if locale.location_code is not None else {"location_name": locale.location_name}),
                **({"language_code": locale.language_code} if locale.language_code else {"language_name": locale.language_name}),
                "tag": tag,
                **({"force_web_search": True} if chatbot == "chatgpt" and force_web_search else {}),
            }
        ]
    else:
        payload = [
            {
                "user_prompt": prompt,
                "model_name": perplexity_model,
                "tag": tag,
                **({"web_search_country_iso_code": locale.country_iso_code} if locale.country_iso_code else {}),
            }
        ]

    response = http_json(f"{base_url.rstrip('/')}{endpoint}", "POST", auth_header, payload=payload, timeout_sec=180)
    if not isinstance(response, dict):
        raise RuntimeError(f"Unexpected DataForSEO response for {chatbot}: {response}")

    status_code = int(response.get("status_code") or 0)
    if status_code != 20000:
        raise RuntimeError(f"DataForSEO request failed for {chatbot}: {response.get('status_message') or response}")

    tasks = response.get("tasks") or []
    if not isinstance(tasks, list) or len(tasks) == 0 or not isinstance(tasks[0], dict):
        raise RuntimeError(f"DataForSEO returned no tasks for {chatbot}: {response}")

    task = tasks[0]
    task_status = int(task.get("status_code") or 0)
    if task_status != 20000:
        raise RuntimeError(f"DataForSEO task failed for {chatbot}: {task.get('status_message') or task}")

    results = task.get("result") or []
    if not isinstance(results, list) or len(results) == 0 or not isinstance(results[0], dict):
        raise RuntimeError(f"DataForSEO returned no result rows for {chatbot}: {task}")

    raw_result = results[0]
    normalized_result = raw_result if mode == "scraper" else normalize_responses_record(raw_result)

    return {
        "task_id": str(task.get("id") or ""),
        "status": "ready",
        "cost": task.get("cost"),
        "result": normalized_result,
        "raw_result": raw_result,
        "request_data": task.get("data") if isinstance(task.get("data"), dict) else {},
        "response_path": task.get("path") if isinstance(task.get("path"), list) else [],
        "mode": mode,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--login",
        default=os.environ.get("DATA_FOR_SEO_LOGIN", os.environ.get("DATAFORSEO_LOGIN", "")),
        help="DataForSEO login (or DATA_FOR_SEO_LOGIN)",
    )
    parser.add_argument(
        "--password",
        default=os.environ.get("DATA_FOR_SEO_PASSWORD", os.environ.get("DATAFORSEO_PASSWORD", "")),
        help="DataForSEO password (or DATA_FOR_SEO_PASSWORD)",
    )
    parser.add_argument("--base-url", default=os.environ.get("DATA_FOR_SEO_API_URL", DEFAULT_BASE_URL))
    parser.add_argument("--check-url", required=True, help="Audit target URL, stored in results.json for report context")
    parser.add_argument("--prompts-file", required=True, help="Text file (one prompt per line) or JSON array")
    parser.add_argument("--chatbots", default="chatgpt,gemini", help="Comma-separated list: chatgpt,gemini,perplexity")
    parser.add_argument("--country", default="US", help="Country code or full location name, e.g. US or United States")
    parser.add_argument("--language", default="en", help="Language code or full language name, e.g. en or English")
    parser.add_argument("--location-name", default="", help="Explicit DataForSEO location_name override")
    parser.add_argument("--language-name", default="", help="Explicit DataForSEO language_name override")
    parser.add_argument("--locations-csv", default=DEFAULT_LOCATIONS_CSV, help="Optional DataForSEO locations/languages CSV export")
    parser.add_argument("--target-domains", default="", help="Comma-separated target domains (your site)")
    parser.add_argument("--brand-terms", default="", help="Comma-separated brand terms")
    parser.add_argument("--competitor-domains", default="", help="Comma-separated competitor domains (optional)")
    parser.add_argument("--out-dir", default="geo-audit-run")
    parser.add_argument("--resume-from", default="", help="Resume from an existing dated run directory")
    parser.add_argument("--force", action="store_true", help="Re-run prompts even if raw results exist in the dated folder")
    parser.add_argument("--force-web-search", action="store_true", help="Only for ChatGPT. Forces web search, which is less faithful to natural behavior.")
    parser.add_argument("--delay-ms", type=int, default=250, help="Delay between live calls to avoid bursty traffic")
    parser.add_argument("--perplexity-model", default="sonar", help="DataForSEO Perplexity model_name for LLM Responses live")
    args = parser.parse_args()

    login = str(args.login).strip()
    password = str(args.password).strip()
    if not login or not password:
        raise SystemExit("Missing DATA_FOR_SEO_LOGIN/DATA_FOR_SEO_PASSWORD (env) or --login/--password")

    prompts = load_prompts(args.prompts_file)
    if len(prompts) == 0:
        raise SystemExit("No prompts found in --prompts-file")

    requested_chatbots = parse_chatbots(str(args.chatbots))
    target_domains = [normalize_domain(x) for x in str(args.target_domains).split(",") if normalize_domain(x)]
    brand_terms = [x.strip() for x in str(args.brand_terms).split(",") if x.strip()]
    competitor_domains = [normalize_domain(x) for x in str(args.competitor_domains).split(",") if normalize_domain(x)]
    locale = build_locale_target(
        str(args.country),
        str(args.language),
        str(args.location_name),
        str(args.language_name),
        str(args.locations_csv).strip(),
    )

    run_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    resume_from = str(args.resume_from).strip()
    base_out_dir = str(args.out_dir).strip()
    out_dir = resume_from if resume_from else os.path.join(base_out_dir, date_str)
    raw_dir = os.path.join(out_dir, "raw")
    os.makedirs(raw_dir, exist_ok=True)

    auth_header = build_basic_auth(login, password)
    snapshots: List[Dict[str, str]] = []
    all_results: List[PromptResult] = []

    for chatbot in requested_chatbots:
        for prompt_index, prompt in enumerate(prompts, start=1):
            prompt_slug = re.sub(r"[^a-z0-9]+", "-", prompt.lower()).strip("-")[:48] or f"prompt-{prompt_index}"
            raw_path = os.path.join(raw_dir, f"{chatbot}-{prompt_index:02d}-{prompt_slug}.json")

            if resume_from and os.path.exists(raw_path) and not args.force:
                raw_payload = read_json(raw_path)
            else:
                tag = f"geo-audit:{chatbot}:{prompt_index}"
                print(f"Fetching {chatbot} prompt {prompt_index}/{len(prompts)}...")
                raw_payload = post_prompt(
                    base_url=str(args.base_url),
                    auth_header=auth_header,
                    chatbot=chatbot,
                    prompt=prompt,
                    locale=locale,
                    force_web_search=bool(args.force_web_search),
                    tag=tag,
                    perplexity_model=str(args.perplexity_model).strip() or "sonar",
                )
                write_json(raw_path, raw_payload)
                if args.delay_ms > 0:
                    time.sleep(args.delay_ms / 1000)

            result_record = raw_payload.get("result") if isinstance(raw_payload, dict) else None
            if not isinstance(result_record, dict):
                continue

            task_id = str(raw_payload.get("task_id") or "")
            snapshots.append(
                {
                    "chatbot": chatbot,
                    "status": str(raw_payload.get("status") or "ready"),
                    "task_id": task_id,
                    "mode": str(raw_payload.get("mode") or ""),
                }
            )

            analyzed = analyze_record(
                chatbot=chatbot,
                record=result_record,
                prompt=prompt,
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
    print(
        "Next: render the standalone HTML report with "
        f"'node geo-audit-report/scripts/render-report.mjs --in {results_path}'"
    )


if __name__ == "__main__":
    main()
