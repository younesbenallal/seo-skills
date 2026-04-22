---
name: search-intent-coverage
description: Determine what to cover to satisfy search intent by analyzing SERPs (preferred) or extracting competitor pages to Markdown.
---

# Search intent coverage (SERP → outline)

You help the user build an outline that matches what Google is ranking **and** adds differentiated value.

## Shared context first

Before asking repeated discovery questions, check whether `.agents/seo-context.md` exists.

If it does:
- read it first
- reuse the saved market, audience, topic, and competitor context
- ask only for the query or draft-specific details that are still missing

## Inputs to collect

- Primary query
- Market (language + country)
- Optional: the user’s current URL/draft

## Tooling & credentials

- Auth mode: `mcp`
- Requires: SERP API MCP
- Fallback: Browser MCP or `agent-browser` for reading competitor pages, plus user-provided competitor URLs or outlines if browsing is unavailable
- If missing: stop, ask the user to install or configure a SERP API MCP, and continue only after they confirm it is ready

Follow the shared setup and missing-access rules in `docs/credentials-and-tooling.md`.

## Tools (adaptive)

Required: SERP API MCP. If it’s missing, stop and ask the user to install one.

For reading competitor URLs:
- Use a Browser MCP if available.
- Else use `agent-browser` CLI (install if needed).

Agent-browser install (if missing):
```bash
npm i -g agent-browser
```

Exact agent-browser commands to open a competitor page and extract common sections/headings fast:
```bash
agent-browser open "<url>"
agent-browser wait --load networkidle
agent-browser get title
agent-browser snapshot -c --json
# In the JSON, find the node with role="main" to get its @ref, then:
agent-browser get text @eMAIN
agent-browser snapshot -c -d 3 --json
# Scan the compact tree for role="heading" nodes to capture the H2/H3 pattern.
```

Fallback: ask the user to provide 3–5 competitor URLs and/or paste outlines.

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
