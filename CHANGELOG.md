# Changelog

All notable changes to Claude Council are documented here.

## [1.0.0] - 2026-02-01

### Plugin System
- Added `.claude-plugin/plugin.json` manifest for Claude Code plugin marketplace compatibility
- Added `.claude-plugin/marketplace.json` so the repo works as both a plugin and a marketplace source
- Added `hooks/sessions-init.sh` SessionStart hook to auto-create session directories on first use
- Renamed `skill.md` to `SKILL.md` in all skill directories to match plugin conventions
- Three install methods: plugin (`/plugin install`), script (`./install.sh`), manual copy
- Plugin skills namespaced as `/claude-council:council`, `/claude-council:council-debate`, `/claude-council:council-history`
- Natural language triggering ("ask the council") works with all install methods

### CLI Helper (`council_cli.py`)
- Added `skills/council/council_cli.py` — single-file, stdlib-only Python CLI for deterministic logic
- Subcommands: `parse`, `topic`, `assign`, `prompt`, `synthesis-prompt`, `session` (create/load/append/list/rate/outcome), `historian`, `similarity`
- All output is JSON to stdout; errors to stderr
- No external dependencies — Python 3 standard library only
- Skill auto-detects CLI availability and falls back to LLM-based processing if absent
- CLI detection supports both plugin (`$CLAUDE_PLUGIN_ROOT`) and manual install (`~/.claude/skills/`) paths

### Structured Briefing Format
- Agent responses now include evidence tagging: `[ANCHORED]`, `[INFERRED]`, `[SPECULATIVE]`
- Each advisor ends with a `RECOMMENDATION:` line
- Briefings include **Evidence Audit** flagging speculative consensus
- Briefings include **What To Do Next** with concrete, verb-first action items
- Briefings include **Disagreement Matrix** table showing each advisor's position per issue
- Briefings include **Key Tension** identifying the core trade-off the user needs to decide

### Rating and Outcome Tracking
- Users can rate sessions 1-5 (`/rate N`)
- Users can annotate outcomes: `followed`, `partial`, `ignored`, `wrong`
- Historian weights past sessions by rating (unrated defaults to 3/5)
- Historian weights by outcome (followed: 1.2x boost, wrong: 0.5x penalty)
- Outcome annotations included in Prior Council Context when relevant

### Similarity Detection
- Agent responses checked for Jaccard similarity before synthesis
- Warning displayed when two advisors exceed 60% keyword overlap
- Helps identify when different models converge on the same heuristics

### Targeted Drill-Downs
- Follow-up replies can reference specific briefing sections for focused re-dispatch
- "Tell me more about the key tension" routes to all advisors on that specific point
- "I disagree with Codex" routes to that specific advisor for deeper explanation
- "Debate the key tension" suggests escalation to `/council-debate`

### Debate Session Saving
- `/council-debate` sessions now save JSON checkpoints to `~/.claude/council/sessions/`
- Debate sessions use `"type": "debate"` to distinguish from council sessions
- Historian can find past debates when checking for related sessions
- `/council-history` lists both council and debate sessions

### Install Script Improvements
- Default mode changed to symlink (edits in repo or install dir stay in sync)
- Added `--copy` flag for independent file copies
- Added `council_cli.py` to installed files
- Added Python 3 availability check (informational, not blocking)

## [0.2.0] - 2026-01-31

### Dispatch Modes
- Added `--mode` flag: `parallel`, `staggered` (default), `sequential`
- Staggered mode launches Codex + Gemini together, then Claude separately
- Reduces resource contention on machines where parallel causes timeouts

### Fun Personas
- Added 6 fun personas: The Jokester, The Trickster, The Cheater, The Conspiracy Theorist, The Time Traveler, The Intern
- Added `--fun` flag to randomly inject one fun persona into a council session
- Fun personas never auto-assigned — only via `--fun` or explicit `--personas`

### Bug Fixes
- Added `--skip-git-repo-check` to codex exec command to prevent git-related failures
- Reduced agent timeout from 120s to 60s to avoid resource contention lockups

## [0.1.0] - 2026-01-31

### Initial Release
- Three skills: `/council`, `/council-debate`, `/council-history`
- Three external AI agents: Codex (OpenAI), Gemini (Google), Claude (Anthropic)
- 18 personas: 3 core, 9 specialist, 6 fun
- Automatic persona assignment based on topic classification
- Manual persona override with `--personas` flag
- Historian role: mediator checks past sessions for relevant context
- JSON session auto-save after every synthesis round
- Markdown archive export to `~/Documents/council/`
- Context isolation: council dispatch runs in Task subagent
- Follow-up rounds without re-invoking `/council`
- Consensus detection with `/council-debate` escalation suggestion
- Structured debate with opening arguments, rebuttals, and verdict
- Session management: list, recap, archive, delete, resume
- `install.sh` for automated setup
