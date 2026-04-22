# Credentials And Tooling

This repo now uses one shared contract for tools, MCPs, and credentials.

The goal is to keep three things consistent across every skill:

- users get one clear setup path
- skills follow the same behavior when access is present or missing
- secrets stay on the user's machine and never in chat

## Core rules

Every skill should follow these rules:

1. Check whether the required tool or credential is already available before asking the user to do anything.
2. Never ask the user to paste secrets in chat.
3. Never print or echo secret values.
4. If setup is missing, stop and give the user exact next steps.
5. After the user confirms setup, verify presence only and continue.
6. Prefer MCP-managed auth over repo-local secret handling whenever an MCP is the intended integration path.
7. Do not invent a fallback auth mode unless the skill explicitly supports one.

## Auth modes

Use one of these four auth modes in each skill.

| Auth mode | Meaning | Typical examples |
| --- | --- | --- |
| `none` | No external auth required | local analysis, scaffolding, writing |
| `mcp` | Access comes from an MCP the user installs and configures outside the repo | SERP API MCP, GSC MCP |
| `env` | The user sets one or more local environment variables | `BRIGHTDATA_API_KEY` |
| `manual-file` | The user provides a local export or config file instead of live auth | CSV/JSON export |

## Universal runtime contract

Every skill should behave like this:

### If access is already available

- continue immediately
- mention briefly what was detected
- do not re-explain setup unless the user asks

### If access is missing

- stop before the dependent workflow starts
- tell the user exactly what is missing
- tell them exactly how to set it up
- tell them what to say when they are ready
- resume only after confirmation

### If the skill supports a fallback

- offer only the documented fallback for that skill
- make the tradeoff explicit
- do not silently switch data sources

## User instructions

Use direct, plain-English setup steps. The user should never have to infer what to do next.

Recommended structure:

1. Explain what the skill needs.
2. Explain whether the user must install an MCP or set a local env var.
3. Give the exact command or action.
4. Ask the user to confirm when it is ready.

## Standard wording

### Missing MCP

Use wording like:

```text
This skill needs a configured <TOOL NAME> MCP before it can continue.
Please install or connect that MCP in your agent, then tell me when it's ready.
I will verify that the tool is available and continue from there.
```

### Missing env var

Use wording like:

```text
This workflow needs <ENV_VAR_NAME>, but it is not available in the current shell.
Please set it locally in your terminal instead of pasting it here:

export <ENV_VAR_NAME>="your-secret-here"

When that's done, tell me and I'll verify only that it is set.
```

### Manual-file fallback

Use wording like:

```text
If you do not want to connect live access, you can provide a local export instead.
Share the file path for the CSV or JSON export and I will continue with that input.
```

## Tool-specific setup

### Browser access

Preferred path:

- use a Browser, Chrome, or Playwright MCP if the user already has one
- otherwise use `agent-browser`

User setup:

```bash
agent-browser --help
```

If missing:

```bash
npm install -g agent-browser
```

Agent behavior:

- prefer MCP if present
- otherwise use `agent-browser`
- if neither path is available, ask the user to provide content manually

### SERP API MCP

Used by:

- `linking-opportunities`
- `search-intent-coverage`
- optionally `seo-roast`
- optionally `programmatic-seo`

User setup:

- install and configure a SERP provider MCP in the agent

Agent behavior:

- if present, use it
- if missing, stop and ask the user to install/configure it
- do not invent an env-var fallback

### Google Search Console MCP

Used by:

- `subkeyword-injector`
- optionally `seo-audit-report` as an export source

User setup:

- install and configure a GSC MCP in the agent

Agent behavior:

- if present, use it
- if missing and the skill supports exports, offer CSV/JSON export as the fallback
- otherwise stop and ask the user to install/configure it

### Bright Data API

Used by:

- `geo-audit-report`

User setup:

```bash
export BRIGHTDATA_API_KEY="your-secret-here"
```

Agent behavior:

- verify only whether `BRIGHTDATA_API_KEY` is set
- never print the value
- if missing, stop and give the export command above

## Skill author checklist

Every skill that depends on tooling or credentials should include a short `Tooling & credentials` section with:

- auth mode
- required tools or env vars
- allowed fallback, if any
- what to do if missing

Suggested template:

```md
## Tooling & credentials

- Auth mode: `mcp` | `env` | `manual-file` | `none`
- Requires: `<tool name>` or `<ENV_VAR_NAME>`
- Fallback: `<fallback>` or `none`
- If missing: stop, give exact setup steps, and continue only after user confirmation
```

The detailed user setup should live in this doc and in the root `README.md`, not as repeated long-form prose inside every skill.
