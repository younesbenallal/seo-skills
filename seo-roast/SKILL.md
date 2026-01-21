---
name: seo-roast
description: Roast a landing page or article from an SEO perspective (technical + on-page + content/intent). Optionally generate a screenshot-rich HTML report.
---

# SEO Roast (landing page / article)

You produce a blunt, actionable SEO roast using a consistent rubric, then ask whether to generate a detailed HTML report with screenshots.

## Inputs to collect

- URL(s) to roast (1–5)
- Page type: landing / product / blog article / programmatic page
- Target keyword (optional but strongly recommended)
- Market: language + country

## Tools (adaptive)

**Preferred**
- URL → Markdown tool (content extraction)
- SERP tool (to compare to what ranks)
- Screenshot tool (browser MCP / `agent-browser` / Playwright) to visualize the page  and for the HTML report

**Fallbacks**
- If content extraction fails: ask the user to paste the page HTML/markdown or the main copy.
- If no screenshots: produce report without screenshots (but still generate HTML).

## Roast rubric (use this order)

### 1) Indexing & SERP basics
- Title tag: uniqueness, keyword fit, clickability
- Meta description: relevance + CTR hook
- Canonical: correct self-canonical
- Robots meta: not accidentally `noindex`

### 2) Search intent & information architecture
- Does the page *answer* what the searcher wants within 10 seconds?
- Is the H1 aligned with the primary query?
- Are key sections missing vs. top-ranking pages?

### 3) On-page quality (content)
- Value early, above the fold
- Readability: short paragraphs, lots of different formats (lists/tables/callouts/images/etc.)
- Visual support: illustration ideas where needed
- Avoid: “only text blocks”, “fully AI content”, misleading anchors
- Bonus: multiple layouts, TL;DR/key takeaways, AEO/GEO-friendly phrasing

### 4) Internal linking & topical authority
- What should it link to (parent/child pages)? check anchor/link resemblence
- Are anchors truthful and specific?

### 5) Technical UX (lightweight)
- Clear CTAs, scannability, mobile layout issues
- Performance red flags you can infer (heavy hero, too many scripts)

## Output format (first response)

1. **Top 5 fixes** (highest ROI)
2. **Quick wins (<60 minutes)**
3. **Missing sections** (search intent gaps)
4. **Internal linking plan** (5–10 links)
5. **Snippet-ready improvements** (exact title/H1/meta suggestions)

Then ask:
> “Do you want a detailed HTML report (with screenshots)?”

## If user says “yes” (HTML report)

### Tool check
- If screenshot capability exists: capture at least 1 above-the-fold + 1 mid-page screenshot per URL.
- If not: generate the report with “screenshot unavailable” placeholders.

### Report requirements
- Single `report.html` output
- Use CSS variables (no hardcoded colors)
- Include sections matching the rubric + a prioritized backlog
- Footer must include: `holly-and-stick.com`

