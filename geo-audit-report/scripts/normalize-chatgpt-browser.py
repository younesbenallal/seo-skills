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
from urllib.parse import urlparse


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
        return record
    record["answer_text_markdown"] = clean_answer(capture["raw"]["answerText"])
    record["recommendations"] = entities(capture["raw"]["answerText"])
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
    # Fanout Fox cannot tie <Cite/> markers to URLs on this payload, so "citations" stays absent
    # and the contract reports actual citations as missing rather than inventing them.
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
    for index, answer in enumerate(answers, start=1):
        if "error" in answer:
            rejected_records.append(
                {"chatbot": "chatgpt", "index": index, "prompt": answer["prompt"][:200], "reason": answer["error"][:300]}
            )
            continue
        capture = by_conversation.get(answer["url"].rstrip("/").split("/")[-1])
        without_capture += capture is None
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
        f" ({len(rejected_records)} rejected, {without_capture} without a Fanout Fox capture)"
    )


if __name__ == "__main__":
    main()
