---
name: geo-audit-report
description: Create a GEO audit using Bright Data or DataForSEO and output a reusable dashboard-ready JSON, a static HTML report, and a Next.js template app that should be used by default.
---

# GEO audit report (provider → dashboard)

You help the user:
1) define prompts that matter for their business,  
2) collect results from major LLM experiences (ChatGPT / Perplexity / optionally Gemini),  
3) generate a dashboard-ready audit package with explicit JSON artifacts and the Next.js template wired by default, plus a standalone HTML export,  
4) review the results and turn them into actionable insights.

Automated collection can use either Bright Data or DataForSEO.

## Shared context first

Before asking repeated discovery questions, check whether `.agents/seo-context.md` exists.

If it does:
- read it first
- reuse the saved site, market, competitor, and content-priority context
- ask only for GEO-specific gaps that are still missing

## Inputs to collect

- Brand/site:
  - target domains (ex: `example.com`)
  - brand terms (ex: product name, founder name)
  - competitor domains (optional)
- Prompt list (2-10 to start)
- Country / language

## Execution phases

Treat the workflow as four distinct phases. Do not blur them together.

### Phase 1: prompt set

- find or create the prompt list
- validate prompt coverage before running anything
- save or confirm the prompt file path

### Phase 2: audit run

- choose the collection provider
- run the matching collector
- produce the dated audit folder
- do not start editing the dashboard template yet

### Phase 3: audit package

- verify that the JSON artifacts are complete
- require `geo-audit-v3` semantics:
  - final-answer brand mentions
  - actual citations (`cited: true`)
  - uncited citation candidates
  - captured search sources
  - attached links
  - structured map placements
  - competitor entities with evidence channels
  - provider metadata and collection status
- normalize defensively:
  - turn missing arrays into empty arrays while marking their evidence state `missing`
  - safely coerce recognizable boolean and numeric variations and record a warning
  - preserve unknown provider fields under `provider_metadata.unknown_fields`
  - reject only the malformed record, not the entire run
  - never infer actual citations when reliable `cited` flags are unavailable
- prepare the dashboard inputs
- render the standalone HTML page from `results.json`
- connect the run to the Next.js template by default
- only skip the template when the user explicitly asks not to use it, or force majeure prevents it (for example: missing dependencies, broken build tooling, or incomplete artifacts that make the template unusable)

### Phase 4: analysis

- analyze the run
- summarize the opportunity funnel: searched → retrieved → mapped → mentioned → cited
- report actual citations separately from candidates and search sources
- analyze answer, citation, search, and map competitors as separate channels
- surface a prioritized, prospect-facing action plan before raw evidence
- add optional manual recommendations
- give the user the exact local HTML file path so they can click it from chat

If a run failed or the JSON is incomplete, stop in Phase 2 or 3 and say so clearly instead of pretending the dashboard or template is ready.

### Evidence states

Every response must expose `evidence_status` for answer, web search, actual citations, citation candidates, search sources, attached links, maps, and fan-out queries:

- `supported`: the provider supplied a canonical value
- `inferred`: a safe coercion or structural normalization was applied
- `missing`: the provider did not supply enough evidence
- `malformed`: the provider supplied unusable evidence

Treat `missing` and `malformed` as unknown, never as zero. Only report absence when the channel is `supported` or `inferred`.

## How to gather prompts with the user

Do not assume the user already has a finished prompt list. In most cases, help them find one.

### Prompt preflight

Before generating new prompts:

1. Check whether a prompt file already exists in the workspace.
2. Prefer likely files such as:
   - a user-provided prompts file path
   - `prompts.txt` in the current project
   - `geo-audit-report/test-prompts.txt`
   - prompt/tracking files from earlier GEO runs if the project has them
3. If you find an existing prompts file, read it first and summarize it briefly:
   - number of prompts
   - a few representative examples
   - whether it looks broad, branded, competitor-led, or JTBD-focused
4. Ask the user whether they want to:
   - run the audit on those prompts as-is
   - refine that list
   - replace it with a new list

Do not jump straight into generating a fresh prompt set if a plausible existing file is already present.

### Prompt discovery workflow

If the user does not already have a strong prompt list, build one with them from business context.

Collect or infer:
- the main product or service
- the core jobs-to-be-done
- the target audience or persona
- key alternatives / competitors
- the site sections that matter most
- any geographic context that changes recommendations

Then gather direction from available materials. Prefer concrete inputs over guessing:
- visit the main website
- inspect the homepage and core product/service pages
- inspect the blog, resources, docs, integrations, use-case pages, and comparison pages if they exist
- look for sitemap files, article lists, navigation labels, collections, and category pages
- use headings, CTAs, repeated claims, and topic clusters to identify high-intent themes

Useful sources of prompt ideas:
- homepage positioning and category language
- product or feature pages
- use-case and industry pages
- competitor comparison pages
- blog posts and article titles
- FAQ sections
- templates, tools, calculators, and lead magnets
- integration pages

### What good prompts should look like

Prompts should sound like real user intent, not internal marketing copy.

Aim for a mix of:
- category discovery prompts
- best-tool / ranking prompts
- alternatives / comparison prompts
- workflow or problem-solving prompts
- no-code / privacy / compliance / localization prompts when relevant
- prompts tied to the user's actual content themes

The list should usually contain 2-10 prompts to start, but the important part is coverage, not round numbers.

### How to turn site content into prompts

Translate content themes into natural-language prompts a buyer or user might ask:

- category page -> "best [category] tool for [persona]"
- workflow page -> "how to [job to be done] with [constraints]"
- comparison page -> "alternatives to [competitor] for [use case]"
- blog cluster -> "how to solve [pain point]" / "tools for [problem]"
- feature page -> "tool that lets me [specific outcome]"

When useful, generate prompt clusters around:
- best / top / rank / compare
- alternatives / versus
- how to / set up / automate
- privacy-safe / no-code / local-first / global-friendly
- timezone-aware / multilingual / regional requirements

### Prompt quality bar

Avoid:
- branded prompts only
- vague one-word prompts
- prompts that merely restate the company tagline
- prompts disconnected from pages the site already has or wants to win on

Prefer prompts that:
- map to an actual business outcome
- map to existing or desired pages/content
- reveal whether the brand gets cited, mentioned, or ignored
- help uncover fan-out opportunities and missing content

### Prompt coverage guide

When helping the user shape the prompt set, try to guide it toward a healthy mix across:

- category prompts
- competitor / alternative prompts
- workflow / JTBD prompts
- buyer-evaluation or ranking prompts
- brand-adjacent prompts tied to actual product strengths

This is not a rigid checklist. The goal is to help the user find a set that reflects how buyers actually search, while avoiding a list that is too concentrated in only one angle.

## Provider selection

Choose the provider before Phase 2.

- Prefer Bright Data when the user has it.
- Use DataForSEO when the user only has DataForSEO access or explicitly asks for it.
- Do not silently switch providers. Say which one you are using.

Provider tradeoffs:
- Bright Data gives the richest search-trigger and search-result trace fidelity, especially for ChatGPT.
- DataForSEO is a valid fallback, but its trace fidelity is weaker.
- With DataForSEO:
  - ChatGPT uses `llm_scraper/live/advanced`
  - Gemini uses `llm_scraper/live/advanced`
  - only ChatGPT and Gemini are supported in this skill
  - fan-out and source traces are less complete than Bright Data
  - there is no Bright Data-style dataset snapshot workflow

### Bright Data collection mode

- Use synchronous `/datasets/v3/scrape` by default for 1-20 prompts.
- Let the collector handle automatic conversion to a snapshot when Bright Data returns `snapshot_id`.
- Use asynchronous `/datasets/v3/trigger` for more than 20 prompts, explicit batch runs, or when `--collection-mode async` is requested.
- Preserve the raw provider response before normalization.
- To rebuild a report from an existing raw export without a paid rerun, use:

```bash
python geo-audit-report/scripts/normalize-brightdata-geo.py \
  --raw <raw-brightdata.json> \
  --out <run-dir>/results.json \
  --check-url <site-url> \
  --target-domains <domain> \
  --brand-terms <comma-separated-brand-terms> \
  --dataset-id <original-dataset-id> \
  --snapshot-id <original-snapshot-id> \
  --run-at <original-run-timestamp>
```

## Tooling & credentials

- Auth mode: `env`
- Requires: either `BRIGHTDATA_API_KEY` or `DATA_FOR_SEO_LOGIN` + `DATA_FOR_SEO_PASSWORD`
- Fallback: Bright Data or DataForSEO
- If missing: stop, ask the user to set the env var locally, and continue only after they confirm it is ready

Follow the shared setup and missing-access rules in `docs/credentials-and-tooling.md`.

### Bright Data setup

Requires:
- `BRIGHTDATA_API_KEY`
- Bright Data dataset IDs for each chatbot you plan to run

Dataset IDs:

```
CHATGPT_DATASET_ID = "gd_m7aof0k82r803d5bjm"
PERPLEXITY_DATASET_ID = "gd_m7dhdot1vw9a7gc1n"
GEMINI_DATASET_ID = "gd_mbz66arm2mf9cu856y"
```

Before running the Bright Data script, ask the user which chatbots they want to run:
- ChatGPT
- Perplexity  
- Gemini

They can select one, two, or all three. Only pass the dataset IDs for the selected chatbots to the script.

Verify only whether `BRIGHTDATA_API_KEY` is set:

```bash
if [ -z "$BRIGHTDATA_API_KEY" ]; then echo "Not set"; else echo "Set"; fi
```

If it is missing, ask the user to set it locally in their own terminal:

```bash
export BRIGHTDATA_API_KEY="your-key-here"
```

Do not ask the user to paste the key in chat, and never print the key value.

### DataForSEO setup

Requires:
- `DATA_FOR_SEO_LOGIN`
- `DATA_FOR_SEO_PASSWORD`

Verify only whether both env vars are set:

```bash
if [ -z "$DATA_FOR_SEO_LOGIN" ] || [ -z "$DATA_FOR_SEO_PASSWORD" ]; then echo "Not set"; else echo "Set"; fi
```

If missing, ask the user to set them locally:

```bash
export DATA_FOR_SEO_LOGIN="your-login"
export DATA_FOR_SEO_PASSWORD="your-password"
```

Do not ask the user to paste either secret in chat, and never print the values.

## Verification gates

Before delivering a report:

1. Compare raw and normalized record counts.
2. Confirm citation appearances equal the number of provider records marked `cited: true`.
3. Derive canonical domains from URLs; retain provider display labels separately.
4. Confirm search sources, attached links, and map placements were not dropped.
5. Confirm absent brands are labelled absent, not “mentioned only.”
6. Confirm Markdown answers render and provider UI boilerplate is removed.
7. Run collector unit tests, dashboard typecheck/lint/build, and inspect the exported report.
8. Inspect `collection_diagnostics`; disclose partial runs, warnings, rejected records, and unavailable channels.

Before running the DataForSEO script, ask the user which chatbots they want to run:
- ChatGPT
- Gemini

Important DataForSEO nuance:
- ChatGPT and Gemini use scraper endpoints
- Perplexity is intentionally not supported in this fallback
- Do not claim DataForSEO has Bright Data-equivalent search-trigger telemetry

## Collection scripts (Python)

Use:
- `geo-audit-report/scripts/brightdata-geo.py`
- `geo-audit-report/scripts/dataforseo-geo.py`

Bright Data collector:
- triggers selected datasets up front
- polls pending snapshots together
- downloads snapshots
- saves results to `results.json` with both response-level details and summary metrics

DataForSEO collector:
- calls live AI Optimization endpoints directly
- stores one raw response per chatbot/prompt pair
- saves the same normalized `results.json` schema used by the Bright Data collector
- does not use dataset IDs or snapshot polling
- only supports ChatGPT and Gemini

Important implementation notes:
- Do not force ChatGPT web search on or off in the input payload. Let the model decide naturally so the audit stays as close as possible to a real user experience.
- Query fan-out coverage depends on what the provider exposes. Bright Data ChatGPT currently returns the richest query-level search data.
- Always preserve and surface whether search was actually triggered per response. Missing citations on a no-search response should be interpreted differently from missing citations on a searched response.
- The collector should be resumable in a lightweight way: reuse existing raw data when available, skip unnecessary re-fetches unless forced, and write `results.partial.json` during progress.

DataForSEO-specific notes:
- ChatGPT scraper exposes `fan_out_queries`, `sources`, and `search_results`, which map well to the current schema.
- Gemini scraper maps well for citations and answer text, but has weaker search-trace detail than Bright Data ChatGPT.
- Do not overstate search-trigger certainty when using DataForSEO. Missing citations does not necessarily mean no search happened.

Timing note:
- Bright Data processing can take **1 minute to several minutes** depending on prompt count.
- DataForSEO live calls can take **up to 120 seconds per request**, and each live call accepts only one task.
- Inform the user which timing profile applies before you run the audit.

**Output structure**: All files are saved in a dated folder (`YYYY-MM-DD`) within the specified `--out-dir`:
- `{out-dir}/{YYYY-MM-DD}/results.json` - Complete results data
- `{out-dir}/{YYYY-MM-DD}/raw/...json` - Raw provider payloads
- `{out-dir}/{YYYY-MM-DD}/report.html` - standalone HTML report rendered from `results.json`
- `{cwd}/geo-audit-report-{run-folder}.html` - duplicate of the same HTML report in the current working directory

Provider-specific raw files:
- Bright Data: `snapshots/{chatbot}.json` and `raw/{chatbot}-{snapshot_id}.json`
- DataForSEO: `raw/{chatbot}-{prompt-index}-{prompt-slug}.json`

### Example run

```bash
# Bright Data
python3 geo-audit-report/scripts/brightdata-geo.py \
  --check-url "https://example.com" \
  --prompts-file prompts.txt \
  --chatgpt-dataset-id "gd_m7aof0k82r803d5bjm" \
  --perplexity-dataset-id "gd_m7dhdot1vw9a7gc1n" \
  --gemini-dataset-id "gd_mbz66arm2mf9cu856y" \
  --target-domains "example.com" \
  --brand-terms "Example,Example Product" \
  --out-dir ./geo-run

# DataForSEO
python3 geo-audit-report/scripts/dataforseo-geo.py \
  --check-url "https://example.com" \
  --prompts-file prompts.txt \
  --chatbots "chatgpt,gemini" \
  --country "US" \
  --language "en" \
  --target-domains "example.com" \
  --brand-terms "Example,Example Product" \
  --out-dir ./geo-run
```

Notes:
- For Bright Data, only include the dataset ID flags for chatbots the user selected.
- For DataForSEO, only include the chatbots the user selected in `--chatbots`.
- Files will be saved in `./geo-run/YYYY-MM-DD/`.

## Required audit artifacts

The audit is not complete unless the dated run folder contains the expected artifacts.

### Required

- `{out-dir}/{YYYY-MM-DD}/results.json`
- at least one raw provider payload under `{out-dir}/{YYYY-MM-DD}/raw/`

### Optional but expected in normal usage

- `{out-dir}/{YYYY-MM-DD}/snapshots/` for Bright Data runs
- `{out-dir}/{YYYY-MM-DD}/tracked-prompts.json`
- `{out-dir}/{YYYY-MM-DD}/report.html`
- `{cwd}/geo-audit-report-{run-folder}.html`

### Artifact roles

- `results.json`
  Main run output for the dashboard and summary analysis.
- `tracked-prompts.json`
  Long-lived prompt tracking companion file used to compare prompt visibility over time.
- `report.html`
  Default standalone deliverable rendered from `results.json`.
- `geo-audit-report-{run-folder}.html`
  Convenience copy of the same report written to the current working directory so the user can retrieve it without digging through hidden folders.

## Post-execution analysis

**After the script completes successfully**, you MUST:

1. Read the `results.json` file from the dated output folder
2. Analyze the data and provide initial conclusions, including:
   - Overall visibility summary (cited vs mentioned vs not visible)
   - Which chatbots perform best/worst for the brand
   - Key patterns across prompts (e.g., which prompts get cited, which don't)
   - Which prompts triggered search and which did not
   - Fan-out query insights (what related queries are being suggested)
   - Aggregated fan-out query summary (query, count, whether the brand appeared, whether it was cited, whether the domain appeared in captured search results)
   - Source breakdown insights (UGC vs YouTube vs web dominance)
   - Competitor mentions if any
   - Top priority actions based on the data

3. **Prepare the dashboard files**:
   - Use `results.json` as the main audit input for the Next.js template in `geo-audit-report/template`
   - Prepare or update `tracked-prompts.json` if prompt history is available or should start from this run
   - Optionally add a couple of manual recommendations in `manual_recommendations`
   - Generate `report.html` in the same dated output folder with `geo-audit-report/scripts/render-report.mjs`
   - Duplicate that HTML file into the current working directory
   - Wire the dated run into the Next.js template unless the user explicitly told you not to, or force majeure prevents it
   - Validate that the template can read the audit data
   - Return the absolute local file path to the user so they can click it directly from chat

4. Present these conclusions clearly and concisely to the user, and let them know the template and static HTML deliverables are ready. If the template was skipped, explain exactly why.

## Static HTML export

Use:
- `geo-audit-report/scripts/render-report.mjs`

It:
- reads `results.json`
- builds a standalone `report.html` beside the audit run
- duplicates the same HTML file into the current working directory
- prints the generated file paths so you can share the exact local link in the final response
- renders each `answer_text_markdown` field into HTML instead of showing raw Markdown

Example:

```bash
node geo-audit-report/scripts/render-report.mjs \
  --in ./geo-run/2025-01-15/results.json
```

## Output requirements

### Next.js dashboard template

**IMPORTANT**: The Python script produces the audit JSON, and the Next.js template in `geo-audit-report/template` reads that JSON directly during build time.

Treat the Next.js template as the default artifact for this skill in almost all cases. The standalone HTML report is still required, but it is the companion deliverable, not the substitute. Use the template unless:

- the user explicitly instructs you not to use it
- force majeure makes it impractical or impossible in this run (for example dependency failures, broken template build/runtime, or unusable audit artifacts)

The default path is:

1. run the collector
2. verify the JSON artifacts
3. render the static HTML export
4. connect the run to the template
5. review the template output
6. report both deliverables back to the user

Do not describe the audit as “done” if the collector succeeded but the JSON does not match what the dashboard expects.
Do not describe the audit as “done” if you skipped the template without one of the allowed exceptions above.

The expected workflow is:

1. Run the collector to produce `results.json`
2. Render `results.json` to `report.html`
3. Copy the same JSON into the template app's `public/data/...` folder or point the build to it with `AUDIT_DATA_PATH` and `TRACKED_PROMPTS_PATH`
4. Add a few manual recommendations directly in the JSON after reviewing the data
5. Run the Next build or otherwise launch the template so the dashboard can actually be used
   - keep the exported dashboard compatible with direct local-file opening, not only hosted server access
   - ensure asset paths are relative so the export does not break on `file://` with absolute `/_next/...` URLs
6. Launch the app and review the three tabs:
   - Overview
   - Prompts
   - Sources
7. Share the absolute local file path for the HTML report and the template access path in the final response

### Dashboard input contract

At minimum, the dashboard run should expose:

- `run_at`
- `check_url`
- `target_domains`
- `brand_terms`
- `snapshots`
- `responses`

Recommended fields:

- `manual_recommendations`
- `fan_out_summary`

Each response should ideally expose:

- `prompt`
- `chatbot`
- `model`
- `mentions`
- `cited`
- `first_citation_rank`
- `used_web_search`
- `fan_out_queries`
- `fan_out_details`
- `sources`

### Dashboard requirements

The dashboard should support:

- Overview metrics and prompt visibility
- Prompt-level drilldown per chatbot
- Source grouping by domain
- Search-trigger status per response and per prompt rollup
- Fan-out queries per response, including whether we appeared in the response and whether our domain appeared in captured search results
- A global fan-out query summary with counts and appearance status
- Manual recommendations added by AI in the JSON
- A separate JSON file tracking prompts over time
- Footer including `holly-and-stick.com`

## Tracked prompts companion file

`tracked-prompts.json` should be treated as a first-class companion artifact for repeated audits.

Use this minimum structure:

```json
{
  "tracked_prompts": [
    {
      "prompt": "best treasury software for multi-entity groups",
      "first_tracked_at": "2026-04-24",
      "last_tracked_at": "2026-04-24",
      "status": "active",
      "notes": "Enterprise category prompt",
      "history": [
        {
          "date": "2026-04-24",
          "visibility": 0
        }
      ]
    }
  ]
}
```

When to create or update it:

- create it on the first run if the user wants repeated GEO tracking
- update it on later runs when the same prompt reappears
- keep it separate from `results.json` so each run stays immutable

If the user only wants a one-off audit, say explicitly that `tracked-prompts.json` is optional and may be skipped.

## Fan-out analysis requirements

Treat fan-out analysis as a required output, not a side observation.

### Per response

For each response with search fan-out data, capture:

- the exact query or queries
- whether search triggered
- whether the brand appeared in the response
- whether the brand was cited
- whether the target domain appeared in captured search results

### Aggregated

Across the run, provide a grouped query summary with:

- query
- count
- prompts it appeared on
- chatbots it appeared on
- how many times the brand appeared in the response
- how many times the brand was cited
- how many times the target domain appeared in captured search results

Use guidance from `obsidian/GEO Playbook.md`:
- list prompts → track → wait → analyze fan-outs
- create missing content for fan-outs
- target UGC-dominant sources strategically
