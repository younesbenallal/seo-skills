---
name: seo-roast
description: Roast a landing page or article for technical SEO, on-page quality, and search intent. Use when the user wants a direct page critique or an optional screenshot-based HTML report.
---

# SEO Roast (landing page / article)

Use this skill when the user wants a direct, actionable SEO review of one to five landing pages, product pages, or articles. Start with the rubric-based roast and offer the optional HTML report afterward.

## Context and preflight

Run the shared preflight in [`../docs/credentials-and-tooling.md`](../docs/credentials-and-tooling.md) before discovery. Reuse `.seo-context.md` when it exists, then ask only for URL-, keyword-, or market-specific gaps. Record assumptions and limitations; do not invent business priorities, target markets, or edit permission.

## Inputs to collect

- URL(s) to roast (1–5)
- Page type: landing / product / blog article / programmatic page
- Target keyword (optional but strongly recommended)
- Market: language + country

## Tooling & credentials

- Auth mode: `none`
- Requires: no external credential
- Fallback: if Browser access is unavailable, ask the user for the main copy and key page sections
- Optional tools: Browser MCP, `agent-browser`, or structured SERP access
## Tool selection

**Browser selection workflow**
1) Detect whether a Browser/Chrome/Playwright MCP is available; if yes, use it for page access and screenshots.
2) If no browser MCP, check for the `agent-browser` CLI and use it when installed. Do not install global packages without the user's approval; if it is missing, use the copy-only fallback.
3) If browsing is unavailable: ask for the main copy and key sections such as title, H1, and meta description.

**SERP**
- Use structured SERP data when available to compare against what ranks. If it is unavailable, inspect Google results with the available browser path and label the source clearly.

## Roast rubric (use this order)

### 1) Indexing & SERP basics
- Title tag: uniqueness, keyword fit, clickability
- Meta description: relevance + CTR hook
- Canonical: correct self-canonical
- Robots meta: not accidentally `noindex`

### 2) Search intent & information architecture
- Does the page make the answer or next useful action apparent from the opening viewport?
- Is the H1 aligned with the primary query?
- Are key sections missing vs. top-ranking pages?

### 3) On-page quality (content)
- Value early, above the fold
- Readability: paragraph length and formats that support the subject, such as lists, tables, callouts, or images where useful
- Visual support: illustration ideas where needed
- Flag long uninterrupted text where a list, table, example, or visual would communicate the same idea more clearly
- Flag unsupported generic copy, repeated abstractions, and misleading anchors
- Look for concise direct answers to definition or question queries, plus structured takeaways when they help the reader

### 4) Internal linking & topical authority
- What should it link to (parent/child pages)? Check that each proposed link is relevant and present or clearly marked as missing.
- Are anchors truthful and specific?

### 5) Technical UX (lightweight)
- Clear CTAs, scannability, mobile layout issues
- Suspected performance risks such as oversized hero media or excessive scripts; label them as suspected unless measurement or network evidence confirms them

## Output format (first response)

Tie each finding to observed page text, markup, layout, or SERP evidence. Label recommendations based on inference or unavailable access instead of presenting them as observations.

1. **Top 5 fixes** (highest ROI)
2. **Quick wins (<60 minutes)**
3. **Missing sections** (search intent gaps)
4. **Internal linking plan** (up to 5–10 evidence-backed links; return fewer when the site lacks suitable targets)
5. **Snippet-ready improvements** (exact title/H1/meta suggestions)

Then ask:
> “Do you want a detailed HTML report (with screenshots)?”

## Optional HTML report

If the user says yes, follow [`references/html-report.md`](references/html-report.md). Otherwise, stop after the roast and the offer.
