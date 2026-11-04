# Linkuma API

Linkuma is a French sponsored-article **network**, not a marketplace: you order an article type and a thematic, and Linkuma picks the site in its own network, writes, and publishes. Its main use here is **relinking**: Tier 2 packs that push an article Linkuma already published, and cheap Tier 2 or anchor-diversity articles pointing at any URL. The API is in beta.

Sources, checked on 2026-11-04: the API docs supplied by the user (from `https://app.linkuma.com`), live read calls with a client key (`/settings`, `/projects`, `/carts`), and cart simulations on `/carts/price`. No order or relinking pack was placed yet: confirm the points marked "to check" on the first real one and update this file.

## Access

- Base URL: `https://app.linkuma.com/api/v1`
- Auth header: `Authorization: Bearer <key>`, plus `Accept: application/json` and `Content-Type: application/json`
- Env var by convention: `LINKUMA_API_KEY`. Verify it is set, never print it. The key is generated on `https://app.linkuma.com/myaccount` ("Regénérer clé API") and shown once; regenerating does not revoke older keys.
- `GET /orders/types` and `GET /thematics/{type}` work without a key. Everything else needs it.
- Rate limit: 1000 requests per minute per account, then HTTP 429. Headers `X-RateLimit-Limit` and `X-RateLimit-Remaining`.
- Prices are in Linkuma credits. A negotiated rate may apply to the account: the price that counts is the one returned by `POST /carts/price` or by the relinking response, never `/orders/types`. The Holly&Stick account gets lower prices than the public list (in November 2026: Starter 3, Linkuma 7). Credit to euro conversion and tax: to check.
- 401 means a missing or revoked key, 403 a key that is not on a client account.

## Endpoints for buying

| Method and path | Use |
| --- | --- |
| `GET /settings` | Credit balance: `[{"user_id": …, "credit": 2930}]`, an array without `data` envelope. Monthly-billed accounts get the articles ordered this month instead. Check before ordering. |
| `GET /orders/types` | Order types and public unit prices. |
| `GET /thematics/{type}?lang=fr` | Thematics and their categories for a type. Keep the `id` of the thematic and category. |
| `GET /projects` | List projects with their orders (without posts). Reuse the project for the user's site. |
| `POST /projects` | Create a project: `{"name": "…"}`. |
| `GET /projects/{id}` | One project with its orders, thematics, and **published** posts. |
| `POST /carts/price` | Simulate a cart: per-line and total price, full validation, nothing created or debited. |
| `POST /carts/order` | Place the cart. |
| `GET /carts`, `GET /carts/{id}` | Paid carts with orders and posts. |
| `GET /orders/{id}` | One order with its posts. 402 if not paid yet. |
| `GET /posts/{id}` | One post, with its attached `indexes_ou_remplaces` and `maillage_interne` posts. |
| `POST /posts/{id}/relinking` | Buy a Tier 2 relinking pack for a published post. |

The `/editor/*` endpoints are for publishers selling their own sites; out of scope here.

## Order types

| `type` | Label | Public price | Thematics |
| --- | --- | --- | --- |
| `basic` | Starter | 7 | Generalist only, one per language |
| `standard` | Linkuma | 10 | Full catalog |
| `premium` | Boost | 30 | Full catalog, premium sites |
| `citation_linkuma` | Citation Linkuma | 15 | Same as `standard` |
| `citation_boost` | Citation Boost | 35 | Same as `premium` |

Languages: `fr`, `en`, `de`, `es`, `it`, `nl`, `pt`. In Spanish and Italian only the generalist thematic is orderable. Marketplace, homepage, and forum links are web-app only.

Since Linkuma chooses the site, the vetting in [vetting.md](vetting.md) cannot run before the order. Vet the published post afterwards (indexed, on topic, not a link farm), and keep Linkuma for jobs where the relaxed profile is enough: Tier 2, relinking, anchor diversity.

## Relinking a Linkuma post

`POST /posts/{post_id}/relinking` adds Tier 2 links to a post Linkuma already published. Linkuma writes and publishes the relinking articles automatically, one per day, starting immediately.

```json
POST /posts/{post_id}/relinking
Idempotency-Key: rlk-<post_id>-<date>
{ "tier": "linkuma", "qty": 5 }
```

- `tier`: `starter` (generalist thematic), `linkuma` (thematic of the original post), `boost` (same thematic, premium sites).
- `qty`: 3, 5, or 10.
- Payment is always an immediate debit of credits. The amount is computed by the server and only known from the response (`linkuma` × 5 returned 30 in the docs example). There is no price simulation: give the user the expected amount from a previous pack or the web app, and get approval on that amount.
- The `post_id` comes from `orders[].posts[].id` in `GET /projects/{id}`, `GET /carts/{id}`, or `GET /orders/{id}`. Only posts with `is_post_ready: true` qualify; otherwise the API answers 422 "Disponible une fois votre lien publié".
- Response: `data.relinking_pack_id`, `tier`, `qty`, `amount`, `already_processed`. Record the pack id as the order id.
- Always send an `Idempotency-Key`: without it, two identical calls buy two packs. On a 409 the first call is still running; wait and retry with the same key. On a 402 (not enough credits) the key becomes reusable after a top-up.
- How relinking articles show up afterwards (an order of type `relinking`, or a post attached to the original): to check on the first pack.

To relink a backlink bought elsewhere (Linkavista, Serpzilla, a guest post), use a normal cart order with the Tier 1 source as `url` (see below).

## Placing a cart

Always call `POST /carts/price` first with the exact body, show the returned prices, then send the same body to `POST /carts/order` with the payment fields and an `Idempotency-Key`.

```json
{
  "items": [
    {
      "type": "standard",
      "project_id": "…",
      "thematic_id": "…",
      "category_id": "…",
      "url": "https://example.com/page/",
      "pagekw": "main keyword of the target page",
      "qty": 1,
      "anchor": "custom",
      "anchor_value": "anchor text",
      "distribution": "direct",
      "started_at": "2026-11-10",
      "fast_publication": false
    }
  ],
  "payment_method": "direct_credits",
  "nice_name": "[client] Tier 2 – 2026-11"
}
```

- `pagekw` is required. `thematic_id` must belong to the type's thematic list, or the API answers 422. `category_id` is optional.
- `anchor`: `url` (the URL as anchor), `generic` (Linkuma draws a generic anchor in the thematic's language), `custom` (text in `anchor_value`, several anchors comma-separated for `qty` > 1).
- `distribution`: `direct` (`started_at` for all), or `schedule` with `distribution_value`, the number of days between two publications. The response names them `dillution` and `dillution_value`.
- Second link: `url2` and `anchor2_type`, plus `custom_anchor2` when `anchor2_type` is `custom` (not `anchor2_value`). Costs 3 credits per article on the Holly&Stick account.
- `additional_words_count`: omit it for the base length. Otherwise 100, 200, 300, or 500 (one credit per 100 words); 0 or 150 is rejected with 422.
- Other paid options: `improved_text`, `ytg_posts_data` (YourTextGuru `{keyword, title}` pairs).
- `brief` is kept only for citations and with `improved_text`; it is silently ignored otherwise. A forced title is not supported: `title` stays null.
- Your own article on `basic`, `standard`, `premium`: `provide_content: true` with `provided_title` (becomes the H1), `provided_content` (HTML), and optionally `provided_meta_title`, `provided_meta_description`, `provided_thumbnail`, `provided_thumbnail_source`.
- Citations (`citation_*`): `map` (Google Maps URL), `brief`, and `is_no_link: true` for a mention without link.
- `payment_method`: `direct_credits` (default, immediate debit, 402 if the balance is short), `reversed_credits` (monthly invoice, needs a permission), `pending_payment` (cart left unpaid in the web app, needs a permission; only then is `external_ref` stored).

The price simulation also returns `editor_status`, `editor_writer`, and `editor_min_started_at`, undocumented. The 201 response returns the cart `id` and `orders[].id`: record both. On a 409 with the same idempotency key, check `GET /carts` before retrying with a new key; the order may have gone through.

## Follow-up

Order statuses: `created` awaiting payment, `pending` paid, `ordered`, `active` in production, `delivered`, `completed`, `published` (URL available), `canceled`, `remove` and `retrait` (link removal), `refunded`.

A post is live when `is_post_ready` is true: read `url`, `anchor` (the anchor actually placed), and `traited_at` (publication date). `GET /posts/{id}` also shows the attached indexing or replacement post and internal-linking post, each with its own `due_date`.
