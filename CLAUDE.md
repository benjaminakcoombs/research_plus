# Research Banking Boutique — Agent Entry Point

> **This file is a pointer.** All repo instructions, protocols, and conventions live in `.agent/config.md`.
> **IMPORTANT:** You MUST follow both the loading AND closing protocols below. Every session must update the session log, decisions, and index. No exceptions.

## Loading Protocol (start of every session)

1. **Read `.agent/config.md`** — repo instructions, conventions, maintenance rules
2. **Read `.agent/session-log.md`** — what happened last session and what to do next
3. **Read `.agent/index.md`** — file map, architecture summary, key entry points
4. **Read `.agent/decisions/decisions-key.md`** — quick reference for active decisions
5. **Load session-type-specific files** per the token budget table in `.agent/config.md`

## Closing Protocol (end of every session — MANDATORY)

1. **Update `.agent/session-log.md`** — what was done, files touched, decisions made, next priorities
2. **Sync decisions** — if ANY decisions were made, update BOTH `decisions-key.md` AND `decisions-full.md`
3. **Update `.agent/index.md`** — if any files were created, moved, or architecture changed
4. **Update `open-questions.md`** — if new questions surfaced or existing ones were resolved
