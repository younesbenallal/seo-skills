---
name: illustration-ideas
description: Propose specific illustrations that improve comprehension of a web page. Use when the user provides a URL or article and wants visual concepts with placement and layout guidance.
---

# Illustration ideas (from a URL)

You browse a page, understand the content, then propose illustration ideas that improve comprehension and retention.

## Preflight

Run the shared [task preflight and tooling contract](../docs/credentials-and-tooling.md). For this skill, resolve the URL or supplied article content and the intended audience when it materially changes the visual recommendation. Do not imply that a page was reviewed when access failed.

## Inputs to collect

- URL
- Audience level (beginner / intermediate / expert) [optional]

## Tooling & credentials

- Auth mode: `none`
- Requires: no external credential
- Optional tools: Browser MCP or `agent-browser`
- Fallback: user-provided content or a detailed outline, following the shared browser-selection rules

Follow the shared browser-selection and extraction rules.

## Workflow

1. Review all accessible page or article content, not only the opening section or headings. Inspect its structure, claims, comparisons, processes, and data.
2. Identify places where a visual would reduce explanation cost or make a relationship easier to understand.
3. Reject decorative ideas that do not clarify a specific passage.
4. Present the strongest content-grounded visual concepts using the format below.

## Output requirements

For each strong illustration opportunity, output a suggestion with the following details:

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
