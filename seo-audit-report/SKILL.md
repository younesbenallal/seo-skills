---
name: seo-audit-report
description: Document how to scaffold a Vite+React SEO audit report that ingest Search Console data, stores it in sql.js, and visualizes query/page KPIs.
---

# SEO audit report (scaffold instructions)

Use this skill when the user wants an interactive, client-side report that imports Search Console exports and keeps them in a lightweight SQLite database for repeated inspection.

## Shared context first

Before asking repeated discovery questions, check whether `.seo-context.md` exists.

If it does:
- read it first
- reuse the saved site, KPI, and tooling context
- ask only for project-specific scaffold details that are still missing

## Mandatory preflight

Before substantive work, inspect `.seo-context.md`, relevant project evidence, and the tools or MCPs actually callable in the runtime. Do not infer that Search Console or another connected service is unavailable because no local export or config file exists. When GSC is callable, list accessible properties, resolve the current project's canonical domain, normalize URL-prefix and `sc-domain:` variants, and use the unique match. Ask the user only when several plausible properties remain.

If high-impact inputs remain unknown, ask one compact checkpoint before continuing. Explain that the user may skip it; if they decline and the task remains safe, proceed with explicit assumptions, limitations, and lower confidence. Never silently invent business priorities, target markets, conversion value, or permission to edit.

## Required inputs
- Project directory name.
- Data source: live connected GSC data, an MCP export, or a manual JSON/CSV file.
- Persistence target: in-browser IndexedDB via `sql.js`.

## Tooling & credentials

- Auth mode: `mcp` or `manual-file`
- Requires: connected GSC access or a manual CSV/JSON file
- Input path: live GSC data materialized to JSON/CSV, an MCP export, or a manual file
- Fallback: manual file remains the default fallback when live MCP access is unavailable

Read and follow the shared preflight, setup, and missing-access rules in `docs/credentials-and-tooling.md`.

## Workflow

1. **Scaffold the project**
   - Run `npm create vite@latest <project-name> -- --template react-ts` (or `bun create vite@latest ...` if Bun is preferred).
   - Enter the new folder and install deps (`npm install`/`bun install`).
   - Use `exa` (or web search) to confirm the latest Vite React template command if the tooling switches.

2. **Add dependencies**
   - Install `react`, `react-dom` (if not already) along with `zod`.
   - Install runtime helpers: `sql.js` for the SQLite engine and `idb-keyval` for Persisting exported bytes.
   - Keep `typescript` + `vite` dev dependencies aligned with the template.

3. **Implement the app**
   - Configure `sql.js` using the `sql-wasm.wasm` bundle; wrap initialization in a helper to reuse across hooks.
   - Build an import flow that accepts CSV/JSON and normalizes rows into `{ date, query, page, clicks, impressions, ctr, position }`.
   - Store normalized rows into a `gsc_rows` table with indexes on `date`, `query`, and `page`, then export the database and persist via `idb-keyval`.
   - Surface KPIs: total clicks/impressions/CTR/weighted position, top queries, top pages, and CTR gap opportunities filtered by impressions/position buckets.
   - Include file + fetch controls (`<input type="file">`, fetch from `/gsc/latest.json`), custom filters, and a reset button.
   - Style the layout with CSS variables and card/grid patterns, keeping readability front-and-center (sticky header, callouts, narrow text width).

4. **Run & iterate**
   - Start the dev server with `npm run dev` or `bun run dev`.
   - Load sample exports (provide a `public/gsc/latest.json` for convenience) and verify persistence across reloads.
   - Document expected import schema and heuristics for CTR opportunities in README or inline comments.

## Tool checks
- When unsure which packages to add or how to initialize `sql.js`, run an `exa` search such as `exa "vite react sql.js setup"` to gather up-to-date commands.
- Refer to the `Skill creation process` section of `seo-skills/README.md` when expanding the skill further.
