# Marketplaces and comparators

This skill works with marketplaces through their REST API, with a key in a local env var. No MCP to install or manage, and each API is documented in its own reference file once it has been used. Checked on 2026-10-27: confirm access with a read call (balance, capabilities, catalog) before planning around a platform, and update this file when something has changed.

## Marketplaces

### Documented in this skill

| Platform | Env var | Search catalog | Order | Reference |
| --- | --- | --- | --- | --- |
| Linkavista | `LINKAVISTA_API_KEY` | yes | yes | [linkavista.md](linkavista.md), tested with live orders |
| Collaborator.pro | `COLLABORATOR_API_KEY` | yes, once support enables it | no: the user orders in the web app, the API tracks the deal | [collaborator.md](collaborator.md), from the OpenAPI schema |

### API available, not documented yet

Read the platform's API docs, test read calls, then write a reference file like the ones above before ordering through it.

| Platform | API | Docs | Notes |
| --- | --- | --- | --- |
| Serpzilla | REST, OpenAPI | public: serpzilla.com/api | Projects, blacklist, guest posts, permanent and rental niche edits, automatic buying modes. |
| Rixot | REST `/v1`, personal key | public: rixot.com and github.com/mkrupkin/rixot-mcp | Basket, then publish from the prepaid balance. Links from $1: vet hard. |
| BuyLinksForSEO | REST, personal key | public: buylinksforseo.com | Same tools as Rixot, likely the same inventory. |
| Placement API | REST, typed client `placementapi` on npm | public: placementapi.com | Several suppliers deduplicated, domain price comparison. Ordering needs a key scope separate from read-only. |
| getreach | REST | after login: app.getreach.com/api-docs | About 190,000 sites. Publisher price plus a service fee of up to $79 per link. |
| Backlink (trybacklink.com) | REST, ordering only | not found publicly | About 25,000 sites, search, order, brief, status. |
| Linkhouse | REST | on request: support@linkhouse.net | Search, offer details, order history, balance. |

Platforms without a known advertiser API (Paper Club, Ereferer, Getfluence, RocketLinks, Soumettre, and others) stay out of the ordering path. Their offers can still show up in a comparator.

## Comparators

Use a comparator after vetting, on the shortlisted domains, to find the cheapest marketplace for each one. Comparator metrics do not replace the vetting checks.

| Tool | Coverage | Agent access | Notes |
| --- | --- | --- | --- |
| LinkPricer | 40+ marketplaces | web app, no public API found | Bulk paste of domains, free to compare. |
| Mentionable | Soumettre, Ereferer, Getalink, LemmiLink, 1erePlace, Prnews, Linkavista | free web comparator, up to 50 domains | Best French coverage. |
| WeblinkBuzz | 22+ marketplaces, mostly international | web app and Chrome extension, no API found | Bulk check of 50 domains. |
| FatGrid | 15+ marketplaces | paid API, 1 unit per domain | Adds Semrush metrics to each result. |
| Link Finder | 30+ marketplaces | web app, paid | |
| Référencime | French marketplaces | web app | Shows what each offer includes (writing, indexation guarantee). |

Without an API, open the comparator in a browser session the user is logged into, paste the shortlist, and read the results. Record the comparator and the date, since most of them refresh catalogs once a day.
