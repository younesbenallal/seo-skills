# Collaborator API

Collaborator.pro is an international guest-post marketplace. Its public API reads the catalog and your orders ("deals"). It **cannot place an order**: prepare the order with the agent, then the user places it in the web app. Reference: the OpenAPI schema at `https://collaborator.pro/api/public/default/schema`, rendered at `https://collaborator.pro/api/public/default/docs`. Checked on 2026-10-27 from the schema only, without a live key.

## Access

- Base URL: `https://collaborator.pro`
- Auth header: `X-Api-Key: <key>`, created in the account settings. Any registered account can get one.
- Env var by convention: `COLLABORATOR_API_KEY`. Verify it is set, never print it.
- The catalog endpoint is "available upon request from support": ask support to enable it on the account before planning around it. `GET /api/public/me/capabilities` returns the account role (`customer` or `owner`) and what the key can use; call it first.

## Endpoints

| Method and path | Use |
| --- | --- |
| `GET /api/public/me/capabilities` | Account role and enabled tools. |
| `GET /api/public/creator/list` | Catalog search (sites are called "creators"). |
| `GET /api/public/deal/list` | Your orders as a customer, with status, prices, and published URL. Filter with `projects[]`. |
| `GET /api/public/dictionary/countries`, `/regions?countryId=`, `/cities?regionId=`, `/languages` | Ids for the geographic and language filters. |

Pagination: `page` and `per-page` (20, 40, 60, or 100). Responses return `items` and `pagination` (`totalCount`, `pageCount`, `page`, `pageSize`). The `language` parameter only sets the language of labels (`en`, `pl`, `ua`, `ru`); use `en`.

## Catalog filters worth using

- Market: `_language[]` (language ids), `countries[]`, `_regions[]`, `_city[]`
- Price: `_price_min`, `_price_max`, `_price_with_writing=true`
- Traffic and rankings: `_traffic` (thousands of monthly visits, minimum), `is_traffic_grown=true`, `ahrefs_traffic_min`, `ahrefs_keywords_min`, `serp_keywords_min` (queries in the top)
- Authority: `ahrefs_dr_min`, `ahrefs_refdomains_min`, `_tf_min`, `_moz_da_min`
- Outbound links: `serp_ext_domains_max` (outgoing domains). Useful for the vetting check on link density.
- Link: `nofollow=0` for dofollow only, `max_anchors[]` (1, 2, or 3 links), `advertising_mark=false` to skip sites that label the post as an ad
- Format and site: `format_id=1` (article), `_cre_type_id[]` (1 personal blog, 2 corporate blog, 3 media, 5 information site, 6 portal), `with_insurance=true` (insurance against deletion and deindexing)
- `keywords[]` to search by topic, `_url` to look up one domain, `sort` (for example `-da_moz`)

## Catalog fields worth reading

- `name` (domain), `url` (catalog page), `categories`, `country`, `siteType`, `placementSpeed`
- `traffic` is a formatted string ("353.1 k") from Google Analytics or Similarweb. Re-check traffic with the SEO data provider.
- `tf`, `cf`, `daMoz`, `indexGoogle`, `siteAge`, `linkExchange` (listed on automatic link exchanges: a red flag)
- `prices[]`, one entry per placement format: `pricePublication`, `priceSpelling` (writing), `priceAnnouncement`, `linkType` (`dofollow` or `nofollow`), `numberOfLinks`, `priceContrCategories`. Prices are formatted strings with a currency ("2 768.78 USD"): strip the spaces and read the currency before comparing.

## Ordering

The API has no endpoint to create a deal. After the user approves a Collaborator line in the basket:

1. Prepare everything the order form needs: site, format, article (HTML, title, meta) or brief, anchors and target URLs.
2. The user places the order in the web app, or asks the agent to do it in a browser session they are logged into.
3. Read `GET /api/public/deal/list` to confirm the deal exists, then record its id in the purchase log. Use the same endpoint to follow its status and `urlOfPublishedArticle`.
