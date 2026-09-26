# Granola Engineer

A Cursor plugin for this FastAPI starter kit. It adds a **granola-engineer**
agent that checks Granola meeting notes before implementation choices, plus
the Granola MCP server.

This is a **thin overlay**, not a fork of the [official Granola plugin](https://github.com/granola-inc/granola-cursor-plugin).
Install Granola from the Cursor Marketplace if you also want `/granola-plan`,
`/granola-spec`, and the rest of that suite.

## What it includes

| Path | Role |
| --- | --- |
| `agents/granola-engineer.md` | Subagent: cite meetings, flag gaps, respect this kit's sqlite3 baseline |
| `commands/granola-engineer.md` | Slash command `/granola-engineer` |
| `skills/granola-engineer/` | Loaded when a task looks like it came from a meeting |
| `rules/check-meeting-context.mdc` | Always-on nudge to query Granola on non-trivial work |
| `mcp.json` | Remote MCP at `https://mcp.granola.ai/mcp` |

## Install

**This repository (already wired):** clones pick up `.cursor/agents` and
`.cursor/mcp.json`. The first Granola tool call prompts browser sign-in.

**As a Cursor plugin:**

1. Cursor **Customize** → install from this folder, or add a team marketplace
   that points at [`.cursor-plugin/marketplace.json`](../../.cursor-plugin/marketplace.json).
2. Local live reload: copy or symlink this directory to
   `~/.cursor/plugins/local/granola-engineer` and reload the window.

You need a [Granola](https://granola.ai) account with meeting notes. If MCP is
not signed in, the agent must say so and follow [docs/PLATFORM_BASELINE.md](../../docs/PLATFORM_BASELINE.md).

## Layout

```
plugins/granola-engineer/
├── .cursor-plugin/plugin.json
├── mcp.json
├── agents/granola-engineer.md
├── commands/granola-engineer.md
├── skills/granola-engineer/SKILL.md
├── rules/check-meeting-context.mdc
├── assets/logo.svg
└── README.md
```
