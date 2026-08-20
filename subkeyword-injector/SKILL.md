---
name: subkeyword-injector
description: Use a page's Search Console queries to propose or apply focused long-tail content edits. Use when the user wants to refresh an existing page based on the queries it already ranks for.
---

# Subkeyword injector (GSC-driven refresh)

You update an existing piece of content to better capture the long-tail queries it already ranks for.

## Preflight

Run the shared [task preflight and tooling contract](../docs/credentials-and-tooling.md). For this skill, resolve the page URL, matching GSC property, date range, content constraints, and mutation scope before querying or editing. A local path permits inspection only; it does not grant permission to modify the file.

## Inputs to collect

- Page URL
- Editing access:
  - local file path (if the user has the content in the repo), OR
  - “no local access” (you’ll provide a patch plan)
- Constraints: “don’t change meaning”, “keep tone”, “keep sections”, etc.

## Tooling & credentials

- Auth mode: `mcp`
- Requires: Google Search Console MCP
- Fallback: none
- Optional tools: Browser MCP or `agent-browser` for reading the current page
- If missing: stop, ask the user to install or configure a GSC MCP or provide an export, and continue only after they confirm the path forward

## Page content access (for planning edits)

Use the browser fallback in [references/page-access.md](references/page-access.md) when the page is not available locally or through a connected tool. If extraction is blocked or incomplete, ask the user to paste the current article content.

Use the connected GSC path described by the shared contract. Do not substitute a manual export for the required MCP.

## Workflow

### 1) Pull queries for this page

Collect page-level queries and metrics:
- impressions, clicks, CTR, avg position
- date range: default 28 days (ask if they want 3 months / 12 months)

### 2) Select subkeywords (no fluff)

Prioritize queries that are:
- **Position 6–25** with meaningful impressions (easy uplift)
- **High impressions + low CTR** (snippet/title mismatch)
- **Query variants** (plural/singular, “best”, “examples”, “template”, “pricing”, “vs”)

Avoid:
- unrelated queries (accidental rankings)
- adding 30 synonyms (keyword stuffing)

### 3) Decide insertion strategy per query cluster

Pick one per cluster:
- Add/rename an H2/H3
- Add a short paragraph in an existing section
- Add a mini-FAQ block
- Add a comparison subsection (“X vs Y”)
- Add a concise definition that directly answers the query

Preserve the page's existing readability and tone unless the user supplies different constraints; do not invent a house style.

### 4) Produce edits

If the user explicitly authorizes editing and you have local file access:
- apply edits directly (minimal diff, no refactors)

Otherwise:
- output a “patch plan” with:
  - exact headings to add
  - copy blocks to paste
  - where to place them (anchors)

### 5) Output

- A table containing each chosen query cluster, its GSC metrics, selection rationale, insertion location, and `proposed` or `applied` status
- Updated title/H1/meta suggestions (only if CTR issue)
