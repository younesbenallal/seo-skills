# SEO Skills (Codex CLI)

A collection of **Codex CLI skills** for day-to-day SEO work (audits, SERP research, internal linking, content ops, programmatic SEO, and GEO/LLM visibility).

## Install

Codex looks for skills in `~/.agents/skills/` (global), or in a project’s `.agents/skills/` (repo-local).

### Option A — install globally (recommended)

```bash
git clone https://github.com/<you>/<this-repo>.git
cd <this-repo>

mkdir -p ~/.agents/skills
for d in linking-opportunities seo-roast subkeyword-injector seo-audit-report illustration-ideas search-intent-coverage programmatic-seo geo-state-report; do
  ln -s "$PWD/$d" "$HOME/.agents/skills/$d"
done
```

### Option B — install into a specific project

```bash
mkdir -p .agents/skills
for d in linking-opportunities seo-roast subkeyword-injector seo-audit-report illustration-ideas search-intent-coverage programmatic-seo geo-state-report; do
  ln -s "$PWD/$d" ".agents/skills/$d"
done
```

If you vendored this repo into another repo (e.g. as `seo-skills/`), run `cd seo-skills` first.

## Tooling model (MCPs, scripts, fallbacks)

These skills try to be **tool-adaptive**. Each skill starts by checking which tools are available, then chooses the best route:

- **Page → Markdown**: prefer a URL-to-markdown MCP (ex: Jina). Fallback: browser automation + copy extraction.
- **Screenshots**: prefer a browser MCP / `agent-browser` / Playwright. If unavailable, skip screenshots and roast based on DOM/text only.
- **SERP**:
  - Best: a SERP MCP you already have installed.
  - Fallback: `serper.dev` via `SERPER_API_KEY` using `scripts/serper-dev.mjs`.
- **Google Search Console (GSC)**:
  - Best: a GSC MCP you already have installed.
  - If a skill says GSC is required and you don’t have a GSC MCP, it should **stop** and tell you how to install one or use a manual export.
- **Bright Data (mandatory for GEO state)**:
  - Requires `BRIGHTDATA_API_KEY` and dataset IDs.

To see what MCP servers you have:

```bash
codex mcp list
```

## API keys / env vars

- `SERPER_API_KEY`: for `serper.dev` SERP fallback (`scripts/serper-dev.mjs`).
- `BRIGHTDATA_API_KEY`: for GEO state report collection (`geo-state-report/scripts/brightdata-geo.py`).

You can export them in your shell:

```bash
export SERPER_API_KEY="..."
export BRIGHTDATA_API_KEY="..."
```

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

- SERP (Serper.dev): `scripts/serper-dev.mjs`
- Link opp mining (Serper.dev): `linking-opportunities/scripts/link-opps.mjs`
- Roast HTML rendering (optional): `seo-roast/scripts/render-report.mjs`
- GEO collection + report: `geo-state-report/scripts/brightdata-geo.py`

## Skill creation process (reference)

1. **Understand real use cases**: list concrete examples, ask clarifying questions, and document what the skill must solve before touching files.
2. **Plan reusable resources**: decide which workflows need scripts, references, or assets, and keep the details in those files rather than bloating `SKILL.md`.
3. **Initialize with `scripts/init_skill.py`** (when available) to scaffold `SKILL.md` + sample resource folders, then delete unused samples.
4. **Implement commands, instructions, and resources** in imperative form; keep `SKILL.md` lean and reference the bundled assets only when they are necessary.
5. **Package with `scripts/package_skill.py`** once validation passes, then iterate after real usage feedback.

Use tools like `exa`/`mcp` searches when you need up-to-date scaffolding commands or boilerplate guidance.
