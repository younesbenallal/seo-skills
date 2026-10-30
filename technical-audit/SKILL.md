---
name: technical-audit
description: Run a focused technical audit of a website for SEO, GEO (AI answers), and CRO, and deliver a prioritized HTML report. Checks only what moves results - crawl and index access, AI crawler access (robots.txt and CDN blocking), presence in Google, Bing, Brave and DuckDuckGo, canonicalization, JavaScript rendering, one clear keyword per page, cannibalization, internal linking, field speed, schema suggestions, and the technical conversion path. Use when the user asks for a technical audit, a tech SEO check, a site health check, "why isn't my site indexed / cited by ChatGPT", or an audit report for a client or prospect.
---

# Technical audit

Find the few technical problems that limit traffic, AI citations, or conversions, prove each one, and hand over a report that says what to fix first. This is not a checklist dump: a check that cannot change rankings, citations, or conversions does not belong in the findings.

Most SEO problems are authority problems, not technical ones. Say so when the site is technically clean, and keep the report short.

## Preflight

Run the shared [task preflight and tooling contract](../docs/credentials-and-tooling.md). Read `.seo-context.md` when present: canonical domain, money pages and their target keywords, clusters, markets, and the tooling inventory. Read earlier audits of the same site in the project so you report what changed instead of starting over.

Then ask once, in one compact checkpoint (the user can skip):

- the canonical domain and the market (language, country);
- the money pages and their target keywords, if `.seo-context.md` does not list them;
- the report language and where to save the run folder (suggest `<project>/audits/technical-audit-YYYY-MM-DD/`);
- whether the user has Screaming Frog (licence or MCP) or wants the built-in crawler.

## Tooling and credentials

- Auth mode: `none` for the core audit; `mcp` for Search Console
- Requires: Python 3 (standard library only)
- Recommended: Google Search Console MCP (indexing, cannibalization, keyword alignment), a browser tool (Bing/Brave/DuckDuckGo checks, CRO checks, AI fetch test), Google Chrome or Chromium (rendering check)
- Optional: `PAGESPEED_API_KEY` env var (the keyless PageSpeed quota is often exhausted), Screaming Frog or LibreCrawl for large sites ([references/crawlers.md](references/crawlers.md)), Bing Webmaster Tools access
- Fallback: without GSC, run every crawl-based check and list index coverage, cannibalization, and query alignment under `limits`. Without a browser, mark engine presence `unknown`.

Scripts live in `scripts/`. Run them with `python3 <skill-dir>/scripts/<name>.py`. Put every output in the run folder, never in the skill folder.

## Workflow

### 1. Crawl the raw HTML

```bash
python3 scripts/crawl.py https://example.com --out <run>/ --max-pages 1000
```

It reads robots.txt and sitemaps, crawls internal `<a href>` links breadth-first (raw HTML, like AI crawlers), fetches sitemap and `llms.txt` URLs that links never reach, and writes `summary.json`, `pages.jsonl`, `links.csv`, and `sitemap.json`. Read `summary.json` first; open `pages.jsonl` or `links.csv` only for the detail a finding needs.

In `links.csv`, `template=1` marks navigation: links inside nav/header/footer markup, or the same target and anchor repeated on more than half of the pages (logo, menus built with divs). `counts=0` marks links on noindex or nofollow pages, which search engines ignore. `internal_linking.sections` compares each section's hub with its pages: a hub that links to 50 of 209 articles without crawlable pagination is the usual cause of pages reachable only through the sitemap. "Related articles" blocks count as contextual; check their anchors before calling a page well supported.

If the crawl is partial (the script says so), raise `--max-pages`, or for very large sites crawl one section at a time, or use a dedicated crawler (see [references/crawlers.md](references/crawlers.md)). Suggest Screaming Frog when the user has a licence, and LibreCrawl (free) as the alternative; install LibreCrawl only with their approval. Never present a partial crawl as complete.

### 2. Site-level checks

```bash
python3 scripts/site_checks.py https://example.com --out <run>/site.json --urls <money page> <blog post> <other template> --psi
```

Host and protocol variants, robots.txt verdicts for every search and AI agent, CDN/WAF blocking by user agent, trailing-slash and parameter variants, soft 404, the text of llms.txt, stack and analytics detection, and PageSpeed field data. Read the llms.txt text like page copy: AI systems may quote it, so outdated offers, wrong prices, or wording the client may not use are findings; `summary.json` > `llms_txt` lists the URLs in it that redirect, break, or are missing from the sitemap. Read [references/ai-crawlers.md](references/ai-crawlers.md) before writing any AI-access finding: a refused spoofed user agent is not proof of a block.

### 3. JavaScript rendering

Pick one URL per template: home, a money page, a blog post, a category or hub, a programmatic page.

```bash
python3 scripts/render_check.py <url> <url> ... --out <run>/render.json
```

It compares the raw HTML with headless Chrome's DOM. Read `text_only_after_js_sample` before concluding: cookie banners and chat widgets are filtered, but check the sample is real page content. Without Chrome, save `document.documentElement.outerHTML` from a browser tool and pass `--rendered URL=FILE`.

### 4. Search Console

Resolve the property per the shared contract, use the last 90 complete days, and record the property and range.

- Indexing: `batch_url_inspection` or `check_indexing_issues` on money pages and one URL per template. Some GSC MCPs cap a batch at 10 URLs: split the list. When the batch result omits the Google-selected canonical, use the single-URL inspection tool (e.g. `inspect_url_enhanced`) on money pages, and note the canonical whenever it differs from the page.
- Sitemaps: `get_sitemaps` for submission dates and errors. Its `indexed` count is a deprecated API field that echoes the submitted count; never report it as indexed pages.
- Funnel: sitemap URLs, indexed, URLs with impressions, URLs in the top 3 for at least one query. The API has no site-wide indexed count: use the number from the user's Pages report if they give it, otherwise "indexed among N inspected URLs" with N stated, otherwise drop that row.
- Cannibalization: pull `query,page` (page through all rows), save the file, then run `python3 ../gsc-analysis/scripts/gsc_rows.py cannibalization <file>` and keep the cases on money or BOFU queries. Drop pages that now redirect or 404 in `pages.jsonl`: Search Console keeps reporting old URLs for weeks, and a redirected URL is already consolidated. Follow the cannibalization rules in `../gsc-analysis/references/recipes.md`.
- Query alignment for the keyword map (step 6): top queries per strategic page.

### 5. Presence in other engines

Use a browser tool. Scripts get blocked or served wrong results by these engines.

- Bing: `site:<domain>`, then `site:<domain>/<money-page-path>` for each money page. If the user has Bing Webmaster Tools, check its URL inspection instead.
- Brave: `https://search.brave.com/search?q=site%3A<domain>` (Brave's index feeds Claude).
- DuckDuckGo: `site:<domain>` (its results come mostly from Bing; a gap here usually means a Bing gap).
- Staging and duplicate hosts: `site:<project>.webflow.io`, `site:<project>.vercel.app`, `site:staging.<domain>`, and any former domain. The staging name is rarely in the HTML: look in the client's project files and notes, or ask. Record them in `index_presence` with `"expected": "absent"` so a correct absence shows as good.

Bing often ignores `site:` (it returns unrelated pages) or shows a CAPTCHA. Then search the quoted domain (`"example.com"`) and each money page's exact title in quotes with the brand: the page appearing with its own URL proves it is indexed. Never solve a CAPTCHA; mark the engine `unknown`.

Record `indexed`, `partial` (some money pages missing), `absent`, or `unknown` (blocked, CAPTCHA) with what you saw. Do not trust result counts.

If a browser tool is available, also ask ChatGPT (search on), Perplexity, or Claude to open a money page and quote its H1. A correct quote proves AI agents can read the page.

### 6. One page, one keyword

Build `keyword_map` for the homepage, money pages, hubs, and the top 20 GSC pages, following section 5 of [references/checks.md](references/checks.md). Propose a rewritten title for every page that is `no-target`, `mismatch`, or `weak`. Keep the brand at the end and the keyword first.

### 7. Internal linking

From `summary.json` and `links.csv`: orphans, depth, fake links, links to redirects or errors, and the contextual links each money page receives (exclude `template=1` and sitewide links). Then propose up to 10 contextual links from pages that already earn clicks to the money or hub pages of the same cluster, after checking the passage exists. Offer the `internal-linking` skill for a full plan.

### 8. CRO, speed, schema

Run the CRO checks in section 9 of [references/checks.md](references/checks.md) on the homepage and money pages at mobile width. Report speed only from field data. Add schema suggestions per template, always low priority.

`site_checks.py --psi` returns `field_url` only when Google has data for that exact URL; `field_origin` is the whole site. When the keyless API returns 429, open https://pagespeed.web.dev/analysis?url=<url> in a browser tab in the foreground (background tabs do not render the results), wait for the report, and read the "Discover what your real users are experiencing" block with its "This URL" / "Origin" switch. If "This URL" has no data, the numbers shown are the origin's: label them so, and do not repeat identical origin values for every page.

### 9. Prioritize and write

Go through [references/checks.md](references/checks.md) and keep only failing checks. Assign impact by what the issue touches (money pages and large shares of the site first), merge findings with one root cause, and pick the top 3 by impact-to-effort. Put tool-flagged noise the client may have seen in `ignored`, and everything not checked in `limits`.

Write `audit.json` following [references/report.md](references/report.md), render it, and open the HTML in a browser to check it before delivering:

```bash
python3 scripts/render_report.py <run>/audit.json --out <run>/report.html
```

## Output

1. In chat: the verdict, the top 3 actions, and the count of findings per impact.
2. The path to `report.html` (and send the file when the runtime supports it).
3. Offer the follow-ups that fit: the `internal-linking` plan, `gsc-analysis` for deeper query work, `geo-audit-report` to measure AI visibility, or applying fixes the user owns (robots.txt, titles, redirects) after explicit approval.

Never change robots.txt, CDN settings, redirects, or CMS content without explicit approval for that change.

## Related skills

- `seo-roast`: a deep review of one page's content and intent.
- `gsc-analysis`: traffic drops, decay, quick wins, CTR gaps.
- `internal-linking`: the full linking plan and approved edits.
- `geo-audit-report`: measure mentions and citations in ChatGPT, Perplexity, and Gemini.
