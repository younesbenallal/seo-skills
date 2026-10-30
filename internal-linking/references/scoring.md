# Candidate scoring and eligibility

Use this reference only when the inventory is large and complete enough for numeric prioritization. Treat scores as triage, not truth.

Score candidates from 0 to 100:

- topical and intent relevance: 0–30
- validated destination value: 0–20
- source authority proxy: 0–15
- contextual placement quality: 0–15
- target technical eligibility: 0–10
- cluster or orphan coverage gain: 0–10

Require each source to be a 200 HTML page that is indexable, crawlable, and resolved to its own canonical URL. Hard-exclude non-200, redirected, noindex, blocked, or canonicalized-away targets. Keep relationships from ineligible sources as diagnostic-only, and omit candidates with an existing sufficient contextual link.

Subtract 10 points for each verified anchor mismatch, cannibalization risk, duplicate/canonical conflict, or sitewide/template placement, then clamp to 0–100. Use these bands only for triage:

- `80–100`: review first
- `60–79`: useful queue
- `<60`: normally omit

Use numeric scores only when source content, target eligibility, and the complete-graph threshold are verified. The graph is complete only when internal outlinks were extracted for at least 80% of in-scope indexable URLs and contextual links can be distinguished from template links.
