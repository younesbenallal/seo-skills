# Check catalogue

Each check says where its evidence comes from, when it is a finding, and its default impact. Raise or lower the impact by what the issue touches: a problem on money pages or on most of the site is worth more than the same problem on an old blog post. Report a check only when it fails; passing checks go in the scorecard note.

Sources: `S` = `summary.json` from `crawl.py`, `site` = `site.json` from `site_checks.py`, `R` = `render.json` from `render_check.py`, `GSC` = Search Console MCP, `B` = browser.

## 1. Crawl and index access

| Check | Evidence | Finding when | Impact |
| --- | --- | --- | --- |
| robots.txt reachable | `site.robots.status`, `served_html_instead_of_text` | 5xx (Google reads it as disallow-all), HTML served, or 404 on a site that needs rules | 5xx: critical. HTML: high. 404: low, unless the sitemap is not declared anywhere else |
| Important paths blocked | `site.robots.verdicts` for search agents, `S.robots_blocked_examples` | Googlebot or Bingbot blocked from pages that should rank, or from CSS/JS needed to render | critical |
| Sitemap exists and is declared | `S.sitemap_files`, `site.robots.sitemaps` | No sitemap, not declared in robots.txt, or not submitted in GSC | missing on a site over 50 pages: high; not declared: low |
| Sitemap hygiene | `S.sitemap.*` | Redirected, non-200, noindex, or canonicalized-away URLs listed | medium; high when they are over 10% of the sitemap |
| Indexable pages missing from sitemap | `S.indexable_not_in_sitemap` | Strategic pages missing | medium |
| noindex on pages that should rank | `S.noindex_pages`, `GSC` | Any money page, template, or cluster page with noindex | critical |
| Soft 404 | `site.soft_404.ok` | Random URL returns 200 | medium |
| Index coverage | `GSC` (`check_indexing_issues`, `batch_url_inspection` on money pages and one URL per template, `get_sitemaps`) | Money pages "Discovered/Crawled – currently not indexed", Google-selected canonical different from the page, large share of the sitemap not indexed | critical for money pages; high when over 30% of the sitemap |
| Indexed in Bing, Brave, DuckDuckGo | `B` (see SKILL.md step 5) | Site or money pages absent | Bing absent: critical for GEO (it feeds Copilot, DuckDuckGo, and ChatGPT search). Brave absent: high (it feeds Claude) |
| Staging or duplicate hosts indexed | `B` `site:` queries on `*.webflow.io`, `*.vercel.app`, `staging.`, `dev.`, old domains | Copies of the site indexed | high |

## 2. AI access (GEO)

Read [ai-crawlers.md](ai-crawlers.md) first.

| Check | Evidence | Finding when | Impact |
| --- | --- | --- | --- |
| AI search and user agents allowed in robots.txt | `site.robots.verdicts` where `purpose` is `ai_search` or `ai_user` | Any blocked on pages the business wants cited | critical |
| Edge blocking | `site.bot_fetch.reading`, `site.bot_fetch_inner` | Googlebot passes and AI agents are refused | critical (confirm before stating as fact). Agents in `bot_fetch.untested` have no published user agent: report their CDN status as `untested` |
| Content Signals | `site.robots.content_signals` | `ai-input=no` | high |
| Training agents blocked | `site.robots.verdicts` where `purpose` is `training` | Blocked | information only; state it in the AI table, not as a finding, unless the user wants training access |
| Content readable without JS | `R` | See section 4 | |
| llms.txt presence | `site.llms_txt` | Absence is never a finding above low | low |
| llms.txt content | `site.llms_txt[*].text`, `S.llms_txt` | Wrong or outdated claims, wording the client may not use, links to redirected or broken URLs, or to pages missing from the sitemap | medium (AI systems may quote it); high when it contradicts compliance rules |

## 3. Canonicalization and duplicates

| Check | Evidence | Finding when | Impact |
| --- | --- | --- | --- |
| One origin | `site.hosts.single_origin`, `https_enforced` | http/https or www/non-www variants serve 200 without redirecting | high |
| Permanent redirects | `site.hosts.temporary_or_unusual_redirects`, `S.urls.temporary_redirects` | 302/307 for permanent moves (host, http→https) | medium |
| Redirect hops | `site.hosts.multi_hop`, `S.urls.redirect_chains` | More than one hop | low; medium for internal links |
| Every indexable page has a canonical | `S.canonicals.missing` | Missing on templates | medium; high when variants also return 200 (see below) |
| Self-referencing canonicals | `S.canonicals.points_elsewhere` | A unique page canonicalizes elsewhere (template bug, all pages to home) | critical when it hits money pages or a template |
| Canonical targets | `S.canonicals.to_non_200`, `to_other_scheme_or_host` | Canonical to a redirect, 404, http, or other host | high |
| Trailing slash | `site.url_variants.trailing_slash_toggled`, `S.urls.trailing_slash_duplicates` | Both versions 200 without a canonical to one | high when internal links use both; medium otherwise |
| Parameters | `site.url_variants.tracking_param`, `search_param`, `S.canonicals.parameter_urls_self_canonical`, `S.urls.parameter_urls_crawled` | Parameter URLs 200 with a self canonical or none, or linked internally | medium; high when faceted or search URLs are crawlable at scale |
| Internal search pages | `B` site search, `S.urls.parameter_urls_crawled` | `/search?q=` pages indexable or linked | medium |
| Uppercase | `site.url_variants.uppercase` | 200 without redirect or canonical | low |
| Cannibalization | `GSC` + `../gsc-analysis/scripts/gsc_rows.py cannibalization` | Two pages share a money query (each 10%+ of its impressions, positions unstable) | high on money queries, medium otherwise |

## 4. JavaScript rendering

Non-rendering crawlers (all AI crawlers, Bing in most cases, Google before rendering) only see the raw HTML.

| Check | Evidence | Finding when | Impact |
| --- | --- | --- | --- |
| Main content in raw HTML | `R.verdict`, `raw_share_of_rendered_text`, `text_only_after_js_sample` | `js-dependent` on any template that should rank | critical |
| Title, canonical, robots, H1 in raw HTML | `R.changed_or_js_only` | Changed or added by JS | critical for robots and canonical; high for title and H1 |
| Links in raw HTML | `R.links_only_after_js`, `S.rendering_suspicion.few_links_in_raw_html` | Navigation or contextual links exist only after JS | high |
| Fake links | `S.rendering_suspicion.fake_links` | Navigation built with `<div role="link">`, `onclick`, `data-href`, or encoded URLs (`data-ofb64`) instead of `<a href>` | high when it hides money pages or categories from crawlers |
| Structured data injected by JS | `R.schema_only_after_js` | JSON-LD only after rendering | low (Google reads it late; AI crawlers never) |
| Empty shell | `site.stack.empty_js_shell` | Homepage raw HTML is an empty app root | critical |

`S.rendering_suspicion.thin_raw_html` only tells you where to run `render_check.py`; never report it alone as a JS problem. A landing page can be short and fully server-rendered. Never report "no structured data" from raw HTML alone: check `R` or a browser first.

## 5. One page, one keyword (on-page targeting)

Scope: the homepage, every money page, category or hub pages, and the 20 pages with the most clicks or impressions in GSC.

For each page, record the target keyword (from `.seo-context.md`, otherwise inferred from title, H1, URL, and the top GSC queries), then check:

- **Clear target**: the title and H1 name one search intent. Generic titles ("Home", "Features", "Solutions", "Platform", brand only) are `no-target`. The homepage should target the category query the product wants to own ("[category] software for [ICP]"), plus the brand.
- **Title quality**: primary keyword in the first 50 characters, specific benefit or qualifier, brand at the end, unique across the site. Length matters only when truncation cuts the keyword (`S.on_page.title_over_65_chars`); otherwise ignore it.
- **Alignment with demand**: compare the target with the page's top GSC queries over 90 days. `aligned` when the top non-brand query matches the target intent; `mismatch` when the page earns impressions for another intent (rewrite the title for the query it ranks for, or create the page that targets the other one); `weak` when it ranks for the target beyond position 20 and a quick title or H1 change could help.
- **Duplicates**: `S.on_page.title_duplicate` among indexable pages.
- **Missing H1 or title**: `S.on_page.h1_missing`, `title_missing`.

Impact: a money page or the homepage with no clear target is high. A mismatch on a page with real impressions is medium to high. Title tweaks on low-traffic pages are low. Put the full table in `keyword_map` and the pages that need action in findings.

## 6. Internal linking

Use `S.internal_linking` and `links.csv`, and the playbook logic: authority flows from pages that already earn clicks and links (cornerstones) to the pages that need to rank, within the same topic.

| Check | Evidence | Finding when | Impact |
| --- | --- | --- | --- |
| Orphans | `S.internal_linking.orphans_in_sitemap` | Sitemap pages with no internal link (links from noindex or nofollow pages do not count) | high for money pages, medium otherwise |
| Hub coverage | `S.internal_linking.sections` | A section hub links to a small share of its pages and has no crawlable pagination, so `not_reachable_by_links` is high | high when it hides more than 20% of a section |
| No contextual support | `S.internal_linking.no_contextual_inlink` | Pages linked only from navigation | medium; high for money pages |
| Depth | `pages_by_depth`, `deeper_than_3` | Money pages deeper than 3 clicks, or `not linked` count is large | medium to high |
| Money pages' contextual support | `links.csv` filtered on `template=0` and `counts=1`, `top_contextual_inlinks` | A money page receives fewer contextual links than average, or none from the pages that earn the most clicks in its cluster | high |
| Links to redirects and errors | `links_to_redirects`, `links_to_errors` | Internal links point to 3xx or 4xx | medium (errors), low (redirects) |
| Mixed hosts or protocols | `links_with_other_host_or_scheme` | Internal links to http:// or the other www variant | medium |
| Fake links | section 4 | | |

Then propose up to 10 links in `internal_links`: source = a page with clicks (GSC) in the same cluster, target = a money or hub page that needs support, with a natural anchor and the sentence where it fits. Check the passage exists in the source page before proposing it. For a full plan, hand off to the `internal-linking` skill.

## 7. Speed (secondary)

Only field data (CrUX) is a finding. Run `site_checks.py --psi` on the homepage and up to 3 money pages.

- `field_url` or `field_origin` in `POOR` for LCP or INP on money pages: medium (high when it is also a conversion page with ad or SEO traffic).
- `AVERAGE`: low, mention only.
- No field data: report lab values as context in `speed`, never as a finding.
- Lab score alone is never a finding.

PSI without `PAGESPEED_API_KEY` shares a public quota and often returns 429. Then use https://pagespeed.web.dev in a browser for the homepage and one money page, or skip and list it in `limits`.

## 8. Structured data (suggestions)

Never above low, never a blocker. Suggest, per template, what is missing and useful:

- Home: `Organization` (logo, sameAs), `WebSite`.
- Product or pricing pages: `SoftwareApplication` or `Product` with `offers` when prices are public.
- Articles: `Article` with author and dates, `BreadcrumbList`.
- Comparison or FAQ sections: `FAQPage` only when the Q&A is visible on the page.
- Fix invalid JSON-LD (`S.schema_invalid_json`) and GSC rich-result errors before adding anything.

## 9. CRO (technical layer only)

On the homepage and money pages, in a browser at mobile width:

- The primary CTA is a real `<a href>` or `<button>` in the raw HTML and visible in the first viewport.
- CTA and booking links resolve (no 404, no redirect to the homepage); forms load (do not submit them).
- Analytics is installed (`site.stack.analytics`) so SEO conversions can be measured; flag none detected as high.
- No interstitial or cookie banner hides the main content on mobile.
- Pages ranking for commercial queries have a conversion path; a top-traffic article with no link to a money page is a CRO finding.

Copy and design critique is out of scope: point to the `cro` or `seo-roast` skills.

## Noise: never report as findings

List the ones a client may have seen in another tool under `ignored`, with one line on why.

- Missing alt text counts, image file sizes (unless they cause poor field LCP).
- Meta description length or absence (Google rewrites most snippets). Exception: a money page with a generic or duplicate description can be a CTR quick win.
- Multiple H1s, heading order, text-to-HTML ratio, word count on landing pages.
- Meta keywords, W3C validation, HTML size under 2 MB, missing Open Graph or Twitter cards (social, not search).
- Security headers, HTTP/2, cookie flags.
- Lab-only performance scores, "moderate response time".
- llms.txt absence (low at most).
- Nofollow on external links, links without anchor text in icon-only footers.
- "Duplicate content" flags on pagination or tag archives that are already noindex.
