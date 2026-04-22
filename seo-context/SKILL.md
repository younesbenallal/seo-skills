---
name: seo-context
description: Create or update a reusable SEO context file for a site, product, or content program. Use when the user wants to avoid repeating SEO fundamentals across tasks, or when they mention SEO context, site context, content context, target market, priority pages, competitors, or tooling setup. Other SEO skills should read this context first before asking for basics again.
---

# SEO context

You help the user create and maintain a reusable SEO context document for a project.

The document lives at `.agents/seo-context.md`.

Other SEO skills should read this file first, then ask only for task-specific details that are still missing.

## When to use this

Use this skill when:
- the user is starting SEO work on a new project
- the user is tired of repeating the same SEO basics across tasks
- multiple SEO tasks will be run against the same site
- the user wants a reusable brief for markets, competitors, priorities, and tooling

## Tooling & credentials

- Auth mode: `none`
- Requires: no external credential
- Fallback: none

Follow the shared setup and missing-access rules in `docs/credentials-and-tooling.md` when recording downstream tool availability in the context file.

## Workflow

### 1) Check for existing context first

Look for:
- `.agents/seo-context.md`
- older or alternative project docs that already contain the same information:
  - `README.md`
  - `docs/`
  - strategy notes in the repo
  - product or marketing docs

If `.agents/seo-context.md` already exists:
- read it
- summarize what is already captured
- update only the stale or missing sections

If it does not exist:
- gather what you can from the repo first
- only then ask the user for missing information

### 2) Gather the minimum useful shared context

Capture the information that many SEO tasks reuse:

1. Site and business basics
- brand or project name
- primary domain
- site type: SaaS, marketplace, media site, ecommerce, agency, local business, docs site
- short description of what the company offers

2. SEO goals
- main business goal from SEO
- primary conversions to drive
- top KPIs if known

3. Audience and market
- target audience or ICP
- country / language targets
- important regions or localization constraints

4. Priority surfaces
- top pages, templates, or sections that matter most
- priority content themes
- important queries or topic clusters if already known

5. Competitive context
- direct competitors
- comparison targets
- substitute workflows or alternatives

6. Tooling and data access
- browser tooling available
- SERP data source
- Search Console availability
- analytics / keyword tools available
- any hard constraints around access

7. Content and technical constraints
- CMS or framework if known
- tone or brand constraints
- approval constraints
- markets or compliance concerns that affect content

### 3) Reuse repo context before asking the user

Before asking questions, inspect:
- `README.md`
- `docs/`
- page templates or content directories
- existing SEO notes or exported audits
- any obvious product, ICP, or competitor references

Do not ask the user for information that is already easy to infer from the project.

### 4) Create or update the context file

Use the template in `references/context-template.md`.

Keep the document practical:
- concise
- easy for another SEO skill to scan quickly
- focused on facts that affect execution

### 5) Tell downstream skills how to use it

When this context file exists, other SEO skills should:
- read `.agents/seo-context.md` first
- skip repeated discovery questions when the answers are already there
- ask only for missing task-specific inputs

## Output requirements

After creating or updating the file:
- summarize what was added or changed
- call out the most important missing fields, if any
- tell the user that other SEO skills can now reuse this context automatically

## References

- Use `references/context-template.md` for the exact structure
