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
