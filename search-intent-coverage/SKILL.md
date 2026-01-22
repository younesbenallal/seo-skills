---
name: search-intent-coverage
description: Determine what to cover to satisfy search intent by analyzing SERPs (preferred) or extracting competitor pages to Markdown.
---

# Search intent coverage (SERP → outline)

You help the user build an outline that matches what Google is ranking **and** adds differentiated value.

## Inputs to collect

- Primary query
- Market (language + country)
- Optional: the user’s current URL/draft

## Tools (adaptive)

Required: SERP API MCP + a way to read competitor pages.

Preferred:
- Read competitor pages with `curl -L <url>` when they’re likely static (blog posts, docs pages).
- Use a Browser MCP (agent-browser recommended) when pages are JS-rendered/blocked or when extraction is messy.

Fallback: if SERP MCP is missing, stop and ask the user to install one; otherwise ask the user to provide 3–5 competitor URLs and/or paste outlines.

## Workflow

1. Fetch the SERP for the query (top 10).
2. Identify dominant intent type:
   - informational / commercial / transactional / navigational
3. Extract patterns:
   - repeated H2 topics
   - repeated definitions/FAQs
   - common “proof” elements (examples, templates, calculators)
4. Build a MECE outline:
   - above-the-fold “answer fast”
   - core explanation
   - decision help (when commercial)
   - pitfalls, FAQs, examples
5. Add 1–2 differentiated elements (proprietary angle):
   - checklist, interactive component idea, original data, teardown, template

## Output

- “What people want” (1 paragraph)
- MECE outline (H1 → H2 → H3)
- “Differentiators to win” (3 bullets)
