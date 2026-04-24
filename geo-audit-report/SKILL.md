---
name: geo-audit-report
description: Create a GEO audit using Bright Data datasets (mandatory) and output a reusable dashboard-ready JSON plus a React template app.
---

# GEO audit report (Bright Data → dashboard)

You help the user:
1) define prompts that matter for their business,  
2) collect results from major LLM experiences (ChatGPT / Perplexity / optionally Gemini),  
3) generate a dashboard-ready audit package with explicit JSON artifacts,  
4) review the results and turn them into actionable insights.

The Bright Data API is mandatory for automated collection.

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

- run the Bright Data collector
- produce the dated audit folder
- do not start editing the dashboard template yet

### Phase 3: audit package

- verify that the JSON artifacts are complete
- prepare the dashboard inputs
- only then connect the run to the React template

### Phase 4: analysis

- analyze the run
- summarize visibility, citations, search-trigger behavior, and fan-out
- add optional manual recommendations

If a run failed or the JSON is incomplete, stop in Phase 2 or 3 and say so clearly instead of pretending the dashboard is ready.

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

## Required tools

- `BRIGHTDATA_API_KEY` env var
- Bright Data dataset IDs for each chatbot you plan to run

## Tooling & credentials

- Auth mode: `env`
- Requires: `BRIGHTDATA_API_KEY`
- Fallback: none for automated collection
- If missing: stop, ask the user to set the env var locally, and continue only after they confirm it is ready

Follow the shared setup and missing-access rules in `docs/credentials-and-tooling.md`.

### Dataset IDs (always the same)

```
CHATGPT_DATASET_ID = "gd_m7aof0k82r803d5bjm"
PERPLEXITY_DATASET_ID = "gd_m7dhdot1vw9a7gc1n"
GEMINI_DATASET_ID = "gd_mbz66arm2mf9cu856y"
```

**IMPORTANT**: Before running the script, ask the user which chatbots they want to run:
- ChatGPT
- Perplexity  
- Gemini

They can select one, two, or all three. Only pass the dataset IDs for the selected chatbots to the script.

### API key handling

Before running the script, verify only whether `BRIGHTDATA_API_KEY` is set:

```bash
if [ -z "$BRIGHTDATA_API_KEY" ]; then echo "Not set"; else echo "Set"; fi
```

If it is missing, ask the user to set it locally in their own terminal:

```bash
export BRIGHTDATA_API_KEY="your-key-here"
```

Do not ask the user to paste the key in chat, and never print the key value.

## Collection script (Python)

Use:
- `geo-audit-report/scripts/brightdata-geo.py`

It:
- triggers selected datasets up front (part 1),
- polls pending snapshots together (part 2),
- downloads snapshots,
- saves results to `results.json` with both response-level details and summary metrics.

Important implementation notes:
- Do not force ChatGPT web search on or off in the input payload. Let the model decide naturally so the audit stays as close as possible to a real user experience.
- Query fan-out coverage depends on what each provider exposes through Bright Data. ChatGPT currently returns the richest query-level search data.
- Always preserve and surface whether search was actually triggered per response. Missing citations on a no-search response should be interpreted differently from missing citations on a searched response.
- The collector should be resumable in a lightweight way: reuse existing snapshot metadata when available, skip raw redownloads unless forced, and write `results.partial.json` during progress.

**Important timing note**: BrightData processing can take **1 minute to several minutes** depending on the number of prompts. With many prompts (e.g., 10+), expect 3-5+ minutes of wait time. Inform the user about this before running the script so they know what to expect.

**Output structure**: All files are saved in a dated folder (`YYYY-MM-DD`) within the specified `--out-dir`:
- `{out-dir}/{YYYY-MM-DD}/results.json` - Complete results data
- `{out-dir}/{YYYY-MM-DD}/snapshots/{chatbot}.json` - Snapshot metadata per chatbot
- `{out-dir}/{YYYY-MM-DD}/raw/{chatbot}-{snapshot_id}.json` - Raw snapshot data
- `{out-dir}/{YYYY-MM-DD}/report.html` - optional HTML report (generated by AI if requested)

### Example run

```bash
# Ensure BRIGHTDATA_API_KEY is set (user should export it themselves)
python3 geo-audit-report/scripts/brightdata-geo.py \
  --check-url "https://example.com" \
  --prompts-file prompts.txt \
  --chatgpt-dataset-id "gd_m7aof0k82r803d5bjm" \
  --perplexity-dataset-id "gd_m7dhdot1vw9a7gc1n" \
  --gemini-dataset-id "gd_mbz66arm2mf9cu856y" \
  --target-domains "example.com" \
  --brand-terms "Example,Example Product" \
  --out-dir ./geo-run

# Files will be saved in: ./geo-run/2025-01-15/ (or current date)
```

Note: Only include the dataset ID flags for chatbots the user selected (ChatGPT, Perplexity, and/or Gemini).

## Required audit artifacts

The audit is not complete unless the dated run folder contains the expected artifacts.

### Required

- `{out-dir}/{YYYY-MM-DD}/results.json`
- `{out-dir}/{YYYY-MM-DD}/snapshots/{chatbot}.json`
- `{out-dir}/{YYYY-MM-DD}/raw/{chatbot}-{snapshot_id}.json`

### Optional but expected in normal usage

- `{out-dir}/{YYYY-MM-DD}/tracked-prompts.json`
- `{out-dir}/{YYYY-MM-DD}/report.html`

### Artifact roles

- `results.json`
  Main run output for the dashboard and summary analysis.
- `tracked-prompts.json`
  Long-lived prompt tracking companion file used to compare prompt visibility over time.
- `report.html`
  Optional static export if the user wants a standalone deliverable.

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
   - Use `results.json` as the main audit input for the React template in `geo-audit-report/template`
   - Prepare or update `tracked-prompts.json` if prompt history is available or should start from this run
   - Optionally add a couple of manual recommendations in `manual_recommendations`
   - If the user wants an HTML export too, generate `report.html` in the same dated output folder

4. Present these conclusions clearly and concisely to the user, and let them know the dashboard JSON is ready.

## Output requirements

### React dashboard template

**IMPORTANT**: The Python script produces the audit JSON, and the React template in `geo-audit-report/template` reads that JSON directly.

Treat the React template as the expected companion artifact for the skill, not an optional extra. If the user wants a usable deliverable, the default path is:

1. run the collector
2. verify the JSON artifacts
3. connect the run to the template
4. review the dashboard

Do not describe the audit as “done” if the collector succeeded but the JSON does not match what the dashboard expects.

The expected workflow is:

1. Run the collector to produce `results.json`
2. Copy that file into the template app's `public/data/...` folder or point the app to it with env vars
3. Add a few manual recommendations directly in the JSON after reviewing the data
4. Launch the app and review the three tabs:
   - Overview
   - Prompts
   - Sources

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
