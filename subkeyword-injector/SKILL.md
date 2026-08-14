---
name: subkeyword-injector
description: For a given URL, pull Search Console queries it already ranks for and propose (or apply) content edits to capture more long-tail traffic.
---

# Subkeyword injector (GSC-driven refresh)

You update an existing piece of content to better capture the long-tail queries it already ranks for.

## Shared context first

Before asking repeated discovery questions, check whether `.seo-context.md` exists.

If it does:
- read it first
- reuse the saved site, audience, market, and tooling context
- ask only for page-specific constraints that are still missing

## Mandatory preflight

Before substantive work, inspect `.seo-context.md`, relevant project evidence, and the tools or MCPs actually callable in the runtime. Do not infer that Search Console is unavailable because no local export or config file exists. When GSC is callable, list accessible properties, resolve the current project's canonical domain, normalize URL-prefix and `sc-domain:` variants, and use the unique match. Ask the user only when several plausible properties remain.

If high-impact inputs remain unknown, ask one compact checkpoint before continuing. Explain that the user may skip it; if they decline and the task remains safe, proceed with explicit assumptions, limitations, and lower confidence. Never silently invent business priorities, target markets, conversion value, or permission to edit.

## Inputs to collect

- Page URL
- Editing access:
  - local file path (if the user has the content in the repo), OR
  - “no local access” (you’ll provide a patch plan)
- Constraints: “don’t change meaning”, “keep tone”, “keep sections”, etc.

## Tooling & credentials

- Auth mode: `mcp`
- Requires: Google Search Console MCP
- Fallback: manual CSV export from Search Console, if the user does not have MCP access
- Optional tools: Browser MCP or `agent-browser` for reading the current page
- If missing: stop, ask the user to install or configure a GSC MCP or provide an export, and continue only after they confirm the path forward

Read and follow the shared preflight, setup, and missing-access rules in `docs/credentials-and-tooling.md`.

## Page content access (for planning edits)

Use a Browser MCP if available. If not, use the `agent-browser` CLI (install if needed).

Agent-browser commands to capture current headings/sections:
```bash
agent-browser open <url>
agent-browser snapshot --json > /tmp/page.json
jq -r '.. | objects | select(.role=="heading") | (.name // "")' /tmp/page.json
```

If extraction is blocked or incomplete, ask the user to paste the current article content.

## Required tool

This skill requires **Google Search Console data**.

Prefer a connected **GSC MCP** so you can query by page/URL and date range. List accessible properties and select the one matching the current project's canonical domain before asking for an export.

If no GSC MCP is available:
- stop and ask the user to install one, OR
- ask them for a manual export (CSV) and proceed with the export.

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
- Add a definition snippet (AEO/GEO friendly)

Use the readability rules from `obsidian/Article writing playbook.md`.

### 4) Produce edits

If you have local file access:
- apply edits directly (minimal diff, no refactors)

If you do NOT have access:
- output a “patch plan” with:
  - exact headings to add
  - copy blocks to paste
  - where to place them (anchors)

### 5) Output

- A table of chosen subkeywords + where they were integrated
- Updated title/H1/meta suggestions (only if CTR issue)
