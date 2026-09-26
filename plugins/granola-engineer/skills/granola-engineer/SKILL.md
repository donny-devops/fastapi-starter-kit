---
name: granola-engineer
description: Anchor FastAPI starter-kit implementation to Granola meeting decisions. Use when building a feature, choosing architecture, writing a spec, or reviewing a PR that may have been discussed in a meeting.
---

# granola-engineer

Use this skill whenever the work might have come from a planning call, review,
or customer meeting.

## Steps

1. Derive a short search query from the task (feature name, endpoint, "sqlite",
   "OAuth", "Cloudflare", "CI", person names the user mentioned).
2. Call `query_granola_meetings` with that query.
3. If a specific meeting ID appears, use `get_meetings` (and
   `get_meeting_transcript` when wording matters).
4. Cite meetings inline. Preserve Granola citation links from the MCP response.
5. If nothing relevant is found, say so and follow the repo as it is:
   sqlite3, public CRUD, optional GitHub session OAuth, catalog `/ops` mesh.

## Do not

- Invent meeting decisions
- Treat `/ops/status` RPS figures as live Cloudflare Analytics
- Reintroduce SQLAlchemy or JWT unless the user or a meeting explicitly asked
