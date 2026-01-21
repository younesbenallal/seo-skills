---
name: illustration-ideas
description: Generate high-quality illustration/chart ideas for a URL, including placement + layout suggestions (HTML-like or Mermaid).
---

# Illustration ideas (from a URL)

You browse a page, understand the content, then propose illustration ideas that improve comprehension and retention.

## Inputs to collect

- URL
- Audience level (beginner / intermediate / expert)

## Tools

Preferred: URL → Markdown tool.
Fallback: ask the user to paste the content or main outline.

## Output requirements

Return a list of suggestions. For each suggestion include:
- **Placement**: exact section heading / before-after which paragraph
- **What it shows**: concept, comparison, flow, data
- **Format**: diagram / chart / table / UI mock / timeline
- **Design notes**: labels, axes, callouts, do/don’t
- A **code block** containing either:
  - an ASCII representation of the illustration
  - Mermaid (flowchart/sequence) when relevant

Keep suggestions grounded in the page’s content (no “generic illustrations”).

