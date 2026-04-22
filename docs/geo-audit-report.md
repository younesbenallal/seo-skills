# GEO Audit Report

## What changed

The old `geo-state-report` skill has been renamed to `geo-audit-report` and now ships with a reusable React dashboard template under `geo-audit-report/template`.

## Main files

| File | Responsibility |
| --- | --- |
| `geo-audit-report/scripts/brightdata-geo.py` | Collects Bright Data snapshots and writes a richer `results.json` with response-level data the dashboard can render directly. |
| `geo-audit-report/SKILL.md` | Documents the audit workflow around Bright Data collection plus the dashboard template. |
| `geo-audit-report/template/src/App.tsx` | Main three-tab dashboard UI: overview, prompts, and sources. |
| `geo-audit-report/template/src/lib/audit-data.ts` | Normalizes audit JSON, loads configured files, and builds all UI aggregates. |
| `geo-audit-report/template/public/data/demo/brightdata-results.json` | Demo audit file used by `npm run dev:test`. |
| `geo-audit-report/template/public/data/demo/tracked-prompts.json` | Long-lived prompt tracking file for the visibility-over-time tab. |

## Main flows

1. Run `brightdata-geo.py` to produce a dated `results.json`.
2. Point the template app at that JSON with `VITE_AUDIT_DATA_PATH`.
3. Keep `tracked-prompts.json` as a separate timeline file across audit runs.
4. Add manual recommendations directly in the audit JSON so the overview tab can render AI-curated next steps without code changes.

## Data shape notes

- `results.json` now includes `schema_version`, `manual_recommendations`, and `responses`.
- `responses` mirrors the summary rows but keeps the fields the UI needs for drilldowns: answer text, citations count, fan-out queries, brands mentioned, and normalized sources.
- The dashboard still falls back to `results` if `responses` is absent, but full prompt/source drilldowns work best with the richer schema.
