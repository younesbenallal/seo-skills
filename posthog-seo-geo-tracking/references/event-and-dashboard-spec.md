# PostHog SEO/GEO event and dashboard specification

Read this reference when implementing the tracking contract, generating a coding-agent handoff, creating a dashboard through MCP, or producing the PostHog AI dashboard prompt.

## Canonical measurement contract

### Acquisition fields

Store these as immutable first-touch person properties or on every server-side conversion event. Use the codebase's equivalent names when they already exist:

| Field | Meaning |
| --- | --- |
| `first_touch_channel` | Normalized acquisition channel |
| `first_touch_referrer` | Original referrer URL or safe host-level value |
| `first_touch_referring_domain` | Original referring hostname |
| `first_touch_utm_source` | First UTM source |
| `first_touch_utm_medium` | First UTM medium |
| `first_touch_utm_campaign` | First UTM campaign |
| `first_touch_landing_path` | First eligible marketing landing path |
| `first_touch_at` | Timestamp of the first eligible touch |

Recommended channel values:

`organic_search`, `llm_referral`, `paid_search`, `paid_social`, `email`, `referral`, `social`, `direct`, `other`.

Classify the referring domain before generic referral logic. Keep internal domains, OAuth providers, checkout/payment redirects, localhost, and test hosts out of acquisition classification according to the repository's environment and consent rules.

Initial LLM referral domains:

`chatgpt.com`, `chat.openai.com`, `claude.ai`, `perplexity.ai`, `gemini.google.com`, `copilot.microsoft.com`, `poe.com`, and `you.com`.

The list is a starting point, not a claim that it is exhaustive. Store the observed referring domain so new sources can be identified and added deliberately.

### Events

Use lowercase snake_case. Fire each event from its source of truth:

| Event | Trigger | Required or useful properties | Source of truth |
| --- | --- | --- | --- |
| `signup_started` | User begins the real signup flow | `signup_method` when known | Client flow |
| `signup_completed` | User record is successfully created | `signup_method`, `plan_selected` when known | Auth/backend success |
| `subscription_started` | Active paid subscription is confirmed | `subscription_id`, `stripe_customer_id`, `plan`, `billing_interval`, `mrr_usd`, `currency` | Verified provider webhook |
| `invoice_paid` | Invoice payment is confirmed | `invoice_id`, `subscription_id`, `stripe_customer_id`, `amount_usd`, `currency` | Verified provider webhook |
| `subscription_cancelled` | Cancellation is confirmed | `subscription_id`, `plan`, `cancellation_reason` when known | Verified provider webhook |

Revenue is the trusted `amount_usd` on `invoice_paid`, deduplicated by invoice/provider event ID. Do not accept revenue, plan, or subscription status from the browser. Attach first-touch fields to server-side events or make them queryable as immutable person properties after identity is stitched.

### Definitions for reporting

- **SEO:** sessions or people whose first-touch channel is `organic_search`.
- **GEO:** sessions or people whose first-touch channel is `llm_referral`. In this skill, GEO means observable LLM-referral acquisition, not AI-answer visibility.
- **Signed-up users:** unique people with `signup_completed`.
- **Subscribed users:** unique people with `subscription_started`.
- **Revenue:** sum of deduplicated `amount_usd` from `invoice_paid`.
- **Attribution model:** first-touch attributed. Use “attributed” language; do not call it causal revenue.
- **Unbranded SEO:** query-level branded/unbranded classification requires Search Console or another search-query source. A PostHog-only landing-path rule is an **unbranded SEO proxy**, configured from maintained non-brand paths and labelled as such.

## Coding-agent implementation prompt

Use this when the user wants a prompt for an AI coding agent, or when the current task is a handoff rather than direct code implementation.

```text
Implement production-ready PostHog acquisition and conversion tracking in this SaaS codebase.

First inspect the repository and identify:
- framework, package manager, auth implementation, marketing-site/app domains, and cross-subdomain behavior
- current PostHog, analytics, consent, Stripe, and webhook implementations
- existing tracking events, user IDs, and tests

Do not duplicate working instrumentation. Use one PostHog project across the marketing website and product app when the journey crosses both surfaces. Follow the current official PostHog SDK documentation and existing codebase conventions.

Goal: track the journey from an anonymous first visit to signup, subscription, and revenue with reliable first-touch SEO and LLM-referral attribution.

Requirements

1. Client installation and pageviews
- Install or reuse the PostHog browser SDK on the marketing site and app.
- Capture pageviews and SPA route changes exactly once.
- Respect the existing cookie-consent model; wait for consent where required.
- Exclude localhost, test accounts, internal traffic, self-referrals, OAuth redirects, and payment redirects according to the existing reporting convention.
- Do not send PII, secrets, raw payment data, or sensitive query-string values.

2. Acquisition attribution
- Preserve immutable first-touch fields from the first eligible marketing landing:
  first_touch_channel, first_touch_referrer, first_touch_referring_domain,
  first_touch_utm_source, first_touch_utm_medium, first_touch_utm_campaign,
  first_touch_landing_path, first_touch_at.
- Reuse PostHog automatic properties where available and add only the minimum normalization logic.
- Normalize channels to: organic_search, llm_referral, paid_search, paid_social, email, referral, social, direct, other.
- Keep the domain matcher in one documented location. Start with:
  chatgpt.com, chat.openai.com, claude.ai, perplexity.ai,
  gemini.google.com, copilot.microsoft.com, poe.com, you.com.
- Classify LLM referrals before generic referral traffic.
- Preserve first-touch data across marketing-site to app navigation, including cross-subdomain navigation.
- Never overwrite first-touch values on later visits.

3. Identity
- Keep visitors anonymous before authentication.
- After successful signup or login, identify with the stable internal user ID, never a shared value or an email when the codebase has a stable non-PII ID.
- Use the same internal user ID as the server-side distinct ID.
- Set durable person properties only when already supported by the data model.
- Reset on logout.
- Ensure first-touch fields remain queryable after identity stitching.

4. Conversion events
Emit lowercase snake_case events from the correct source of truth:
- signup_started: when the user begins the real signup flow
- signup_completed: after the user record is successfully created
- subscription_started: after a trusted billing webhook confirms an active paid subscription
- invoice_paid: after a trusted webhook confirms payment
- subscription_cancelled: after a trusted webhook confirms cancellation

Use these properties where available:
- signup_completed: signup_method, plan_selected
- subscription_started: subscription_id, stripe_customer_id, plan, billing_interval, mrr_usd, currency
- invoice_paid: invoice_id, subscription_id, stripe_customer_id, amount_usd, currency
- subscription_cancelled: subscription_id, plan, cancellation_reason

For every server-side conversion event, attach immutable first-touch fields or make them queryable as person properties. Revenue must come from the provider/backend, never browser input.

5. Billing and webhook safety
- Verify webhook signatures.
- Make emissions idempotent using provider event IDs and invoice/subscription IDs.
- Link the billing customer to the internal user in the database.
- If a billing event cannot be linked to a user, log it safely and do not invent attribution.

6. Documentation and verification
- Add a concise tracking-plan document listing event, trigger, properties, source of truth, consent behavior, and deduplication key.
- Add tests for channel classification, first-touch immutability, and webhook idempotency where the existing test setup supports them.
- Verify: anonymous visit -> organic/LLM acquisition -> signup -> identify -> subscription -> invoice_paid.
- Report changed files, the final schema, test results, and assumptions or gaps.
```

## PostHog AI dashboard prompt

Use this when no dashboard-write MCP is available, or when the user wants a prompt they can paste into PostHog AI. Replace bracketed placeholders only after inspecting the project schema.

```text
Create a dashboard named “SEO & GEO Acquisition to Revenue”.

Before creating insights, inspect this project's actual event and property names and map them to:
- pageviews and sessions
- entry/current URL path
- referring domain and initial referring domain
- first-touch acquisition channel
- first-touch landing path
- signup_completed
- subscription_started
- invoice_paid
- amount_usd
- first-touch UTM and referrer fields

Use the project's existing schema. Do not create duplicate events or properties. If a requested metric cannot be mapped, say which field is missing and omit or clearly label the affected insight.

Definitions:
- SEO = sessions or people whose first-touch acquisition channel is organic_search.
- GEO = sessions or people whose first-touch acquisition channel is llm_referral.
- LLM domains include chatgpt.com, chat.openai.com, claude.ai, perplexity.ai, gemini.google.com, copilot.microsoft.com, poe.com, and you.com.
- Attribution = first-touch attributed. Label revenue and conversions as attributed, not causal.
- Revenue = deduplicated sum of amount_usd on invoice_paid.
- Signed-up users = unique people with signup_completed.
- Subscribed users = unique people with subscription_started.
- Unbranded SEO proxy = organic traffic landing on a configured list of non-brand paths. Do not claim this is query-level unbranded attribution. Add a note that Search Console is required for verified branded/unbranded query reporting. Never assume the homepage is unbranded.

Set the default date range to the last 30 days and compare with the prior period where supported. Add dashboard-level filters for date range, acquisition channel, first-touch landing path, referring domain, LLM source, and the configured unbranded SEO proxy.

Create these sections and insights:

1. Acquisition overview
- Total visitors, sessions, and pageviews.
- SEO visitors/sessions and signup conversion rate.
- GEO visitors/sessions and signup conversion rate.
- SEO versus GEO traffic trend by day or week.

2. Search engines and LLM sources
- SEO sessions for the last 14 and 30 days, broken down by search-engine/referring domain.
- GEO sessions for the last 14 and 30 days, broken down by LLM referring domain.
- A ranking table of source, sessions, signups, subscriptions, and attributed invoice-paid revenue.

3. SEO conversion and revenue
- Funnel: SEO session or landing pageview -> signup_completed -> subscription_started -> invoice_paid.
- Monthly series for SEO-attributed signups, subscribed users, and revenue.
- Session-to-signup and signup-to-subscription conversion rates.
- Organic landing-page table with sessions, signups, subscriptions, signup rate, subscription rate, and revenue.
- Monthly-by-page SEO table with traffic, signups, subscriptions, and revenue.
- Duplicate relevant SEO insights with the unbranded SEO proxy filter available and clearly labelled.

4. GEO conversion and revenue
- Funnel: GEO session or landing pageview -> signup_completed -> subscription_started -> invoice_paid.
- Monthly series for GEO-attributed signups, subscribed users, and revenue.
- LLM landing-page table with LLM source, sessions, signups, subscriptions, conversion rate, and revenue.
- Monthly-by-page GEO table with traffic, signups, subscriptions, and revenue.
- LLM source by landing-page table ordered by subscriptions, then revenue.

5. Data-quality note
Add a text tile stating:
- Browser analytics cannot recover organic search queries; use Search Console for verified branded/unbranded reporting.
- Observable LLM referrals undercount influence that becomes direct or branded search.
- Revenue is first-touch attributed and is a consistent operating model, not proof of causality.

Use readable titles, currency formatting, unique-person counting for signups/subscriptions, and the project's known internal/test-user exclusion. Do not use warehouse tiles for core metrics unless the project's schema requires them and the filters remain understandable.
```

## MCP dashboard creation checklist

When a PostHog MCP is callable, the agent should discover capabilities rather than assume endpoint names. Look for tools that can:

1. identify the PostHog organization/project and current user permissions;
2. inspect event names, properties, property values, and existing dashboards/insights;
3. query representative data to validate the event/property mapping;
4. create a dashboard, create insights or SQL queries, and attach tiles;
5. read back the created dashboard and tiles for verification.

A write-capable MCP can create the dashboard without the user opening the PostHog UI, provided the connection has permission. Prefer a small set of verified insights over a large set of speculative tiles. Preserve the project timezone, existing filters, and naming conventions. If only query tools are available, stop before mutation and hand off the prompt with the discovered schema. If no PostHog tools are exposed, say so plainly; do not claim that a dashboard was created.
