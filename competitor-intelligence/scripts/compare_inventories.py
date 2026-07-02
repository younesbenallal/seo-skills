#!/usr/bin/env python3
"""Compare two pages.csv sitemap snapshots."""

import argparse
import csv
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


def read_inventory(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return {row["url"]: row for row in csv.DictReader(handle)}


def change_row(change, row, previous=None):
    return {
        "change": change,
        "url": row["url"],
        "page_type": row.get("page_type", ""),
        "first_segment": row.get("first_segment", ""),
        "old_lastmod": previous.get("lastmod", "") if previous else "",
        "new_lastmod": row.get("lastmod", "") if change != "removed" else "",
    }


def breakdown(rows, field):
    return dict(Counter(row.get(field, "") or "/" for row in rows).most_common())


def main():
    parser = argparse.ArgumentParser(description="Compare old and new sitemap inventory CSVs.")
    parser.add_argument("old_inventory")
    parser.add_argument("new_inventory")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    old = read_inventory(args.old_inventory)
    new = read_inventory(args.new_inventory)
    added = [new[url] for url in sorted(new.keys() - old.keys())]
    removed = [old[url] for url in sorted(old.keys() - new.keys())]
    changed = [
        new[url]
        for url in sorted(new.keys() & old.keys())
        if new[url].get("lastmod", "") != old[url].get("lastmod", "")
    ]

    changes = [change_row("added", row) for row in added]
    changes += [change_row("removed", row, row) for row in removed]
    changes += [change_row("lastmod-changed", row, old[row["url"]]) for row in changed]

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "changes.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = [
            "change",
            "url",
            "page_type",
            "first_segment",
            "old_lastmod",
            "new_lastmod",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(changes)

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "old_inventory": str(Path(args.old_inventory)),
        "new_inventory": str(Path(args.new_inventory)),
        "totals": {
            "old_urls": len(old),
            "new_urls": len(new),
            "added": len(added),
            "removed": len(removed),
            "lastmod_changed": len(changed),
        },
        "added_by_page_type": breakdown(added, "page_type"),
        "added_by_first_segment": breakdown(added, "first_segment"),
        "removed_by_page_type": breakdown(removed, "page_type"),
        "added_samples": [row["url"] for row in added[:30]],
        "removed_samples": [row["url"] for row in removed[:30]],
        "notes": [
            "a removed URL may have moved to another sitemap or canonical URL",
            "a changed lastmod value does not prove an editorial update",
        ],
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"Added: {len(added)}")
    print(f"Removed: {len(removed)}")
    print(f"Lastmod changed: {len(changed)}")
    print(f"Changes: {output_dir / 'changes.csv'}")
    print(f"Summary: {output_dir / 'summary.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
