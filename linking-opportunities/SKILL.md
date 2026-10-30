---
name: linking-opportunities
description: Find contextual backlink opportunities on a specific prospect site using localized SERPs, page evidence, and outreach angles. Use when the user wants pages on another domain that could link to their content.
---

# Linking opportunities (site-specific)

You help the user find **contextual backlink opportunities**: pages on another website (the prospect) that could link to the user's page(s). These are not internal links, because the source and target belong to different sites.

## Shared context first

Run the shared preflight in [`../docs/credentials-and-tooling.md`](../docs/credentials-and-tooling.md). Read `.seo-context.md` when present, reuse its saved site, target pages, competitors, and market context, and ask only for prospect-specific gaps.

## Inputs to collect (ask fast, 1–2 lines each)

1. **Prospect site**: domain (example: `example.com`)
2. **Your site**: domain + 1–3 target URLs you want links to
3. **Topic/keywords**: 5–30 seed keywords (or “use my target page to extract them”)
4. **Market**: language + country (for SERP localization)

If the user doesn’t know the keywords yet, extract them from:
- the target page (URL → markdown), or
- the page title/H1 + section headings, or
- Search Console queries (if available).

## Tooling & credentials

- Auth mode: `none` or `mcp`, depending on the SERP source
- Requires: live SERP access through a structured provider API, SERP MCP, or browser tool
- Fallback: use Browser, Chrome, Playwright, or computer-use access to inspect live SERPs when structured SERP data is unavailable
- If no live SERP path is available: stop and ask the user to connect one or provide a SERP export

## Browser tool selection and evidence capture

When validating candidate pages, follow [references/browser-evidence.md](references/browser-evidence.md). Do not use `curl` or recommend a candidate from a snippet alone.

## Workflow

### 1) Confirm what “good opportunities” means

Ask which link type they want:
- “Contextual mention inside an existing article”
- “Resource list / tools list”
- “Glossary definition”
- “Comparison / alternatives”

### 2) Generate non-redundant “site:” queries

Build queries for each seed keyword:
- `site:PROSPECT keyword`
- `site:PROSPECT intitle:keyword`
- `site:PROSPECT (resources OR tools OR checklist OR guide) keyword`
- `site:PROSPECT "exact phrase"`

Also run link-likely patterns (even without keywords):
- `site:PROSPECT (resources OR tools OR glossary OR directory OR partners OR integrations)`
- `site:PROSPECT ("recommended" OR "we use" OR "stack" OR "alternatives")`

### 3) Pull SERPs and dedupe URLs

For each query:
- Fetch top results
- Keep **organic results**
- Deduplicate by canonical URL when possible

### 4) Score and label each opportunity

For each candidate page, produce:
- **Opportunity type**: resource list / blog / glossary / comparison / integration / docs
- **Relevance**: why this page matches the user’s target
- **Suggested anchor**: specific and truthful
- **One outreach angle**: “quick win reason” for the editor to link

Use a lightweight 1–5 score for each candidate: relevance to the target page, contextual fit of the source passage, likelihood the link is editorially plausible, and outreach value. Average the four dimensions (or explain a deliberate override); this is a prioritization aid, not a prediction of link acquisition.

### 5) Output (copy/paste friendly)

Return:
- A short top-10 list (highest impact)
- A table of all opportunities with columns:
  - `prospect_url`, `query_used`, `type`, `page_title`, `evidence_snippet`, `why_link_fits`, `suggested_anchor`, `outreach_angle`, `score`

Include the observed page title and a 2–4 sentence evidence snippet for every recommended opportunity. If screenshots were captured, include their path or URL. Keep observed evidence distinct from the proposed anchor and outreach copy.

## Notes

Use whichever live SERP source is available and record it in the output. Structured providers such as DataForSEO, Serper.dev, SerpApi, and Bright Data are useful for repeatable data, while browser inspection is a valid fallback for smaller runs.
