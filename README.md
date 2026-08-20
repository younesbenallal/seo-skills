# SEO skills for AI coding agents

Reusable SEO skills for Claude Code, Codex, Cursor, and other AI coding agents. The workflows cover content research, technical audits, SERP analysis, Google Search Console, internal linking, competitor research, and GEO reporting.

Holly&Stick builds these skills for practical SEO work on B2B SaaS websites. Learn more at [holly-and-stick.com](https://holly-and-stick.com), or follow [Younes Benallal on LinkedIn](https://linkedin.com/in/younès-benallal) and [X](https://x.com/youarenes).

## Install

Install the whole collection with the open Agent Skills CLI:

```bash
npx skills add younesbenallal/seo-skills
```

Install one skill when you only need a specific workflow:

```bash
npx skills add younesbenallal/seo-skills --skill seo-context
```

The same skills can be used by Claude Code, Codex, Cursor, and other supported agents.

## Setup

Start with [docs/credentials-and-tooling.md](docs/credentials-and-tooling.md). It explains how the skills discover project context, connected properties, credentials, and fallbacks.

Google Search Console MCP is the required shared integration. Connect it in your agent before using the collection so skills can resolve the right property and use query and page performance data. Individual workflows may also need browser access, structured SERP data, email access, or provider credentials.

### Browser access

Use any available Browser, Chrome, Playwright, or computer-use tool to read pages, navigate sites, and capture screenshots. If no browser connector is available, `agent-browser` can be used as a CLI fallback when it is already installed.

### SERP data

When a workflow needs live SERPs, use structured SERP data when possible. This can come from a provider API or an MCP integration. Examples include [DataForSEO](https://dataforseo.com/), [Serper.dev](https://serper.dev/), [SerpApi](https://serpapi.com/), and [Bright Data](https://brightdata.com/). There are many valid providers, so the skills do not require one specific product or call both an API and an MCP.

If structured SERP access is unavailable, use a browser to inspect the results directly when the workflow allows it. Record the source and market, and do not describe browser observations as an API dataset.

### Other access

- Guest-post outreach may need an email connector or an interactive browser tool for approved submissions.
- Ahrefs, Semrush, DataForSEO, or another SEO data provider can add keyword, traffic, authority, or backlink data where a workflow supports it.
- GEO audits need either a Bright Data API key or DataForSEO credentials.

## Skills

- `seo-context`: create reusable project context so SEO workflows stop asking for the same site, market, competitor, and tooling basics.
- `article-writing`: research and write articles using the site's content, search results, and confirmed editorial preferences.
- `internal-linking`: map internal authority flow, strengthen priority pages, and reinforce topical clusters.
- `linking-opportunities`: find contextual backlink opportunities on a target site using SERP and page evidence.
- `backlink-outreach`: find and qualify guest-post, niche-edit, or link-exchange opportunities, match them to existing content, draft tailored outreach, maintain a flexible Markdown campaign log, and submit approved requests.
- `seo-roast`: review a landing page or article for technical SEO, on-page quality, and search intent.
- `subkeyword-injector`: use Search Console queries to propose or apply content updates for long-tail coverage.
- `seo-audit-report`: build a small interactive audit report from Search Console data.
- `illustration-ideas`: generate illustration and chart ideas from a page's content, with placement and layout suggestions.
- `search-intent-coverage`: analyze search results and produce a non-overlapping content outline.
- `programmatic-seo`: run a focused workflow for SEO pages at scale.
- `competitor-intelligence`: discover SEO competitors, map sitemap and content patterns, and identify gaps.
- `geo-audit-report`: measure LLM visibility, mentions, citations, and search fan-out with a dashboard-ready report.
- `posthog-seo-geo-tracking`: implement first-touch SEO and LLM-referral tracking through signup, subscription, and revenue.

## Suggested workflow

1. Install the collection with `npx skills add`.
2. Connect Google Search Console MCP and read the shared tooling contract.
3. Run `seo-context` once to save the site's goals, market, competitors, money pages, and available tools.
4. Use the task-specific skill for the work at hand.

For a common content workflow, start with `competitor-intelligence`, use `search-intent-coverage` for the brief, draft with `article-writing`, then use `subkeyword-injector` and `internal-linking` for refreshes and distribution.

## Claude Code plugin

This repository also includes Claude Code plugin metadata. Add the marketplace with:

```text
/plugin marketplace add younesbenallal/seo-skills
```

Then install the plugin from the `seo-skills` marketplace:

```text
/plugin install seo-skills@seo-skills
```
