# GSC analysis recipes

Each recipe lists the pulls, the script command, the thresholds, and how to read the result. `S` below means `python3 <skill>/scripts/gsc_rows.py`. All thresholds are defaults: adjust them to the site's size and say so.

Tool calls are written generically as `analytics(dimensions, start, end, filters)`. With `AminForou/mcp-gsc`, this is `get_advanced_search_analytics` with `site_url`, `start_date`, `end_date`, `dimensions`, `filters` (JSON), `row_limit`, `start_row`.

## Health check

- Pull `analytics(date, 16 months)`.
- `S aggregate trend.json --by month` (use `--by week` to find the exact break).
- Then `analytics(page, last 28 days)` and the prior 28 days; run the drop diagnosis comparison below even when the trend looks flat, to see what moves underneath.
- Read CTR and position together: clicks down with impressions stable and position worse is a ranking loss; clicks and impressions down with position stable is lost query coverage or demand.

## Drop diagnosis

1. Find the break: `S aggregate trend.json --by week`, then daily rows around the break week.
2. Pull `page` for two equal windows on each side of the break (e.g. 28 days before, 28 days after, excluding the break week).
3. `S compare --before before.json --after after.json --by page`
4. Read the `diagnosis` column:

| Diagnosis | Rule | Usual meaning | Next check |
|---|---|---|---|
| ranking drop | position worse by > 2 | lost rankings | SERP for the main queries, competitors, content age |
| impressions loss, position stable | impressions < 70% of before | page shown for fewer queries, SERP change, partial deindexing | `compare --by query` filtered to the page; URL inspection |
| CTR collapse, position stable | CTR < 70% of before | SERP features or AI Overview taking clicks, worse snippet | inspect the live SERP |
| disappeared | no rows after, ≥ 5 clicks before | deindexed, redirected, removed, canonicalized away | URL inspection, redirects, sitemap |
| stable / demand | none of the above | seasonal or demand change | year-over-year comparison |

5. `share_of_total_change` shows which pages explain the loss. Usually a few pages explain most of it: focus there.
6. Drill into the top pages with `compare --by query` on a `page equals <url>` filter.
7. Line the break date up with site changes (CMS publish logs, migrations, template changes) and known Google update dates. Report these as hypotheses unless confirmed.

## Content decay

- Pull `page` for three consecutive 30-day windows (oldest, middle, newest), ending before the incomplete days.
- `S decay --periods p1.json p2.json p3.json --by page`
- Flags pages whose clicks fell in both steps, with at least 10 clicks in the oldest window.
- `rankings declining` means refresh content and links; `rankings stable (CTR or demand decline)` means inspect the SERP and snippet first.

## Quick wins

- Pull `query` (or `query,page` to know the target URL) for the last 28 days.
- `S opportunities quick-wins q.json` : positions 4-15, ≥ 100 impressions.
- `potential_extra_clicks` = impressions × (expected CTR at position 3 − current CTR).
- Action: strengthen the page that already ranks (answer depth, subqueries as sections, internal links from related pages, title), not a new page.

## CTR gap

- Pull `page` or `query` for 28-90 days.
- `S opportunities ctr-gap pages.json --by page` : positions ≤ 20, ≥ 500 impressions, CTR at least 1 point under the curve.
- Expected CTR by position 1-10: 28.5, 15.7, 11.0, 8.0, 7.2, 5.1, 4.0, 3.2, 2.8, 2.5 %. The curve is an average; branded or SERP-feature-heavy queries deviate.
- The `note` column flags top-3 rows with CTR under 1%: the SERP answers the query. Recommend a reason to click instead of a title test.
- Otherwise: test a new title and meta description, keep the old version and date, and re-measure after 3-4 weeks.

## Content gaps

- Pull `query` for 90 days.
- `S opportunities content-gaps q.json` : positions > 20, ≥ 50 impressions.
- Group the results by topic. A gap becomes a new page only when no existing page covers the intent; otherwise it is a new section.

## Cannibalization

- Pull `query,page` for 90 days, paging until complete.
- `S cannibalization qp.json` : ≥ 2 pages each holding ≥ 10% of a query's impressions, ≥ 50 impressions total.
- Confirm with position volatility (daily rows for the query) and the live SERP. If two pages share most of their top-10 results, Google treats them as the same intent.
- Pick the winner: best position, then most clicks over 90 days, then most backlinks; tiebreaker is fewer internal links to update.
- Fix: merge the unique content into the winner, 301 the others, update internal links. Canonicals are only a hint. Avoid year-specific URLs competing with an evergreen one.

## Intent and brand segmentation

- Pull `query` for the period.
- `S segment q.json --segment 'brand=<brand terms>' --segment 'bofu=<regex>' --segment 'info=<regex>'`. First match wins, so put brand first.
- English BOFU: `\b(best|top|vs|versus|alternatives?|compar(e|ison)|pricing|price|cost|reviews?|software|tools?|platforms?|solutions?|agency|services?|consultant)\b`
- English informational: `\b(how to|guide|tutorial|step by step|tips|ways to|learn|what is|meaning|definition|examples?)\b`
- French BOFU: `\b(meilleur(e|s)?|avis|comparatif|vs|alternative|prix|tarifs?|co[uû]t|devis|logiciel|outil|plateforme|agence|cabinet|consultant|expert)\b`
- French informational: `\b(comment|pourquoi|qu.est.ce|d[ée]finition|exemples?|guide|tuto(riel)?|[ée]tapes?|astuces?)\b`
- Read: share of clicks and impressions by segment, CTR and position per segment. Commercial segments with high impressions and low position are the priority list.

## Page refresh inputs

- Pull `query` filtered on `page equals <url>` for 90 days.
- List the queries the page gets impressions for but does not answer explicitly: they become sections, FAQ entries, or examples.
- For the full edit workflow, hand off to `subkeyword-injector`.
- A page that still does not rank after a few months of work can be moved to a fresh URL with a 301; recommend it only with that history.

## GEO query signals

- `S segment q.json --segment 'conversational=^(how|what|why|which|when|where|can|should|is|are|do|does|comment|pourquoi|quel(le)?s?|est-ce)(\s+\S+){9,}'`
- Long question queries (10+ words) look like prompts. Treat them as input for GEO pages and answer-first sections, not as a traffic source.

## Indexing checks

- For the pages behind a drop, and for every money page: batch URL inspection (verdict, coverage state, Google-selected canonical, last crawl).
- Check sitemap status and errors.
- A Google-selected canonical different from the page means consolidation or duplication, not a content problem.
