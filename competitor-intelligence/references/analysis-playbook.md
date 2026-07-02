# Competitor analysis playbook

Use the relevant section for the current task. Keep raw datasets outside the context window and inspect aggregates or targeted slices.

## Contents

- Competitor discovery
- Sitemap analysis
- Provider data
- Gap prioritization
- Monitoring
- Report quality checks

## Competitor discovery

Build 10–30 queries when the user has not supplied a set. Cover several clusters so one head term does not distort the map:

| Query family | Examples | What it reveals |
| --- | --- | --- |
| Category | `[category] software`, `[service] agency` | Direct competitors |
| Jobs | `how to [job]`, `[job] tool` | Problem and solution competitors |
| Commercial | `best [category]`, `[brand] alternatives` | Evaluation-stage competitors |
| Segment | `[category] for [role/industry]` | Audience and vertical positioning |
| Assets | `[topic] template`, `[topic] calculator` | Content-led audience competitors |
| Education | `what is [topic]`, `[topic] guide` | Publishers owning attention |

Use one locale and device consistently. Record:

- query;
- query family;
- rank;
- result domain and URL;
- result/page type when identifiable;
- branded versus non-branded;
- direct, audience, incumbent, or unknown classification.

Rank recurrence within each family. A domain appearing across category and commercial queries is stronger evidence of direct competition than a domain appearing only for broad educational queries.

Verify the offer and audience on the candidate's homepage or product pages before labeling it direct. Preserve `unknown` when evidence is thin.

## Sitemap analysis

### Collection

Check, in order:

1. sitemap declarations in `/robots.txt`;
2. `/sitemap.xml`;
3. `/sitemap-0.xml`;
4. `/sitemap_index.xml`;
5. CMS conventions such as `/wp-sitemap.xml`;
6. sitemap links found in the site's HTML or documentation.

An index can contain hundreds of child sitemaps. Use `sitemap_inventory.py` to recurse and deduplicate. Keep collection errors; a partial sitemap must not be presented as complete.

### URL interpretation

Use path segments and slug tokens to infer:

- page family or template;
- topic/keyword;
- search intent;
- buyer or vertical;
- funnel stage;
- product connection.

Useful path signals include:

| Signal | Possible interpretation |
| --- | --- |
| `/pricing`, `/demo`, `/buy` | Transactional/commercial |
| `/compare`, `/vs`, `/alternatives` | Evaluation |
| `/solutions`, `/use-cases`, `/for/` | Segment or job targeting |
| `/integrations`, `/apps` | Ecosystem demand capture |
| `/templates`, `/examples`, `/tools` | Linkable/product-led acquisition |
| `/blog`, `/guides`, `/resources` | Educational content |
| repeated two-level structures | Programmatic/template strategy |

Do not infer success from existence. A slug is only evidence of targeting. Open a bounded sample:

- 3–5 URLs from each important page family;
- the newest-looking pages when `lastmod` is credible;
- ambiguous families;
- pages central to a proposed recommendation.

### Date interpretation

Report `lastmod` coverage as a percentage. Compare timestamp distributions and watch for identical bulk timestamps, which often indicate deployments rather than editorial updates. Describe publishing cadence only when dates vary plausibly and are supported by page-level dates or repeated snapshots.

### Efficient inspection

Prefer commands such as:

```bash
jq '.totals, .page_types, .top_first_segments, .lastmod' summary.json
```

```bash
python3 - <<'PY'
import csv
from collections import Counter

with open("pages.csv", newline="", encoding="utf-8") as handle:
    rows = csv.DictReader(handle)
    counts = Counter(row["page_type"] for row in rows)
print(counts)
PY
```

Use `rg` against CSV for a few explicit terms. Do not paste thousands of URLs into the model.

## Provider data

Accept live MCP data or local CSV/JSON exports. Before comparing domains, align:

- country/database;
- desktop/mobile scope;
- date or snapshot;
- root domain, subdomain, or exact URL scope;
- filters and traffic definitions.

### Organic keywords and pages

Segment branded and non-branded terms. Then classify non-branded terms by intent:

- transactional;
- commercial investigation;
- problem-aware;
- informational;
- navigational.

Give extra weight to keywords where the product can be naturally demonstrated, named, compared, or used. Inspect the page connected to each valuable keyword cluster; keyword lists without page context can mislead.

### Backlinks

Prefer recently gained referring domains and link-level evidence over total backlink counts. For each meaningful new link, identify:

- linking page and domain;
- target page;
- anchor/context;
- asset type;
- likely acquisition mechanism: original data, tool, template, quote, partnership, list inclusion, news, or organic editorial mention.

Exclude or flag obvious spam, sitewide links, redirects, and duplicate domains. Do not imply causality without evidence.

### Traffic

Treat provider traffic as an estimate. Use it to compare direction, concentration, and change—not as analytics truth. Highlight:

- dependence on a few pages or keywords;
- brand versus non-brand concentration;
- traffic attached to weak commercial relevance;
- lower-volume pages with strong product or revenue fit.

## Gap prioritization

Score each opportunity from 1–5:

- **Business relevance:** closeness to the user's offer and audience.
- **Intent:** likelihood the searcher is evaluating or can benefit from the product.
- **Product fit:** ability to show the product naturally and credibly.
- **Evidence:** consistency across SERPs, sitemap patterns, provider data, and sampled pages.
- **Attainability:** realistic ability to create a stronger page and compete.
- **Effort:** expected content, product, data, design, and authority work.

Use judgment rather than pretending the scores are precise. A practical priority signal is:

`(business relevance + intent + product fit + evidence + attainability) / effort`

Always explain the top recommendations in prose. Do not let the arithmetic overrule obvious strategic constraints.

## Monitoring

Create a stable folder layout:

```text
competitor-research/
  example.com/
    2026-07-02/
      pages.csv
      summary.json
      provider-exports/
    diffs/
      2026-07-02/
        changes.csv
        summary.json
```

Choose cadence based on activity:

- weekly for fast-moving publishers or launches;
- monthly for normal content programs;
- quarterly for slow-moving B2B sites.

Track:

- added and removed URLs;
- changed `lastmod` values, labeled as signals;
- new page families or topic clusters;
- newly ranking commercial keywords;
- meaningful ranking gains/losses;
- newly earned referring domains and linkable assets.

Separate first observation from confirmed pattern. One snapshot is a baseline; two snapshots show change; several snapshots can support a cadence or strategy inference.

## Report quality checks

Before delivery:

- state collection date, locale, tools, scope, and failures;
- separate direct from audience competitors;
- keep facts separate from inference;
- attach confidence to strategic claims;
- avoid raw URL or keyword dumps;
- prioritize commercial relevance over traffic alone;
- name specific page families and examples;
- make every recommendation traceable to evidence;
- disclose incomplete sitemaps, missing provider access, and estimate limitations.
