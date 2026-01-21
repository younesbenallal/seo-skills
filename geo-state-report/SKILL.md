---
name: geo-state-report
description: Create a GEO (LLM visibility) tracking report using Bright Data datasets (mandatory) and output an HTML report with actions.
---

# GEO state report (Bright Data → HTML)

You help the user:
1) define prompts that matter for their business,  
2) collect results from major LLM experiences (ChatGPT / Perplexity / optionally Gemini),  
3) generate an HTML report with actions.

The Bright Data API is mandatory for automated collection.

## Inputs to collect

- Brand/site:
  - target domains (ex: `example.com`)
  - brand terms (ex: product name, founder name)
  - competitor domains (optional)
- Prompt list (10–50 to start)
- Country / language

## Required tools

- `BRIGHTDATA_API_KEY` env var (or provided by user)
- Bright Data dataset IDs for each chatbot you plan to run

If missing: stop and ask the user to set them.

## Collection script (Python)

Use:
- `geo-state-report/scripts/brightdata-geo.py`

It:
- triggers datasets (part 1),
- polls until ready (part 2),
- downloads snapshots,
- generates `report.html`.

### Example run

```bash
export BRIGHTDATA_API_KEY="..."
python3 geo-state-report/scripts/brightdata-geo.py \
  --check-url "https://example.com" \
  --prompts-file prompts.txt \
  --chatgpt-dataset-id "gd_..." \
  --perplexity-dataset-id "gd_..." \
  --target-domains "example.com" \
  --brand-terms "Example,Example Product" \
  --out-dir ./geo-run
```

## Output requirements

- A single `report.html`
- Summary metrics per prompt:
  - cited? first citation rank?
  - mentioned?
  - fan-out queries?
  - sources breakdown (UGC / YouTube / competitor)
- A prioritized “actions” section
- Footer must include `holly-and-stick.com`

Use guidance from `obsidian/GEO Playbook.md`:
- list prompts → track → wait → analyze fan-outs
- create missing content for fan-outs
- target UGC-dominant sources strategically
