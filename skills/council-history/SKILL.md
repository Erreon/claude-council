---
name: council-history
description: Use when the user wants to review, recap, archive, or clean up past council sessions. Invoked with /council-history or when the user says "council history", "past councils", "recap councils", "clean up council", "archive council", etc.
---

# Council History

Browse, recap, archive, and clean up saved council sessions.

## Storage Locations

- **Working data (JSON):** `~/.claude/council/sessions/` — auto-saved checkpoints from every council session. Contains full agent responses, metadata, and round history.
- **Archive (Markdown):** `~/Documents/council/` — permanently saved sessions the user explicitly chose to keep. Human-readable, shareable.

## CLI Acceleration (Optional)

The council CLI helper can handle session operations directly. Detect availability once at the start:

```bash
if [ -n "$CLAUDE_PLUGIN_ROOT" ] && python3 "$CLAUDE_PLUGIN_ROOT/skills/council/council_cli.py" --version >/dev/null 2>&1; then
    COUNCIL_CLI="$CLAUDE_PLUGIN_ROOT/skills/council/council_cli.py"
elif python3 "$HOME/.claude/skills/council/council_cli.py" --version >/dev/null 2>&1; then
    COUNCIL_CLI="$HOME/.claude/skills/council/council_cli.py"
else
    COUNCIL_CLI=""
fi
```

**CLI paths:**
- **List sessions:** `python3 "$COUNCIL_CLI" session list`
- **Load session:** `python3 "$COUNCIL_CLI" session load --id "SESSION_ID"`
- **Rate session:** `python3 "$COUNCIL_CLI" session rate --id "SESSION_ID" --rating N`
- **Annotate outcome:** `python3 "$COUNCIL_CLI" session outcome --id "SESSION_ID" --status "..." --note "..."`

## Flow

### 1. List Sessions

**If CLI available:** `python3 "$COUNCIL_CLI" session list` — returns JSON with a `sessions` array. Format into the table below.

**Otherwise:** Read all JSON files from `~/.claude/council/sessions/` and present a summary table:

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

When recapping a session, present it concisely. Sessions may use either old-format keys (`codex`, `gemini`, `claude`) or new-format keys (`advisor_1`, `advisor_2`, `advisor_3`).

**Key format detection:** Check the session's `personas` object. If it has keys like `codex`/`gemini`/`claude`, use provider names as labels. If it has keys like `advisor_1`/`advisor_2`/`advisor_3`, check the `labels` object for display names (fallback to "Advisor 1/2/3" if no labels).

---

**Council Session: [Topic]** — [Date]

**Question:** [Original question]

**Rounds:** [N]

**Final positions:**
- **[Advisor 1 display name]:** [1 sentence]
- **[Advisor 2 display name]:** [1 sentence]
- **[Advisor 3 display name]:** [1 sentence]

For old sessions: display names are "Codex", "Gemini", "Claude".
For new sessions with all-same labels: display names are the persona names.
For new sessions with different labels: display names are "Label as Persona".

**Outcome:** [Consensus / Split / Debate escalated] — [1-2 sentence summary of where it landed]
[**Result:** [status] — [note] (if outcome annotation exists)]
**Rating:** [N/5 or "Unrated"]

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
