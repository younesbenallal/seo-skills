#!/usr/bin/env python3
"""Compare the raw HTML with the JavaScript-rendered DOM for a few URLs.

Usage:
  python3 render_check.py URL [URL ...] --out ./audit-run/render.json [--chrome PATH]

Take one URL per template (home, money page, blog post, category, programmatic page). Pass them in
one run: text that appears only after JS on two or more templates is treated as a sitewide widget
(cookie banner, contact pop-in) and ignored in the verdict.
The rendered DOM comes from headless Chrome (`--dump-dom`). When Chrome is not found, the script
stops and says so: get the rendered HTML from a browser tool instead (document.documentElement.outerHTML),
save it, and pass it with --rendered URL=FILE.

For each URL it reports what exists only after rendering: title, meta description, canonical,
robots, H1, body words, internal links, JSON-LD types. Anything that exists only after rendering is
invisible to crawlers that do not execute JavaScript (GPTBot, ClaudeBot, PerplexityBot, OAI-SearchBot,
and Google until its render queue gets to the page).
"""

import argparse
import json
import re
from collections import Counter
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from seo_html import extract, fetch, same_site  # noqa: E402

CHROME_PATHS = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
]


WIDGET_TEXT = re.compile(r"(cookie|consent|consentement|gdpr|rgpd|privacy|confidentialit|traceurs|tracking|préférences|preferences|chat with|live chat|intercom|crisp|hubspot|newsletter|subscribe|abonnez|inscrivez-vous|pop-?up)", re.I)


def find_chrome(explicit=None):
    if explicit:
        return explicit
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome"):
        path = shutil.which(name)
        if path:
            return path
    return next((p for p in CHROME_PATHS if Path(p).exists()), None)


def render(chrome, url):
    command = [chrome, "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check", "--hide-scrollbars", "--virtual-time-budget=10000", "--dump-dom", url]
    result = subprocess.run(command, capture_output=True, text=True, timeout=90)
    return result.stdout


def facts(data, url):
    internal = {link["url"] for link in data["links"] if same_site(link["url"], url)}
    return {
        "title": data["title"],
        "meta_description": data["meta_description"],
        "canonical": data["canonical"],
        "meta_robots": data["meta_robots"],
        "h1": data["h1"],
        "words": data["unique_word_count"],
        "internal_links": len(internal),
        "schema_types": data["schema_types"],
        "_links": internal,
        "_texts": data["texts"],
    }


def js_only_texts(url, raw_html, rendered_html):
    raw_text = " ".join(extract(raw_html, url)["texts"])
    return {t for t in extract(rendered_html, url)["texts"] if t not in raw_text}


def compare(url, raw_html, rendered_html, widgets=frozenset()):
    raw = facts(extract(raw_html, url), url)
    rendered = facts(extract(rendered_html, url), url)
    js_only = {}
    for key in ("title", "meta_description", "canonical", "meta_robots"):
        if rendered[key] and rendered[key] != raw[key]:
            js_only[key] = {"raw": raw[key], "rendered": rendered[key]}
    if rendered["h1"] and not raw["h1"]:
        js_only["h1"] = {"raw": raw["h1"], "rendered": rendered["h1"]}
    added_links = rendered["_links"] - raw["_links"]
    missing_schema = sorted(set(rendered["schema_types"]) - set(raw["schema_types"]))
    link_share = len(raw["_links"] & rendered["_links"]) / len(rendered["_links"]) if rendered["_links"] else 1
    # Share of the rendered text (sentences of 40+ characters) already present in the raw HTML,
    # ignoring cookie banners, chat widgets, and pop-ins that scripts inject on every page.
    raw_text = " ".join(raw["_texts"])
    ignored = [t for t in dict.fromkeys(rendered["_texts"]) if t not in raw_text and (WIDGET_TEXT.search(t) or t in widgets)]
    rendered_texts = [t for t in dict.fromkeys(rendered["_texts"]) if t not in ignored]
    rendered_only_text = [t for t in rendered_texts if t not in raw_text]
    total = sum(len(t.split()) for t in rendered_texts)
    word_share = 1 - sum(len(t.split()) for t in rendered_only_text) / total if total else 1
    critical = any(k in js_only for k in ("title", "canonical", "meta_robots", "h1"))
    # Close to SEOmator's thresholds: when most of the rendered text needs JS, the content is JS-dependent.
    if word_share < 0.33 or critical:
        verdict = "js-dependent"
    elif word_share < 0.8 or link_share < 0.8 or js_only:
        verdict = "partly-js-dependent"
    else:
        # JSON-LD added by JS is reported in schema_only_after_js, not in the content verdict.
        verdict = "server-rendered"
    for side in (raw, rendered):
        side["internal_links"] = len(side.pop("_links"))
        side.pop("_texts")
    return {
        "url": url,
        "verdict": verdict,
        "raw": raw,
        "rendered": rendered,
        "raw_share_of_rendered_text": round(word_share, 2),
        "raw_share_of_rendered_links": round(link_share, 2),
        "changed_or_js_only": js_only,
        "links_only_after_js": sorted(added_links)[:20],
        "schema_only_after_js": missing_schema,
        "text_only_after_js_sample": rendered_only_text[:12],
        "ignored_widget_text_sample": ignored[:5],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("urls", nargs="+")
    parser.add_argument("--out", required=True)
    parser.add_argument("--chrome", help="Path to a Chrome/Chromium binary")
    parser.add_argument("--rendered", action="append", default=[], help="URL=FILE with rendered HTML saved from a browser tool")
    args = parser.parse_args()

    provided = dict(item.split("=", 1) for item in args.rendered)
    chrome = find_chrome(args.chrome)
    if not chrome and not provided:
        sys.exit("No Chrome/Chromium found. Save document.documentElement.outerHTML from a browser tool and pass --rendered URL=FILE.")

    results, pages = [], []
    for url in args.urls:
        response = fetch(url)
        final = response["final_url"]
        if response["status"] != 200:
            results.append({"url": url, "error": f"status {response['status']}"})
            continue
        rendered_html = Path(provided[url]).read_text() if url in provided else render(chrome, final)
        if not rendered_html.strip():
            results.append({"url": url, "error": "empty rendered DOM"})
            continue
        pages.append((final, response["text"], rendered_html))

    # Text that only appears after JS on two or more different templates is a sitewide widget
    # (contact pop-in, newsletter modal), not page content.
    seen = Counter(t for final, raw_html, rendered_html in pages for t in js_only_texts(final, raw_html, rendered_html))
    widgets = frozenset(t for t, n in seen.items() if n >= 2) if len(pages) >= 2 else frozenset()
    for final, raw_html, rendered_html in pages:
        result = compare(final, raw_html, rendered_html, widgets)
        results.append(result)
        print(f"{result['verdict']:<20} text in raw {result['raw_share_of_rendered_text']:.0%}  words raw/rendered {result['raw']['words']}/{result['rendered']['words']}  links {result['raw']['internal_links']}/{result['rendered']['internal_links']}  {final}")

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(results, indent=1, ensure_ascii=False))
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
