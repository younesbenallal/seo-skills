#!/usr/bin/env python3
"""Rebuild a geo-audit-v3 results.json from an existing Bright Data raw export."""

import argparse
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", required=True, help="Existing Bright Data JSON array")
    parser.add_argument("--out", required=True, help="Destination results.json")
    parser.add_argument("--chatbot", default="chatgpt")
    parser.add_argument("--check-url", required=True)
    parser.add_argument("--target-domains", required=True)
    parser.add_argument("--brand-terms", required=True)
    parser.add_argument("--competitor-domains", default="")
    parser.add_argument("--dataset-id", default="")
    parser.add_argument("--snapshot-id", default="")
    parser.add_argument("--run-at", default="")
    args = parser.parse_args()

    collector = load_collector()
    raw_path = Path(args.raw).expanduser().resolve()
    out_path = Path(args.out).expanduser().resolve()
    records = json.loads(raw_path.read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise SystemExit("--raw must contain a JSON array")

    run_at = args.run_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    target_domains = [collector.normalize_domain(item) for item in comma_list(args.target_domains)]
    brand_terms = comma_list(args.brand_terms)
    competitor_domains = [collector.normalize_domain(item) for item in comma_list(args.competitor_domains)]
    results = []
    rejected_records = []
    for record in records:
        if not isinstance(record, dict):
            rejected_records.append(
                {"chatbot": args.chatbot, "index": None, "reason": "record_was_not_an_object"}
            )
            continue
        try:
            result = collector.analyze_record(
                args.chatbot,
                record,
                run_at=run_at,
                target_domains=target_domains,
                brand_terms=brand_terms,
                competitor_domains=competitor_domains,
            )
            if result.prompt:
                results.append(result)
            else:
                rejected_records.append(
                    {
                        "chatbot": args.chatbot,
                        "index": record.get("index"),
                        "reason": "missing_prompt",
                    }
                )
        except Exception as error:
            rejected_records.append(
                {
                    "chatbot": args.chatbot,
                    "index": record.get("index"),
                    "prompt": str(record.get("prompt") or "")[:200],
                    "reason": f"{type(error).__name__}: {error}",
                }
            )

    payload = collector.build_results_payload(
        run_at=run_at,
        check_url=args.check_url,
        target_domains=target_domains,
        brand_terms=brand_terms,
        snapshots=[
            {
                "chatbot": args.chatbot,
                "dataset_id": args.dataset_id or None,
                "snapshot_id": args.snapshot_id or None,
                "status": "ready",
                "collection_method": "raw_import",
                "raw_file": str(raw_path),
            }
        ],
        all_results=results,
        rejected_records=rejected_records,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"Wrote {len(results)} normalized responses to {out_path}"
        f" ({len(rejected_records)} rejected)"
    )


if __name__ == "__main__":
    main()
