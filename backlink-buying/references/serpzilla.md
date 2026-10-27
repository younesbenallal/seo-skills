# Serpzilla API

Serpzilla is an international marketplace for guest posts, link insertions, and rental links. Its API covers the full buying path: search, content, order, approval, tracking. This file covers permanent guest posts and link insertions only; rental links, sitewide packages, and automatic buying modes are out of scope.

Sources, checked on 2026-10-27 without a live account: the OpenAPI schema at `https://app.serpzilla.com/openapi_spec` (about 200 endpoints), the guides at `https://serpzilla.com/api/authentication` and `https://serpzilla.com/api/buy-permanent`. Confirm the points marked "to check" on the first real order and update this file.

## Access

- Base URL: `https://app.serpzilla.com`
- Credentials: the account login and an API token from the Passport section of the account. Env vars by convention: `SERPZILLA_LOGIN` and `SERPZILLA_API_TOKEN`. Verify they are set, never print them.
- Auth takes two steps, and every later call sends both values:
  1. `POST /login` with `{"login": "...", "apiToken": "..."}` returns the `AUTH_TICKET` cookie.
  2. `GET /auth` with `Cookie: AUTH_TICKET=...` returns a JWT.
  3. Then call with `Authorization: Bearer <jwt>` and `Cookie: AUTH_TICKET=<ticket>`.
- `GET /rest/User/info` checks the session and returns `balance` and `minimalBalanceReplenishment`. On a 401, log in again. The JWT lifetime is not documented (to check).
- Prices are in USD for English-language accounts.

## Endpoints for buying

| Method and path | Use |
| --- | --- |
| `GET /rest/User/info` | Session check, balance. |
| `GET /rest/System/configuration` | Ids for `languagesPermanent`, `worldwideCategories`, `worldwideRegions`, `domainZones`, plus status and action labels. Call once and keep the ids. |
| `POST /rest/Project/addSimpleProjectAndContent` | Create a project from `{"domain": "https://example.com/"}`. Returns the project `id`, plus a `urlId` and `textId` for the homepage. |
| `GET /rest/Project` | List projects. Reuse the project for the user's domain instead of creating a new one. |
| `POST /rest/Content/add/texts/projectId/{projectId}` | Add a target URL and its link texts. Returns `urlId` and `textId`. |
| `POST /rest/Content/add/article/projectId/{projectId}` | Add your own article for an advertiser guest post. Returns `articleId` and `urlId`. |
| `POST /rest/SearchPermanent/projectId/{projectId}` | Search sites for one placement type. |
| `GET /rest/Site/{siteId}` | Site card, for a closer look at one candidate. |
| `POST /rest/Placement/permanent/create/projectId/{projectId}` | Place the order. |
| `POST /rest/Project/placements/links?projectId=` | List the project's links with status, price, published URL, indexation. |
| `GET /rest/Placement/placementId/{placementId}` | One link. |
| `PATCH /rest/Placement/action` | Approve content, cancel, and other actions on links. |
| `POST /rest/BlackList/addDomains` | Exclude domains from future searches. |

## Placement types

The search takes `permanentLinkType`, the order takes `linkTypeId`:

| Type | Search `permanentLinkType` | Order `linkTypeId` | You send |
| --- | --- | --- | --- |
| Advertiser's article (guest post you write) | `news` | `21` | `articleId` + `urlId` |
| Publisher's article (the site writes) | `review` | `22` | `textId` + `urlId` |
| Link insertion in a recent article | `link` | `20` | `textId` + `urlId` |
| Link insertion in an archive article | `archive` | `23` | `textId` + `urlId` |

## Content

A link text is the sentence around the link, with the anchor between `#a#` and `#/a#`:

```json
{
  "urlsTexts": [
    { "url": "https://example.com/blog/page/", "texts": [{ "text": "Read our #a#guide to cash management#/a# before investing." }] }
  ]
}
```

An article you write is HTML with at least one link:

```json
{
  "url": "https://example.com/blog/page/",
  "title": "…",
  "body": "<p>… <a href=\"https://example.com/blog/page/\">anchor</a> …</p>",
  "metaTitle": "…",
  "metaDescription": "…",
  "metaKeywords": "…"
}
```

## Search

`POST /rest/SearchPermanent/projectId/{projectId}?permanentLinkType=news&limit=100&page=1&orderBy=price&orderType=asc` with a JSON filter body. Useful filters:

- Market: `siteLanguages` (language ids from the configuration), `worldwideRegionsIds`, `worldwideCategories`, `domainZones`
- Price: `priceArticleFrom`, `priceArticleTo`
- Traffic: `trafficAhrefsFrom`, `trafficSemrushFrom`, `semrushDomainOverviewOrganicTrafficFrom`
- Authority: `ahrefsDomainRatingFrom`, `ahrefsTotalKeywordsFrom`, `semrushAscoreFrom`, `majesticTfFrom`, `mozSpamScoreTo`
- Link quality: `isPlacingNoFollow: 0` (dofollow only), `externalLinksTo` (outbound links), `isShady: 1` (main database, without questionable sites), `domainSeIndexation: 2` (indexed in Google)
- Duplicates: `projectIdsForExcludeSitesWithPlacements: [projectId]` to skip sites already bought for this project
- Topic: `keywords` (text), `smartSearchContentText` with `isSmartSearchUsed: true` (semantic search from a text, to check)

The response returns `items` and a `searchHistoryId` to pass with the order. Fields worth reading per site: `id` (site id), `fullUrl`, `priceNews` (advertiser's article), `priceReview` (publisher's article), `priceArticle`, `priceArchive`, `domainRating`, `trafficAhrefs`, `trafficSemrush`, `semrushAscore`, `mozSpamScore`, `isPlacingNoFollow`, `avgPlacementTime`, `avgDaysToIndex`, `placementPercent`, `siteLanguage`, `worldwideCategories`.

## Placing an order

```json
POST /rest/Placement/permanent/create/projectId/{projectId}?linkTypeId=21
{
  "links": [{ "siteId": 123, "articleId": 456, "urlsTexts": [{ "urlId": 789 }] }],
  "settings": {
    "relType": 0,
    "isContentNeedApproval": true,
    "nofPendingDays": 15,
    "warrantyPackage": 2,
    "checkIndexMode": 2,
    "creditPeriod": 0,
    "isLinkTextFinal": true,
    "searchHistoryId": "…"
  }
}
```

- `relType`: 0 dofollow, 1 nofollow, 2 sponsored. Use 0.
- `isContentNeedApproval: true` makes the publisher submit the content before publishing. Use it for publisher-written articles and link insertions, so the anchor and context can be checked.
- `nofPendingDays`: how long the publisher has to accept (5 to 30).
- `warrantyPackage`: 0 guarantee on indexing and loss, 1 guarantee on loss, 2 none. Guarantees probably cost extra (to check); ask the user.
- `checkIndexMode`: 2 checks indexing in Google.
- `creditPeriod`: 0 pays normally; 90 or 180 is an installment plan.
- `isConfirmedDuplicate`: only when the user approves buying a site already used for this project.

The response returns `placementDataList[]` with `placementId`, `status`, `price`, `siteDomain`, and the flags `isError`, `message`, `isDuplicate`, `isNotEnoughMoney`. Stop on any flag. A `placementId` is the order id to record.

## Follow-up

Status codes: 1 awaiting payment, 10 needs your confirmation, 11 under clarification, 20 to 24 in progress, 25 arbitration, 26 content review, 30 checking placement, 40 posted, 41 restored, 50 placement error, 51 creation error, 60 and 61 frozen (manually, or because the balance ran out), 70 link change, 80 withdrawn, 90 cancelled.

`PATCH /rest/Placement/action` with `{"action": "...", "placementIds": [...]}`:

- `approve_content_seo` approves the content the publisher submitted. Show the content to the user first.
- `approve_seo` confirms a link waiting for confirmation (status 10, to check).
- `cancel_seo`, `cancel_from_on_placement_seo`, `cancel_from_improve_seo` cancel at different stages.

Each approval or cancellation is a user decision, like the order itself. Read `placementUrl`, `isPageIndexedAtGoogle`, and `statusTitle` from the project links list to confirm publication.
