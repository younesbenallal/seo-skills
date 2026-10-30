#!/usr/bin/env python3
"""Render audit.json into one self-contained HTML report.

Usage:
  python3 render_report.py audit.json --out report.html

The JSON shape is documented in references/report.md. The report needs no server: open the file
in a browser, send it as an attachment, or host it as a static page.
"""

import argparse
import json
import sys
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent / "templates" / "report.html"
IMPACTS = {"critical", "high", "medium", "low"}


def check(data):
    problems = []
    for key in ("site", "date", "verdict", "findings"):
        if not data.get(key):
            problems.append(f"missing '{key}'")
    for index, finding in enumerate(data.get("findings", [])):
        label = finding.get("title") or f"finding #{index + 1}"
        if finding.get("impact") not in IMPACTS:
            problems.append(f"{label}: impact must be one of {sorted(IMPACTS)}")
        for key in ("evidence", "fix"):
            if not finding.get(key):
                problems.append(f"{label}: missing '{key}'")
    return problems


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("audit", help="audit.json")
    parser.add_argument("--out", default="report.html")
    args = parser.parse_args()

    data = json.loads(Path(args.audit).read_text())
    problems = check(data)
    if problems:
        sys.exit("audit.json is incomplete:\n- " + "\n- ".join(problems))
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    html = TEMPLATE.read_text().replace("/*__AUDIT_DATA__*/", payload)
    Path(args.out).write_text(html)
    print(f"Wrote {args.out} ({len(data['findings'])} findings)")


if __name__ == "__main__":
    main()
