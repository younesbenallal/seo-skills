# SEO Skills (Codex CLI)

Holly&Stick helps B2B SaaS teams go from SEO 0 → 1. We set the strategy and run content end-to-end so you start getting consistent traffic and leads. Learn more at https://holly-and-stick.com and follow along on [LinkedIn](https://linkedin.com/in/younès-benallal) or [Twitter](x.com/youarenes).

This repo was inspired by https://github.com/coreyhaines31/marketingskills/

## What are Skills?

Skills are modular, declarative packages that teach any coding agent how to execute repeatable SEO workflows with the right tools, prompts, and resources. Thanks to this repo, Claude, Codex, Cursor, and every other major coding agent can share the same procedural knowledge without re-inventing the wheel.

## Skills ecosystem

Skills are now a shared convention across most coding agents. The easiest way to install them is `add-skill` (https://github.com/vercel-labs/add-skill), which supports Codex, Claude Code, Cursor, OpenCode, Gemini CLI, and more.

## Install

### Option A — use `add-skill`

```bash
npx add-skill holly-and-stick/seo-skills
```

## Tooling (MCPs)

Depending on the skill you want to use, your agent will need different MCP servers. If a required MCP is missing, the skill should stop and tell you what to install.

Heavily recommended: use **agent-browser** (https://github.com/vercel-labs/agent-browser). It’s the most reliable “one tool” for reading pages, interacting with websites, and capturing screenshots across agents.

### Skills → required tools

- `seo-roast`: Browser MCP (agent-browser recommended).
- `illustration-ideas`: Browser MCP (agent-browser recommended).
- `subkeyword-injector`: Google Search Console MCP (for queries) + Browser MCP (to read the page if needed).
- `linking-opportunities`: SERP API MCP + Browser MCP.
- `search-intent-coverage`: SERP API MCP + Browser MCP.
- `programmatic-seo`: Browser MCP (recommended) + SERP API MCP (recommended) + optional Ahrefs/Semrush MCP.
- `seo-audit-report`: No MCP required (scaffold only). Data can come from a GSC MCP export or a manual CSV/JSON file.
- `geo-state-report`: Bright Data API (required) via `geo-state-report/scripts/brightdata-geo.py` (requires `BRIGHTDATA_API_KEY`).

### MCP types to install (what they’re for)

- **Browser MCP** (recommended: agent-browser): read content, navigate, copy text, capture screenshots.
- **SERP API MCP**: fetch live Google SERPs. This repo intentionally does not ship an env-var SERP fallback.
- **Google Search Console MCP**: pull query/page metrics to drive content updates.
- **Ahrefs/Semrush MCP (optional)**: keyword research + competitor data for `programmatic-seo`.

Install the agent-browser skill (optional, but recommended):

```bash
npx add-skill vercel-labs/agent-browser --skill agent-browser
```


### Option B — manual symlink

```bash
mkdir -p ~/.agents/skills
for d in linking-opportunities seo-roast subkeyword-injector seo-audit-report illustration-ideas search-intent-coverage programmatic-seo geo-state-report; do
  ln -s "$PWD/$d" "$HOME/.agents/skills/$d"
done
```

If using the repo inside another project (e.g., copied under `seo-skills/`), `cd seo-skills` before running the commands.

If using `add-skill`, skip manual syncing: it installs skills into the right place for your agent(s).

## Skills

- `linking-opportunities`: find link opportunities on a target site using SERPs.
- `seo-roast`: SEO-focused roast of a landing page/article; optionally generates a screenshot-heavy HTML report.
- `subkeyword-injector`: pull page-level queries from GSC and propose/perform content updates to capture more long-tail.
- `seo-audit-report`: scaffold a small interactive audit report web app (Vite + in-browser SQLite).
- `illustration-ideas`: generate illustration/chart ideas from a URL’s content (with placement + layout suggestions).
- `search-intent-coverage`: analyze the SERP and produce a MECE outline that matches search intent.
- `programmatic-seo`: a shorter, execution-first pSEO workflow with tooling hooks.
- `geo-state-report`: track LLM visibility (mentions/citations/fan-out) using Bright Data; outputs an HTML report with actions.

## Included helper scripts

- Roast HTML rendering (optional): `seo-roast/scripts/render-report.mjs`
- GEO collection + report: `geo-state-report/scripts/brightdata-geo.py`

## Skill creation process (reference)

1. **Understand real use cases**: list concrete examples, ask clarifying questions, and document what the skill must solve before touching files.
2. **Plan reusable resources**: decide which workflows need scripts, references, or assets, and keep the details in those files rather than bloating `SKILL.md`.
3. **Initialize with `scripts/init_skill.py`** (when available) to scaffold `SKILL.md` + sample resource folders, then delete unused samples.
4. **Implement commands, instructions, and resources** in imperative form; keep `SKILL.md` lean and reference the bundled assets only when they are necessary.
5. **Package with `scripts/package_skill.py`** once validation passes, then iterate after real usage feedback.

Use tools like `exa`/`mcp` searches when you need up-to-date scaffolding commands or boilerplate guidance.
