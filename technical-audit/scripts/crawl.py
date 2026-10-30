#!/usr/bin/env python3
"""Crawl a site's raw HTML (no JavaScript) and summarize the SEO-relevant technical facts.

Usage:
  python3 crawl.py https://example.com --out ./audit-run [--max-pages 500] [--workers 8]

What it does:
- reads robots.txt and every sitemap it declares (or /sitemap.xml), recursively
- crawls breadth-first from the start URL, following internal <a href> links, to measure click depth
- then fetches sitemap URLs the link crawl never reached (orphan candidates), within --max-pages
- respects robots.txt for its own user agent and records blocked URLs instead of fetching them

Writes to --out:
- pages.jsonl   one line per fetched URL (status, redirect chain, title, canonical, robots, h1, words, links...)
- links.csv     internal links, one row per source/target/anchor (self-links dropped):
                template = navigation (nav/header/footer markup, or repeated on most pages, like the logo)
                counts = 0 when the source is noindex or meta-nofollow, so search engines ignore the link
- sitemap.json  sitemap files and URLs
- summary.json  aggregated checks with counts and example URLs (read this first)

The raw HTML is what non-rendering crawlers see (GPTBot, ClaudeBot, PerplexityBot, most SEO tools in
default mode). Use render_check.py to compare it with the rendered DOM.
"""

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))

from seo_html import (  # noqa: E402
    BROWSER_UA,
    TRACKING_PARAMS,
    bare_host,
    extract,
    fetch,
    is_asset,
    is_noindex,
    load_sitemaps,
    normalize_url,
    parse_robots,
    robots_allows,
    same_site,
    sitemap_seeds,
)

EXAMPLES = 15


def crawl_page(url, user_agent):
    response = fetch(url, user_agent=user_agent)
    headers = response["headers"]
    content_type = headers.get("content-type", "")
    page = {
        "url": url,
        "status": response["status"],
        "final_url": response["final_url"],
        "chain": response["chain"],
        "error": response.get("error"),
        "content_type": content_type.split(";")[0],
        "x_robots_tag": headers.get("x-robots-tag"),
        "elapsed": response["elapsed"],
        "html_bytes": len(response["text"]),
    }
    if response["status"] == 200 and "html" in content_type:
        data = extract(response["text"], response["final_url"])
        data.pop("texts")
        page.update(data)
    return page


def crawl(start, max_pages, workers, user_agent):
    # Crawl from where the start URL lands (e.g. apex -> www), so robots.txt and sitemaps come from the right host.
    landing = fetch(start, user_agent=user_agent)
    start = landing["final_url"] if landing["status"] == 200 else start
    site = bare_host(start)
    robots_response = fetch(f"{urlsplit(start).scheme}://{urlsplit(start).netloc}/robots.txt", user_agent=user_agent)
    robots_text = robots_response["text"] if robots_response["status"] == 200 and "<html" not in robots_response["text"][:500].lower() else ""
    robots = parse_robots(robots_text)
    sitemaps = load_sitemaps(sitemap_seeds(f"{urlsplit(start).scheme}://{urlsplit(start).netloc}", robots["sitemaps"]), user_agent=user_agent)

    origin = f"{urlsplit(start).scheme}://{urlsplit(start).netloc}"
    llms = fetch(origin + "/llms.txt", user_agent=user_agent)
    llms_urls = []
    if llms["status"] == 200 and "<html" not in llms["text"][:500].lower():
        for raw in re.findall(r"https?://[^\s)\]>\"']+", llms["text"]):
            url = normalize_url(raw.rstrip(".,;"))
            if url and same_site(url, site) and url not in llms_urls:
                llms_urls.append(url)

    pages, depth, blocked = {}, {start: 0}, []
    frontier, seen = [start], {start}
    level = 0

    def allowed(url):
        ok, _, rule = robots_allows(robots, "Mozilla", url)  # falls back to the * group
        if not ok:
            blocked.append({"url": url, "rule": rule})
        return ok

    with ThreadPoolExecutor(max_workers=workers) as pool:
        while frontier and len(pages) < max_pages:
            batch = [u for u in frontier if allowed(u)][: max_pages - len(pages)]
            for page in pool.map(lambda u: crawl_page(u, user_agent), batch):
                page["depth"] = level
                pages[page["url"]] = page
            next_frontier = []
            for url in batch:
                page = pages[url]
                followed = [page["final_url"]] if page["chain"] else []
                targets = followed + [link["url"] for link in page.get("links", []) if not link["nofollow"]]
                for target in targets:
                    if same_site(target, site) and not is_asset(target) and target not in seen:
                        seen.add(target)
                        depth[target] = level + 1
                        next_frontier.append(target)
            frontier = next_frontier
            level += 1

        orphans = [u for u in list(sitemaps["urls"]) + llms_urls if u not in seen and same_site(u, site)]
        orphans = list(dict.fromkeys(orphans))
        room = max_pages - len(pages)
        batch = [u for u in orphans[:room] if allowed(u)]
        for page in pool.map(lambda u: crawl_page(u, user_agent), batch):
            page["depth"] = None
            pages[page["url"]] = page

    return {
        "start": start,
        "robots": {"status": robots_response["status"], "text": robots_text, "parsed": robots, "looks_like_html": bool(robots_response["text"]) and not robots_text and robots_response["status"] == 200},
        "sitemaps": sitemaps,
        "llms_txt": {"status": llms["status"], "urls": llms_urls},
        "pages": pages,
        "blocked": blocked,
        "unvisited_frontier": len(frontier),
        "unvisited_sitemap": max(0, len(orphans) - room),
    }


def examples(items):
    items = list(items)
    return {"count": len(items), "examples": items[:EXAMPLES]}


def strip_slash(url):
    parts = urlsplit(url)
    return parts._replace(path=parts.path.rstrip("/") or "/").geturl()


def link_graph(pages, site):
    """Internal link rows plus inlink sets. A link counts as template (navigation) when it sits in
    nav/header/footer markup, or when the same target + anchor appears on more than half of the
    HTML pages (logos, menus built with divs, sidebars). Self-links are dropped. Links on noindex or
    meta-nofollow pages are kept in the rows but do not count as inlinks."""
    html_pages = {u: p for u, p in pages.items() if p["status"] == 200 and "html" in p.get("content_type", "")}
    per_source = {}
    pair_counts = Counter()
    for source, page in html_pages.items():
        own = {strip_slash(source), strip_slash(page["final_url"])}
        links = {}
        for link in page.get("links", []):
            if not same_site(link["url"], site) or is_asset(link["url"]) or strip_slash(link["url"]) in own:
                continue
            key = (link["url"], link["text"].strip().lower())
            if key not in links or (links[key]["template"] and not link["template"]):
                links[key] = link
        per_source[source] = links
        pair_counts.update(links.keys())
    threshold = len(html_pages) / 2 if len(html_pages) >= 6 else float("inf")
    rows, inlinks, contextual = [], defaultdict(set), defaultdict(set)
    for source, links in per_source.items():
        page = html_pages[source]
        robots_values = f"{page.get('meta_robots') or ''},{page.get('x_robots_tag') or ''}".lower()
        counts = not ("nofollow" in robots_values or is_noindex(page.get("meta_robots"), page.get("x_robots_tag")))
        for key, link in links.items():
            template = link["template"] or pair_counts[key] > threshold
            rows.append([source, link["url"], link["text"], int(link["nofollow"]), int(template), int(counts)])
            if counts and not link["nofollow"]:
                inlinks[link["url"]].add(source)
                if not template:
                    contextual[link["url"]].add(source)
    return rows, inlinks, contextual


def sections(pages, indexable_pages, sitemap_urls, contextual, inlinks):
    """For each first path segment with 10+ indexable pages: does its hub page link to them, and how
    many are reachable by links at all? A hub that lists 17 of 211 articles (no crawlable
    pagination) leaves the rest to the sitemap."""
    groups = defaultdict(list)
    for url in indexable_pages:
        segments = [s for s in urlsplit(url).path.split("/") if s]
        if len(segments) >= 2:
            groups[segments[0]].append(url)
    out = []
    for segment, urls in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        if len(urls) < 10:
            continue
        hub = next((u for u in pages if strip_slash(urlsplit(u).path) == "/" + segment and pages[u]["status"] == 200), None)
        hub_links = {l["url"] for l in pages[hub].get("links", [])} if hub else set()
        out.append({
            "section": f"/{segment}/",
            "indexable_pages": len(urls),
            "in_sitemap": sum(1 for u in urls if u in sitemap_urls),
            "hub": hub,
            "hub_links_to_section": sum(1 for u in urls if u in hub_links),
            "not_reachable_by_links": sum(1 for u in urls if indexable_pages[u]["depth"] is None),
            "no_contextual_inlink": sum(1 for u in urls if not contextual.get(u)),
            "median_inlinks": sorted(len(inlinks.get(u, ())) for u in urls)[len(urls) // 2],
            "pagination_links_on_hub": sum(1 for l in hub_links if re.search(r"[?&](page|p|offset)=|/page/\d", l)) if hub else 0,
        })
    return out


def summarize(result):
    pages = result["pages"]
    site = bare_host(result["start"])
    start_scheme = urlsplit(result["start"]).scheme
    sitemap_urls = set(result["sitemaps"]["urls"])
    html_pages = {u: p for u, p in pages.items() if p["status"] == 200 and "html" in p.get("content_type", "")}

    # Final indexability per fetched URL
    def indexable(p):
        if p["status"] != 200 or p["chain"] or "html" not in p.get("content_type", ""):
            return False
        if is_noindex(p.get("meta_robots"), p.get("x_robots_tag")):
            return False
        canonical = p.get("canonical")
        return not canonical or canonical == p["final_url"]

    indexable_pages = {u: p for u, p in pages.items() if indexable(p)}

    rows, inlinks, contextual = link_graph(pages, site)

    status_counts = Counter(str(p["status"]) for p in pages.values())

    # Links to non-200 internal targets
    links_to_redirect, links_to_error = defaultdict(set), defaultdict(set)
    for target, sources in inlinks.items():
        p = pages.get(target)
        if not p:
            continue
        if p["chain"]:
            links_to_redirect[target] |= sources
        elif p["status"] >= 400 or p["status"] == 0:
            links_to_error[target] |= sources

    def with_sources(mapping):
        return examples({"url": t, "status": (pages[t]["chain"] or [{"status": pages[t]["status"]}])[0]["status"], "final_url": pages[t]["final_url"], "linked_from": len(s), "example_source": sorted(s)[0]} for t, s in sorted(mapping.items(), key=lambda kv: -len(kv[1])))

    # Sitemap hygiene
    sm_pages = {u: pages[u] for u in sitemap_urls if u in pages}
    sitemap_issues = {
        "not_fetched": len(sitemap_urls - set(pages)),
        "non_200": examples({"url": u, "status": p["status"]} for u, p in sm_pages.items() if p["status"] != 200 and not p["chain"]),
        "redirected": examples({"url": u, "to": p["final_url"], "status": p["chain"][0]["status"]} for u, p in sm_pages.items() if p["chain"]),
        "noindex": examples(u for u, p in sm_pages.items() if p["status"] == 200 and is_noindex(p.get("meta_robots"), p.get("x_robots_tag"))),
        "canonicalized_elsewhere": examples({"url": u, "canonical": p["canonical"]} for u, p in sm_pages.items() if p.get("canonical") and p["canonical"] != p["final_url"] and not p["chain"]),
        "other_host_or_scheme": examples(u for u in sitemap_urls if urlsplit(u).scheme != start_scheme or urlsplit(u).hostname != urlsplit(result["start"]).hostname),
        "lastmod_coverage": f"{sum(f['lastmod_count'] for f in result['sitemaps']['files'])}/{sum(f['count'] for f in result['sitemaps']['files'] if f.get('type') == 'urlset')}",
    }
    indexable_not_in_sitemap = examples(u for u in indexable_pages if u not in sitemap_urls)

    # Canonicals
    canon = {
        "missing": examples(u for u, p in indexable_pages.items() if not p.get("canonical")),
        "multiple": examples(u for u, p in html_pages.items() if p.get("canonical_count", 0) > 1),
        "points_elsewhere": examples({"url": u, "canonical": p["canonical"]} for u, p in html_pages.items() if p["status"] == 200 and p.get("canonical") and p["canonical"] != p["final_url"]),
        "to_non_200": examples({"url": u, "canonical": p["canonical"], "canonical_status": pages[p["canonical"]]["status"]} for u, p in html_pages.items() if p.get("canonical") in pages and (pages[p["canonical"]]["status"] != 200 or pages[p["canonical"]]["chain"])),
        "to_other_scheme_or_host": examples({"url": u, "canonical": p["canonical"]} for u, p in html_pages.items() if p.get("canonical") and (urlsplit(p["canonical"]).scheme != urlsplit(p["final_url"]).scheme or urlsplit(p["canonical"]).hostname != urlsplit(p["final_url"]).hostname)),
        "parameter_urls_self_canonical": examples(u for u, p in indexable_pages.items() if urlsplit(u).query),
    }

    # Titles and targeting
    titles = defaultdict(list)
    for u, p in indexable_pages.items():
        if p.get("title"):
            titles[p["title"].strip().lower()].append(u)
    on_page = {
        "title_missing": examples(u for u, p in indexable_pages.items() if not p.get("title")),
        "title_duplicate": examples({"title": t, "urls": us[:5], "count": len(us)} for t, us in sorted(titles.items(), key=lambda kv: -len(kv[1])) if len(us) > 1),
        "title_over_65_chars": examples({"url": u, "title": p["title"], "length": len(p["title"])} for u, p in indexable_pages.items() if p.get("title") and len(p["title"]) > 65),
        "title_under_25_chars": examples({"url": u, "title": p["title"]} for u, p in indexable_pages.items() if p.get("title") and len(p["title"]) < 25),
        "h1_missing": examples(u for u, p in indexable_pages.items() if not p.get("h1")),
        "h1_multiple": examples({"url": u, "h1": p["h1"][:3]} for u, p in indexable_pages.items() if len(p.get("h1", [])) > 1),
        "meta_description_missing": examples(u for u, p in indexable_pages.items() if not p.get("meta_description")),
        "lang_missing": examples(u for u, p in html_pages.items() if not p.get("lang")),
        "viewport_missing": examples(u for u, p in html_pages.items() if not p.get("viewport")),
    }

    # Rendering suspicion from raw HTML alone
    rendering = {
        "thin_raw_html": examples({"url": u, "words": p["word_count"], "links": len(p.get("links", []))} for u, p in indexable_pages.items() if p.get("word_count", 0) < 150),
        "few_links_in_raw_html": examples({"url": u, "links": len(p.get("links", []))} for u, p in indexable_pages.items() if len(p.get("links", [])) < 5),
        "fake_links": examples({"url": u, "count": len(p["fake_links"]), "sample": p["fake_links"][:3]} for u, p in html_pages.items() if p.get("fake_links")),
    }

    # Orphans: sitemap URLs (after redirects) that no crawled page links to, under any slash variant.
    def twins(url):
        parts = urlsplit(url)
        path = parts.path.rstrip("/") or "/"
        return {url, parts._replace(path=path).geturl(), parts._replace(path=path if path == "/" else path + "/").geturl()}

    linked = set(inlinks)
    orphans = []
    for url in sorted(sitemap_urls):
        page = pages.get(url)
        if not page or page["status"] != 200 or is_noindex(page.get("meta_robots"), page.get("x_robots_tag")):
            continue
        if page["depth"] is None and not (twins(page["final_url"]) | twins(url)) & linked:
            orphans.append({"url": page["final_url"], "title": page.get("title")})

    # Internal linking
    depths = Counter(p["depth"] for p in indexable_pages.values())
    linking = {
        "pages_by_depth": {("not linked" if k is None else str(k)): v for k, v in sorted(depths.items(), key=lambda kv: 99 if kv[0] is None else kv[0])},
        "orphans_in_sitemap": examples(orphans),
        "deeper_than_3": examples({"url": u, "depth": p["depth"]} for u, p in indexable_pages.items() if p["depth"] is not None and p["depth"] > 3),
        "single_inlink": examples({"url": u, "from": sorted(inlinks[u])[0]} for u in indexable_pages if len(inlinks.get(u, ())) == 1),
        "no_contextual_inlink": examples({"url": u, "all_inlinks": len(inlinks.get(u, ()))} for u in indexable_pages if not contextual.get(u) and u != result["start"]),
        "sections": sections(pages, indexable_pages, sitemap_urls, contextual, inlinks),
        "links_to_redirects": with_sources(links_to_redirect),
        "links_to_errors": with_sources(links_to_error),
        "links_with_other_host_or_scheme": examples(sorted({r[1] for r in rows if r[5] and urlsplit(r[1]).hostname != urlsplit(result["start"]).hostname or urlsplit(r[1]).scheme != start_scheme})),
        "template_targets": sorted({r[1] for r in rows if r[4]})[:80],
        "top_contextual_inlinks": [{"url": u, "contextual_inlinks": len(c), "all_inlinks": len(inlinks.get(u, ()))} for u, c in sorted(contextual.items(), key=lambda kv: -len(kv[1]))[:25]],
    }

    # URL hygiene
    paths = {urlsplit(u).path for u in pages}
    trailing_pairs = sorted(p for p in paths if p != "/" and p.endswith("/") and p.rstrip("/") in paths)
    param_urls = [u for u in pages if urlsplit(u).query]
    tracking = [u for u in param_urls if any(TRACKING_PARAMS.match(k) for k, _ in parse_qsl(urlsplit(u).query))]
    urls = {
        "trailing_slash_duplicates": examples(trailing_pairs),
        "parameter_urls_crawled": examples(param_urls),
        "tracking_params_in_internal_links": examples(tracking),
        "uppercase_paths": examples(u for u in pages if urlsplit(u).path != urlsplit(u).path.lower()),
        "redirect_chains": examples({"url": u, "hops": len(p["chain"]), "final": p["final_url"]} for u, p in pages.items() if len(p["chain"]) > 1),
        "temporary_redirects": examples({"url": u, "status": p["chain"][0]["status"]} for u, p in pages.items() if p["chain"] and p["chain"][0]["status"] in (302, 303, 307)),
    }

    schema = Counter(t for p in indexable_pages.values() for t in p.get("schema_types", []))
    hreflang_pages = [u for u, p in html_pages.items() if p.get("hreflang")]
    slow = sorted(((p["elapsed"], u) for u, p in pages.items() if p["status"] == 200), reverse=True)

    return rows, {
        "start": result["start"],
        "totals": {
            "fetched": len(pages),
            "html_200": sum(1 for p in pages.values() if p["status"] == 200 and "html" in p.get("content_type", "")),
            "indexable": len(indexable_pages),
            "sitemap_urls": len(sitemap_urls),
            "status_codes": dict(status_counts),
            "blocked_by_robots_for_this_crawler": len(result["blocked"]),
            "frontier_left_unvisited": result["unvisited_frontier"],
            "sitemap_urls_left_unvisited": result["unvisited_sitemap"],
        },
        "robots": {"status": result["robots"]["status"], "looks_like_html": result["robots"]["looks_like_html"], "sitemaps_declared": result["robots"]["parsed"]["sitemaps"]},
        "sitemap_files": result["sitemaps"]["files"][:50],
        "sitemap": sitemap_issues,
        "indexable_not_in_sitemap": indexable_not_in_sitemap,
        "llms_txt": {
            "status": result["llms_txt"]["status"],
            "listed_urls": len(result["llms_txt"]["urls"]),
            "redirected_or_broken": examples({"url": u, "status": (pages[u]["chain"] or [{"status": pages[u]["status"]}])[0]["status"], "final_url": pages[u]["final_url"]} for u in result["llms_txt"]["urls"] if u in pages and (pages[u]["chain"] or pages[u]["status"] != 200)),
            "not_in_sitemap": examples(u for u in result["llms_txt"]["urls"] if u not in sitemap_urls and u in pages and not pages[u]["chain"]),
        },
        "noindex_pages": examples(u for u, p in html_pages.items() if is_noindex(p.get("meta_robots"), p.get("x_robots_tag"))),
        "canonicals": canon,
        "on_page": on_page,
        "rendering_suspicion": rendering,
        "internal_linking": linking,
        "urls": urls,
        "schema_types": dict(schema.most_common()),
        "schema_invalid_json": examples(u for u, p in html_pages.items() if p.get("schema_invalid_blocks")),
        "hreflang_pages": len(hreflang_pages),
        "slowest_html_responses_seconds": [{"url": u, "seconds": s} for s, u in slow[:10]],
        "robots_blocked_examples": result["blocked"][:EXAMPLES],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("start", help="Start URL, usually the canonical homepage")
    parser.add_argument("--out", required=True, help="Output directory")
    parser.add_argument("--max-pages", type=int, default=500)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--user-agent", default=BROWSER_UA)
    args = parser.parse_args()

    start = normalize_url(args.start)
    if not start:
        parser.error("start must be an http(s) URL")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    result = crawl(start, args.max_pages, args.workers, args.user_agent)

    with open(out / "pages.jsonl", "w") as handle:
        for page in result["pages"].values():
            handle.write(json.dumps(page, ensure_ascii=False) + "\n")
    rows, summary = summarize(result)
    with open(out / "links.csv", "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["source", "target", "anchor", "nofollow", "template", "counts"])
        writer.writerows(rows)
    (out / "sitemap.json").write_text(json.dumps({"files": result["sitemaps"]["files"], "urls": result["sitemaps"]["urls"]}, indent=1, ensure_ascii=False))
    (out / "summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False))
    totals = summary["totals"]
    print(f"Fetched {totals['fetched']} URLs ({totals['indexable']} indexable, {totals['sitemap_urls']} in sitemaps). Status codes: {totals['status_codes']}")
    if totals["frontier_left_unvisited"] or totals["sitemap_urls_left_unvisited"]:
        print(f"Partial crawl: {totals['frontier_left_unvisited']} discovered and {totals['sitemap_urls_left_unvisited']} sitemap URLs not fetched (raise --max-pages).")
    print(f"Wrote {out}/summary.json, pages.jsonl, links.csv, sitemap.json")


if __name__ == "__main__":
    main()
