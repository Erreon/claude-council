# TODO

## Clarifying Questions Mechanism

The council currently dispatches immediately without asking for clarification, even on ambiguous questions. The follow-up round handles this after the fact, but it wastes a dispatch round. Options to explore:

### Option A: Pre-Flight Check
Mediator asks 1-2 clarifying questions before dispatch if the question is ambiguous. Slower but better first-round quality. Breaks the current "just dispatch immediately" ethos.

### Option B: Post-Briefing Section
Dispatch immediately, but add a "What would sharpen this advice" section to the synthesis. Agents already sometimes say "it depends on X" — this formalizes it. No extra round-trip on simple questions, flags gaps on complex ones.

### Option C: Keep As-Is
The follow-up round system already handles this. User replies to the briefing, agents get the clarification in round 2. Simple, no new mechanism needed.

### Option D: Both Pre + Post
Pre-flight for obviously ambiguous questions (missing key context like budget, timeline, team size), post-briefing section for subtle gaps. Mediator uses judgment on when to ask vs when to dispatch.

## Update Notification

No mechanism exists for users to know a new plugin version is available. Third-party marketplaces don't auto-update, and the plugin update system has known bugs (cache not invalidated, files not re-downloaded). Options:

- Add version check to SessionStart hook (compare installed vs latest)
- Print one-liner at session start when update is available
- Recommend uninstall + reinstall as the reliable update path

## UX Gaps

Known friction points that don't have solutions yet.

### No Progress Feedback During Dispatch

When agents are running (10-60 seconds), the user sees a blank spinner with no indication of what's happening. No "Advisor 1 responded, waiting on 2 and 3..." — just silence. This is the biggest UX gap for new users who don't know if it's working or frozen. Unclear how to solve this given the subagent isolation model — the subagent can't stream partial output to the main conversation.

### Rating Has No Nudge

The historian feedback loop depends on users remembering to `/rate`, but nothing prompts them to do it. The rotating tips sometimes mention it, but that's passive. Options: add a "Was this useful? /rate 1-5" line to every briefing footer, or prompt after every Nth session. Risk: becomes annoying noise if overdone.

### No Single-Agent Retry

If one agent gives a garbage response or times out, the only option is re-running the entire council. There's no "re-run just Advisor 2" mechanism. Would need a way to load the session, identify which slot to re-dispatch, and splice the new response into the existing round before re-synthesizing.

### Pre-Research Not Discoverable

The mediator can do web searches and file reads before dispatch, feeding results as shared context to all agents. But nothing in the UX surfaces this — no flag, no help text, no prompt. Users would never know to say "research X first, then ask the council." Could be a `--research` flag or a mention in `/council-help`.

### ~~Session JSON Schema Drift~~ (Fixed)

Resolved: `normalize_legacy_keys()` in `council_cli.py` now handles `briefing` → `synthesis` rename, flattens `responses` arrays/dicts into `advisor_1/2/3` keys, and unwraps nested advisor objects into plain strings. `load_session()` calls normalization automatically so every read path gets clean data.

### Shell Escaping on Long Context

Agent prompts are passed through shell quoting (`echo "<PROMPT>" | codex exec`). Special characters, quotes, backticks, and large payloads can break dispatch. This is hard to fully solve since each CLI has different quoting rules. Potential mitigation: write prompts to temp files and pipe from file instead of inline echo.
