---
name: geo-audit-report
description: Create a GEO audit using Bright Data datasets (mandatory) and output a reusable dashboard-ready JSON plus a React template app.
---

# GEO audit report (Bright Data → dashboard)

You help the user:
1) define prompts that matter for their business,  
2) collect results from major LLM experiences (ChatGPT / Perplexity / optionally Gemini),  
3) generate a dashboard-ready audit JSON and optional recommendations.

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

## Required tools

- `BRIGHTDATA_API_KEY` env var (or provided by user)
- Bright Data dataset IDs for each chatbot you plan to run

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

### API Key Security Instructions

**Avoid exposing the BrightData API key in chat messages or code.**

1. **Check if key exists**: Before running the script, check if `BRIGHTDATA_API_KEY` is already set in the environment:
   ```bash
   # Check without exposing the value
   if [ -z "$BRIGHTDATA_API_KEY" ]; then echo "Not set"; else echo "Set"; fi
   ```

2. **If key is not set**: Ask the user to export it themselves with these instructions:
   - Go to https://brightdata.com and log in
   - Navigate to your account settings/API section
   - Generate a new API key if needed
   - Go to Terminal and run: `export BRIGHTDATA_API_KEY="your-key-here"`
   - Do NOT paste the key in chat - the user should run the export command themselves but if they do, just use it (it's too late lol)

3. **Never read or display the key**: If you need to verify it's set, only check if the variable exists (is non-empty), never echo or display its value.

If missing: stop and ask the user to set them using the export command above.

## Collection script (Python)

Use:
- `geo-audit-report/scripts/brightdata-geo.py`

It:
- triggers datasets (part 1),
- polls until ready (part 2),
- downloads snapshots,
- saves results to `results.json` with both response-level details and summary metrics.

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

## Post-execution analysis

**After the script completes successfully**, you MUST:

1. Read the `results.json` file from the dated output folder
2. Analyze the data and provide initial conclusions, including:
   - Overall visibility summary (cited vs mentioned vs not visible)
   - Which chatbots perform best/worst for the brand
   - Key patterns across prompts (e.g., which prompts get cited, which don't)
   - Fan-out query insights (what related queries are being suggested)
   - Source breakdown insights (UGC vs YouTube vs web dominance)
   - Competitor mentions if any
   - Top priority actions based on the data

3. **Prepare the dashboard files**:
   - Use `results.json` as the main audit input for the React template in `geo-audit-report/template`
   - Optionally add a couple of manual recommendations in `manual_recommendations`
   - If the user wants an HTML export too, generate `report.html` in the same dated output folder

4. Present these conclusions clearly and concisely to the user, and let them know the dashboard JSON is ready.

## Output requirements

### React dashboard template

**IMPORTANT**: The Python script produces the audit JSON, and the React template in `geo-audit-report/template` reads that JSON directly.

The expected workflow is:

1. Run the collector to produce `results.json`
2. Copy that file into the template app's `public/data/...` folder or point the app to it with env vars
3. Add a few manual recommendations directly in the JSON after reviewing the data
4. Launch the app and review the three tabs:
   - Overview
   - Prompts
   - Sources

### Dashboard requirements

The dashboard should support:

- Overview metrics and prompt visibility
- Prompt-level drilldown per chatbot
- Source grouping by domain
- Manual recommendations added by AI in the JSON
- A separate JSON file tracking prompts over time
- Footer including `holly-and-stick.com`

Use guidance from `obsidian/GEO Playbook.md`:
- list prompts → track → wait → analyze fan-outs
- create missing content for fan-outs
- target UGC-dominant sources strategically
