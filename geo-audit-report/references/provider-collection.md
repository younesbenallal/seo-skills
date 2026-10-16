# Provider and collection reference

## Credentials and provider choice

ChatGPT browser collection is the default for ChatGPT. It drives a real chatgpt.com session in a dedicated Chrome profile and reads Fanout Fox captures, so it needs no API key and returns the model, fan-out queries, and every retrieved source. It covers ChatGPT only.

Use an API provider for Perplexity or Gemini, when the browser setup is unavailable, or when the user asks for one. The auth mode is `env`. Bright Data requires `BRIGHTDATA_API_KEY`; DataForSEO requires both `DATA_FOR_SEO_LOGIN` and `DATA_FOR_SEO_PASSWORD`. Follow the shared credential contract to verify presence without printing values and to explain missing setup. Bright Data has richer search-trigger and actual-citation traces than DataForSEO; DataForSEO supports only ChatGPT and Gemini here. Never silently change providers.

## ChatGPT browser (default for ChatGPT)

The collector lives in `geo-audit-report/scripts/chatgpt-browser/`. It connects with Playwright over CDP to Chrome on port 9333, using the profile `~/.chatgpt-runner-profile`. That profile keeps the ChatGPT login and the Fanout Fox extension between runs.

Setup, once per machine:

1. `bun install --cwd geo-audit-report/scripts/chatgpt-browser`
2. `bun geo-audit-report/scripts/chatgpt-browser/run.ts launch` from a terminal that stays open. Chrome exits with the shell that started it, so use the user's terminal rather than a short-lived agent shell.
3. Ask the user to log in to ChatGPT in that window and to install Fanout Fox from the Chrome Web Store. Never enter credentials yourself. A logged-out session still works but produces no Fanout Fox data if the extension is missing.
4. Recommend turning ChatGPT memory off in that account so earlier chats do not personalize answers.

Before a run, check that `http://127.0.0.1:9333/json/version` answers, then check the Fanout Fox workspace. Every capture is filed under the workspace that is active when ChatGPT answers, and the dashboard and brief aggregate per workspace, so each client needs its own workspace:

```bash
bun geo-audit-report/scripts/chatgpt-browser/run.ts workspaces                      # active workspace marked *
bun geo-audit-report/scripts/chatgpt-browser/run.ts workspace-create "Client" --domains client.com
```

Create the client's workspace only when none matches its name or domain, and confirm the name with the user first. These commands call Fanout Fox's own store module from an extension page, so no UI is needed. Then collect into the dated run folder:

```bash
bun geo-audit-report/scripts/chatgpt-browser/run.ts prompts.txt <out-dir>/YYYY-MM-DD --workspace "Client"
```

`--workspace` is required. The collector activates that workspace before sending anything, stops if it does not exist, and after the run moves back any of the run's captures that were filed elsewhere (for example after a switch in the UI). The active workspace is global to the profile: tell the user not to run their own ChatGPT prompts in that profile during a collection, or their captures will land in the client's workspace.

To fix misfiled captures:

```bash
bun geo-audit-report/scripts/chatgpt-browser/run.ts move "Client" <run-dir>                # every capture of a run
bun geo-audit-report/scripts/chatgpt-browser/run.ts move "Client" --match "prompt text"    # captures whose prompt contains the text
```

Moving a capture never deletes it. Report what moved, and ask before moving captures the current run did not create.

Each prompt opens a new chat in its own tab, two tabs at a time by default (`--concurrency`); lower it to 1 if ChatGPT starts rate-limiting. Only one collection runs at a time: a second one waits for the first to finish (it prints who holds `~/.chatgpt-runner-profile.lock`), because parallel runs share the same Chrome, ChatGPT account and active Fanout Fox workspace. Run clients one after the other instead of starting collections from several sessions. The collector writes `raw/answers.json` (prompt, conversation URL, rendered text, rendered links, timestamp, or an `error`) and `raw/fanoutfox.json` (the matching Fanout Fox captures read from the extension storage). A failed prompt gets `raw/error-N.png`. The collector refuses to send a prompt when the composer holds other text, because ChatGPT restores unsent drafts across tabs, and it checks the sent message against the prompt. To re-read captures for an existing run, use `bun geo-audit-report/scripts/chatgpt-browser/run.ts fanoutfox <run-dir>`.

Then build the v3 file:

```bash
python3 geo-audit-report/scripts/normalize-chatgpt-browser.py \
  --run-dir <out-dir>/YYYY-MM-DD --check-url "https://example.com" \
  --target-domains "example.com" --brand-terms "Example,Example Product"
```

The normalizer reuses the Bright Data collector's analysis, so mentions, fan-out summaries, competitor entities, and diagnostics are computed in the same way as for other providers. Field mapping:

| v3 field | Source |
| --- | --- |
| `answer_text_markdown` | Fanout Fox `raw.answerText`, with ChatGPT UI components converted to Markdown; the rendered text when no capture exists |
| `brands_mentioned` | `<Entity value>` names in the answer |
| `model` | Fanout Fox `model.resolved` |
| `used_web_search`, `fan_out_queries` | Fanout Fox `searchedWeb` and `fanout` |
| `search_sources` | Fanout Fox `sources`, deduplicated by URL |
| `attached_links` | Links rendered in the answer, excluding chatgpt.com |
| `actual_citations` | **Temporary workaround.** `raw/answers.json` → `citations`, resolved by the collector (see below). Missing when that field is absent or `null`, never reported as zero |

### Citations: temporary workaround

Fanout Fox marks a source as cited only through the conversation's `content_references`. Current ChatGPT conversations leave that list empty and put citations inline in the answer as `<Cite refs={["turn130531search1"]}/>`, so every Fanout Fox source reads `cited: false`, and its own dashboard shows "0 cited".

Until Fanout Fox handles this format, the collector resolves the markers itself: after each answer it reloads the conversation, reads the `/backend-api/conversations/<id>` response the page loads, and maps each marker to the search result with the same `ref_id` (`turn_index`, `ref_type`, `ref_index`). The result is stored per answer as `citations: [{code, url, title}]`, where an unresolved marker keeps `url: null`. `bun geo-audit-report/scripts/chatgpt-browser/run.ts citations <run-dir>` does the same for an existing run whose conversations are still in the account. Logged-out conversations (`/uc/` URLs) cannot be reopened.

This is our own reading of ChatGPT's internal format, kept deliberately small. It is meant to be removed once Fanout Fox flags cited sources again: check a recent capture for `cited: true` sources, then delete `resolveCitations` and the `citations` command in `run.ts`, and `citation_records` in the normalizer. Do not extend this parser; prefer Fanout Fox for any other interpretation of ChatGPT.

Fanout Fox's own dashboard and Monday brief aggregate the whole workspace, including test prompts, so use the exported captures rather than the brief's counts as audit evidence.

## Bright Data

Ask which chatbots to run: ChatGPT, Perplexity, and/or Gemini. Pass only selected dataset IDs:

```text
ChatGPT    gd_m7aof0k82r803d5bjm
Perplexity gd_m7dhdot1vw9a7gc1n
Gemini     gd_mbz66arm2mf9cu856y
```

Use synchronous `/datasets/v3/scrape` for 1–20 prompts. Use asynchronous `/datasets/v3/trigger` for more than 20, explicit batch runs, or `--collection-mode async`. Let the collector follow a returned `snapshot_id`, preserve the raw response, poll pending snapshots together, and write `results.partial.json` during progress.

Keep `custom_output_fields` aligned with each dataset's current output schema. The Gemini dataset rejected `sources` in September 2026; the collector requests only its supported core fields and reports unavailable search traces as missing.

Bright Data's ChatGPT schema notice received on 2026-10-06 removes `search_sources_more` and its nested fields, `model`, and `web_search_query`; these now return `null`. The collector excludes them from ChatGPT output requests. `search_sources_more` was never consumed. Report the model and fan-out queries as unavailable when missing, while continuing to use `web_search_triggered`, `search_sources`, and actual citations. Preserve model/query evidence in older exports and other providers. The legacy `recommendations` field, rejected by this dataset on 2026-09-30, is also excluded from requests.

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
