# GEO audit dashboard template

Shared Next.js template for Bright Data and DataForSEO GEO audits. Publish it into a client's audit directory with `node ../scripts/publish-dashboard.mjs <audit-out-dir>`. That command reads every completed dated run, then updates the same `report/index.html` page and its assets.

Publication also reads `report-analysis.json` at the audit root. Update it after reviewing all runs; `through_run_at` must match the newest run and it must contain 3–6 evidenced recommendations. The page shows this single plan above the complete history. Its run selector sits with the run-specific evidence below.

## Quick start

```bash
npm install
npm run dev:test
```

That launches the app with the bundled demo files and reads them on the server:

- `public/data/demo/brightdata-results.json`
- `public/data/demo/tracked-prompts.json`

## Use real data

1. Run the collector:

```bash
python3 ../scripts/brightdata-geo.py ...
```

2. For a local preview of one run, copy `results.json` into `public/data/<your-run>/results.json`.
3. Update `.env.local`:

```bash
AUDIT_DATA_PATH=/data/<your-run>/results.json
TRACKED_PROMPTS_PATH=/data/demo/tracked-prompts.json
```

4. Restart `npm run dev`

## Static export

Because the page loads JSON during the Next build, you can export a static site directly:

```bash
npm run build
```

That writes a static bundle to `out/`. For a client audit, use the publication command instead. It sets `AUDIT_RUNS_DIR` for the build, copies only the client page and required assets, and preserves the previous published page if the build fails.

The template is configured to emit relative asset paths, so opening `out/index.html` directly from disk should still load the exported CSS and JS instead of pointing at absolute `/_next/...` URLs.

## Analysis

The required root-level `report-analysis.json` contains the cross-run overview, findings, comparison note, and current recommendations. See `../references/artifacts-dashboard.md` for its fields. Historical `manual_recommendations` inside dated results are retained as context and are not rendered as separate action plans.

## Prompt tracking over time

The dashboard reads every dated `results.json` for measured history. An optional `tracked-prompts.json` at the audit root holds notes and prompt status; it is not needed to reconstruct the runs.
