# GEO Audit Dashboard Template

Static-first Next.js dashboard for Bright Data GEO audits.

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

2. Copy the generated `results.json` into `public/data/<your-run>/results.json`
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

That writes a static bundle to `out/`.

## Manual recommendations

After reviewing the audit, add recommendations directly in the `manual_recommendations` array inside the audit JSON. The overview tab renders them automatically.

## Prompt tracking over time

`tracked-prompts.json` is intentionally separate from the Bright Data results file. It lets you keep a long-lived prompt history even when each audit run has its own dated `results.json`.
