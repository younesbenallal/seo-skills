# AI crawler access

Read this before judging the `robots` and `bot_fetch` sections of `site.json`.

## The one rule

Blocking **training** is a business choice and costs no visibility. Blocking **AI search** or **user-triggered** agents removes the site from AI answers. Report the first as information and the second as a critical finding when it affects pages the business wants cited.

Vendor docs checked on 2026-10-30. Re-check a vendor's page when a verdict depends on a token not listed here.

## Tokens by purpose

**Search engines (also feed AI answers)**

| Token | Owner | Notes |
| --- | --- | --- |
| `Googlebot` | Google | Also feeds AI Overviews and AI Mode; they cannot be separated |
| `Bingbot` | Microsoft | Feeds Copilot, DuckDuckGo, Yahoo, Ecosia, and is one of ChatGPT search's sources |
| `Applebot` | Apple | Siri, Spotlight, Safari suggestions |
| `DuckDuckBot` | DuckDuckGo | |

**AI search indexes (block = no citations)**

| Token | Owner | Notes |
| --- | --- | --- |
| `OAI-SearchBot` | OpenAI | The ChatGPT search lever. Changes apply in about 24 hours |
| `Claude-SearchBot` | Anthropic | |
| `PerplexityBot` | Perplexity | |
| `DuckAssistBot` | DuckDuckGo | Duck.ai answers; opt-out applies in about 72 hours |
| `meta-webindexer` | Meta | Meta AI search |
| `Amzn-SearchBot` | Amazon | Rufus, Alexa answers |
| `MistralAI-Index` | Mistral | Le Chat search |

**User-triggered fetchers (a person asked the assistant to read the page)**

| Token | Owner | Honors robots.txt |
| --- | --- | --- |
| `ChatGPT-User` | OpenAI | May not apply |
| `Claude-User` | Anthropic | Yes |
| `Perplexity-User` | Perplexity | Generally ignores |
| `MistralAI-User` | Mistral | Not stated |
| `meta-externalfetcher` | Meta | May bypass |
| `Amzn-User` | Amazon | May not follow |

**Training (blocking is a choice)**

| Token | Owner | Notes |
| --- | --- | --- |
| `GPTBot` | OpenAI | Does not affect ChatGPT search |
| `ClaudeBot` | Anthropic | Does not affect Claude search |
| `Google-Extended` | Google | Control token, no crawler. Gemini training and grounding. Does not affect Search or AI Overviews |
| `Applebot-Extended` | Apple | Control token, no crawler |
| `meta-externalagent` | Meta | |
| `CCBot` | Common Crawl | Feeds many model builders |
| `MistralAI-Training` | Mistral | |
| `Amazonbot` | Amazon | |
| `Bytespider` | ByteDance | Poor compliance reported; block at the CDN if needed |

Brave has no crawler token: it indexes what Googlebot may crawl, and `noindex` controls its index. Anthropic uses Brave Search as its web-search provider, so a site missing from Brave is weaker in Claude.

Obsolete tokens to remove from robots.txt when found: `anthropic-ai`, `Claude-Web`. Tokens with no vendor documentation (`xAI-Bot`, `DeepSeekBot`, `BingAI`) do nothing reliable.

Sources: [OpenAI](https://developers.openai.com/api/docs/bots), [Anthropic](https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler), [Perplexity](https://docs.perplexity.ai/docs/resources/perplexity-crawlers), [Google](https://developers.google.com/crawling/docs/crawlers-fetchers/google-common-crawlers), [Apple](https://support.apple.com/en-us/119829), [Meta](https://developers.facebook.com/documentation/sharing/webmasters/web-crawlers), [Mistral](https://docs.mistral.ai/robots/), [Amazon](https://developer.amazon.com/amazonbot), [DuckDuckGo](https://duckduckgo.com/duckduckgo-help-pages/results/duckassistbot/), and Vanessa Fox's [reference guide](https://www.vanessafox.com/complete-reference-blocking-llm-crawlers/) and [CDN settings guide](https://www.vanessafox.com/ai-crawler-settings-by-host-and-cdn-cloudflare-fastly-akamai-wp-engine-shopify-and-more/).

## robots.txt traps

- A bot that matches a named group ignores the `*` group entirely. `User-agent: GPTBot` + `Disallow: /private` means GPTBot may crawl everything else, even what `*` disallows. Conversely, an allowlist of a few named bots plus `User-agent: *` / `Disallow: /` blocks every agent the list forgets.
- A robots.txt that returns 5xx is read as "disallow everything" by Google. A robots.txt that returns HTML (SPA catch-all) is unparseable: say so.
- `Content-Signal: search=yes, ai-input=no, ai-train=no` (Cloudflare's managed robots.txt) is a preference, not a block. `ai-input=no` asks AI systems not to use the content for answers: flag it as a GEO risk if the business wants citations.

## CDN and WAF blocking

robots.txt can allow a bot while the CDN refuses it. Cloudflare's AI Crawl Control (all plans), its legacy "Block AI bots" switch, Bot Fight Mode, Vercel, Fastly, Akamai, DataDome, and Shopify can all refuse AI agents. Per Vanessa Fox's guide, Cloudflare changed defaults for newly onboarded sites in September 2026 (training disallowed, agent fetches blocked on pages with ads); treat that as reported, not verified.

`site_checks.py` requests the page as a browser, then with each bot's user agent (agents without a published user-agent string are listed in `bot_fetch.untested` and only checked in robots.txt), and compares status, words, challenge pages, and block headers (`cf-mitigated`, `x-datadome`, `x-px-blocked`, `x-vercel-mitigated`). Read its `reading` line:

- **Nothing differs**: no edge blocking on user agent. Report as OK.
- **Googlebot passes, AI agents refused**: likely an AI-bot rule. High or critical finding; tell the user where the setting lives (Cloudflare: Security > Bots / AI Crawl Control).
- **Googlebot refused too**: the WAF verifies bots by IP, so spoofed agents are refused while real bots may pass. Inconclusive: ask for the CDN's bot settings or logs filtered on the vendors' published IP ranges. Do not report a block.
- **Browser refused**: the test itself is blocked from this machine. Inconclusive.

A direct test closes the question: ask ChatGPT (search on), Claude, and Perplexity to open a specific URL and quote its H1. A correct quote proves the user-triggered fetch works; a refusal or an invented H1 is evidence of a block or a JS-only page. Use a browser tool when available, and label the result with the date.

## llms.txt

No major AI search engine documents using it for retrieval or ranking: never rank its absence above low. When it exists, read it: it is copy that assistants may fetch and quote, so wrong claims, outdated offers, or links to redirected pages in it are real findings.
