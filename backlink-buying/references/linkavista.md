# Linkavista API

Linkavista is a French-first sponsored-article marketplace with an advertiser REST API. Everything below was observed with a live advertiser key in October 2026; there is no public documentation page, so check a response before relying on a field that is not listed here.

## Access

- Base URL: `https://linkavista.com/api/v1/advertiser`
- Auth header: `X-API-Key: <key>`, plus `Accept: application/json`
- Env var by convention: `LINKAVISTA_API_KEY`. Verify it is set, never print it.
- The key must be an **advertiser** key. A request on a wrong path can look like a permission error; test `/balance` before concluding the key lacks access.
- Rate limit: about 200 requests per minute, then HTTP 429.

## Endpoints

| Method and path | Use |
| --- | --- |
| `GET /balance` | Account balance. Check before ordering. |
| `GET /categories` | Category ids and slugs, used as `category_id[]` filters. |
| `GET /sites` | Catalog search, paginated (`per_page` up to 200, `page`, `last_page` in the response). |
| `POST /orders` | Place an order. |
| `GET /orders/{id}` | Order status, `published_url`, `published_at`. |

Useful `/sites` filters: `language[]=fr`, `category_id[]=<id>`, `price_max`, `keyword_count_min`, `tf_min`, `sort=keyword_count&order=desc`.

## Catalog fields worth reading

- `pricing.price`, `pricing.redaction_price`, `pricing.editor_writing_price` are in **cents**: `33500` means 335 €. Prices are before tax.
- `metrics`: `tf`, `cf`, `da`, `rd`, `total_traffic`, `keyword_count`, `acceptance_rate`, and `analytics_enabled` (the publisher shares Search Console data, visible on the site page in the web app).
- `constraints`: `min_words`, `max_links`, `min_images`, `max_images`.
- `writing_modes`: `platform` (Linkavista writes), `advertiser` (you provide the article), `editor` (the publisher writes).
- `existing_article.available` and `existing_article.price`: link insertion into an existing article.
- `average_publication_delay`, `categories`, `theme`.

## Placing an order

Send an `Idempotency-Key` header built from the campaign and site, so a retry cannot create a second order.

Platform-written article:

```json
{
  "site_id": 12345,
  "article_title": "…",
  "brief": "Audience, angle, what to avoid, where the links go.",
  "anchors": [{ "anchor_text": "…", "target_url": "https://…" }],
  "content_provider": "platform",
  "redaction_option": "classique"
}
```

Article you provide (HTML, at least the site's `min_words`, no more links than `max_links`):

```json
{
  "site_id": 23456,
  "content_provider": "advertiser",
  "content": "<h2>…</h2><p>… <a href=\"https://…\">anchor</a> …</p>",
  "article_title": "…",
  "respect_title": true,
  "anchors": [{ "anchor_text": "…", "target_url": "https://…" }]
}
```

A created order returns `201` with `data.id`, `data.status`, and `data.pricing` (`link_price_cents`, `redaction_cents`, `total_cents`). Stop if `data.sandbox` is true or the status is not 2xx.

## Pitfalls

- A platform-written order starts in `writing` and cannot be cancelled. An article you provide stays cancellable while it waits for the publisher's validation.
- Images must be stable public URLs (for example Wikimedia Commons); the API does not upload files.
- Publishers may widen an anchor slightly when they place it. Check the published link.
- `target_url` accepts any URL, which is how Tier 2 orders work.
- Well-known "best of" ranking sites in a niche are often not in the catalog; they need direct contact (see `backlink-outreach`).
