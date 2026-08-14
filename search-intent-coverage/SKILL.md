---
name: search-intent-coverage
description: Build a standalone search-intent analysis or content outline from localized SERP evidence or competitor pages. Use when the user wants to understand and plan coverage without drafting the complete article.
---

# Search intent coverage (SERP → outline)

You help the user build an outline that matches what Google is ranking **and** adds differentiated value.

## Shared context first

Run the shared preflight in [`../docs/credentials-and-tooling.md`](../docs/credentials-and-tooling.md). Read `.seo-context.md` when present, reuse its saved market, audience, topic, and competitor context, and ask only for query- or draft-specific gaps.

## Inputs to collect

- Primary query
- Market (language + country)
- Intended audience and content type, when they are not clear from context
- Business goal or desired reader action, when it affects the outline
- Optional: the user’s current URL/draft

## Tooling & credentials

- Auth mode: `mcp` for live SERP analysis; `none` for user-provided competitor pages or outlines
- Requires: SERP API MCP for live localized results
- Fallback: analyze user-provided competitor URLs or outlines and label the result `competitor-only`, without claiming current SERP coverage
- Browser fallback: Browser MCP or `agent-browser` for reading supplied competitor pages; pasted outlines when browsing is unavailable

Live SERP analysis requires the SERP MCP. If it is unavailable, either ask the user to configure one or continue with the documented `competitor-only` branch when they provide suitable pages or outlines.

## Workflow

1. Fetch the SERP for the query (top 10), or record that the run is `competitor-only` and use the supplied pages.
2. Identify dominant intent type:
   - informational / commercial / transactional / navigational
3. Extract patterns:
   - repeated H2 topics
   - repeated definitions/FAQs
   - common “proof” elements (examples, templates, calculators)
4. Build a non-overlapping outline:
   - above-the-fold “answer fast”
   - core explanation
   - decision help (when commercial)
   - pitfalls, FAQs, examples
   Give each section one job, remove repeated topics, and note any intentional overlap (such as a short answer that expands later).
5. Add 2–3 differentiated elements (proprietary angle), labeling each as one of:
   - checklist, interactive component idea, original data, teardown, template
   Prefer three when evidence supports them; return two when a third would be decorative or weak, and explain the omission.

## Output

- “What people want” (1 paragraph)
- Non-overlapping outline (H1 → H2 → H3)
- “Differentiators to win” (2–3 bullets, each tied to a gap or evidence point)
