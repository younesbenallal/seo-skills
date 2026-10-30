# Report

Write `audit.json`, then render it:

```bash
python3 <skill>/scripts/render_report.py audit.json --out report.html
```

The template is a single HTML file with the data embedded: no build, no server. Sections without data are not rendered, so omit what you did not check instead of filling it with placeholders.

## Writing rules

- Write in the client's language (`language`: `fr` or `en` sets the template labels).
- Lead with the verdict: two or three sentences a founder understands. Say what is fine as clearly as what is broken.
- One finding = one problem with one fix. Merge symptoms with the same cause ("38 pages unreachable from the menu" and "categories have no inlinks" are one finding about fake links).
- Every finding has numbers and examples: how many URLs, which ones, from which source and date.
- `fix` says exactly what to change and where (CMS setting, template, robots.txt line, redirect rule), not "optimize X".
- Separate facts from inferences. When a verdict comes from a spoofed user agent or a sample, say so in `evidence`.
- No traffic or ranking forecasts. Say what the fix unblocks.
- The top 3 actions are the three findings with the best impact-to-effort ratio, not necessarily the three critical ones.

## Impact scale

- `critical`: stops indexing, AI access, or rendering of money pages or a large share of the site.
- `high`: wastes or splits signals on important pages, or hides them from search engines or AI.
- `medium`: hygiene with an indirect effect, or a real issue limited to secondary pages.
- `low`: worth doing when convenient.

Effort: `S` under an hour (a setting, a robots.txt line, a title), `M` half a day to two days, `L` a project (migration, rendering change).

Channels: `SEO`, `GEO`, `CRO` — the ones the fix actually helps.

## Shape

```json
{
  "site": "example.com",
  "client": "Example",
  "date": "2026-10-30",
  "language": "en",
  "auditor": "Holly&Stick",
  "scope": "412 URLs crawled (raw HTML) · 5 templates rendered · GSC sc-domain:example.com, 90 days",
  "verdict": "Two or three sentences.",
  "top_actions": [
    { "title": "Unblock OAI-SearchBot and PerplexityBot in Cloudflare", "why": "ChatGPT and Perplexity cannot cite the site today." }
  ],
  "scorecard": [
    { "area": "Crawl & indexing", "status": "good", "note": "One line." },
    { "area": "AI access", "status": "bad", "note": "" },
    { "area": "Canonicals & duplicates", "status": "warn", "note": "" },
    { "area": "JavaScript rendering", "status": "good", "note": "" },
    { "area": "Keyword targeting", "status": "warn", "note": "" },
    { "area": "Internal linking", "status": "warn", "note": "" },
    { "area": "Speed", "status": "unknown", "note": "" },
    { "area": "Conversion path", "status": "good", "note": "" }
  ],
  "funnel": [
    { "label": "URLs in sitemap", "value": 517 },
    { "label": "Indexed (GSC Pages report)", "value": 370 },
    { "label": "With impressions (90 d)", "value": 117 },
    { "label": "Top 3 on a query", "value": 20 }
  ],
  "funnel_note": "Source and date.",
  "findings": [
    {
      "title": "Menu categories are not links Google can follow",
      "impact": "high",
      "effort": "M",
      "channels": ["SEO", "GEO"],
      "area": "Internal linking",
      "evidence": "12 menu entries are <div role=\"link\" data-ofb64=...> on 357 of 359 pages. 38 sitemap pages are unreachable from the homepage by links.",
      "why": "Crawlers only follow <a href>. These pages get no internal authority and are discovered through the sitemap only.",
      "fix": "Replace the obfuscated entries in the Webflow navbar component with normal link blocks.",
      "owner": "Webflow developer",
      "affected_count": 38,
      "urls": [{ "url": "https://example.com/solopreneur", "note": "0 contextual inlinks" }],
      "source": "crawl.py, 2026-10-30"
    }
  ],
  "ai_bots": [
    { "token": "OAI-SearchBot", "owner": "OpenAI", "purpose": "ai_search", "robots": "allowed", "cdn": "ok", "note": "" }
  ],
  "index_presence": [
    { "engine": "Google", "status": "indexed", "evidence": "GSC: 370 of 517 sitemap URLs indexed" },
    { "engine": "Bing", "status": "partial", "evidence": "site: shows ~40 results; /pricing absent" },
    { "engine": "Brave", "status": "unknown", "evidence": "Rate-limited; check manually" },
    { "engine": "Staging (example.webflow.io)", "status": "absent", "expected": "absent", "evidence": "site: returns nothing" }
  ],
  "keyword_map": [
    { "url": "https://example.com/", "title": "Home | Example", "target_keyword": "invoicing software for agencies", "top_query": "example", "status": "no-target", "suggested_title": "Invoicing Software for Agencies | Example" }
  ],
  "cannibalization": [
    { "query": "best invoicing software", "pages": [{ "url": "https://example.com/blog/a", "clicks": 12, "impressions": 900, "position": 14.2 }], "recommendation": "Merge B into A and 301." }
  ],
  "internal_links": [
    { "source": "https://example.com/blog/high-traffic-post", "anchor": "invoicing software for agencies", "target": "https://example.com/", "why": "Same cluster, 820 clicks in 90 days" }
  ],
  "internal_links_note": "Optional one-line context.",
  "speed": [
    { "url": "https://example.com/", "lcp": "2.1 s", "lcp_category": "FAST", "inp": "180 ms", "inp_category": "FAST", "cls": "0.02", "cls_category": "FAST", "lab_score": 71 }
  ],
  "speed_note": "Field data, CrUX, mobile, 28 days.",
  "schema_suggestions": [
    { "template": "Home", "present": "none", "add": "Organization, WebSite", "why": "Brand entity for search and AI" }
  ],
  "next_steps": [
    { "when": "This week", "items": ["..."] },
    { "when": "This month", "items": ["..."] }
  ],
  "ignored": ["412 images without alt text: accessibility, no ranking effect at this scale."],
  "limits": ["Bing Webmaster Tools not connected: Bing presence checked by site: only."]
}
```

`status` values: scorecard `good | warn | bad | unknown`; `ai_bots.robots` `allowed | blocked`; `ai_bots.cdn` `ok | refused | inconclusive | untested | n/a` (`untested` for the agents in `bot_fetch.untested`, `n/a` for control tokens with no crawler); `index_presence.status` `indexed | partial | absent | unknown`, with optional `expected` (the desired status, shown green when met); `keyword_map.status` `aligned | weak | mismatch | no-target`. With `language: "fr"` the template translates these values and its labels.

Funnel: only use numbers you have. "Indexed" comes from the user's Search Console Pages report or from the URLs you inspected (say "of N inspected"); never from the sitemap API's `indexed` field.
