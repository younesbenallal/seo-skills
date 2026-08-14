---
name: internal-linking
description: Audit and improve contextual internal linking across a website. Use when the user wants to map links, find orphan or underlinked pages, strengthen a confirmed commercial target or topical cluster, recommend source-to-target links, or apply explicitly approved edits.
---

# Internal linking

Build an evidence-backed internal linking plan from the best site data available. Recommend changes by default. Edit content or a CMS only when the user explicitly asks.

Treat graph scores as internal authority-flow proxies, not Google's PageRank. Internal links help discovery, context, navigation, and the distribution of internal signals; never promise rankings or claim that clicks directly create topical authority.

## Preflight

Run the shared [task preflight and tooling contract](../docs/credentials-and-tooling.md). For this skill, resolve the site/content scope, audit goal, confirmed money pages or conversions, and whether the user wants recommendations or explicitly approved edits. Do not infer strategic priority from page appearance.

## Tooling and access

- Auth mode: `none`
- Baseline inputs: local site content, a sitemap, a connected CMS, or public pages
- Optional: Google Search Console MCP or a local GSC CSV/JSON export
- Optional: Browser/Chrome/Playwright MCP or `agent-browser`
- Missing optional access must not block the baseline analysis

Never ask the user to paste credentials.

Only treat GSC as unavailable after inspecting callable tools and attempting to match an accessible property to the current project's canonical domain. When no live match is available, continue without it and briefly offer
[`Suganthan-Mohanadasan/Suganthans-GSC-MCP`](https://github.com/Suganthan-Mohanadasan/Suganthans-GSC-MCP)
or a manual GSC export only when performance data would materially improve the result.

## Keep the run efficient

Use the least expensive reliable discovery path:

1. local routes and content
2. an already-connected CMS or site data tool
3. sitemap plus public page inspection
4. available web search with `site:domain` queries to find missing SEO pages

Use an available web/search tool for remote discovery. If no tool can fetch public pages and the user supplied no local, CMS, sitemap, or export data, ask for a sitemap or content export. Do not imply that remote pages were inspected.

Do not require a complete crawl to deliver useful findings. State inventory limitations and confidence.

When subagents are available, delegate mechanical work for large or remote sites:

- route and URL discovery
- title, heading, topic, and existing-link extraction
- canonicalization and deduplication
- compact GSC aggregation

Use the least expensive capable model exposed by the runtime. Give each worker a bounded URL batch and a small output schema; do not pass the full site context. Keep page-role decisions, scoring, conflict resolution, and final validation with the lead agent. Never let multiple agents edit the same file.

## Workflow

### 1. Build the SEO page inventory

Collect pages intended to attract or support organic traffic, including:

- commercial and landing pages
- product, feature, use-case, industry, integration, and comparison pages
- blog posts, guides, glossaries, templates, and free tools
- category or topic hubs

For each page, capture what is reliably available:

`url`, `title`, `h1`, `headings/topics`, `page_role`, `canonical`, `indexability`,
`existing_contextual_inlinks`, `existing_contextual_outlinks`, and `source_evidence`.

Normalize URLs and resolve links against the site's canonical host. Exclude or flag non-HTML pages, redirects, non-200 pages, noindex pages, duplicates, canonical conflicts, and canonicalized-away URLs. Resolve recommended targets to the final indexable URL.

Count unique source URLs when possible. Separate contextual body links from navigation, footer, breadcrumb, and repeated template links; do not treat them as equivalent.

If only a slug list is possible, continue with that inventory and mark graph findings as low confidence.

Require verified source content before implementation. Without the source body or rendered DOM, report only a `needs passage validation` relationship. Do not invent a passage, insertion point, or anchor; do not assign it high priority or present it as ready to implement.

### 2. Classify pages and topics

Assign one primary role:

- `money`: can generate signups, leads, or revenue
- `hub`: targets a broader or more competitive topic
- `supporting`: answers a narrower or long-tail intent
- `utility`: primarily navigational, legal, account, or operational

Build a topical cluster map before generating link candidates. Group SEO pages from their title, H1/H2s, copy, URL path, search intent, and GSC queries when available. For each cluster, identify its hub or primary page, confirmed money pages, supporting articles/tools/resources, high-visibility sources, and content gaps. Record ambiguous or overlapping assignments instead of forcing a cluster.

Prefer source-target pairs within the same cluster because semantic and topical proximity strengthens contextual relevance for readers and search engines. Link supporting pages toward the relevant hub or money page, and use hub-to-supporting or sibling links when they improve discovery or complete a reader journey. Consider cross-cluster links only when the source passage establishes a real relationship. Do not claim that same-cluster links pass a fixed or mechanically greater amount of PageRank.

Do not assume every commercial page deserves more links. Validate each proposed money or hub target first:

- it targets a real and coherent search intent
- its content satisfies that intent
- it is a 200, indexable, canonical destination
- it has a meaningful conversion or strategic role
- it does not create an obvious cannibalization conflict

If a target is weak, recommend fixing or consolidating it before sending more internal authority to it.

### 3. Add optional GSC evidence

When GSC is connected or an export is supplied, use a consistent recent period, defaulting to the last 90 complete days unless the user specifies otherwise.

Aggregate page-level clicks, impressions, average position, and query themes. Use them to:

- identify established source pages with organic visibility
- validate the queries and cluster of each page
- find important pages with visibility but weak internal support
- distinguish promising targets from pages with no demonstrated demand
- find high-visibility pages in the same cluster that can naturally support a confirmed money page

Do not equate clicks with link equity. Use GSC as prioritization and relevance evidence, not as a direct PageRank input.

### 4. Model current authority flow

Estimate an internal authority proxy from the best graph evidence available:

- unique contextual inlinks
- source-page authority within the internal graph
- crawl depth and orphan status
- link prominence and surrounding relevance
- optional organic visibility as separate supporting evidence

Treat the graph as sufficiently complete only when internal outlinks were extracted for at least 80% of the in-scope, indexable URLs and contextual links can be distinguished from template links. For a complete graph:

- deduplicate each source-target pair
- weight contextual links `1.0` and repeated navigation/template links `0.2`
- initialize every node equally and iterate with damping `0.85`
- redistribute dangling-node weight across all nodes
- stop after 100 iterations or when total score change is below `0.00000001`
- percentile-normalize the result for the 0–15 source-authority component

Otherwise use transparent capped or percentile-normalized unique contextual inlinks and crawl depth, and do not produce a numeric 0–100 opportunity score. Label every proxy as directional and expose the evidence behind it.

Look for:

- valuable targets with few relevant contextual inlinks
- strong sources that link mostly to low-priority pages
- orphan or deep pages
- cluster hubs without spoke support
- spokes that do not link back to the hub
- relevant sibling pages that remain disconnected

### 5. Generate candidates

Recommend a source-to-target link only when the source contains a real passage where the target helps the reader.

Prioritize:

- relevant supporting or long-tail pages linking to broader, more competitive hubs
- useful cluster hub-to-spoke and spoke-to-hub links
- relevant sibling links that complete a reader journey
- established, topically relevant pages linking to confirmed money pages in the same cluster
- links that repair an orphan or excessive crawl depth

Prefer a few strong contextual links over arbitrary quotas. Avoid forced links, unrelated targets, duplicate links with no added value, circular linking for its own sake, and template-wide placement disguised as contextual work.

For each confirmed money page, measure relevant cluster coverage across articles, tools, hubs, and other supporting pages. Aim for broad support from the cluster, especially from sources with strong internal-graph authority or established organic visibility, but recommend a link only when the source contains a natural passage and the destination advances the reader journey. Treat clicks as visibility evidence, not as link equity or PageRank.

Exclude `utility` pages as sources and targets unless the user explicitly includes them in scope.

Write anchors that are descriptive, truthful, and natural in the sentence. Include the target's topic or a close semantic variant when useful, but vary phrasing and avoid exact-match stuffing.

### 6. Score and review candidates

When the inventory supports quantitative prioritization, use the scoring and eligibility rules in [references/scoring.md](references/scoring.md). Otherwise use qualitative priority and include `needs passage validation` or `needs technical validation`. Keep source evidence and a plausible insertion point for every high-priority recommendation, and lower confidence when page content, graph completeness, or technical state is unverified.

### 7. Deliver the plan

Lead with the highest-leverage findings:

1. inventory coverage and data limitations
2. validated money pages and weak/unsafe targets
3. cluster and authority-flow diagnosis
4. prioritized link opportunities
5. new content or hub gaps that internal linking alone cannot solve

Return opportunities in a copy/paste-friendly table:

| priority | source | target | cluster | why it fits | suggested anchor | insertion context | evidence | confidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

Include component scores when the inventory is large enough for scoring to improve decisions. Clearly separate observed facts from inferred classifications.

## Apply approved edits

Only apply links when explicitly requested.

When the user explicitly requests application, follow [references/apply-edits.md](references/apply-edits.md). Otherwise stop after delivering the recommendation plan.
