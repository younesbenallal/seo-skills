#!/usr/bin/env python3
"""Build a geo-audit-v3 results.json from a ChatGPT browser run.

Reads <run-dir>/raw/answers.json (scraped answers) and <run-dir>/raw/fanoutfox.json (Fanout Fox
captures), maps each answer to the record shape the Bright Data collector understands, and reuses
its normalization so every provider produces the same contract.
"""

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse


def load_collector():
    path = Path(__file__).with_name("brightdata-geo.py")
    spec = importlib.util.spec_from_file_location("brightdata_geo", path)
    if not spec or not spec.loader:
        raise RuntimeError(f"Unable to load collector at {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def comma_list(value):
    return [item.strip() for item in value.split(",") if item.strip()]


def attrs(source):
    return dict(re.findall(r'(\w+)="([^"]*)"', source))


# ChatGPT's raw answer mixes Markdown with UI components (<box>, <Entity/>, <Link/>, <Cite/>...).
def clean_answer(text):
    text = re.sub(r"<form\b.*?</form>", "", text, flags=re.S)
    text = re.sub(r"<Entity\b([^>]*)/>", lambda m: attrs(m.group(1)).get("value", ""), text)
    text = re.sub(
        r"<Link\b([^>]*)/>",
        lambda m: f"[{attrs(m.group(1)).get('title') or attrs(m.group(1)).get('url', '')}]({attrs(m.group(1)).get('url', '')})",
        text,
    )
    text = re.sub(r"<title\b[^>]*>(.*?)</title>", r"\n### \1\n", text, flags=re.S)
    text = re.sub(r"<badge\b[^>]*>(.*?)</badge>", r"*\1*", text, flags=re.S)
    text = re.sub(r"</?[A-Za-z][\w-]*(?:\s[^<>]*)?/?>", "", text)
    lines = [line.strip() for line in text.splitlines()]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def entities(text):
    names = [attrs(m).get("value", "").strip() for m in re.findall(r"<Entity\b([^>]*)/>", text)]
    return list(dict.fromkeys(name for name in names if name))


def url_key(url):
    parsed = urlparse(url or "")
    host = (parsed.hostname or "").removeprefix("www.")
    query = urlencode([(k, v) for k, v in parse_qsl(parsed.query) if not k.startswith("utm_")])
    return f"{host}{parsed.path.rstrip('/')}?{query}"


# TEMPORARY, see citationsIn in chatgpt-browser/run.ts: remove once Fanout Fox flags cited
# sources again. Cited pages come first, in answer order, so first_citation_rank follows the answer.
def citation_records(citations, sources):
    cited = [c for c in citations if c.get("url")]
    cited_keys = {url_key(c["url"]) for c in cited}
    by_key = {url_key(s["url"]): s for s in sources}
    records = []
    for citation in cited:
        key = url_key(citation["url"])
        if any(url_key(r["url"]) == key for r in records):
            continue
        source = by_key.get(key, {"url": citation["url"], "title": citation.get("title")})
        records.append({**source, "cited": True})
    records += [{**s, "cited": False} for s in sources if url_key(s["url"]) not in cited_keys]
    return records


# Fanout Fox skips most conversations run in background tabs. ChatGPT's own conversation JSON
# (raw/conversations/<id>.json, saved by chatgpt-browser/run.ts) holds the same evidence: the queries
# sent to search, every retrieved result, the model and the brands shown as entity cards.
def conversation_messages(conversation):
    if isinstance(conversation.get("messages"), list):
        return conversation["messages"]
    # Older format: a tree of nodes keyed by id, each holding one message
    nodes = (conversation.get("mapping") or {}).values()
    messages = [node["message"] for node in nodes if isinstance(node, dict) and node.get("message")]
    return sorted(messages, key=lambda message: message.get("create_time") or 0)


def tool_call_queries(message):
    # The model's own search call, e.g. {"search_query": [{"q": "..."}]}, when no metadata lists them
    content = message.get("content") or {}
    texts = [content.get("text")] + list(content.get("parts") or [])
    queries = []
    for text in texts:
        try:
            call = json.loads(text) if isinstance(text, str) and text.strip().startswith("{") else None
        except json.JSONDecodeError:
            continue
        for key in ("search_query", "queries", "query"):
            value = (call or {}).get(key)
            for item in value if isinstance(value, list) else [value]:
                query = item.get("q") if isinstance(item, dict) else item
                if isinstance(query, str) and query.strip():
                    queries.append(query.strip())
    return queries


def conversation_capture(path):
    try:
        conversation = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(conversation, dict):
        return None
    queries, sources, brands, model = [], [], [], None
    for message in conversation_messages(conversation):
        metadata = message.get("metadata") or {}
        role = (message.get("author") or {}).get("role")
        if role == "assistant":
            model = metadata.get("resolved_model_slug") or metadata.get("model_slug") or model
            if str(message.get("recipient") or "").startswith("web"):
                queries += tool_call_queries(message)
        queries += [q for q in (metadata.get("search_model_queries") or {}).get("queries") or [] if isinstance(q, str)]
        queries += [q.get("q") for q in metadata.get("search_queries") or [] if isinstance(q, dict) and q.get("q")]
        if role == "tool":
            for group in metadata.get("search_result_groups") or []:
                for entry in group.get("entries") or []:
                    if entry.get("url"):
                        sources.append(
                            {
                                "url": entry["url"],
                                "title": entry.get("title"),
                                "host": group.get("domain") or urlparse(entry["url"]).hostname,
                                "snippet": entry.get("snippet") or None,
                                "pubDate": entry.get("pub_date"),
                            }
                        )
        genui = ((metadata.get("model_dil_v2") or {}).get("appData") or {}).get("opGenui") or {}
        for result in (genui.get("componentResults") or {}).values():
            name = (((result or {}).get("state") or {}).get("action_payload") or {}).get("query")
            if isinstance(name, str) and name.strip():
                brands.append(name.strip())
    unique_sources = list({url_key(source["url"]): source for source in reversed(sources)}.values())[::-1]
    return {
        "model": {"resolved": model or conversation.get("default_model_slug")},
        "searchedWeb": bool(queries or sources),
        "fanout": list(dict.fromkeys(queries)),
        "sources": unique_sources,
        "brands": list(dict.fromkeys(brands)),
    }


# A Fanout Fox capture wins; the conversation only fills what it lacks.
def merge_capture(capture, conversation):
    if not conversation:
        return capture
    if not capture:
        return conversation
    merged = dict(capture)
    for key in ("fanout", "sources"):
        merged[key] = capture.get(key) or conversation[key]
    if not (capture.get("model") or {}).get("resolved"):
        merged["model"] = conversation["model"]
    if capture.get("searchedWeb") is None:
        merged["searchedWeb"] = conversation["searchedWeb"]
    return merged


def to_record(index, answer, capture):
    links = [
        {"text": link.get("text"), "url": link.get("href"), "position": position}
        for position, link in enumerate(
            [link for link in answer.get("links", []) if urlparse(link.get("href", "")).hostname != "chatgpt.com"],
            start=1,
        )
    ]
    record = {
        "prompt": answer["prompt"],
        "index": index,
        "prompt_sent_at": answer.get("at"),
        "links_attached": links,
        # The rendered answer alone is plain text; the capture holds the Markdown.
        "answer_text_markdown": re.sub(r"^ChatGPT said:\s*", "", answer.get("text", "")),
    }
    if not capture:
        if answer.get("citations") is not None:
            record["citations"] = citation_records(answer["citations"], [])
        return record
    if (capture.get("raw") or {}).get("answerText"):
        record["answer_text_markdown"] = clean_answer(capture["raw"]["answerText"])
        record["recommendations"] = entities(capture["raw"]["answerText"])
    else:
        record["recommendations"] = capture.get("brands") or []
    record["model"] = (capture.get("model") or {}).get("resolved")
    record["web_search_triggered"] = capture.get("searchedWeb")
    record["web_search_query"] = capture.get("fanout") or []
    seen = set()
    sources = []
    for source in capture.get("sources") or []:
        if source.get("url") in seen:
            continue
        seen.add(source.get("url"))
        sources.append(
            {
                "url": source.get("url"),
                "title": source.get("title"),
                "domain": source.get("host"),
                "rank": len(sources) + 1,
                "snippet": source.get("snippet"),
                "date_published": source.get("pubDate"),
            }
        )
    record["search_sources"] = sources
    # Without resolved citations the contract reports actual citations as missing, never zero.
    if answer.get("citations") is not None:
        record["citations"] = citation_records(answer["citations"], sources)
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True, help="Dated run folder holding raw/answers.json")
    parser.add_argument("--check-url", required=True)
    parser.add_argument("--target-domains", required=True)
    parser.add_argument("--brand-terms", required=True)
    parser.add_argument("--competitor-domains", default="")
    args = parser.parse_args()

    collector = load_collector()
    run_dir = Path(args.run_dir).expanduser().resolve()
    answers = json.loads((run_dir / "raw" / "answers.json").read_text(encoding="utf-8"))
    fanoutfox_path = run_dir / "raw" / "fanoutfox.json"
    captures = json.loads(fanoutfox_path.read_text(encoding="utf-8")) if fanoutfox_path.exists() else []
    by_conversation = {item["convKey"].split(":", 1)[-1]: item["capture"] for item in captures}

    run_at = min(answer["at"] for answer in answers)[:19] + "Z"
    target_domains = [collector.normalize_domain(item) for item in comma_list(args.target_domains)]
    brand_terms = comma_list(args.brand_terms)
    competitor_domains = [collector.normalize_domain(item) for item in comma_list(args.competitor_domains)]

    results = []
    rejected_records = []
    without_capture = 0
    from_conversation = 0
    for index, answer in enumerate(answers, start=1):
        if "error" in answer:
            rejected_records.append(
                {"chatbot": "chatgpt", "index": index, "prompt": answer["prompt"][:200], "reason": answer["error"][:300]}
            )
            continue
        conversation_id = answer["url"].split("?")[0].rstrip("/").split("/")[-1]
        capture = by_conversation.get(conversation_id)
        without_capture += capture is None
        conversation = conversation_capture(run_dir / "raw" / "conversations" / f"{conversation_id}.json")
        from_conversation += capture is None and conversation is not None
        capture = merge_capture(capture, conversation)
        results.append(
            collector.analyze_record(
                "chatgpt",
                to_record(index, answer, capture),
                run_at=run_at,
                target_domains=target_domains,
                brand_terms=brand_terms,
                competitor_domains=competitor_domains,
            )
        )

    payload = collector.build_results_payload(
        run_at=run_at,
        check_url=args.check_url,
        target_domains=target_domains,
        brand_terms=brand_terms,
        snapshots=[
            {
                "chatbot": "chatgpt",
                "status": "ready",
                "collection_method": "browser_cdp",
                "raw_file": str(run_dir / "raw" / "answers.json"),
                "fanoutfox_captures": len(captures),
                "conversation_fallbacks": from_conversation,
            }
        ],
        all_results=results,
        rejected_records=rejected_records,
    )
    payload["provider"] = "chatgpt_browser"
    payload["provider_method"] = "playwright_cdp_fanoutfox"
    out_path = run_dir / "results.json"
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"Wrote {len(results)} normalized responses to {out_path}"
        f" ({len(rejected_records)} rejected, {without_capture} without a Fanout Fox capture,"
        f" {from_conversation} of them read from the conversation JSON)"
    )


if __name__ == "__main__":
    main()
