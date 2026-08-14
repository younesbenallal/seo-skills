---
name: seo-audit-report
description: Build an interactive Search Console SEO report. Use when the user wants a client-side Vite+React dashboard that imports GSC data, stores it locally, and visualizes query and page KPIs.
---

# SEO audit report (scaffold instructions)

Use this skill when the user wants an interactive, client-side report for inspecting Search Console exports or connected data repeatedly in the browser.

## Context and preflight

Run the shared preflight in [`../docs/credentials-and-tooling.md`](../docs/credentials-and-tooling.md) before discovery or implementation. Reuse `.seo-context.md` when it exists. For live GSC, resolve the project's canonical property from accessible URL-prefix and `sc-domain:` variants; use a manual export when live access is unavailable or the user prefers it. Record unresolved assumptions rather than inventing business priorities or edit permission.

## Required inputs
- Project directory name.
- Data source: live connected GSC data, an MCP export, or a manual JSON/CSV file.
- Persistence target: a serialized `sql.js` database persisted in the browser's IndexedDB.

## Tooling & credentials

- Auth mode: `mcp` or `manual-file`
- Requires: connected GSC access or a manual CSV/JSON file
- Input path: live GSC data materialized to JSON/CSV, an MCP export, or a manual file
- Fallback: use a manual file when live access is unavailable

## Workflow

1. **Scaffold the project**
   - Run `npm create vite@latest <project-name> -- --template react-ts` (or `bun create vite@latest ...` if Bun is preferred).
   - Enter the new folder and install deps (`npm install`/`bun install`).
   - Keep the generated project structure unless the requested report needs a different route or entry point.

2. **Add dependencies**
   - Install `react`, `react-dom` (if not already) along with `zod`.
   - Install runtime helpers: `sql.js` for the in-browser SQLite engine and `idb-keyval` for persisting exported database bytes.
   - Keep `typescript` + `vite` dev dependencies aligned with the template.

3. **Implement the data layer**
   - Configure `sql.js` with the `sql-wasm.wasm` bundle and isolate initialization in a reusable helper.
   - Parse CSV and JSON inputs into `{ date, query, page, clicks, impressions, ctr, position }`, coercing numeric fields and handling missing optional values consistently.
   - Store normalized rows in a `gsc_rows` table with indexes on `date`, `query`, and `page`.
   - Export the database to bytes after imports and persist those bytes with `idb-keyval`; restore them when the app loads.

4. **Implement the report views**
   - Surface total clicks, impressions, CTR, and weighted position, plus top queries, top pages, and CTR-gap opportunities.
   - Make opportunity thresholds and date/page/query filters visible and adjustable rather than hiding them in query code.
   - Include file import, optional fetch from `/gsc/latest.json`, custom filters, and reset controls.

5. **Polish and document the scaffold**
   - Style the layout with CSS variables and card/grid patterns, keeping readability front-and-center with a sticky header, callouts, and a narrow text width.
   - Add a small sample export such as `public/gsc/latest.json` when it helps demonstrate the flow.
   - Document the accepted import schema, persistence model, and CTR-opportunity heuristics in the README or nearby comments.

6. **Run and validate**
   - Start the dev server with `npm run dev` or `bun run dev` and load a representative CSV/JSON export.
   - Exercise import, reload persistence, filters, reset, and the optional `/gsc/latest.json` fetch path. Check the browser console for worker/WASM or IndexedDB errors.
   - Run the project's available typecheck, lint, and build commands. In the README, state which commands ran and any live-GSC or browser limitations.
   - Remember that `sql.js` executes SQLite in the browser; IndexedDB stores the serialized database bytes—it is not the SQLite engine.
