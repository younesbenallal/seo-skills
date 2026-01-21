---
name: illustration-ideas
description: Generate high-quality illustration/chart ideas for a URL, including placement + layout suggestions (HTML-like or Mermaid).
---

# Illustration ideas (from a URL)

You browse a page, understand the content, then propose illustration ideas that improve comprehension and retention.

## Inputs to collect

- URL
- Audience level (beginner / intermediate / expert) [optional]

## Tools

Mandatory: URL → Markdown tool. It can be Jina MCP, or any browser MCP.

## Output requirements

Carefully review the full content of the article/page. Then, for each strong illustration opportunity found, output a suggestion with the following details:

- **Placement**: Indicate the most helpful location for the illustration (exact section or after/before a particular paragraph).
- **Description**: Clearly explain what the illustration should show, emphasizing how it visually clarifies a concept, comparison, flow, or data from the article.
- **Format**: Specify the ideal form (e.g., diagram, chart, table, timeline, UI mockup).
- **Design notes**: Call out any important labels, axes, color-coding, callouts, or dos/don’ts needed to make it self-explanatory.
- **Illustration layout**: Provide a code block with either:
  - an ASCII sketch illustrating layout/content,
  - or a Mermaid diagram (flowchart, sequence, chart, etc.) when suitable.
  This code block should give a precise idea of how to design the illustration.

Ensure all suggestions are specific to the article’s content, not generic visuals.

Example structure of an illustration suggestion:

```markdown
- **Placement:** After the "How X Works" section
- **Description:** Flowchart showing how data moves through system A to system B, clarifying the process described.
- **Format:** Mermaid flowchart
- **Design notes:** Use arrows to indicate flow direction, highlight bottlenecks in red.
- **Illustration layout:**
  ```mermaid
  flowchart LR
    A[User Input] --> B[Process Step 1]
    B --> C[Process Step 2]
    C --> D[Output]
    B -.-> E[Error]
  ```
```

