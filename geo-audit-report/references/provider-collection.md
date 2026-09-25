# Provider and collection reference

## Credentials and provider choice

The auth mode is `env`. Bright Data requires `BRIGHTDATA_API_KEY`; DataForSEO requires both `DATA_FOR_SEO_LOGIN` and `DATA_FOR_SEO_PASSWORD`. Follow the shared credential contract to verify presence without printing values and to explain missing setup.

Bright Data is preferred for richer search-trigger and search-result trace fidelity. DataForSEO is a valid fallback but supports only ChatGPT and Gemini here, with weaker fan-out and source traces. Never silently change providers.

## Bright Data

Ask which chatbots to run: ChatGPT, Perplexity, and/or Gemini. Pass only selected dataset IDs:

```text
ChatGPT    gd_m7aof0k82r803d5bjm
Perplexity gd_m7dhdot1vw9a7gc1n
Gemini     gd_mbz66arm2mf9cu856y
```

Use synchronous `/datasets/v3/scrape` for 1–20 prompts. Use asynchronous `/datasets/v3/trigger` for more than 20, explicit batch runs, or `--collection-mode async`. Let the collector follow a returned `snapshot_id`, preserve the raw response, poll pending snapshots together, and write `results.partial.json` during progress.

Keep `custom_output_fields` aligned with each dataset's current output schema. The Gemini dataset rejected `sources` in September 2026; the collector requests only its supported core fields and reports unavailable search traces as missing.

```bash
python3 geo-audit-report/scripts/brightdata-geo.py \
  --check-url "https://example.com" --prompts-file prompts.txt \
  --chatgpt-dataset-id "gd_m7aof0k82r803d5bjm" \
  --target-domains "example.com" --brand-terms "Example,Example Product" \
  --out-dir ./geo-run
```

To normalize an existing raw export without a paid rerun:

```bash
python3 geo-audit-report/scripts/normalize-brightdata-geo.py \
  --raw <raw-brightdata.json> --out <run-dir>/results.json \
  --check-url <site-url> --target-domains <domain> \
  --brand-terms <comma-separated-brand-terms> \
  --dataset-id <original-dataset-id> --snapshot-id <original-snapshot-id> \
  --run-at <original-run-timestamp>
```

## DataForSEO

Ask which of ChatGPT and Gemini to run. ChatGPT uses `llm_scraper/live/advanced`; Gemini uses the same endpoint. Perplexity is not supported in this fallback, and there are no dataset IDs or snapshot polls.

```bash
python3 geo-audit-report/scripts/dataforseo-geo.py \
  --check-url "https://example.com" --prompts-file prompts.txt \
  --chatbots "chatgpt,gemini" --country "US" --language "en" \
  --target-domains "example.com" --brand-terms "Example,Example Product" \
  --out-dir ./geo-run
```

Do not force ChatGPT search on or off. Preserve whether search actually triggered. DataForSEO calls can take up to 120 seconds per single-task request; Bright Data generally takes one to several minutes depending on prompt count. Tell the user which timing profile applies before running.
