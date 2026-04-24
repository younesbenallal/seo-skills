# GEO Audit Report

## What changed

`geo-audit-report` now preserves search fan-out data in a way the dashboard can render directly, and the skill now defines clearer execution phases plus companion JSON artifacts.

## Main files

| File | Responsibility |
| --- | --- |
| `geo-audit-report/scripts/brightdata-geo.py` | Collects Bright Data snapshots and now stores both per-response and aggregated fan-out query data. |
| `geo-audit-report/SKILL.md` | Defines audit phases, required artifacts, search-trigger interpretation, provider-quality caveats, and tracked-prompts companion-file rules. |
| `geo-audit-report/template/src/lib/audit-data.ts` | Normalizes fan-out details and computes fallbacks for older audit JSON files. |
| `geo-audit-report/template/src/App.tsx` | Renders fan-out diagnostics per response and a global fan-out query summary section. |

## Query fan-out notes

- Do not force ChatGPT web search on or off. The goal is to preserve natural model behavior and then report whether search triggered.
- `fan_out_details` lives on each response and includes:
  - the search query
  - whether the brand appeared in the final response
  - whether the brand was cited
  - whether the brand domain was found in captured search results
  - the captured search result traces when Bright Data exposes them
- `fan_out_summary` aggregates the queries across the whole run so the dashboard can show how often each query was made and whether the brand appeared or was cited.

## Companion artifacts

- `results.json` is the immutable run output.
- `results.partial.json` is the in-progress checkpoint written as chatbot snapshots finish processing.
- `tracked-prompts.json` is the long-lived history file used across multiple runs.
- The React template under `geo-audit-report/template` is the expected companion deliverable when the user wants a usable dashboard.

## Compatibility

The dashboard still works with older `results.json` files that only have `fan_out_queries`, but the richer query diagnostics require a fresh run with the updated collector.
