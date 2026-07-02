---
name: competitor-intelligence
description: Identify, analyze, compare, and monitor SEO competitors using Google SERPs, XML sitemaps, URL patterns, and optional Ahrefs, Semrush, DataForSEO, or similar data. Use when the user asks for competitor discovery, competitor analysis, competitor monitoring, sitemap analysis, content strategy reverse-engineering, SEO competitive intelligence, backlink or keyword comparisons, content gaps, commercial keyword gaps, or a deep-dive comparison between a site and one or more competitors.
---

# Competitor intelligence

Map what competitors publish, infer the strategy behind it, and turn the evidence into prioritized opportunities. Distinguish direct business competitors from audience competitors that rank for the same topics without selling the same product.

## Start from available context

1. Check for `.agents/seo-context.md`, product documentation, and prior competitor files.
2. Reuse known site, market, seed topics, competitors, and tool access.
3. Inspect available tools before asking the user what they have.
4. If invoked without a concrete request, explain in two sentences that this skill can discover competitors, analyze sitemap/content patterns, compare SEO datasets, and monitor changes. Then ask for:
   - the user's domain or product;
   - known competitor domains, if any;
   - target country and language;
   - confirmation of any relevant access not already detected: SERP API, Ahrefs, Semrush, DataForSEO, or exports.

Do not require the user's site when they only want a competitor profiled.

## Tooling and credentials

- Auth mode: `none` for sitemap analysis; `mcp` or `manual-file` for SERP and SEO-provider data
- Requires: competitor domain or sitemap for profiling
- Optional: SERP API MCP for discovery; Ahrefs, Semrush, DataForSEO, or equivalent MCP/export for deeper analysis
- Fallback: user-provided domains, sitemap files, and CSV/JSON exports

Follow `docs/credentials-and-tooling.md`. Never ask the user to paste credentials. Detect callable tools first. Do not block basic sitemap work because premium data is unavailable.

For live Google competitor discovery, require a configured SERP data tool. Do not scrape Google result pages through browser automation. If no SERP tool exists, continue with known/user-provided domains or ask for a SERP export.

## Choose the workflow

- **Discover competitors:** run the discovery workflow, then ask which domains deserve profiling.
- **Profile competitors:** inventory their sitemaps and explain observable content patterns.
- **Compare sites:** profile all sites on a consistent basis, then run a gap analysis.
- **Deep SEO comparison:** add provider keyword, page, traffic, and backlink data.
- **Monitor competitors:** save dated inventories/provider exports and compare snapshots.

Read [references/analysis-playbook.md](references/analysis-playbook.md) before competitor discovery, multi-site comparison, premium-provider analysis, or monitoring. For a basic one-domain sitemap profile, read only the sitemap-analysis section.

## Discover competitors

1. Build a small query set across:
   - product/category and high-intent use cases;
   - alternatives, comparisons, pricing, templates, and jobs-to-be-done;
   - educational topics central to the buyer.
2. Fetch localized top results for each query with the SERP tool.
3. Exclude marketplaces, social networks, generic publishers, and aggregators only when they are irrelevant to the requested analysis.
4. Count domain recurrence by query cluster, not only across the full set.
5. Classify each candidate:
   - **Direct:** sells a substantially similar product or service to a similar buyer.
   - **Audience:** repeatedly reaches the same audience/topics but has a different offer or business model.
   - **SERP incumbent:** ranks often but is neither a meaningful business nor audience competitor.
6. Report the evidence: representative queries, recurrence, positioning, and why the classification fits.

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

Separate every conclusion into:

- **Observed:** URL, slug, sitemap count, date, SERP result, provider metric, or page content.
- **Inferred:** likely keyword, intent, audience, funnel role, template, content cadence, or strategic priority.
- **Confidence:** high, medium, or low, with the reason.

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
