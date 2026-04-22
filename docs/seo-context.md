# SEO Context Skill

## What it does

`seo-context` creates or updates a reusable `.agents/seo-context.md` file for a project.

The goal is simple: other SEO skills should stop re-asking for the same site, market, competitor, and tooling basics every time a new task starts.

## Main files

| File | Responsibility |
| --- | --- |
| `seo-context/SKILL.md` | Defines the workflow for discovering, creating, and updating shared SEO context. |
| `seo-context/references/context-template.md` | Provides the concrete structure for `.agents/seo-context.md`. |
| `README.md` | Documents the new skill and recommends using it first in multi-step SEO workflows. |

## Main flow

1. Check whether `.agents/seo-context.md` already exists.
2. If it exists, read and update only the missing or stale sections.
3. If it does not exist, inspect repo materials like `README.md`, `docs/`, and product or strategy files before asking the user repeated questions.
4. Save a concise shared context file that downstream SEO skills can read first.
5. Ask follow-up questions only for task-specific gaps after the shared context has been reused.

## Shared fields

The context file is designed to capture:

- site basics
- SEO goals and conversions
- audience and market targets
- priority pages and topic clusters
- competitive context
- tooling and data access
- technical and content constraints

## Downstream usage

These skills now explicitly check `.agents/seo-context.md` first:

- `programmatic-seo`
- `search-intent-coverage`
- `subkeyword-injector`
- `seo-roast`
- `linking-opportunities`
- `illustration-ideas`
- `seo-audit-report`
- `geo-audit-report`

## Why this matters

This gives the repo a shared foundation similar to how broader skill libraries use a product-context skill, but keeps it SEO-native and lightweight.
