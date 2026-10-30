---
name: competitor-intelligence
description: Analyze SEO competitors and turn SERP, sitemap, and optional provider evidence into strategy. Use when the user wants competitor discovery, a competitor profile, a site comparison, content or keyword gaps, or monitoring over time.
---

# Competitor intelligence

Map what competitors publish, infer the strategy behind it, and turn the evidence into prioritized opportunities. Distinguish direct business competitors from SEO competitors that rank for the same queries without needing to sell the same product.

## Start from available context

Run the shared preflight in [`../docs/credentials-and-tooling.md`](../docs/credentials-and-tooling.md) before substantive work. Read `.seo-context.md`, product documentation, and prior competitor files when present; reuse known site, market, seed topics, competitors, and tool access. Ask only for task-specific gaps.

If invoked without a concrete request, explain in two sentences that this skill can discover competitors, analyze sitemap/content patterns, compare SEO datasets, and monitor changes. Then ask for:
   - the user's domain or product;
   - known competitor domains, if any;
   - target country and language;
   - confirmation of any relevant access not already detected: SERP API, Ahrefs, Semrush, DataForSEO, or exports.

Do not require the user's site when they only want a competitor profiled.

## Tooling and credentials

- Auth mode: `none` for sitemap analysis; `mcp` or `manual-file` for SERP and SEO-provider data
- Requires: competitor domain or sitemap for profiling
- Optional: structured SERP data from DataForSEO, Serper.dev, SerpApi, Bright Data, or an equivalent API/MCP; Ahrefs, Semrush, or equivalent MCP/export for deeper analysis
- Fallback: user-provided domains, sitemap files, and CSV/JSON exports

Do not block basic sitemap work because premium data is unavailable.

For live Google competitor discovery, use a structured SERP data source when available. If none exists, inspect the results with an available browser tool for smaller runs. If no live search path exists, continue with known/user-provided domains or ask for a SERP export.

## Choose the workflow

- **Discover competitors:** run the discovery workflow, then ask which domains deserve profiling.
- **Profile competitors:** inventory their sitemaps and explain observable content patterns.
- **Compare sites:** profile all sites on a consistent basis, then run a gap analysis.
- **Deep SEO comparison:** add provider keyword, page, traffic, and backlink data.
- **Monitor competitors:** save dated inventories/provider exports and compare snapshots.

Read [references/analysis-playbook.md](references/analysis-playbook.md) before competitor discovery, multi-site comparison, premium-provider analysis, or monitoring. It is the single source of truth for query design, evidence handling, scoring, monitoring, and report quality. For a basic one-domain sitemap profile, read only the sitemap-analysis section.

## Discover competitors

1. Start with 2 to 5 of the most relevant non-branded keywords from `.seo-context.md`, especially money-page targets and important query themes. If the context has no suitable seed set, ask the user to choose a couple. For a full competitor study, expand the set across:
   - product/category and high-intent use cases;
   - alternatives, comparisons, pricing, templates, and jobs-to-be-done;
   - educational topics central to the buyer.
2. Fetch the localized top 10 organic results for each keyword with the SERP tool.
3. Exclude the user's own domain. Keep marketplaces, social networks, generic publishers, aggregators, and other non-business sites when they recur, because they can still be SEO competitors.
4. Normalize domains and count recurrence across the full seed set. Use query-cluster recurrence as an additional view for larger studies. The domains that appear most often are the first SEO-competitor candidates.
5. Check the candidate's site only when business or audience context helps interpret the result. Classify each candidate separately:
   - **Direct:** sells a substantially similar product or service to a similar buyer.
   - **SEO/audience:** repeatedly reaches the same audience or topics with a different offer or business model.
   - **SEO incumbent:** ranks often but is neither a meaningful direct nor audience competitor.
6. Report the evidence: keyword set, locale, date, recurrence, representative URLs, and any business-context check. Keep SERP recurrence as the primary SEO-competitor signal.

Treat SERP overlap as discovery evidence, not proof that two businesses compete.

## Inventory a sitemap without flooding context

Locate sitemap URLs through `robots.txt`, `/sitemap.xml`, `/sitemap-0.xml`, `/sitemap_index.xml`, or visible sitemap references. Use the bundled script for large or nested sitemaps:

```bash
python3 competitor-intelligence/scripts/sitemap_inventory.py \
  "https://example.com/sitemap.xml" \
  --output-dir "competitor-research/example.com/2026-07-02"
```

The script emits:

- `pages.csv`: one compact row per URL;
- `summary.json`: aggregate counts, date coverage, path patterns, and bounded samples;
- `errors.csv`: fetch or parsing failures, only when failures occur.

Read `summary.json` first. Query/filter `pages.csv` instead of loading the full file into context. Keep raw XML out of chat and context unless diagnosing a parser failure.

Infer strategy mainly from paths and slugs. Use `lastmod` as supporting evidence only: it can represent a real update, a build timestamp, or nothing at all. Treat the script's `page_type` as a heuristic grouping, then verify ambiguous or important URLs by opening a small sample of pages.

## Analyze and report

Apply the report quality checks in [references/analysis-playbook.md](references/analysis-playbook.md) for collection metadata, evidence traceability, confidence, and limitations. The analysis below defines the competitor-specific content; the playbook remains the single source for cross-report quality rules.

Use the playbook's observed-versus-inferred distinction and attach confidence to strategic claims.

Cover:

1. business positioning and competitor type;
2. site/content architecture and repeated URL templates;
3. commercial, product, comparison, integration, use-case, and educational coverage;
4. topic clusters, audience segments, funnel balance, and likely keyword targets;
5. publishing/update signals when dates support them;
6. notable strengths, blind spots, and testable opportunities.

Do not equate URL volume with quality, traffic, freshness, or success. Do not call a missing sitemap URL a content gap until indexing/canonical or alternate-path explanations have been considered.

## Compare with premium SEO data

When provider access exists, collect comparable country, date, scope, and database settings for every domain. Prioritize:

- non-brand commercial and problem-aware keywords;
- pages ranking for comparison, alternative, pricing, integration, template, and use-case intent;
- traffic-driving pages that can naturally mention or demonstrate the product;
- recently acquired referring domains and the specific assets earning them;
- keyword/page movement over time, not only current estimates.

Use estimated traffic as directional. A high-traffic keyword is not automatically valuable. Score opportunities using business relevance, intent, product fit, attainability, and evidence—not volume alone.

## Compare and propose gaps

Normalize comparison by page type and topic cluster. Distinguish:

- **Coverage gap:** a relevant topic or intent is absent.
- **Depth gap:** coverage exists but is materially weaker.
- **Format gap:** the winning format is missing, such as a tool, template, comparison, or directory.
- **Authority gap:** competitors earn links or rankings through assets the user lacks.
- **Positioning gap:** competitors frame the problem or buyer differently.

Return a prioritized opportunity table with evidence, expected business value, difficulty, confidence, and a concrete next action. Keep strategic observations separate from recommendations.

## Monitor changes

Store each run in a dated folder. Compare two sitemap inventories with:

```bash
python3 competitor-intelligence/scripts/compare_inventories.py \
  "competitor-research/example.com/2026-06-01/pages.csv" \
  "competitor-research/example.com/2026-07-02/pages.csv" \
  --output-dir "competitor-research/example.com/diffs/2026-07-02"
```

Review added URLs first, grouped by page type and path segment. Treat removed URLs and changed `lastmod` values cautiously until verified. Add provider deltas for new keywords, ranking gains/losses, and new referring domains when available.

If recurring automations are supported, offer to schedule snapshots only after the user chooses cadence and storage location. Never imply monitoring is active merely because a baseline was created.

## Deliverables

Default to:

1. executive summary;
2. competitor map with direct/audience labels;
3. evidence-backed strategy profile for each selected domain;
4. cross-site gaps and prioritized actions;
5. data limitations and confidence notes;
6. monitoring baseline and next-run instructions when requested.

Save detailed artifacts to files when the analysis is large, and give the user their paths.
