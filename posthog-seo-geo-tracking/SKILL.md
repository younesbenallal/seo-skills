---
name: posthog-seo-geo-tracking
description: Set up, audit, and operationalize PostHog tracking from SEO or LLM-referral landing through signup, subscription, and revenue. Use when a user wants SEO/GEO acquisition attribution in a website and SaaS app, a PostHog dashboard for it, or a copy-paste implementation prompt. Do not use for measuring AI-search visibility itself or for query-level SEO reporting without Search Console.
---

# PostHog SEO/GEO tracking

Build a defensible measurement path from anonymous acquisition to business outcome. The core contract is:

`anonymous landing -> immutable first touch -> signup -> identify -> trusted billing event -> dashboard`

Use one PostHog project across the marketing site and app when the product journey crosses both surfaces. Preserve the user's existing framework, consent model, auth, billing, and analytics conventions.

## Scope and boundaries

- This skill owns PostHog instrumentation, first-party acquisition attribution, conversion/revenue events, validation, and the SEO/GEO dashboard.
- `geo-audit-report` measures whether a brand appears in AI answers, citations, maps, and search traces. It is complementary, not a substitute for this skill.
- PostHog can observe organic-search and LLM-referral visits; it cannot recover the Google query behind an organic visit. Use a connected Search Console source for verified branded/unbranded query reporting, or label a landing-page rule as an “unbranded SEO proxy.”
- First-touch attribution is a consistent reporting model, not proof of causality. LLM referrals undercount influence that later becomes direct or branded search.

## Tooling and access

- Auth mode: `mcp` for live PostHog discovery/query/write, or `manual-file`/prompt fallback when no PostHog MCP is exposed.
- Requires: the application repository for implementation; a connected PostHog project for live verification or dashboard creation.
- Optional: connected Search Console data or an export for verified branded/unbranded query reporting.
- Never request PostHog tokens or other secrets in chat. Read the saved tooling inventory first, then inspect callable tools and local configuration when the inventory is missing, stale, or does not list the capability the task needs. Never print secret values.

## Run the workflow

### 1. Preflight the project

Read [`../docs/credentials-and-tooling.md`](../docs/credentials-and-tooling.md) and `.seo-context.md` when present. Inspect the repository before asking for setup details:

- framework, package manager, app boundaries, marketing/app domains, and cross-subdomain behavior;
- existing PostHog or analytics initialization, pageview capture, consent/CMP logic, auth identity calls, and logout handling;
- Stripe or other billing provider, webhook verification, internal user IDs, and idempotency storage;
- existing events, tracking plans, tests, and environment/configuration conventions.

Reuse working instrumentation. Ask only for missing facts that materially change the implementation: canonical domains, PostHog project scope, consent requirements, conversion source of truth, billing provider, or the path list used for an unbranded proxy. Completion means the current implementation and every required unknown are recorded.

For current SDK/API behavior, consult the official PostHog documentation or an available documentation tool before choosing installation or API syntax. Never rely on a remembered package API when the repository or current docs can answer it.

### 2. Choose the deliverable

Use the branch that matches the request:

- **Implement or audit code:** read [references/event-and-dashboard-spec.md](references/event-and-dashboard-spec.md), then produce or review the smallest complete implementation. The coding-agent prompt in that reference is a fallback deliverable when the current task is not the application repository.
- **Create a connected dashboard:** inspect the callable tool registry for PostHog capabilities before asking the user to open PostHog. Use a PostHog MCP only when it exposes the required project/schema discovery and dashboard/insight writes. Do not invent tool names or assume that a generic MCP connection is PostHog.
- **No dashboard-write capability:** use any available read/query capability to map actual event and property names, then provide the PostHog AI prompt from the reference with those mappings filled in. If no PostHog capability is available, provide the prompt with explicit placeholders and state what could not be verified.

If dashboard creation would mutate a connected PostHog project, state the dashboard name, intended tiles, and project before the write. Create only after the user's request clearly authorizes that mutation. Completion means either a verified dashboard URL/ID and tile list, or a ready prompt plus the exact missing capability.

### 3. Implement the measurement contract

Apply the following invariants; adapt names and code to the repository:

1. Capture pageviews and SPA route changes once on the marketing site and app. Respect consent before analytics capture and exclude internal/test traffic using the existing project convention.
2. Preserve immutable first-touch fields from the first eligible marketing landing:
   `first_touch_channel`, `first_touch_referrer`, `first_touch_referring_domain`, `first_touch_utm_source`, `first_touch_utm_medium`, `first_touch_utm_campaign`, `first_touch_landing_path`, and `first_touch_at`.
3. Normalize channels into a small documented enum: `organic_search`, `llm_referral`, `paid_search`, `paid_social`, `email`, `referral`, `social`, `direct`, and `other`. Keep the LLM matcher in one location. Start with the domains in the reference and extend it when observed data requires it.
4. Keep visitors anonymous until signup/login. Then identify with the stable internal user ID, use the same ID for server-side events, and reset on logout. Preserve first-touch values as immutable person properties or copy them onto conversion events so they remain queryable.
5. Emit `signup_started` and `signup_completed` from the actual signup flow. Emit `subscription_started`, `invoice_paid`, and `subscription_cancelled` from trusted backend/provider webhooks, never from browser-supplied amounts or plan state.
6. Verify webhook signatures and make billing emission idempotent using provider event IDs plus invoice/subscription IDs. Do not invent attribution when a billing record cannot be linked to an internal user.
7. Keep PII, secrets, raw payment data, and sensitive query-string values out of events. Add a “How did you first hear about us?” survey field when the product can support it; treat the answer as a triangulation signal, not ground truth.

Use the reference's canonical properties unless the codebase already has an equivalent. Completion means the event triggers, source of truth, identity join, consent behavior, and idempotency behavior are documented and testable.

### 4. Build or hand off the dashboard

Discover the actual event/property taxonomy before creating insights. Map logical fields to the project rather than assuming names such as `signup_completed` exist. Prefer native event-based insights for the core dashboard so dashboard filters work consistently; use SQL or warehouse data only when the connected capability and schema make it necessary.

The default dashboard is “SEO & GEO Acquisition to Revenue”, with a 30-day date range and prior-period comparison where supported. It should cover:

- total traffic, SEO traffic, GEO/LLM-referral traffic, and trends;
- search-engine and LLM-source breakdowns for 14- and 30-day windows;
- SEO and GEO funnels from landing/session to signup, subscription, and paid invoice;
- separate signup, subscribed-user, and revenue trends using unique people and trusted invoice amounts;
- landing-page tables for sessions, signups, subscriptions, conversion rates, and revenue;
- monthly-by-page evolution and LLM-source × landing-page performance;
- filters for date, acquisition channel, landing path, referring domain, LLM source, and the configured unbranded proxy.

Never label homepage traffic as unbranded by default. If Search Console is connected, use its verified query dimension or an explicitly documented join. Otherwise use a maintained non-brand landing-path list and label every tile “unbranded SEO proxy.”

### 5. Validate and report

Test the path `anonymous visit -> acquisition -> signup -> identify -> trusted subscription -> invoice_paid` in a safe environment. Check consent gating, duplicate pageviews/events, cross-subdomain continuity, logout reset, webhook retries, revenue deduplication, and absence of PII. Where live PostHog access exists, verify representative events and the created dashboard; otherwise state the unverified boundary.

Return:

- changed files or audit findings;
- final event/property schema and attribution definitions;
- test or verification evidence;
- dashboard ID/URL and tile summary, or the PostHog AI prompt and missing-access note;
- caveats for query-level unbranded SEO, LLM undercounting, and first-touch causality.

Read [references/event-and-dashboard-spec.md](references/event-and-dashboard-spec.md) when you need the canonical event schema, LLM domain list, implementation prompt, dashboard prompt, or MCP write checklist.
