---
name: geo-audit-report
description: Audit GEO and AI-search visibility. Use when the user wants to measure brand mentions, citations, search traces, maps, competitors, or fan-out queries in AI answers and receive a reusable report.
---

# GEO audit report

Use this skill when the user wants to measure how an organization appears in AI answers, citations, search traces, maps, or related fan-out queries. The workflow has four phases: prompt set, audit run, audit package, and analysis.

## Before the audit

Run the shared preflight in [`../docs/credentials-and-tooling.md`](../docs/credentials-and-tooling.md). Read `.seo-context.md` when present and reuse it for site, market, competitor, and content-priority context. Resolve the canonical domain from project evidence and ask one compact checkpoint only for high-impact GEO inputs that remain unknown. If the user skips a question, state assumptions and limitations; never invent priorities, markets, conversion value, or edit permission.

Collect:

- target domain(s), brand terms, and optional competitor domains
- a prompt file or 2–10 initial prompts
- country and language
- the provider and chatbots to run

## Tooling & credentials

- Default for ChatGPT: browser collection, with Chrome, `bun`, a ChatGPT login, and the Fanout Fox extension in the dedicated profile. No API key needed.
- API providers, for Perplexity, Gemini, or on request: auth mode `env`, with `BRIGHTDATA_API_KEY`, or both `DATA_FOR_SEO_LOGIN` and `DATA_FOR_SEO_PASSWORD`
- Do not silently switch between collection methods
- If missing: follow the shared setup rules and wait for the user to confirm access before collection

Provider-specific setup and collection behavior live in [references/provider-collection.md](references/provider-collection.md).

## Phase 1: prompt set

Check for an existing prompt file before generating one. Prefer a user-provided path, `prompts.txt`, `geo-audit-report/test-prompts.txt`, and prior GEO tracking files. Summarize a found file and ask whether to run, refine, or replace it. If no useful list exists, build prompts from the buyer decisions in the category, the site's positioning, jobs-to-be-done, audience, alternatives, important pages, and geography. Use the prompt guidance in [references/prompt-design.md](references/prompt-design.md).

Do not begin collection until the prompt list and its path are confirmed. Prompts should represent real user intent rather than taglines, cover useful angles, and connect to existing or desired content.

## Phase 2: audit run

Choose the collection method before collecting. For ChatGPT, use the browser collector by default: it runs the prompts in a real chatgpt.com session and exports Fanout Fox captures, which give the model, fan-out queries, and every retrieved source. Use Bright Data for Perplexity or Gemini, or when the browser setup is unavailable; use DataForSEO only when it is the available provider or the user explicitly requests it. State the choice and its fidelity tradeoff: the browser method resolves actual citations through a temporary workaround described in the provider reference. Do not silently switch methods.

Follow [references/provider-collection.md](references/provider-collection.md) for setup, chatbot selection, credentials, command examples, timing, raw preservation, resumability, and limitations. Use:

- `geo-audit-report/scripts/chatgpt-browser/run.ts` to collect ChatGPT answers and Fanout Fox captures into `{run-dir}/raw/`. Always start by listing the Fanout Fox workspaces and checking that the client has its own; create it or move misfiled captures when needed, then pass `--workspace` to the run
- `geo-audit-report/scripts/normalize-chatgpt-browser.py` to build the run's `results.json` from those raw files
- `geo-audit-report/scripts/brightdata-geo.py`
- `geo-audit-report/scripts/dataforseo-geo.py`
- `geo-audit-report/scripts/normalize-brightdata-geo.py` to rebuild a run from an existing raw Bright Data export

Keep the raw payloads, write the dated run folder, and stop clearly if collection fails. Keep collection separate from dashboard work so partial provider output is not presented as a finished report.

## Phase 3: audit package

Treat `results.json` as a `geo-audit-v3` contract, not a loose provider export. Preserve final-answer mentions, actual citations, citation candidates, search sources, attached links, map placements, competitor entities, provider metadata, and collection diagnostics. Normalize defensively: missing arrays become empty with a `missing` state; safe coercions are recorded; unknown provider fields remain under `provider_metadata.unknown_fields`; malformed records may be rejected individually; never infer an actual citation without a reliable `cited` flag.

Use [references/artifacts-dashboard.md](references/artifacts-dashboard.md) for the evidence states, artifact layout, tracked prompts, the dashboard template, presentation rules, and verification checks. The audit package has two layers:

- immutable dated `results.json` and raw provider payloads for every run
- one root-level `report-analysis.json` covering all completed runs
- one client-facing page at `{out-dir}/report/index.html`, rebuilt from all completed runs by `scripts/publish-dashboard.mjs`

Keep the page path stable across runs. Add new sections within the shared template when the evidence calls for them; retain its layout, visual tokens, and evidence meanings. If a client already has a customized dashboard, inspect its source and preserve useful content before publishing the common template. A failed build leaves the last published page intact; explain the failure.

Before every publication, read the old and new answers together and update `report-analysis.json`. Keep one current plan with 3–6 recommendations. Reassess old actions against the latest evidence, retire stale ones, and cite the runs or prompts that support each surviving action. The dashboard refuses a synthesis that does not cover the latest run. Keep the dated JSON as the historical record; per-run `manual_recommendations` are legacy context, not separate plans on the page.

## Phase 4: analysis

Read every completed dated `results.json` after collection. Write a cross-run conclusion and the single current action plan in `report-analysis.json`, then support it with the evidence. Cover:

- the searched → retrieved → mapped → mentioned → cited funnel
- visibility by chatbot and prompt
- actual citations separately from citation candidates and search sources
- which responses triggered search
- fan-out queries, including an aggregated query summary
- source-type patterns (including UGC and YouTube where present)
- answer, citation, search, and map competitors as separate channels
- a diagnosis of each important lost prompt: missing page, weak page, technical issue, or third-party sources
- for third-party sources, whether each one needs an own, claim, earn, or contest action
- reviewed recommendations grounded in the captured evidence, each one a change to test on named prompts in the next run

Use [references/analysis.md](references/analysis.md) for channel interpretation, fan-out fields, the lost-prompt diagnosis, source actions, the rerun loop, disclosure of missing or malformed evidence, and the GEO Playbook guidance. Give the user the exact absolute path to `{out-dir}/report/index.html`. Clearly disclose any unusable JSON contract or dashboard build instead of presenting the full package as delivered.

## Operational defaults

- Do not force ChatGPT web search on or off; report whether it triggered.
- The ChatGPT browser method gives the model, fan-out queries, and full retrieved sources. Its actual citations come from a temporary workaround until Fanout Fox flags cited sources again. Bright Data no longer returns ChatGPT models or fan-out queries since October 2026, but keeps actual citations and maps. DataForSEO supports ChatGPT and Gemini with weaker trace fidelity.
- Name browser run folders `YYYY-MM-DD` (or `YYYY-MM-DD-HHMMSS`) so the dashboard picks them up.
- Preserve `results.partial.json` when the collector supports it and disclose partial runs, warnings, rejected records, and unavailable channels through `collection_diagnostics`.
- Keep secrets on the user's machine; never print or request them in chat.
- Use relative asset paths for a dashboard export that works when opened from `file://`.
