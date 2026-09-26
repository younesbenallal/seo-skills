# Artifacts and dashboard contract

## Data and publication

Each response exposes `prompt`, `chatbot`, `model`, `mentions`, `cited`, `first_citation_rank`, `used_web_search`, `fan_out_queries`, `fan_out_details`, and `sources`. The v3 contract also separates `answer_text_markdown`, `actual_citations`, `citation_candidates`, `uncited_citation_candidates`, `search_sources`, `attached_links`, `map_results`, `competitor_entities`, `provider_metadata`, `evidence_status`, and normalization warnings. `sources` is a compatibility alias for actual citations. Group domains by URL hostname and retain provider labels as `display_domain`.

Evidence states are `supported`, `inferred`, `missing`, and `malformed`. Missing and malformed mean unknown. A zero is justified only when the channel was measured. Keep collection diagnostics, including normalized and rejected records, warnings, unknown fields, and capability totals.

Save each completed run under `{out-dir}/{YYYY-MM-DD}/` with `results.json`, raw provider JSON, and Bright Data snapshots where relevant. Preserve `results.partial.json` during collection. A second run on the same day needs a distinct time suffix. Keep every completed `results.json` immutable. Keep optional `tracked-prompts.json` at `{out-dir}/` for notes and prompt status; the dashboard derives measured history from every dated `results.json` so the history still works without this companion file.

Keep one `{out-dir}/report-analysis.json` for the current interpretation of the full history. Before each publication, review all dated answers, the prior analysis, prompt changes, and evidence availability. Update the overview, cross-run findings, comparison caveat, and 3–6 priority recommendations. Each recommendation has an evidence sentence naming relevant runs, prompts, or counts. `through_run_at` must equal the newest `run_at`; a stale or missing analysis blocks publication.

```json
{
  "through_run_at": "2026-09-02T11:20:32Z",
  "overview": "Concise conclusion across all runs.",
  "comparison_note": "Explain changes in prompts, chatbots, provider, or evidence quality.",
  "findings": ["A specific trend backed by the runs."],
  "recommendations": [
    {"priority": "High", "title": "Action", "summary": "What to do and why.", "evidence": "Run dates, prompts, and measured signals."}
  ]
}
```

The example shows field meanings; a publishable file needs 3–6 distinct, evidenced recommendations. Do not carry forward an old recommendation just because it appeared in a previous run.

Publish from the skill repository with:

```bash
node geo-audit-report/scripts/publish-dashboard.mjs <out-dir>
```

This builds the common Next.js template from all completed runs and updates `{out-dir}/report/index.html` and its `_next/` assets. The path remains the same on every run. The build must succeed before replacing the previous page. Give that path to the user. Treat the dated JSON as the audit record and the published page as its current view.

## How to present the evidence

The template is a visual and semantic base, not a fixed set of cards. Adapt its sections to the actual data while keeping one design system and one page per client:

- Lead with the current cross-run conclusion and a single action plan from `report-analysis.json`.
- Show aggregate response and chatbot coverage, the trend for each run, prompt history, and the evidence quality that limits interpretation. Keep aggregate counts separate from comparisons between nonmatching prompt sets.
- Show the dated runs together and let the reader open each one. State when changes in prompts, chatbots, market, provider, or evidence availability make comparisons unreliable. Use available-response denominators.
- Show the searched → retrieved → mapped → mentioned → cited funnel. Distinguish a model's final answer from search results and map placements. Each stage is a separate signal, not a guaranteed conversion from the preceding one.
- Make prompt and chatbot results inspectable, with the actual answer and supporting records close to their summary.
- In the prompt matrix, show fan-query counts per prompt. Let each prompt expand into model tabs, including GPT and Perplexity, with other collected models when present. In each tab, show the original prompt and fan queries first, confirmed citations and unconfirmed candidates second, then the generated answer. Show an unavailable state when a model or evidence channel was not collected.
- Separate actual citations from citation candidates, search sources, attached links, and maps. Label a channel unknown when its evidence is missing or malformed.
- Group competing entities by the channel where they appeared. Show source domains and individual URLs so claims can be checked.
- Show fan-out queries and source-type patterns, including UGC or YouTube, when captured. Omit empty sections whose absence has no analytical meaning; explain meaningful gaps in methodology.
- Preserve `answer_text_markdown` formatting and remove provider boilerplate. Keep `holly-and-stick.com` in the footer.

Before delivery, compare raw and normalized counts; verify actual citations match records explicitly marked `cited: true`; check that search sources, attached links, maps, and fan-out data were retained; inspect the exported page, including run selection, Markdown, and `collection_diagnostics`. Run collector tests and dashboard typecheck/lint/build when their code changed.
