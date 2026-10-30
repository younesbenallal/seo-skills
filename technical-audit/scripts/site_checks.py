#!/usr/bin/env python3
"""Site-level technical checks that a page crawl does not cover.

Usage:
  python3 site_checks.py https://example.com --out ./audit-run/site.json \
      [--urls URL ...] [--psi]

Checks:
- hosts: http/https and www/non-www variants all 301 to one canonical origin
- robots.txt: status, served as text, declared sitemaps, Content-Signal lines, and the verdict for
  each search and AI user agent on the homepage and sample URLs (Google's matching rules)
- bot_fetch: the homepage requested with each bot's user agent, compared with a browser, to catch
  CDN/WAF blocking (Cloudflare AI bot blocking, 403 challenges) that robots.txt does not show
- url_variants: on a sample inner URL, the trailing-slash twin, a tracking parameter, an internal
  search-style parameter, and uppercase; each should redirect or canonicalize to the clean URL
- soft_404: a random URL must return 404/410
- llms_txt: presence and text of /llms.txt and /llms-full.txt (read it: it is copy AI systems may quote)
- stack: CMS or framework hints (Webflow, WordPress, Framer, Next.js, Nuxt, empty JS shell)
- psi (--psi): PageSpeed Insights field data (CrUX) and lab score, mobile, for the homepage and --urls.
  Uses PAGESPEED_API_KEY when set; works without a key at low volume.

Index presence on Bing, Brave and DuckDuckGo is not scripted: their HTML endpoints ignore `site:` or
block scripts. Check it in a browser (see SKILL.md).

Python 3 standard library only.
"""

import argparse
import json
import os
import re
import sys
import time
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlencode, urlsplit, urlunsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))

from seo_html import BROWSER_UA, bare_host, extract, fetch, fetch_once, is_noindex, load_sitemaps, normalize_url, parse_robots, robots_allows, sitemap_seeds  # noqa: E402

# Product tokens as written in robots.txt, and the user-agent strings the bots send.
# Purpose: search = classic search index; ai_search = index used to answer and cite in AI search;
# ai_user = fetch triggered by a user's prompt; training = model training (blocking is a business choice).
BOTS = [
    ("Googlebot", "search", "Google", "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"),
    ("Bingbot", "search", "Microsoft (also feeds Copilot and other engines)", "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm) Chrome/116.0.1938.76 Safari/537.36"),
    ("Applebot", "search", "Apple (Spotlight, Siri, Safari suggestions)", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Safari/605.1.15 (Applebot/0.1; +http://www.apple.com/go/applebot)"),
    ("DuckDuckBot", "search", "DuckDuckGo", "DuckDuckBot/1.1; (+http://duckduckgo.com/duckduckbot.html)"),
    ("OAI-SearchBot", "ai_search", "OpenAI (ChatGPT search)", "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; OAI-SearchBot/1.0; +https://openai.com/searchbot"),
    ("Claude-SearchBot", "ai_search", "Anthropic (Claude search)", "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Claude-SearchBot/1.0; +https://www.anthropic.com)"),
    ("PerplexityBot", "ai_search", "Perplexity", "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; PerplexityBot/1.0; +https://perplexity.ai/perplexitybot)"),
    ("DuckAssistBot", "ai_search", "DuckDuckGo (Duck.ai answers)", "DuckAssistBot/1.2; (+http://duckduckgo.com/duckassistbot.html)"),
    ("meta-webindexer", "ai_search", "Meta (Meta AI search)", None),
    ("Amzn-SearchBot", "ai_search", "Amazon (Rufus, Alexa answers)", None),
    ("MistralAI-Index", "ai_search", "Mistral (Le Chat search index)", None),
    ("ChatGPT-User", "ai_user", "OpenAI (user-triggered fetch)", "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; ChatGPT-User/1.0; +https://openai.com/bot"),
    ("Claude-User", "ai_user", "Anthropic (user-triggered fetch)", "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Claude-User/1.0; +Claude-User@anthropic.com)"),
    ("Perplexity-User", "ai_user", "Perplexity (user-triggered fetch)", "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Perplexity-User/1.0; +https://perplexity.ai/perplexity-user)"),
    ("MistralAI-User", "ai_user", "Mistral (Le Chat, user-triggered fetch)", "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; MistralAI-User/1.0; +https://docs.mistral.ai/robots)"),
    ("meta-externalfetcher", "ai_user", "Meta (user-triggered fetch)", None),
    ("Amzn-User", "ai_user", "Amazon (user-triggered fetch)", None),
    ("GPTBot", "training", "OpenAI", "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; GPTBot/1.2; +https://openai.com/gptbot)"),
    ("ClaudeBot", "training", "Anthropic", "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; ClaudeBot/1.0; +claudebot@anthropic.com)"),
    ("Google-Extended", "training", "Google (Gemini training and grounding; token only, fetched by Googlebot)", None),
    ("Applebot-Extended", "training", "Apple (token only, fetched by Applebot)", None),
    ("meta-externalagent", "training", "Meta", "meta-externalagent/1.1 (+https://developers.facebook.com/docs/sharing/webmasters/crawler)"),
    ("CCBot", "training", "Common Crawl (used by many model builders)", "CCBot/2.0 (https://commoncrawl.org/faq/)"),
    ("Bytespider", "training", "ByteDance", "Mozilla/5.0 (Linux; Android 5.0) AppleWebKit/537.36 (KHTML, like Gecko) Mobile Safari/537.36 (compatible; Bytespider; spider-feedback@bytedance.com)"),
    ("MistralAI-Training", "training", "Mistral", None),
    ("Amazonbot", "training", "Amazon (training)", "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Amazonbot/0.1; +https://developer.amazon.com/support/amazonbot) Chrome/119.0.6045.214 Safari/537.36"),
]
# Agents whose exact user-agent string is not published: robots.txt is checked, the CDN is not.
UNTESTED = [token for token, purpose, _, ua in BOTS if not ua and purpose in ("ai_search", "ai_user")]
CHALLENGE = re.compile(r"(just a moment|attention required|cf-chl|challenge-platform|captcha|access denied|are you a robot|ddos protection|error 1020|error 54113|request blocked|bot detected)", re.I)
BLOCK_HEADERS = ("cf-mitigated", "x-datadome", "x-px-blocked", "x-vercel-mitigated", "x-amzn-waf-action")
REFUSED = {401, 402, 403, 405, 406, 418, 429, 503}


def host_variants(start):
    host = bare_host(start)
    results = []
    for scheme in ("http", "https"):
        for prefix in ("", "www."):
            url = f"{scheme}://{prefix}{host}/"
            response = fetch(url)
            results.append({
                "url": url,
                "status": response["status"],
                "final_url": response["final_url"],
                "hops": [f"{h['status']} {h['url']}" for h in response["chain"]],
                "error": response.get("error"),
            })
    finals = {r["final_url"] for r in results if r["status"] == 200}
    canonical_origin = next((r["final_url"] for r in results if r["url"] == start and r["status"] == 200), None) or (finals and sorted(finals)[0]) or None
    non_301 = [r for r in results if r["hops"] and not r["hops"][0].startswith(("301", "308"))]
    return {
        "variants": results,
        "single_origin": len(finals) == 1,
        "canonical_origin": canonical_origin,
        "https_enforced": all(r["final_url"].startswith("https://") for r in results if r["status"] == 200),
        "temporary_or_unusual_redirects": non_301,
        "multi_hop": [r for r in results if len(r["hops"]) > 1],
    }


def robots_check(origin, sample_urls):
    response = fetch(origin.rstrip("/") + "/robots.txt")
    text = response["text"] if response["status"] == 200 else ""
    looks_html = "<html" in text[:1000].lower() or "<!doctype" in text[:200].lower()
    parsed = parse_robots("" if looks_html else text)
    verdicts = []
    for token, purpose, owner, _ in BOTS:
        blocked = []
        for url in sample_urls:
            ok, group, rule = robots_allows(parsed, token, url)
            if not ok:
                blocked.append({"url": url, "rule": rule, "group": group})
        group = robots_allows(parsed, token, sample_urls[0])[1]
        verdicts.append({
            "token": token,
            "purpose": purpose,
            "owner": owner,
            "group_used": group,
            "blocked_urls": len(blocked),
            "of": len(sample_urls),
            "examples": blocked[:5],
        })
    content_signals = [o["value"] for o in parsed["other"] if o["directive"] == "content-signal"]
    return {
        "url": origin.rstrip("/") + "/robots.txt",
        "status": response["status"],
        "content_type": response["headers"].get("content-type"),
        "served_html_instead_of_text": looks_html,
        "bytes": len(text),
        "sitemaps": parsed["sitemaps"],
        "content_signals": content_signals,
        "other_directives": [o for o in parsed["other"] if o["directive"] not in ("content-signal",)][:20],
        "groups": [{"agents": g["agents"], "rules": len(g["rules"])} for g in parsed["groups"]],
        "verdicts": verdicts,
        "text": text[:6000],
    }


def _probe(url, user_agent):
    response = fetch_once(url, user_agent=user_agent)
    if response["status"] == 429:
        time.sleep(10)
        response = fetch_once(url, user_agent=user_agent)
    words = extract(response["text"], url)["word_count"] if response["status"] == 200 else 0
    return {
        "status": response["status"],
        "bytes": len(response["text"]),
        "words": words,
        "challenge": bool(CHALLENGE.search(response["text"][:8000])) and words < 300,
        "block_headers": {h: response["headers"][h] for h in BLOCK_HEADERS if h in response["headers"]},
    }


def bot_fetch(url):
    """Request the URL as a browser, then as each bot. The bot's UA is sent from this machine's IP,
    so a WAF that verifies bots by IP can refuse the test while the real bot gets through."""
    baseline = _probe(url, BROWSER_UA)
    rows = [{"agent": "Browser", "purpose": "baseline", **baseline}]
    for token, purpose, _, ua in BOTS:
        if not ua:
            continue
        time.sleep(0.5)
        probe = _probe(url, ua)
        refused = probe["status"] in REFUSED or probe["challenge"] or bool(probe["block_headers"])
        thin = probe["status"] == 200 and baseline["words"] > 200 and probe["words"] < baseline["words"] * 0.5
        rows.append({"agent": token, "purpose": purpose, **probe, "differs_from_browser": refused or thin or probe["status"] != baseline["status"]})
    if baseline["status"] != 200 or baseline["challenge"]:
        return {"url": url, "rows": rows, "blocked_ai_agents": [], "reading": "The browser baseline itself is refused or challenged from this machine: inconclusive.", "untested": UNTESTED}
    googlebot = next(r for r in rows if r["agent"] == "Googlebot")
    blocked_ai = [r["agent"] for r in rows if r["purpose"] in ("ai_search", "ai_user") and r.get("differs_from_browser")]
    if not blocked_ai:
        reading = "No AI search or user agent is treated differently from a browser."
    elif googlebot.get("differs_from_browser"):
        reading = "Googlebot is also refused: the CDN probably verifies bots by IP, so spoofed user agents are blocked. Inconclusive; check the CDN's bot settings or server logs."
    else:
        reading = "Googlebot passes but these AI agents are refused or served less content: likely a CDN/WAF AI-bot rule (e.g. Cloudflare AI Crawl Control). Confirm in the CDN settings or logs filtered on the vendor's IP ranges."
    return {"url": url, "rows": rows, "blocked_ai_agents": blocked_ai, "reading": reading, "untested": UNTESTED}


def page_facts(url):
    response = fetch(url)
    facts = {"requested": url, "status": response["status"], "final_url": response["final_url"], "hops": [f"{h['status']} {h['url']}" for h in response["chain"]]}
    if response["status"] == 200 and "html" in response["headers"].get("content-type", ""):
        data = extract(response["text"], response["final_url"])
        facts.update({"canonical": data["canonical"], "noindex": is_noindex(data["meta_robots"], response["headers"].get("x-robots-tag"))})
    return facts


def url_variants(sample):
    parts = urlsplit(sample)
    path = parts.path or "/"
    toggled = path[:-1] if path.endswith("/") and path != "/" else path + "/"
    variants = {
        "clean": sample,
        "trailing_slash_toggled": urlunsplit((parts.scheme, parts.netloc, toggled, parts.query, "")),
        "tracking_param": urlunsplit((parts.scheme, parts.netloc, path, "utm_source=audit&utm_medium=test", "")),
        "search_param": urlunsplit((parts.scheme, parts.netloc, path, "q=test&page=2", "")),
        "uppercase": urlunsplit((parts.scheme, parts.netloc, path.upper(), parts.query, "")) if path.lower() != path.upper() else None,
    }
    results = {}
    for name, url in variants.items():
        if not url:
            continue
        facts = page_facts(url)
        resolved = facts["final_url"] if facts["hops"] else (facts.get("canonical") or None)
        facts["ok"] = name == "clean" or facts["status"] in (404, 410) or resolved == sample or (facts["status"] == 200 and facts.get("noindex"))
        results[name] = facts
    return results


def soft_404(origin):
    url = f"{origin.rstrip('/')}/{uuid.uuid4().hex[:12]}-does-not-exist"
    facts = page_facts(url)
    facts["ok"] = facts["status"] in (404, 410)
    return facts


def llms_txt(origin):
    """Presence plus the text, so its claims can be checked like any other page copy. The status of
    the URLs it lists is in crawl.py's summary (llms_txt)."""
    out = {}
    for path in ("/llms.txt", "/llms-full.txt"):
        response = fetch(origin + path)
        text = response["text"] if response["status"] == 200 and "<html" not in response["text"][:500].lower() else ""
        out[path] = {"status": response["status"], "bytes": len(text), "text": text[:8000]}
    return out


def detect_stack(url):
    response = fetch(url)
    html = response["text"]
    hints = []
    checks = [
        ("Webflow", r"data-wf-(site|page|domain)|generator\" content=\"Webflow"),
        ("WordPress", r"wp-content|wp-includes|generator\" content=\"WordPress"),
        ("Framer", r"framerusercontent|data-framer"),
        ("Wix", r"wix\.com|_wixCssImports"),
        ("Squarespace", r"squarespace"),
        ("HubSpot CMS", r"hs-scripts|hubspot"),
        ("Shopify", r"cdn\.shopify\.com"),
        ("Next.js", r"__NEXT_DATA__|/_next/static"),
        ("Nuxt", r"__NUXT__|/_nuxt/"),
        ("Gatsby", r"___gatsby"),
        ("Astro", r"astro-island|/_astro/"),
        ("Angular", r"ng-version|<app-root"),
    ]
    for name, pattern in checks:
        if re.search(pattern, html, re.I):
            hints.append(name)
    data = extract(html, url) if response["status"] == 200 else {"word_count": 0, "links": []}
    shell = bool(re.search(r"<div id=\"(root|app|__next)\"[^>]*>\s*</div>", html)) and data["word_count"] < 100
    analytics = [name for name, pattern in [("GA4/gtag", r"gtag\(|googletagmanager\.com/gtag"), ("GTM", r"googletagmanager\.com/gtm\.js"), ("PostHog", r"posthog"), ("Plausible", r"plausible\.io"), ("Matomo", r"matomo"), ("Segment", r"segment\.(com|io)"), ("HubSpot", r"js\.hs-scripts|hs-analytics")] if re.search(pattern, html, re.I)]
    return {"cms_or_framework": hints, "empty_js_shell": shell, "raw_words": data["word_count"], "raw_links": len(data["links"]), "analytics": analytics, "server": response["headers"].get("server"), "cdn": next((h for h in ("cf-ray", "x-vercel-id", "x-amz-cf-id", "x-served-by", "x-netlify-id") if h in response["headers"]), None)}


def psi(url):
    params = {"url": url, "strategy": "mobile", "category": "performance"}
    if os.environ.get("PAGESPEED_API_KEY"):
        params["key"] = os.environ["PAGESPEED_API_KEY"]
    response = fetch_once("https://www.googleapis.com/pagespeedonline/v5/runPagespeed?" + urlencode(params), timeout=90)
    if response["status"] != 200:
        return {"url": url, "error": f"PSI status {response['status']}", "detail": response["text"][:300]}
    data = json.loads(response["text"])

    def field(block):
        metrics = (block or {}).get("metrics", {})
        keys = {"LARGEST_CONTENTFUL_PAINT_MS": "LCP_ms", "INTERACTION_TO_NEXT_PAINT": "INP_ms", "CUMULATIVE_LAYOUT_SHIFT_SCORE": "CLS", "EXPERIMENTAL_TIME_TO_FIRST_BYTE": "TTFB_ms"}
        out = {label: {"p75": metrics[key].get("percentile"), "category": metrics[key].get("category")} for key, label in keys.items() if key in metrics}
        if "CLS" in out and out["CLS"]["p75"] is not None:
            out["CLS"]["p75"] = out["CLS"]["p75"] / 100
        return {"overall": (block or {}).get("overall_category"), "metrics": out} if out else None

    lab = data.get("lighthouseResult", {})
    audits = lab.get("audits", {})
    return {
        "url": url,
        "field_url": field(data.get("loadingExperience")) if data.get("loadingExperience", {}).get("id", "").rstrip("/") == url.rstrip("/") else None,
        "field_origin": field(data.get("originLoadingExperience")),
        "lab_score": round((lab.get("categories", {}).get("performance", {}).get("score") or 0) * 100),
        "lab": {k: audits.get(k, {}).get("displayValue") for k in ("largest-contentful-paint", "total-blocking-time", "cumulative-layout-shift", "server-response-time")},
        "top_opportunities": [audits[k]["title"] for k in sorted((k for k, v in audits.items() if v.get("details", {}).get("type") == "opportunity" and (v.get("numericValue") or 0) > 300), key=lambda k: -audits[k].get("numericValue", 0))][:5],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("start", help="Canonical homepage URL")
    parser.add_argument("--out", required=True, help="Output JSON file")
    parser.add_argument("--urls", nargs="*", default=[], help="Important URLs to test (money pages, a blog post, a template page)")
    parser.add_argument("--psi", action="store_true", help="Run PageSpeed Insights (mobile) on the homepage and --urls")
    args = parser.parse_args()

    start = normalize_url(args.start)
    landing = fetch(start)
    home = landing["final_url"] if landing["status"] == 200 else start
    origin = f"{urlsplit(home).scheme}://{urlsplit(home).netloc}"
    robots_preview = parse_robots(fetch(origin + "/robots.txt")["text"])
    sample = [home] + [normalize_url(u) for u in args.urls if normalize_url(u)]
    if len(sample) < 4:
        sitemap = load_sitemaps(sitemap_seeds(origin, robots_preview["sitemaps"]), limit_files=5, limit_urls=200)
        sample += [u for u in list(sitemap["urls"])[:: max(1, len(sitemap["urls"]) // 6)] if u not in sample][: 8 - len(sample)]
    if len(sample) < 2 and landing["status"] == 200:
        sample += [link["url"] for link in extract(landing["text"], home)["links"] if bare_host(link["url"]) == bare_host(home) and urlsplit(link["url"]).path not in ("", "/") and not urlsplit(link["url"]).query][:5]
        sample = list(dict.fromkeys(sample))
    inner = next((u for u in sample if urlsplit(u).path not in ("", "/")), None)

    report = {
        "start": start,
        "home": home,
        "hosts": host_variants(home),
        "robots": robots_check(origin, sample),
        "bot_fetch": bot_fetch(home),
        "bot_fetch_inner": bot_fetch(inner) if inner else None,
        "url_variants": url_variants(inner) if inner else None,
        "soft_404": soft_404(origin),
        "llms_txt": llms_txt(origin),
        "stack": detect_stack(home),
        "sample_urls": sample,
    }
    if args.psi:
        report["psi"] = [psi(u) for u in [home] + [u for u in sample[1:4]]]

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(report, indent=1, ensure_ascii=False))
    blocked = [v["token"] for v in report["robots"]["verdicts"] if v["blocked_urls"] and v["purpose"] in ("search", "ai_search", "ai_user")]
    print(f"Home: {home} | single origin: {report['hosts']['single_origin']} | robots.txt {report['robots']['status']}")
    print(f"robots.txt blocks search/AI-answer agents: {blocked or 'none'} | CDN: {report['bot_fetch']['reading']}")
    print(f"Soft 404 ok: {report['soft_404']['ok']} | stack: {report['stack']['cms_or_framework']} | wrote {args.out}")


if __name__ == "__main__":
    main()
