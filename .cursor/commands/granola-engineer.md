---
name: granola-engineer
description: Run implementation in granola-engineer mode. Ground the current FastAPI starter-kit task in Granola meeting decisions before coding.
---

# /granola-engineer

Switch into the granola-engineer agent for the current task.

1. Identify the feature, bug, or decision from the user request and the repo
   (routers, sqlite3 CRUD, optional GitHub OAuth, origin mesh, CI).
2. Search Granola with `query_granola_meetings`. If you need exact wording,
   follow up with `get_meeting_transcript`.
3. State what meetings (title + date) inform the work, or that none were found.
4. Implement against [docs/PLATFORM_BASELINE.md](docs/PLATFORM_BASELINE.md) and
   the current code. Do not add JWT or SQLAlchemy unless the meetings or the
   user asked for that.
5. After the change, note what is aligned with meetings, what is missing, and
   what is new.

If Granola MCP is unauthenticated or returns no notes, say so and continue from
the repository baseline.
