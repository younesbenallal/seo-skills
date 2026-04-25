# GEO Audit Report

## What changed

`geo-audit-report` now ships with a standalone HTML renderer so each run can end with a clickable `report.html`, not just JSON and a dashboard template. The renderer also converts captured Markdown answers into HTML and duplicates the final page into the current working directory for easier retrieval. The companion dashboard template is now a static-first Next.js app rather than Vite.

## Main files

| File | Responsibility |
| --- | --- |
| `geo-audit-report/scripts/brightdata-geo.py` | Collects Bright Data snapshots and now stores both per-response and aggregated fan-out query data. |
| `geo-audit-report/scripts/render-report.mjs` | Renders `results.json` into a standalone `report.html`, duplicates it into the current working directory, and prints the generated file paths. |
| `geo-audit-report/SKILL.md` | Defines audit phases, required artifacts, static export expectations, and tracked-prompts companion-file rules. |
| `geo-audit-report/template/src/lib/audit-data.ts` | Normalizes fan-out details and computes fallbacks for older audit JSON files. |
| `geo-audit-report/template/src/App.tsx` | Renders fan-out diagnostics per response and a global fan-out query summary section. |
| `geo-audit-report/templates/report.html` | Base static HTML shell used by the GEO report renderer. |

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
- `report.html` is now the default static deliverable written beside the dated run.
- `geo-audit-report-{date}.html` is the convenience duplicate written to the current working directory.
- The Next.js template under `geo-audit-report/template` remains the interactive companion deliverable when the user wants a dashboard.

## Static export flow

After the collector finishes:

1. Read the dated `results.json`.
2. Run `geo-audit-report/scripts/render-report.mjs --in <results.json>`.
3. Use the emitted absolute file path for the final chat response so the user can click the generated HTML page directly.
4. The renderer writes:
   - `<run-dir>/report.html`
   - `<cwd>/geo-audit-report-<run-folder>.html`

## Markdown rendering

The static exporter turns each `answer_text_markdown` field into HTML before writing the final page. This keeps the deliverable readable when Bright Data returns headings, lists, links, code fences, or paragraph breaks in Markdown form.

## Compatibility

The dashboard still works with older `results.json` files that only have `fan_out_queries`, but the richer query diagnostics require a fresh run with the updated collector.
