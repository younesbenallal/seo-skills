---
name: linking-opportunities
description: Find contextual backlink opportunities on a specific prospect site using SERPs (site: queries), then propose concrete outreach angles + anchors.
---

# Linking opportunities (site-specific)

You help the user find **contextual internal-link opportunities on another website** (a prospect) that could link to the user’s page(s).

## Inputs to collect (ask fast, 1–2 lines each)

1. **Prospect site**: domain (example: `example.com`)
2. **Your site**: domain + 1–3 target URLs you want links to
3. **Topic/keywords**: 5–30 seed keywords (or “use my target page to extract them”)
4. **Market**: language + country (for SERP localization)

If the user doesn’t know the keywords yet, extract them from:
- the target page (URL → markdown), or
- the page title/H1 + section headings, or
- Search Console queries (if available).

## Required tools

You need **one** of:
- A **SERP MCP** (preferred), OR
- `serper.dev` API key (`SERPER_API_KEY`) + the helper script `scripts/serper-dev.mjs`

If neither is available, stop and tell the user exactly how to set up one of them.

## Workflow

### 1) Confirm what “good opportunities” means

Ask which link type they want:
- “Contextual mention inside an existing article”
- “Resource list / tools list”
- “Glossary definition”
- “Comparison / alternatives”

### 2) Generate “site:” queries (MECE)

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

### 5) Output (copy/paste friendly)

Return:
- A short top-10 list (highest impact)
- A table of all opportunities with columns:
  - `prospect_url`, `query_used`, `type`, `why_link_fits`, `suggested_anchor`, `outreach_angle`

## Optional: run the Serper fallback script

If no SERP MCP is available but `SERPER_API_KEY` exists, you can generate raw SERPs with:

```bash
node scripts/serper-dev.mjs --q 'site:example.com "pricing"' --pages 2
```

Then use the `organic_all` URLs as the starting set.
