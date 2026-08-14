# Artifacts and dashboard contract

Each response should expose `prompt`, `chatbot`, `model`, `mentions`, `cited`, `first_citation_rank`, `used_web_search`, `fan_out_queries`, `fan_out_details`, and `sources`. The v3 response also separates `answer_text_markdown`, `actual_citations`, `citation_candidates`, `uncited_citation_candidates`, `search_sources`, `attached_links`, `map_results`, `competitor_entities`, `provider_metadata`, `evidence_status`, and normalization warnings. `sources` is a compatibility alias for actual citations. Derive grouping domains from URL hostnames and retain provider labels as `display_domain`.

Evidence states are `supported`, `inferred`, `missing`, or `malformed`. Treat missing and malformed as unknown, not zero; report absence only when supported or safely inferred. The run-level `collection_diagnostics` should disclose normalized and rejected counts, warnings, unknown fields, and capability totals.

Save files under `{out-dir}/{YYYY-MM-DD}/`: `results.json`, at least one `raw/...json` provider payload, `snapshots/` for Bright Data, `results.partial.json` while supported, optional `tracked-prompts.json`, and `report.html`. Also write `{cwd}/geo-audit-report-{run-folder}.html` as the convenience copy. A one-off audit may omit `tracked-prompts.json`; repeated audits should create or update it while keeping each `results.json` immutable. Its minimum shape is:

```json
{"tracked_prompts":[{"prompt":"...","first_tracked_at":"2026-04-24","last_tracked_at":"2026-04-24","status":"active","notes":"...","history":[{"date":"2026-04-24","visibility":0}]}]}
```

Render the static page with:

```bash
node geo-audit-report/scripts/render-report.mjs --in <results.json>
```

It renders `answer_text_markdown`, writes the dated report, duplicates it in the current working directory, and prints paths. Use `results.json` as input to `geo-audit-report/template`; copy it under `public/data/...` or set `AUDIT_DATA_PATH` and `TRACKED_PROMPTS_PATH`. Add manual recommendations only after reviewing the run. Build or launch the template, validate that it reads the data, and review Overview, Prompts, and Sources. Keep relative asset paths so a static export works from `file://`.

The dashboard must support overview visibility, prompt-by-chatbot drilldown, source grouping by domain, per-response and prompt-level search status, per-response and global fan-out summaries, manual recommendations, prompt tracking, and a footer containing `holly-and-stick.com`.

Before delivery, compare raw and normalized counts; verify actual citations equal records explicitly marked `cited: true`; verify search sources, attached links, maps, and fan-out data were not dropped; ensure absent brands are not mislabeled as “mentioned only”; confirm Markdown is rendered and provider boilerplate is removed; run collector tests and dashboard typecheck/lint/build; inspect the exported report and `collection_diagnostics`.
