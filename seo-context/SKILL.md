---
name: seo-context
description: Create or update reusable SEO context for a site, product, or content program. Use when the user wants to preserve shared SEO facts across tasks, or when another SEO skill needs site, market, priority-page, competitor, or tooling context that has not been recorded yet.
---

# SEO context

Create and maintain `.seo-context.md` in the project root so SEO skills can reuse durable project facts instead of repeating discovery.

Article-specific writing preferences belong in `.agents/article-writing-context.md`, which is created and maintained by the `article-writing` skill. Do not force voice, image, source, or publishing preferences into this SEO context unless they are also durable business or content constraints.

Other SEO skills should read this file first and ask only for missing task-specific details.

## Preflight

Read and follow the shared project, connected-tool, property-resolution, missing-input, and secret-handling rules in [`../docs/credentials-and-tooling.md`](../docs/credentials-and-tooling.md).

For this skill, confirm high-impact business facts rather than silently inferring them. If money-page status, conversions, target markets, or strategic priorities remain unknown, record them as unknown or as candidates awaiting confirmation.

Use `.seo-context.md` as the reusable record for project tooling. On the first run, inspect callable tools and connectors, save the relevant inventory with its check date and status source, and ask the user whether other tools are available but not visible to the agent. On later runs, reuse that inventory instead of repeating broad discovery. Re-check a specific tool when the task needs live access, the inventory is missing or unknown, the user reports a setup change, or the check is more than 30 days old.

## Tooling & credentials

- Auth mode: `none`
- Requires: no external credential
- Fallback: none

## Workflow

### 1) Check for existing context first

Look for:
- `.seo-context.md`
- older or alternative project docs that already contain the same information:
  - `README.md`
  - `docs/`
  - strategy notes in the repo
  - product or marketing docs
- page templates or content directories
- existing SEO notes or exported audits
- connected Search Console data or existing GSC exports, when available

Read the tooling inventory in `.seo-context.md` before broad tool discovery. If it is absent or stale, follow the reusable tooling inventory rules in [`../docs/credentials-and-tooling.md`](../docs/credentials-and-tooling.md).

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
- a money-page keyword map with one row per confirmed page. Use the page slug, URL, or title as the page identifier and record its target keyword or keywords
- the topic cluster each money page belongs to and the supporting articles, tools, or resources that should reinforce it
- priority content themes
- important queries or topic clusters if already known

For the money-page keyword map:
- use a two-column Markdown table: `Page slug or title` and `Target keyword(s)`
- default to one primary target keyword per page
- put multiple keywords in one row only when one page intentionally serves closely related queries
- do not assign the same primary keyword to multiple pages unless the different intents are clear and documented
- use the map to inform internal-link targets, descriptive anchor ideas, content briefs, and page targeting. Validate each suggestion against the page content and search intent

Build a compact topical cluster map rather than storing a flat page list. For each cluster, capture:
- the core topic, search intent, or job-to-be-done
- the hub or primary page
- confirmed money pages from the money-page keyword map
- supporting articles, tools, templates, and other resources
- high-click pages and query themes from GSC when available
- important gaps, overlaps, or uncertain page assignments

Do not infer that a page is a money page from its format alone. Use conversion, analytics, CRM, or user evidence when available. If the project materials do not identify the pages responsible for most business results, ask the user which pages generate the majority of qualified leads or revenue. Offer likely commercial and bottom-of-funnel candidates for confirmation when useful, such as product, service, comparison, alternative, and "best X" pages.

Before asking the user to identify important organic pages, query connected Search Console data or inspect a supplied export when either is available. Record page-level clicks and impressions by relevant cluster, together with the property and date range. Treat clicks as organic-visibility evidence, not proof of conversions, business value, or PageRank.

5. Competitive context
- direct/business competitors: companies with a substantially similar offer and buyer
- SEO competitors: websites that repeatedly appear in the top 10 organic results for the project's relevant keywords. They do not need to sell the same kind of product
- comparison targets
- substitute workflows or alternatives

When SEO competitors are unknown, discover them from a small seed set of 2 to 5 relevant keywords. Prefer keywords from the money-page table and important query themes. Use the same Google country, language, device, and date for every query, then:

1. Pull the top 10 organic results for each keyword.
2. Normalize result URLs to their root domains and exclude the project's own domain.
3. Count how often each domain appears across the full query set. Record the queries, appearances, locale, source, and date.
4. Review the domains that recur most often. Check the site's offer or audience only when that context helps interpret the result. Business similarity is secondary to repeated SERP visibility.

If the context does not contain enough relevant seed keywords, ask the user to choose a couple before running this discovery. Treat the resulting domains as SEO competitors even when they are publishers, directories, marketplaces, tools, or other businesses. Keep direct/business classification separate.

6. Tooling and data access
- reusable tool and connector inventory, including the check date and whether each status was agent-observed or user-reported
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

### 3) Create or update the context file

Use the template in `references/context-template.md`.

Keep the document practical:
- concise
- easy for another SEO skill to scan quickly
- focused on facts that affect execution

### 4) Hand off the context

Tell downstream SEO skills to:
- read `.seo-context.md` first
- skip repeated discovery questions when the answers are already there
- ask only for missing task-specific inputs
- use its topical cluster map and money-page keyword map as evidence, not as permission to force a recommendation

## Output requirements

After creating or updating the file:
- summarize what was added or changed
- say whether the tooling inventory was created or refreshed, and separate agent-observed tools from user-reported tools
- call out the most important missing fields, if any
- tell the user that other SEO skills can now reuse this context automatically

## References

- Use `references/context-template.md` for the exact structure
