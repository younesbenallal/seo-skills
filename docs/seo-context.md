# SEO Context Skill

## What it does

`seo-context` creates or updates a reusable `.seo-context.md` file in the project root.

The goal is simple: other SEO skills should stop re-asking for the same site, market, competitor, and tooling basics every time a new task starts.

## Main files

| File | Responsibility |
| --- | --- |
| `seo-context/SKILL.md` | Defines the workflow for discovering, creating, and updating shared SEO context. |
| `seo-context/references/context-template.md` | Provides the concrete structure for `.seo-context.md`. |
| `README.md` | Documents the new skill and recommends using it first in multi-step SEO workflows. |

## Main flow

1. Check whether `.seo-context.md` already exists.
2. If it exists, read and update only the missing or stale sections.
3. If it does not exist, inspect repo materials like `README.md`, `docs/`, product or strategy files, and connected Search Console data before asking the user repeated questions.
4. On the first run, inspect callable tools, save the reusable tooling inventory, and ask the user whether other tools or connectors should be recorded.
5. Save a concise shared context file that downstream SEO skills can read first.
6. Ask follow-up questions only for task-specific gaps after the shared context has been reused.

## Shared fields

The context file is designed to capture:

- site basics
- SEO goals and conversions
- audience and market targets
- a money-page keyword table mapping each page slug or title to its target keyword or keywords
- a topical cluster map connecting hubs, money pages, supporting content, gaps, and high-click organic pages from Search Console when available
- a reusable tooling inventory with check dates and agent-observed or user-reported statuses
- competitive context
- separate direct/business competitors from SEO competitors, with the latter backed by recurring top-10 Google results for a small keyword set
- tooling and data access
- technical and content constraints

## Downstream usage

These skills now explicitly check `.seo-context.md` first:

- `programmatic-seo`
- `search-intent-coverage`
- `subkeyword-injector`
- `seo-roast`
- `linking-opportunities`
- `guest-post-outreach`
- `illustration-ideas`
- `seo-audit-report`
- `geo-audit-report`
- `competitor-intelligence`
- `internal-linking`
- `article-writing`

## Why this matters

This gives the repo a shared foundation similar to how broader skill libraries use a product-context skill, but keeps it SEO-native and lightweight.
