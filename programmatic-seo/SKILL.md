---
name: programmatic-seo
description: Design SEO-driven pages at scale using templates and data. Use when the user wants a programmatic SEO strategy, page-family specification, or implementation for directory, location, comparison, integration, or other template-driven pages.
---

# pSEO

You help the user ship pSEO that avoids thin content and actually ranks.

Produce a strategy and implementation spec by default. Edit code only when the user explicitly asks for implementation.

## Shared context first

Run the shared preflight in [`../docs/credentials-and-tooling.md`](../docs/credentials-and-tooling.md). Read `.seo-context.md` when present. Inspect the codebase for existing templates, data sources, product or ICP documentation, and prior SEO strategy before asking for pSEO-specific gaps.

## Tooling & credentials

- Auth mode: `none`
- Requires: no external credential
- Optional tools: Browser MCP or `agent-browser`, structured SERP access, Ahrefs/Semrush MCP
- Fallback: continue with repo context, manual URLs, and user-provided data if external tools are unavailable

## Core Principles

1. Unique Value Per Page: Every page must provide value specific to that page—not just swapped variables. Maximize unique content and avoid thin content penalties.

2. Proprietary Data Wins: Best pSEO uses data competitors can't easily replicate. Hierarchy: proprietary > product-derived > user-generated > licensed > public.

3. Prefer Subfolders: Default to subfolders such as `yoursite.com/templates/resume/` for a cohesive site and simpler tracking. Use a subdomain only when product architecture, ownership, or deployment constraints justify the separation.

4. Genuine Search Intent Match: Pages must actually answer what people are searching for—don't over-optimize keywords at the expense of usefulness.

## pSEO Patterns

Read [references/pattern-catalog.md](references/pattern-catalog.md) when selecting a pattern. Choose one primary scalable pattern with real demand. A secondary modifier (for example, a location or persona) is allowed only when it changes the page's search intent and data requirements; document both rather than treating the combination as two independent templates.

## Workflow

1. Pattern Selection: Choose one primary pattern from the catalog, with an optional secondary modifier only when it creates meaningful page-specific value.

2. Unique Value Rules: Define what makes each page unique—what changes per page that matters. Avoid thin content by ensuring genuine differentiation.

3. Template Design:
   - Intent-matching core content
   - Data-driven block (unique per page)
   - Comparison/alternatives (if relevant)
   - FAQ/definitions (AEO/GEO friendly)

4. URL Structure: Use subfolders, clean slugs, consistent pattern. Example: `/templates/[type]/` or `/[service]/[city]/`

5. Page Value Review: Explain how each page goes beyond variable substitution, answers its specific intent, and uses page-specific data or insight. Recommend consolidation, exclusion from indexing, or a smaller page set when the available data cannot support useful differentiation.

6. Production Plan:
   - Data generation/acquisition
   - Page rendering (template + data)
   - Internal linking (hub + spokes model)
   - Sitemap + indexation strategy

7. Measurement: Track indexing rate, impressions, CTR, position buckets by pattern

## Output

- Template spec: Sections + data fields required
- Unique value rules: Checklist for what makes each page unique
- First 10 pages: Prioritized list to build first
- Internal linking plan: Hub page + spoke pages structure
- Quality checklist: Pre-launch validation criteria
