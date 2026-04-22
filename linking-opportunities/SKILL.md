---
name: linking-opportunities
description: Find contextual backlink opportunities on a specific prospect site using SERPs (site: queries), then propose concrete outreach angles + anchors.
---

# Linking opportunities (site-specific)

You help the user find **contextual internal-link opportunities on another website** (a prospect) that could link to the user’s page(s).

## Shared context first

Before asking repeated discovery questions, check whether `.agents/seo-context.md` exists.

If it does:
- read it first
- reuse the saved site, target pages, competitors, and market context
- ask only for prospect-specific gaps that are still missing

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

- Auth mode: `mcp`
- Requires: SERP API MCP
- Fallback: Browser MCP or `agent-browser` for validating candidate pages, but no fallback for live SERP collection
- If missing: stop, ask the user to install or configure a SERP API MCP, and continue only after they confirm it is ready

Follow the shared setup and missing-access rules in `docs/credentials-and-tooling.md`.

## Required tools

Require:
- A **SERP API MCP** (to fetch live Google results).

For opening candidate pages and confirming context:
- Use a **Browser MCP** if available.
- Otherwise, use the **agent-browser CLI** (install if needed).

If the SERP MCP is missing, stop and ask the user to install a SERP provider MCP (this repo intentionally does not ship an env-var fallback).

## Browser tool selection and evidence capture

Use this exact workflow for each candidate URL to validate context and capture evidence. Do not use `curl`.

### If Browser MCP is available

1) Open the page:
   - `Open URL: https://example.com/path`
2) Find a relevant paragraph/section:
   - Search the page for the keyword or topic.
   - Identify the closest heading + paragraph that could contain a link.
3) Capture evidence:
   - Record the **page title**.
   - Copy a **2–4 sentence snippet** from the paragraph that would contain the link.
   - If the MCP supports screenshots, take one focused on the paragraph and note the file/URL.

### If Browser MCP is NOT available (agent-browser CLI fallback)

1) Install if missing:
   - `npm i -g @openai/agent-browser`
2) Open the candidate URL:
   - `agent-browser open "https://example.com/path"`
3) Find the relevant paragraph/section:
   - `agent-browser find "keyword or phrase"`
4) Capture evidence:
   - `agent-browser title`
   - `agent-browser extract --near "keyword or phrase" --sentences 4`
   - If screenshots are supported: `agent-browser screenshot --selector "css-selector-for-paragraph"`

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

## Notes

This repo intentionally does not ship an env-var SERP fallback. Use a SERP API MCP.
