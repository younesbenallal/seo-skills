#!/usr/bin/env python3
"""
Bright Data GEO / LLM visibility collector.

This script uses Bright Data's synchronous endpoint for runs of up to 20
prompts, with automatic fallback to the snapshot workflow when Bright Data
returns a snapshot_id. Larger runs use the snapshot workflow directly.

Note: Render the static HTML report from results.json with
`node geo-audit-report/scripts/render-report.mjs --in <results.json>`.

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

EVIDENCE_STATES = {"supported", "missing", "inferred", "malformed"}


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
    "prompt_sent_at",
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

KNOWN_PROVIDER_FIELDS = set(
    CHATGPT_OUTPUT_FIELDS
    + PERPLEXITY_OUTPUT_FIELDS
    + GEMINI_OUTPUT_FIELDS
    + ["answer_text", "source_html", "response_raw", "answer_html", "web_search"]
)


def coerce_bool(value: Any) -> Tuple[Optional[bool], bool]:
    if isinstance(value, bool):
        return value, False
    if value in (0, 1) and not isinstance(value, bool):
        return bool(value), True
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes"}:
            return True, True
        if normalized in {"false", "0", "no"}:
            return False, True
    return None, False


def coerce_number(value: Any) -> Tuple[Optional[float], bool]:
    if isinstance(value, bool):
        return None, False
    if isinstance(value, (int, float)):
        return float(value), False
    if isinstance(value, str):
        try:
            return float(value.strip()), True
        except ValueError:
            pass
    return None, False


def coerce_integer(value: Any) -> Tuple[Optional[int], bool]:
    number, coerced = coerce_number(value)
    if number is None or not number.is_integer():
        return None, False
    return int(number), coerced


def read_list_field(
    record: Dict[str, Any],
    field: str,
    warnings: List[Dict[str, Any]],
) -> Tuple[List[Any], str]:
    if field not in record or record.get(field) is None:
        return [], "missing"
    value = record.get(field)
    if isinstance(value, list):
        return value, "supported"
    if isinstance(value, dict):
        warnings.append(
            {
                "code": "singleton_object_coerced_to_array",
                "field": field,
                "message": f"{field} was an object and was safely wrapped in an array.",
            }
        )
        return [value], "inferred"
    warnings.append(
        {
            "code": "malformed_array",
            "field": field,
            "message": f"{field} was {type(value).__name__}; expected an array.",
        }
    )
    return [], "malformed"


def evidence_state(
    state: str,
    *,
    records: int,
    note: Optional[str] = None,
) -> Dict[str, Any]:
    if state not in EVIDENCE_STATES:
        state = "malformed"
    return {"state": state, "records": records, "note": note}


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


def scrape_dataset(
    *,
    base_url: str,
    api_key: str,
    dataset_id: str,
    input_rows: List[Dict[str, Any]],
    custom_output_fields: str,
) -> Any:
    url = build_url(
        base_url,
        "/datasets/v3/scrape",
        {
            "dataset_id": dataset_id,
            "custom_output_fields": custom_output_fields,
            "include_errors": "true",
            "format": "json",
        },
    )
    return http_json(url, "POST", api_key, payload=input_rows, timeout_sec=120)


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


def canonical_domain(url: str, fallback: str = "") -> str:
    if url:
        try:
            hostname = urllib.parse.urlparse(url).hostname or ""
            if hostname:
                return normalize_domain(hostname.removeprefix("www."))
        except Exception:
            pass
    fallback_domain = normalize_domain(fallback)
    return fallback_domain if "." in fallback_domain else ""


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


def normalize_source(
    item: Dict[str, Any],
    *,
    source_kind: str,
    warnings: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    warnings = warnings if warnings is not None else []
    url = item.get("url") if isinstance(item.get("url"), str) else ""
    title = item.get("title") if isinstance(item.get("title"), str) else ""
    display_domain = item.get("domain") if isinstance(item.get("domain"), str) else ""
    domain = canonical_domain(url, display_domain)
    position, position_coerced = coerce_integer(item.get("position"))
    answer_position, answer_position_coerced = coerce_integer(item.get("answer_position"))
    rank, rank_coerced = coerce_integer(item.get("rank"))
    cited, cited_coerced = coerce_bool(item.get("cited"))
    for field, was_coerced in [
        ("position", position_coerced),
        ("answer_position", answer_position_coerced),
        ("rank", rank_coerced),
        ("cited", cited_coerced),
    ]:
        if was_coerced:
            warnings.append(
                {
                    "code": "safe_scalar_coercion",
                    "field": field,
                    "message": f"{field} was safely coerced to its canonical type.",
                }
            )
    for field, normalized in [
        ("position", position),
        ("answer_position", answer_position),
        ("rank", rank),
    ]:
        if item.get(field) is not None and normalized is None:
            warnings.append(
                {
                    "code": "malformed_number",
                    "field": field,
                    "message": f"{field} was present but not a usable integer.",
                }
            )
    return {
        "title": title or None,
        "url": url or None,
        "domain": domain or None,
        "display_domain": display_domain or None,
        "type": classify_domain(domain or url),
        "source_kind": source_kind,
        "cited": cited,
        "position": position if position is not None else rank,
        "answer_position": answer_position,
        "description": item.get("description") or item.get("snippet") or None,
        "date_published": item.get("date_published") or None,
    }


def normalize_source_list(
    record: Dict[str, Any],
    field: str,
    *,
    source_kind: str,
    warnings: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[List[Dict[str, Any]], str]:
    warnings = warnings if warnings is not None else []
    items, state = read_list_field(record, field, warnings)
    out = []
    for item in items:
        if isinstance(item, dict):
            normalized = normalize_source(item, source_kind=source_kind, warnings=warnings)
            if normalized.get("url") or normalized.get("title"):
                out.append(normalized)
            else:
                warnings.append(
                    {
                        "code": "empty_evidence_item",
                        "field": field,
                        "message": f"Ignored a {field} item without a usable URL or title.",
                    }
                )
                state = "malformed"
        else:
            warnings.append(
                {
                    "code": "malformed_array_item",
                    "field": field,
                    "message": f"Ignored a non-object item in {field}.",
                }
            )
            state = "malformed"
    return out, state


def split_citations(
    record: Dict[str, Any],
    warnings: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], str, str]:
    warnings = warnings if warnings is not None else []
    candidates, candidates_state = normalize_source_list(
        record,
        "citations",
        source_kind="citation_candidate",
        warnings=warnings,
    )
    cited_values = [item.get("cited") for item in candidates]
    raw_items = record.get("citations") if isinstance(record.get("citations"), list) else []
    malformed_flags = any(
        isinstance(item, dict)
        and item.get("cited") is not None
        and coerce_bool(item.get("cited"))[0] is None
        for item in raw_items
    )
    if candidates_state in {"missing", "malformed"}:
        actual_state = candidates_state
    elif malformed_flags:
        actual_state = "malformed"
        warnings.append(
            {
                "code": "citation_flags_malformed",
                "field": "citations.cited",
                "message": "Some cited flags were unusable; only explicit true values count.",
            }
        )
    elif candidates and all(value is None for value in cited_values):
        actual_state = "missing"
        warnings.append(
            {
                "code": "citation_flags_missing",
                "field": "citations.cited",
                "message": "Citation candidates were captured, but actual citation status is unknown.",
            }
        )
    elif any(value is None for value in cited_values):
        actual_state = "malformed"
        warnings.append(
            {
                "code": "citation_flags_partial",
                "field": "citations.cited",
                "message": "Some citation candidates lacked a usable cited flag; only explicit true values count.",
            }
        )
    else:
        actual_state = "inferred" if candidates_state == "inferred" else "supported"
    actual = [item for item in candidates if item.get("cited") is True]
    return actual, candidates, actual_state, candidates_state


def normalize_attached_links(
    record: Dict[str, Any],
    warnings: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[List[Dict[str, Any]], str]:
    warnings = warnings if warnings is not None else []
    items, state = read_list_field(record, "links_attached", warnings)
    out = []
    for item in items:
        if not isinstance(item, dict):
            warnings.append(
                {
                    "code": "malformed_array_item",
                    "field": "links_attached",
                    "message": "Ignored a non-object attached link.",
                }
            )
            state = "malformed"
            continue
        url = item.get("url") if isinstance(item.get("url"), str) else ""
        text = item.get("text") if isinstance(item.get("text"), str) else ""
        position, coerced = coerce_integer(item.get("position"))
        if coerced:
            warnings.append(
                {
                    "code": "safe_scalar_coercion",
                    "field": "links_attached.position",
                    "message": "Attached-link position was safely coerced to a number.",
                }
            )
        if item.get("position") is not None and position is None:
            warnings.append(
                {
                    "code": "malformed_number",
                    "field": "links_attached.position",
                    "message": "Attached-link position was not a usable integer.",
                }
            )
        out.append(
            {
                "text": text or None,
                "url": url or None,
                "domain": canonical_domain(url) or None,
                "position": position,
            }
        )
        if not url and not text:
            out.pop()
            warnings.append(
                {
                    "code": "empty_evidence_item",
                    "field": "links_attached",
                    "message": "Ignored an attached link without a usable URL or label.",
                }
            )
            state = "malformed"
    return out, state


def normalize_map_results(
    record: Dict[str, Any],
    warnings: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[List[Dict[str, Any]], str]:
    warnings = warnings if warnings is not None else []
    items, state = read_list_field(record, "map", warnings)
    out = []
    for item in items:
        if not isinstance(item, dict):
            warnings.append(
                {
                    "code": "malformed_array_item",
                    "field": "map",
                    "message": "Ignored a non-object map result.",
                }
            )
            state = "malformed"
            continue
        website_url = item.get("website_url") if isinstance(item.get("website_url"), str) else ""
        rating, rating_coerced = coerce_number(item.get("rating"))
        review_count, reviews_coerced = coerce_integer(item.get("review_count"))
        position, position_coerced = coerce_integer(item.get("position"))
        for field, was_coerced in [
            ("map.rating", rating_coerced),
            ("map.review_count", reviews_coerced),
            ("map.position", position_coerced),
        ]:
            if was_coerced:
                warnings.append(
                    {
                        "code": "safe_scalar_coercion",
                        "field": field,
                        "message": f"{field} was safely coerced to a number.",
                    }
                )
        for field, raw_value, normalized in [
            ("map.rating", item.get("rating"), rating),
            ("map.review_count", item.get("review_count"), review_count),
            ("map.position", item.get("position"), position),
        ]:
            if raw_value is not None and normalized is None:
                warnings.append(
                    {
                        "code": "malformed_number",
                        "field": field,
                        "message": f"{field} was present but not a usable number.",
                    }
                )
        name = str(item.get("name") or "").strip()
        out.append(
            {
                "name": name or None,
                "category": str(item.get("category") or "").strip() or None,
                "rating": rating,
                "review_count": review_count,
                "website_url": website_url or None,
                "domain": canonical_domain(website_url) or None,
                "position": position,
                "phone_number": item.get("phone_number") or None,
                "directions_url": item.get("directions_url") or None,
                "description": item.get("description") or None,
            }
        )
        if not name and not website_url:
            out.pop()
            warnings.append(
                {
                    "code": "empty_evidence_item",
                    "field": "map",
                    "message": "Ignored a map result without a usable name or website.",
                }
            )
            state = "malformed"
    return out, state


def clean_answer_markdown(value: Any) -> str:
    markdown = str(value or "").replace("\r\n", "\n").strip()
    leading_boilerplate = r"^(?:#{1,6}\s*)?Give feedback\s*\n+"
    trailing_boilerplate = (
        r"\n*(?:#{1,6}\s*)?Give feedback\s*"
        r"(?:\n+(?:Good response|Bad response|Copy|Regenerate)[^\n]*)*\s*$"
    )
    markdown = re.sub(leading_boilerplate, "", markdown, flags=re.IGNORECASE)
    return re.sub(trailing_boilerplate, "", markdown, flags=re.IGNORECASE).strip()


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


def compute_used_web_search(
    record: Dict[str, Any],
    warnings: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[Optional[bool], str]:
    warnings = warnings if warnings is not None else []
    if "web_search_triggered" not in record or record.get("web_search_triggered") is None:
        return None, "missing"
    triggered, coerced = coerce_bool(record.get("web_search_triggered"))
    if triggered is None:
        warnings.append(
            {
                "code": "malformed_boolean",
                "field": "web_search_triggered",
                "message": "web_search_triggered was present but not a recognizable boolean.",
            }
        )
        return None, "malformed"
    if coerced:
        warnings.append(
            {
                "code": "safe_scalar_coercion",
                "field": "web_search_triggered",
                "message": "web_search_triggered was safely coerced to a boolean.",
            }
        )
    return triggered, "inferred" if coerced else "supported"


def legacy_used_web_search(record: Dict[str, Any]) -> bool:
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


def to_search_results(
    record: Dict[str, Any],
    warnings: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[List[Dict[str, Any]], str]:
    return normalize_source_list(
        record,
        "search_sources",
        source_kind="search_source",
        warnings=warnings,
    )


def entity_name(source: Dict[str, Any]) -> str:
    display = str(source.get("display_domain") or "").strip()
    if display and "." not in display:
        return display
    title = str(source.get("title") or "").strip()
    if title:
        return re.split(r"\s[-–—|:]\s", title, maxsplit=1)[0].strip()
    return str(source.get("domain") or "").strip()


def build_competitor_entities(
    *,
    markdown: str,
    actual_citations: List[Dict[str, Any]],
    citation_candidates: List[Dict[str, Any]],
    search_sources: List[Dict[str, Any]],
    attached_links: List[Dict[str, Any]],
    map_results: List[Dict[str, Any]],
    target_domains: List[str],
    brand_terms: List[str],
) -> List[Dict[str, Any]]:
    entities: Dict[str, Dict[str, Any]] = {}
    targets = {normalize_domain(item) for item in target_domains}
    target_terms = {item.strip().lower() for item in brand_terms if item.strip()}
    answer_lower = markdown.lower()
    compact_answer = re.sub(r"[^a-z0-9]+", "", answer_lower)

    def add(name: str, domain: str, channel: str) -> None:
        clean_name = name.strip()
        clean_domain = canonical_domain("", domain)
        if not clean_name and not clean_domain:
            return
        if clean_domain in targets or clean_name.lower() in target_terms:
            return
        key = clean_domain or clean_name.lower()
        current = entities.setdefault(
            key,
            {"name": clean_name or clean_domain, "domain": clean_domain or None, "channels": set()},
        )
        current["channels"].add(channel)

    for source in citation_candidates:
        name = entity_name(source)
        domain = str(source.get("domain") or "")
        compact_name = re.sub(r"[^a-z0-9]+", "", name.lower())
        if name and (
            name.lower() in answer_lower
            or (len(compact_name) >= 5 and compact_name in compact_answer)
        ):
            add(name, domain, "answer")
        add(name, domain, "citation" if source in actual_citations else "citation_candidate")
    for source in search_sources:
        add(entity_name(source), str(source.get("domain") or ""), "search")
    for link in attached_links:
        name = str(link.get("text") or link.get("domain") or "")
        add(name, str(link.get("domain") or ""), "attached_link")
    for placement in map_results:
        add(str(placement.get("name") or ""), str(placement.get("domain") or ""), "map")

    return [
        {**item, "channels": sorted(item["channels"])}
        for item in sorted(entities.values(), key=lambda item: str(item["name"]).lower())
    ]


def build_fan_out_details(
    *,
    queries: List[str],
    target_domains: List[str],
    mentions: int,
    cited: bool,
    search_results: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    if len(queries) == 0:
        return []

    search_results = search_results or []
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
    used_web_search: Optional[bool]
    sources_count: int
    ugc_sources_count: int
    youtube_sources_count: int
    competitor_domains: List[str]
    brands_mentioned: List[str]
    sources: List[Dict[str, Any]]
    actual_citations: List[Dict[str, Any]]
    citation_candidates: List[Dict[str, Any]]
    uncited_citation_candidates: List[Dict[str, Any]]
    search_sources: List[Dict[str, Any]]
    attached_links: List[Dict[str, Any]]
    map_results: List[Dict[str, Any]]
    target_found_in_search: bool
    target_found_in_maps: bool
    competitor_entities: List[Dict[str, Any]]
    provider_metadata: Dict[str, Any]
    evidence_status: Dict[str, Dict[str, Any]]
    normalization: Dict[str, Any]


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
    warnings: List[Dict[str, Any]] = []
    markdown_value = record.get("answer_text_markdown")
    if markdown_value is None:
        markdown_value = record.get("answer_text")
    answer_state = "supported" if isinstance(markdown_value, str) else "missing"
    if markdown_value is not None and not isinstance(markdown_value, str):
        answer_state = "inferred"
        warnings.append(
            {
                "code": "safe_scalar_coercion",
                "field": "answer_text_markdown",
                "message": "Answer text was safely coerced to a string.",
            }
        )
    markdown = clean_answer_markdown(markdown_value)
    actual_citations, citation_candidates, actual_citations_state, candidates_state = split_citations(
        record,
        warnings,
    )
    uncited_candidates = [item for item in citation_candidates if item.get("cited") is False]
    search_sources, search_sources_state = to_search_results(record, warnings)
    attached_links, attached_links_state = normalize_attached_links(record, warnings)
    map_results, maps_state = normalize_map_results(record, warnings)
    first_rank = compute_first_citation_rank(actual_citations, target_domains)
    cited = first_rank is not None
    mentions = count_mentions(markdown, brand_terms, target_domains)
    used_web_search, web_search_state = compute_used_web_search(record, warnings)
    raw_fan_out, fan_out_state = read_list_field(record, "web_search_query", warnings)
    fan_out = []
    for item in raw_fan_out:
        if isinstance(item, str) and item.strip():
            fan_out.append(item.strip())
            continue
        warnings.append(
            {
                "code": "malformed_array_item",
                "field": "web_search_query",
                "message": "Ignored a fan-out query that was not a non-empty string.",
            }
        )
        fan_out_state = "malformed"
    fan_out_count = len(fan_out)
    target_found_in_search = any(
        domain_matches_target(str(item.get("domain") or item.get("url") or ""), target_domains)
        for item in search_sources
    )
    target_found_in_maps = any(
        domain_matches_target(str(item.get("domain") or item.get("website_url") or ""), target_domains)
        for item in map_results
    )
    brands_mentioned = record.get("recommendations") or []
    fan_out_details = build_fan_out_details(
        queries=fan_out,
        target_domains=target_domains,
        mentions=mentions,
        cited=cited,
        search_results=search_sources,
    )

    metadata_booleans = {}
    for field in ["is_map", "shopping_visible"]:
        raw_value = record.get(field)
        if raw_value is None:
            metadata_booleans[field] = None
            continue
        normalized, coerced = coerce_bool(raw_value)
        metadata_booleans[field] = normalized
        if normalized is None:
            warnings.append(
                {
                    "code": "malformed_boolean",
                    "field": field,
                    "message": f"{field} was present but not a recognizable boolean.",
                }
            )
        elif coerced:
            warnings.append(
                {
                    "code": "safe_scalar_coercion",
                    "field": field,
                    "message": f"{field} was safely coerced to a boolean.",
                }
            )

    ugc = sum(1 for s in actual_citations if s.get("type") == "ugc")
    yt = sum(1 for s in actual_citations if s.get("type") == "youtube")

    competitors_found: List[str] = []
    answer_lower = markdown.lower()
    for dom in competitor_domains:
        d = normalize_domain(dom)
        if d and d in answer_lower:
            competitors_found.append(d)
    competitors_found = sorted(set(competitors_found))
    competitor_entities = build_competitor_entities(
        markdown=markdown,
        actual_citations=actual_citations,
        citation_candidates=citation_candidates,
        search_sources=search_sources,
        attached_links=attached_links,
        map_results=map_results,
        target_domains=target_domains,
        brand_terms=brand_terms,
    )

    return PromptResult(
        chatbot=chatbot,
        model=str(record.get("model") or "").strip() or None,
        prompt=prompt,
        captured_at=run_at,
        answer_text_markdown=markdown,
        mentions=mentions,
        cited=cited,
        first_citation_rank=first_rank,
        citations_count=len(actual_citations),
        fan_out_queries=fan_out,
        fan_out_details=fan_out_details,
        fan_out_count=fan_out_count,
        used_web_search=used_web_search,
        sources_count=len(actual_citations),
        ugc_sources_count=ugc,
        youtube_sources_count=yt,
        competitor_domains=competitors_found,
        brands_mentioned=[str(item).strip() for item in brands_mentioned if str(item).strip()]
        if isinstance(brands_mentioned, list)
        else [],
        sources=actual_citations,
        actual_citations=actual_citations,
        citation_candidates=citation_candidates,
        uncited_citation_candidates=uncited_candidates,
        search_sources=search_sources,
        attached_links=attached_links,
        map_results=map_results,
        target_found_in_search=target_found_in_search,
        target_found_in_maps=target_found_in_maps,
        competitor_entities=competitor_entities,
        provider_metadata={
            "index": record.get("index"),
            "country": record.get("country"),
            "prompt_sent_at": record.get("prompt_sent_at"),
            "is_map": metadata_booleans["is_map"],
            "shopping_visible": metadata_booleans["shopping_visible"],
            "unknown_fields": {
                key: value for key, value in record.items() if key not in KNOWN_PROVIDER_FIELDS
            },
        },
        evidence_status={
            "answer": evidence_state(answer_state, records=1 if markdown else 0),
            "web_search": evidence_state(web_search_state, records=1 if used_web_search is not None else 0),
            "actual_citations": evidence_state(
                actual_citations_state,
                records=len(actual_citations),
                note=(
                    "Only explicit cited=true records count."
                    if actual_citations_state != "supported"
                    else None
                ),
            ),
            "citation_candidates": evidence_state(candidates_state, records=len(citation_candidates)),
            "search_sources": evidence_state(search_sources_state, records=len(search_sources)),
            "attached_links": evidence_state(attached_links_state, records=len(attached_links)),
            "maps": evidence_state(maps_state, records=len(map_results)),
            "fan_out_queries": evidence_state(fan_out_state, records=len(fan_out)),
        },
        normalization={
            "status": "warning" if warnings else "ok",
            "warnings": warnings,
        },
    )


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
    snapshots: List[Dict[str, Any]],
    all_results: List["PromptResult"],
    rejected_records: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    rejected_records = rejected_records or []
    warnings = [
        {
            "chatbot": result.chatbot,
            "prompt": result.prompt,
            **warning,
        }
        for result in all_results
        for warning in result.normalization.get("warnings", [])
    ]
    unknown_fields = sorted(
        {
            field
            for result in all_results
            for field in result.provider_metadata.get("unknown_fields", {})
        }
    )
    channels = [
        "answer",
        "web_search",
        "actual_citations",
        "citation_candidates",
        "search_sources",
        "attached_links",
        "maps",
        "fan_out_queries",
    ]
    capabilities = {
        channel: {
            state: sum(
                1
                for result in all_results
                if result.evidence_status.get(channel, {}).get("state") == state
            )
            for state in sorted(EVIDENCE_STATES)
        }
        for channel in channels
    }
    has_unavailable_evidence = any(
        result.evidence_status.get(channel, {}).get("state") in {"missing", "malformed"}
        for result in all_results
        for channel in channels
    )
    diagnostics_status = (
        "partial"
        if rejected_records or has_unavailable_evidence
        else "complete_with_warnings"
        if warnings
        else "complete"
    )
    return {
        "schema_version": "geo-audit-v3",
        "provider": "brightdata",
        "provider_method": "datasets_v3_auto",
        "run_at": run_at,
        "check_url": check_url,
        "target_domains": target_domains,
        "brand_terms": brand_terms,
        "snapshots": snapshots,
        "manual_recommendations": [],
        "collection_diagnostics": {
            "status": diagnostics_status,
            "records_received": len(all_results) + len(rejected_records),
            "records_normalized": len(all_results),
            "records_rejected": len(rejected_records),
            "warning_count": len(warnings),
            "warnings": warnings,
            "rejected_records": rejected_records,
            "unknown_provider_fields": unknown_fields,
            "capabilities": capabilities,
        },
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
    parser.add_argument(
        "--collection-mode",
        choices=["auto", "sync", "async"],
        default="auto",
        help="auto uses synchronous collection for up to 20 prompts and async otherwise",
    )
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

    snapshots: List[Dict[str, Any]] = []
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
            inputs = build_inputs(prompts, args.check_url, args.country, chatbot=chatbot)
            custom_fields = get_custom_output_fields(chatbot)
            use_sync = args.collection_mode == "sync" or (
                args.collection_mode == "auto" and len(inputs) <= 20
            )
            if use_sync:
                print(f"Collecting {chatbot} synchronously...")
                response = scrape_dataset(
                    base_url=args.base_url,
                    api_key=api_key,
                    dataset_id=dataset_id,
                    input_rows=inputs,
                    custom_output_fields=custom_fields,
                )
                if isinstance(response, list):
                    raw_path = raw_snapshot_path(out_dir, chatbot, "sync")
                    write_json(raw_path, response)
                    snapshots.append(
                        {
                            "chatbot": chatbot,
                            "dataset_id": dataset_id,
                            "snapshot_id": "sync",
                            "status": "ready",
                            "collection_method": "sync",
                        }
                    )
                elif isinstance(response, dict) and response.get("snapshot_id"):
                    snapshots.append(
                        {
                            "chatbot": chatbot,
                            "dataset_id": dataset_id,
                            "snapshot_id": str(response["snapshot_id"]),
                            "status": "triggered",
                            "collection_method": "sync_auto_async",
                        }
                    )
                else:
                    raise RuntimeError(
                        f"Bright Data sync request returned an unexpected response: {response}"
                    )
            else:
                print(f"Triggering {chatbot} dataset asynchronously...")
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
                        "collection_method": "async",
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
    rejected_records: List[Dict[str, Any]] = []
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

            write_json(raw_path, raw)

        if not isinstance(raw, list):
            continue
        for record in raw:
            if not isinstance(record, dict):
                continue
            try:
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
                else:
                    rejected_records.append(
                        {
                            "chatbot": chatbot,
                            "index": record.get("index"),
                            "reason": "missing_prompt",
                        }
                    )
            except Exception as error:
                rejected_records.append(
                    {
                        "chatbot": chatbot,
                        "index": record.get("index"),
                        "prompt": str(record.get("prompt") or "")[:200],
                        "reason": f"{type(error).__name__}: {error}",
                    }
                )

        write_json(
            os.path.join(out_dir, "results.partial.json"),
            build_results_payload(
                run_at=run_at,
                check_url=args.check_url,
                target_domains=target_domains,
                brand_terms=brand_terms,
                snapshots=snapshots,
                all_results=all_results,
                rejected_records=rejected_records,
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
            rejected_records=rejected_records,
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
