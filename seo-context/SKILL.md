---
name: seo-context
description: Create or update a reusable SEO context file for a site, product, or content program. Use when the user wants to avoid repeating SEO fundamentals across tasks, or when they mention SEO context, site context, content context, target market, money pages, priority pages, competitors, or tooling setup. Other SEO skills should read this context first before asking for basics again.
---

# SEO context

You help the user create and maintain a reusable SEO context document for a project.

The document lives at `.seo-context.md` in the project root.

Article-specific writing preferences belong in `.agents/article-writing-context.md`, which is created and maintained by the `article-writing` skill. Do not force voice, image, source, or publishing preferences into this SEO context unless they are also durable business or content constraints.

Other SEO skills should read this file first, then ask only for task-specific details that are still missing.

## Mandatory preflight

Before substantive work, inspect relevant project evidence and the tools or MCPs actually callable in the runtime. Do not infer that Search Console or another connected service is unavailable because no local export or config file exists. When GSC is callable, list accessible properties, resolve the current project's canonical domain, normalize URL-prefix and `sc-domain:` variants, and use the unique match. Ask the user only when several plausible properties remain.

If high-impact business or SEO inputs remain unknown, ask one compact checkpoint before creating or updating the context. Explain that the user may skip it; if they decline, record explicit unknowns and inferred candidates rather than inventing facts. Never silently assign money-page status, conversions, target markets, or strategic priorities.

## When to use this

Use this skill when:
- the user is starting SEO work on a new project
- the user is tired of repeating the same SEO basics across tasks
- multiple SEO tasks will be run against the same site
- the user wants a reusable brief for markets, competitors, priorities, and tooling

## Tooling & credentials

- Auth mode: `none`
- Requires: no external credential
- Fallback: none

Read and follow the shared preflight, setup, and missing-access rules in `docs/credentials-and-tooling.md` when recording downstream tool availability in the context file.

## Workflow

### 1) Check for existing context first

Look for:
- `.seo-context.md`
- older or alternative project docs that already contain the same information:
  - `README.md`
  - `docs/`
  - strategy notes in the repo
  - product or marketing docs

If `.seo-context.md` already exists:
- read it
- summarize what is already captured
- update only the stale or missing sections

If it does not exist:
- gather what you can from the repo first
- only then ask the user for missing information

### 2) Gather the minimum useful shared context

Capture the information that many SEO tasks reuse:

1. Site and business basics
- brand or project name
- primary domain
- site type: SaaS, marketplace, media site, ecommerce, agency, local business, docs site
- short description of what the company offers

2. SEO goals
- main business goal from SEO
- primary conversions to drive
- top KPIs if known

3. Audience and market
- target audience or ICP
- country / language targets
- important regions or localization constraints

4. Priority surfaces and topical clusters
- top pages, templates, or sections that matter most
- confirmed money pages: commercial or bottom-of-funnel pages that generate a disproportionate share of qualified leads, revenue, or other primary conversions
- the topic cluster each money page belongs to and the supporting articles, tools, or resources that should reinforce it
- priority content themes
- important queries or topic clusters if already known

Build a compact topical cluster map rather than storing a flat page list. For each cluster, capture:
- the core topic, search intent, or job-to-be-done
- the hub or primary page
- confirmed money pages
- supporting articles, tools, templates, and other resources
- high-click pages and query themes from GSC when available
- important gaps, overlaps, or uncertain page assignments

Use the cluster map as the default framework for internal linking. Prefer links between semantically and topically close pages because the surrounding context makes the relationship clearer to readers and search engines. Within a cluster, connect supporting pages to the relevant hub or money page and add hub-to-supporting or sibling links when they improve discovery and the reader journey. Use cross-cluster links only when the relationship is genuinely useful. Do not claim that topical proximity creates a fixed or measurable multiplier of link equity.

Do not infer that a page is a money page from its format alone. Use conversion, analytics, CRM, or user evidence when available. If the project materials do not identify the pages responsible for most business results, ask the user which pages generate the majority of qualified leads or revenue. Offer likely commercial and bottom-of-funnel candidates for confirmation when useful, such as product, service, comparison, alternative, and "best X" pages.

When a Google Search Console connection or export is available, retrieve page-level clicks and impressions before asking the user to identify important organic pages. Record a concise list of high-click pages by relevant cluster, together with the Search Console property and date range. Use these pages as candidates for strong internal-link sources and as evidence of organic visibility. Do not treat clicks as proof that a page generates leads, revenue, or PageRank; confirm money-page status from conversion evidence or the user.

5. Competitive context
- direct competitors
- comparison targets
- substitute workflows or alternatives

6. Tooling and data access
- browser tooling available
- SERP data source
- Search Console availability
- analytics / keyword tools available
- any hard constraints around access

7. Content and technical constraints
- CMS or framework if known
- tone or brand constraints
- approval constraints
- markets or compliance concerns that affect content

### 3) Reuse repo context before asking the user

Before asking questions, inspect:
- `README.md`
- `docs/`
- page templates or content directories
- existing SEO notes or exported audits
- any obvious product, ICP, or competitor references
- connected Search Console data or existing GSC exports, when available

Do not ask the user for information that is already easy to infer from the project.

### 4) Create or update the context file

Use the template in `references/context-template.md`.

Keep the document practical:
- concise
- easy for another SEO skill to scan quickly
- focused on facts that affect execution

### 5) Tell downstream skills how to use it

When this context file exists, other SEO skills should:
- read `.seo-context.md` first
- skip repeated discovery questions when the answers are already there
- ask only for missing task-specific inputs
- use its topical cluster map before selecting internal-link sources and targets
- use confirmed money pages as priority destinations when a relevant, useful internal link supports the reader journey; never force unrelated or sitewide links

## Output requirements

After creating or updating the file:
- summarize what was added or changed
- call out the most important missing fields, if any
- tell the user that other SEO skills can now reuse this context automatically

## References

- Use `references/context-template.md` for the exact structure
