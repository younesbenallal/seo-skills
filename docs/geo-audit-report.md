# GEO Audit Report

## What changed

`geo-audit-report` writes `geo-audit-v3`. The contract preserves each evidence layer instead of treating every provider citation candidate as an actual citation. A single Next.js template publishes one stable page per client, with all completed runs available inside it.

The skill now supports two collection providers:
- Bright Data as the primary, higher-fidelity option
- DataForSEO as a fallback when Bright Data is not available

## Main files

| File | Responsibility |
| --- | --- |
| `geo-audit-report/scripts/brightdata-geo.py` | Collects Bright Data synchronously for up to 20 prompts with snapshot fallback, then writes v3 evidence. |
| `geo-audit-report/scripts/normalize-brightdata-geo.py` | Rebuilds v3 results from an existing raw Bright Data export without a paid rerun. |
| `geo-audit-report/scripts/dataforseo-geo.py` | Collects DataForSEO AI Optimization results and normalizes them into the same audit schema used by the Bright Data collector. |
| `geo-audit-report/scripts/publish-dashboard.mjs` | Builds the shared template from every completed run and updates the stable client report path. |
| `geo-audit-report/SKILL.md` | Defines audit phases, dated evidence, publication, and presentation rules. |
| `geo-audit-report/template/src/lib/audit-data.ts` | Normalizes v3 evidence and keeps a compatibility fallback for older results. |
| `geo-audit-report/template/src/components/audit-dashboard.tsx` | Renders the prospect-facing funnel, prompt matrix, competitive/local views, and evidence viewer. |

## Query fan-out notes

- Do not force ChatGPT web search on or off. The goal is to preserve natural model behavior and then report whether search triggered.
- `fan_out_details` lives on each response and includes:
  - the search query
  - whether the brand appeared in the final response
  - whether the brand was cited
  - whether the brand domain was found in captured search results
  - the captured search result traces when the provider exposes them
- `fan_out_summary` aggregates the queries across the whole run so the dashboard can show how often each query was made and whether the brand appeared or was cited.

## v3 evidence contract

Each response separates:

- `answer_text_markdown`: cleaned final answer
- `actual_citations`: only provider citation records explicitly marked `cited: true`
- `citation_candidates`: every citation candidate
- `uncited_citation_candidates`: candidates explicitly marked `cited: false`
- `search_sources`: structured search retrieval
- `attached_links`: links attached to the answer
- `map_results`: structured local placements with position, rating, reviews, category, and website
- `competitor_entities`: entities grouped by answer, citation, candidate, search, link, and map channels
- `provider_metadata`: provider timestamps and response-format signals
- `evidence_status`: availability and confidence for every evidence channel
- `normalization`: record-level coercion and malformed-field warnings

`sources` remains a compatibility alias for `actual_citations`. Domain grouping must use the hostname derived from the URL; `display_domain` preserves the provider label.

## Tolerant ingestion

Provider payloads are accepted defensively:

- missing arrays normalize to `[]` and retain a `missing` evidence state
- singleton objects in array fields are safely wrapped and marked `inferred`
- recognizable boolean and numeric strings are coerced and recorded as warnings
- unusable values are marked `malformed`
- unknown top-level provider fields are preserved in `provider_metadata.unknown_fields`
- one rejected record produces a partial audit instead of aborting valid prompts

Actual citations are conservative. When citation candidates exist but reliable `cited` flags do not, `actual_citations` stays empty and its evidence state is `missing` or `malformed`. Consumers must display “citation status unavailable,” not “zero citations.”

The run-level `collection_diagnostics` object contains normalized/rejected counts, warnings, unknown provider fields, and capability-state totals. A `partial` status is deliverable only when the report clearly discloses the missing or malformed evidence.

## Provider notes

- Bright Data remains the better source for search-trigger, citation, search-result, and map fidelity.
- Runs of 1-20 prompts use synchronous `/scrape` by default. If Bright Data auto-converts the request, the collector follows the returned snapshot.
- DataForSEO fallback uses:
  - ChatGPT scraper
  - Gemini scraper
- DataForSEO does not replicate Bright Data dataset snapshots and exposes weaker fan-out/search-trigger diagnostics than Bright Data.

## Companion artifacts

- `results.json` is the immutable run output.
- `results.partial.json` is the in-progress checkpoint written as chatbot snapshots finish processing.
- Optional root-level `tracked-prompts.json` holds prompt notes and status.
- Root-level `report-analysis.json` holds one reviewed synthesis and 3–6 recommendations across all completed runs.
- Dated `results.json` files provide the measured history.
- `{out-dir}/report/index.html` is the sole client-facing HTML path, updated after each completed run.

## Publication flow

After the collector finishes:

1. Verify the dated `results.json` and raw provider data.
2. Review old and new results together and update `report-analysis.json` through the latest run.
3. Run `node geo-audit-report/scripts/publish-dashboard.mjs <out-dir>` from the skill repository.
4. Inspect the emitted `{out-dir}/report/index.html`, including the cross-run summary and the run detail selector, then share that path.

## Markdown rendering

The dashboard renders each `answer_text_markdown` field with Markdown support, including headings, lists, links, code fences, and paragraph breaks.

## Compatibility

The dashboard reads older results by treating their `sources` array as citations, but older files cannot recover evidence that was dropped during normalization. When a raw Bright Data export exists, rebuild it with `normalize-brightdata-geo.py`.
