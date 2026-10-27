# Marketplaces and comparators

What each platform lets an agent do, as checked on 2026-10-27. Platforms change their APIs often: confirm access with a read call (balance, catalog) before planning around one, and update this file when something has changed.

## Marketplaces

| Platform | Access | Search catalog | Order | Notes |
| --- | --- | --- | --- | --- |
| Linkavista | REST API, `env` | yes | yes | French-first catalog. Details and pitfalls in [linkavista.md](linkavista.md). |
| Serpzilla | Hosted MCP (serpzilla.com/api/mcp) | yes, with Ahrefs and Semrush data | yes: guest posts, permanent and rental niche edits, contextual links | Projects, anchors, favorites, blacklist. Asks for confirmation before a purchase. |
| getreach | MCP and REST API (app.getreach.com/api-docs, behind login) | yes, about 190,000 sites | yes, final purchase needs explicit confirmation | Publisher price plus a service fee of up to $79 per link, lower when you provide the article. The fee weighs heavily on cheap links. |
| Placement API | Hosted MCP `https://api.placementapi.com/mcp`, bearer key | yes, several suppliers deduplicated | yes, with an order scope separate from the read-only key | Also compares one domain across suppliers, maps competitor link gaps, and reads Search Console. Prices are held 4 hours. |
| Collaborator.pro | REST API for any registered user (docs after login) | yes | to confirm in the docs | Large international catalog, also Telegram channels. |
| Linkhouse | REST API on request (support@linkhouse.net) | yes | order monitoring confirmed, placing orders to confirm | Search, offer details, order history, balance. |
| Backlink (trybacklink.com) | MCP for Claude and ChatGPT | yes, about 25,000 publishers | yes, each order confirmed | 12 markets. |
| Rixot, BuyLinksForSEO | MCP and REST API | yes | yes: basket, then `publish_basket` spends the balance | Links from $1. Vet hard: at that price most sites fail the strict profile. |

Platforms without a known advertiser API (Paper Club, Ereferer, Getfluence, RocketLinks, Soumettre, and others): use their catalogs through a comparator, or a browser session the user is logged into, and let the user place the order unless they explicitly ask the agent to do it in the browser.

## Comparators

Use a comparator after vetting, on the shortlisted domains, to find the cheapest marketplace for each one. Comparator metrics do not replace the vetting checks.

| Tool | Coverage | Agent access | Notes |
| --- | --- | --- | --- |
| LinkPricer | 40+ marketplaces | web app, no public API found | Bulk paste of domains, free to compare. Can also order on your behalf through the marketplaces' APIs. |
| Mentionable | Soumettre, Ereferer, Getalink, LemmiLink, 1erePlace, Prnews, Linkavista | free web comparator, up to 50 domains; MCP on paid plans | Good French coverage. The MCP is a GEO tool: its `list_backlink_opportunities` ranks domains cited by AI answers with their marketplace prices, and `list_tracked_links` tracks bought links. |
| WeblinkBuzz | 22+ marketplaces, mostly international | web app and Chrome extension, no API found | Bulk check of 50 domains, competitor backlink view. |
| FatGrid | 15+ marketplaces | paid API, 1 unit per domain | Adds Semrush metrics to each result. |
| Link Finder | 30+ marketplaces | web app, paid | Its data also feeds getreach's price comparisons. |
| Référencime | French marketplaces | web app | Shows what each offer includes (writing, indexation guarantee). |

When a comparator has no API, open it in a browser session the user is logged into, paste the shortlist, and read the results. Record the comparator and the date, since most of them refresh catalogs once a day.
