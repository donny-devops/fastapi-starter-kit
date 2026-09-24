# Granola (granola-engineer)

Your meetings in your workflow.

This is the project-local Cursor plugin for [Granola](https://granola.ai). It gives the agent access to what the team discussed, decided, and committed to in meetings — and ships the **granola-engineer** agent that anchors implementation choices to that context.

Source: adapted from [granola-inc/granola-cursor-plugin](https://github.com/granola-inc/granola-cursor-plugin) for this starter kit.

## Setup

1. Open this repository in Cursor.
2. The plugin lives at `.cursor/plugins/granola/` and is discovered as a local plugin.
3. Workspace MCP is also declared in `.cursor/mcp.json`. The first time you use a Granola tool, sign in via the browser. You need a [Granola](https://granola.ai) account with meeting data.

You can also install the published plugin from the [Cursor Marketplace](https://cursor.com/marketplace/granola).

## What's included

### Agent

**`/granola-engineer`** — A decisions-aware assistant that anchors implementation choices to meeting context. It cites meetings when justifying decisions, flags when you're building something that wasn't discussed, and surfaces contradictions between meetings.

### Skills

Skills are loaded autonomously — the agent decides when to use them based on what you're doing. You don't need to invoke them.

| Skill | Description |
| --- | --- |
| `granola-context` | Look up what was discussed or decided. |
| `granola-review` | Check work against meeting decisions before submitting. |
| `granola-prep` | Prepare for an upcoming meeting from prior calls on the same topic or with the same people. |

### Commands

Commands are invoked manually with `/` and produce a document you keep.

| Command | Description |
| --- | --- |
| `/granola-plan` | Prioritized build plan from recent meeting decisions and action items. |
| `/granola-spec` | Structured spec from meeting discussions, traced to specific meetings. |
| `/granola-brief` | Briefing that synthesizes a topic across meetings. |
| `/granola-bug-report` | Structured bug report from a walkthrough call. |
| `/granola-pr` | PR description grounded in meeting decisions. |
| `/granola-gaps` | Meeting decisions that have not shown up in code yet. |

### Rule

`check-meeting-context` is always on. It nudges the agent to check Granola when you are implementing features or making decisions — without you having to ask.

### MCP tools

The plugin connects to Granola's MCP server at `https://mcp.granola.ai/mcp`:

- `query_granola_meetings` — semantic search across meetings
- `list_meetings` — browse meetings by date range or folder
- `list_meeting_folders` — discover folder IDs, titles, descriptions, and note counts
- `get_meetings` — retrieve detailed meeting info by ID
- `get_meeting_transcript` — full transcript with speakers

## Layout

```
.cursor/plugins/granola/
├── .cursor-plugin/plugin.json
├── mcp.json
├── agents/granola-engineer.md
├── skills/granola-context|granola-prep|granola-review/SKILL.md
├── commands/granola-*.md
├── rules/check-meeting-context.mdc
├── README.md
├── CHANGELOG.md
└── LICENSE
```
