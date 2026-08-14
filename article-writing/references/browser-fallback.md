# Browser SERP fallback

Inspect a localized Google result page with the country and language of the ICP. Use `hl=<language>` and `gl=<country code>` where supported, and state that this is country-biased rather than a precise location simulation.

Ask the user to choose DataForSEO setup or this less reproducible fallback before switching. When chosen:

1. Use an already available Browser, Chrome, or Playwright tool.
2. Otherwise check `agent-browser --help`.
3. If missing, ask the user to install it locally with `npm install -g agent-browser`, then resume after confirmation.
4. If browser access remains unavailable, ask for 3–5 competitor URLs.

Inspect the best 3–5 relevant organic results, not blindly the first links. Open each chosen result and capture title, URL, snippet, and H1–H6 headings only. Do not treat search-result snippets as page outlines, and do not load every full page into the main context.
