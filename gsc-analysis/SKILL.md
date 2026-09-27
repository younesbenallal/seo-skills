---
name: gsc-analysis
description: Analyze Google Search Console performance for a site and turn it into prioritized SEO actions. Use when the user asks to check, audit, or explain GSC data - traffic drops, content decay, quick wins, CTR problems, cannibalization, content gaps, brand vs non-brand or intent splits, indexing checks, or "what should we work on" from Search Console.
---

# GSC analysis

Turn Search Console data into a diagnosis and a short list of actions ranked by business impact. Every number comes from GSC; every cause is labelled as a hypothesis unless the data proves it.

## Preflight

Run the shared [task preflight and tooling contract](../docs/credentials-and-tooling.md). For this skill:

- Resolve the GSC property from the accessible list (`sc-domain:` and URL-prefix variants), and state which one you use.
- Read `.seo-context.md` and any existing analyses in the project first, so you do not repeat them and so priorities follow the confirmed money pages, ICP, and conversions.
- Confirm the question: health check, drop diagnosis, opportunities, a specific page or cluster. Default to a health check plus opportunities when the user just says "check the GSC".

## Tooling & credentials

- Auth mode: `mcp`
- Requires: a GSC MCP whose search analytics tool accepts a property, an explicit start/end date, dimensions, filters, and paging. [`AminForou/mcp-gsc`](https://github.com/AminForou/mcp-gsc) covers all of these (`get_advanced_search_analytics`: `row_limit` up to 25,000, `start_row`, `start_date`/`end_date`, `site_url` on every tool, plus `batch_url_inspection`).
- MCPs that bind one default property or only accept "last N days" still work for the default property; say which analyses they prevent.
- Script: [`scripts/gsc_rows.py`](scripts/gsc_rows.py), Python 3 standard library only.
- Fallback: none for live data. A user-provided GSC UI export can be analyzed with the script, labelled as an export.
- If missing: stop, ask the user to connect a GSC MCP, and continue after they confirm.

## Data rules

Apply these before reading any number:

1. **Exclude the last 2-3 days** (incomplete data) or request final data only.
2. **Impressions are not search volume**, and anonymized queries mean query totals are lower than page or site totals.
3. **Weight positions by impressions** whenever rows are summed. Never average position columns.
4. **Recompute CTR** from clicks / impressions. MCPs return it as a percent or a fraction.
5. **Compare equal-length windows** starting on the same weekday. Add year-over-year when the site is seasonal.
6. **Split brand from non-brand** before judging SEO performance. Brand clicks hide non-brand losses.
7. **Check completeness.** If a call returns exactly `row_limit` rows or `has_more`, page with `start_row` or narrow the filter. Never conclude from a truncated result.
8. **Regex filters** (`includingRegex`, `excludingRegex`) are a Search Console API feature; some MCPs pass them through without documenting them. Test once; if refused, pull wider data and segment with the script.

## Pulling data efficiently

- Pull only the dimensions the question needs. `date` alone for trends; `page` or `query` for rankings; `query,page` only for cannibalization or page-level query mapping.
- Large results are often saved to a file by the agent runtime. Do not read them into context: run the script on the file.
- Save each pull to a scratch file (JSON as returned) when it will be reused, and name it by property, dimensions, and date range.

## Workflow

1. **Trend first.** Pull `date` for 16 months, then `gsc_rows.py aggregate <file> --by month`. Locate breaks before looking at pages.
2. **Run the recipes the question calls for** from [references/recipes.md](references/recipes.md):
   - drop diagnosis, content decay, quick wins, CTR gap, content gaps, cannibalization, intent and brand segmentation, page refresh inputs, GEO query signals, indexing checks.
3. **Tie findings to the business.** Rank actions by proximity to conversion (money pages, BOFU queries, ICP topics) first, then by potential clicks. Say when a large traffic opportunity has low business value.
4. **Verify** the key numbers in the final answer against the pulled data before presenting them.

## Interpretation rules

- Separate **facts** (numbers, dates, pages) from **hypotheses** (causes). Name the checks that would confirm a cause: site changes on that date, Google update dates, URL inspection, SERP inspection.
- A page in **positions 1-3 with CTR under 1%** is not a title problem: the SERP already answers the query (featured snippet, AI Overview, tool). Recommend a reason to click (calculator, worked example, template, data) rather than a title rewrite.
- **Impressions down with position stable** means Google shows the page for fewer queries or the SERP changed; it is not a content-quality ranking loss. Check the queries the page lost.
- **Cannibalization** is a problem only when several pages hold a meaningful share of the same query's impressions and positions are unstable. Low-impression secondary URLs are normal.
- Do not recommend creating new pages for queries an existing page already ranks for in positions 5-20; improve that page first.

## Output

- Lead with a 3-5 line summary: the current state, the main break or opportunity, and the first action.
- Then one table per recipe used, with exact figures and the date range and property stated once.
- End with prioritized actions: action, target page, evidence, expected impact, and whether it is a quick win or a project.
- Write in the user's language.
- **Ask before saving a file.** Present the analysis in chat. Then ask whether to save it and where; suggest a dated name such as `YYYY-MM-DD-gsc-<topic>.md` in the project's client or SEO folder. Do not write files without that answer.

## Related skills

- Refreshing one page from its queries: `subkeyword-injector`.
- Link fixes for underlinked targets or consolidated pages: `internal-linking`.
- Reviewing a page flagged here: `seo-roast`.
- A reusable interactive dashboard from GSC data: `seo-audit-report`.
