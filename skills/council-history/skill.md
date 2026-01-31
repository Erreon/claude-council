---
name: council-history
description: Use when the user wants to review, recap, archive, or clean up past council sessions. Invoked with /council-history or when the user says "council history", "past councils", "recap councils", "clean up council", "archive council", etc.
---

# Council History

Browse, recap, archive, and clean up saved council sessions.

## Storage Locations

- **Working data (JSON):** `~/.claude/council/sessions/` — auto-saved checkpoints from every council session. Contains full agent responses, metadata, and round history.
- **Archive (Markdown):** `~/Documents/council/` — permanently saved sessions the user explicitly chose to keep. Human-readable, shareable.

## Flow

### 1. List Sessions

Read all JSON files from `~/.claude/council/sessions/` and present a summary table:

```
| # | Date       | Topic                        | Rounds | Archived |
|---|------------|------------------------------|--------|----------|
| 1 | 2026-01-31 | Backyard chickens            | 4      | No       |
| 2 | 2026-01-31 | Moving out of Louisiana      | 1      | No       |
| 3 | 2026-01-31 | Meeting scheduling agent     | 1      | Yes      |
```

Sort by date, most recent first.

### 2. User Actions

Present the user with options:

- **Recap [#]** — Show a concise summary of that session: the original question, final positions, key agreements/disagreements, and outcome. Pull from the JSON data.
- **Full [#]** — Show the complete session with all rounds and full agent responses.
- **Archive [#]** — Export the session as a formatted Markdown file to `~/Documents/council/` and mark it as archived in the JSON. If already archived, note it.
- **Delete [#]** — Delete the JSON session file from `~/.claude/council/sessions/`. If it's been archived, the Markdown in `~/Documents/council/` is preserved. If not archived, warn the user first: "This session hasn't been archived. Delete it anyway, or archive it first?"
- **Clean up** — Show all non-archived sessions and ask which ones to delete or archive. Good for periodic maintenance.
- **Continue [#]** — Resume a previous council session. Load the JSON context and treat the next user message as a follow-up reply, dispatching to all agents with the full history.

### 3. Recap Format

When recapping a session, present it concisely:

---

**Council Session: [Topic]** — [Date]

**Question:** [Original question]

**Rounds:** [N]

**Final positions:**
- **Codex:** [1 sentence]
- **Gemini:** [1 sentence]
- **Claude:** [1 sentence]

**Outcome:** [Consensus / Split / Debate escalated] — [1-2 sentence summary of where it landed]

---

### 4. Archive Format

When archiving to `~/Documents/council/`, create a Markdown file with:

- Title and date
- Original question
- Each round's full briefing as presented to the user
- Follow-up rounds with user pushback and position shifts
- Final mediator summary

Filename: `YYYY-MM-DD-[slug].md`

## Important Notes

- **Read-only by default:** This skill only reads and presents data unless the user explicitly asks to archive, delete, or clean up.
- **Non-destructive:** Archiving copies to `~/Documents/council/` — it never moves or deletes the JSON source. Only explicit "delete" removes JSON files.
- **Continue sessions:** When resuming a session, load the full JSON context and pass it to the council skill's follow-up flow. The user's next message becomes the follow-up prompt.
