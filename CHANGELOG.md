# Changelog

How Claude Council evolved from a simple multi-model experiment to a full deliberation system with institutional memory. Each iteration was driven by real usage — running sessions about backyard chickens, app revenue strategy, local LLM setups, and more — and watching where the system fell short.

---

## The Beginning — v0.1.0 (January 31, 2026)

The initial idea was straightforward: what if you could ask the same question to Codex, Gemini, and Claude simultaneously and get a synthesized answer? Not just three separate opinions, but a briefing that identified where they agreed, where they disagreed, and what the actual decision point was.

The first version shipped with three skills:

- **`/council`** — The core loop. Frame a question, dispatch to three CLI tools, synthesize.
- **`/council-debate`** — Structured adversarial deliberation with assigned positions and rebuttals.
- **`/council-history`** — Browse, recap, and resume past sessions.

The key design choices that stuck from day one:

**Personas over prompts.** Instead of sending the same prompt to all three agents, each gets a persona (The Contrarian, The Pragmatist, The User Advocate, etc.) that shapes how they approach the question. This creates productive friction by design — you're not hoping for disagreement, you're engineering it.

**Context isolation.** The entire dispatch runs inside a Task subagent. Raw agent responses (~1500+ words each) never enter the main conversation. Only the final briefing (~300 words) makes it back. This prevents long council sessions from blowing up context windows.

**Institutional memory.** Before each session, the mediator scans past session files for relevant history and includes it in agent prompts. The council can reference what it said last time about a similar topic rather than starting from scratch.

**Persona catalog.** 18 personas total — 3 core (always available), 9 specialist (auto-assigned by topic), 6 fun (manual activation only). Topic detection maps questions to persona combinations: architecture questions get Contrarian + Pragmatist + Systems Thinker, business questions get Contrarian + Economist + Risk Analyst, and so on.

The first sessions worked, but immediately exposed problems.

---

## Fixing Real-World Breakage — v0.2.0 (January 31, 2026)

Running actual sessions on a MacBook revealed that launching all three CLI tools simultaneously was a bad idea. The `claude` CLI is heavy — when it competed with Codex and Gemini for resources, timeouts became common and the machine would lock up.

**Dispatch modes.** Added `--mode` with three options: `parallel` (all at once — fast machines only), `staggered` (Codex + Gemini together, Claude after they finish — the new default), and `sequential` (one at a time — for when everything else fails). Staggered mode solved most timeout issues because the heaviest process runs alone.

**Timeout reduction.** Dropped the per-agent timeout from 120s to 60s. The old timeout was masking resource contention rather than surfacing it.

**Codex fix.** The Codex CLI was failing in non-git directories because it defaults to checking the git repo. Added `--skip-git-repo-check` to the exec command.

The other addition in this release was less about fixing problems and more about making the system fun to use:

**Fun personas.** Six chaotic personas — The Jokester (comedy roast), The Trickster (counterintuitive advice), The Cheater (every shortcut and loophole), The Conspiracy Theorist (paranoid pattern matching), The Time Traveler (answers from 10 years in the future), and The Intern (devastatingly insightful "dumb" questions). Activated with `--fun`, which randomly replaces one council seat with a fun persona. They still try to be useful — just through an unhinged lens.

At this point the system was usable and sessions were producing genuinely useful output. But the output format was too loose, and there was no way to close the feedback loop.

---

## Structured Output & Feedback Loops — v0.3.0 (February 1, 2026)

After running about a dozen sessions across different topics, patterns emerged in what made a briefing useful vs forgettable. The good briefings had clear disagreements and actionable next steps. The bad ones had vague synthesis that smoothed over the interesting tensions.

**Evidence tagging.** Agents now tag each key claim as `[ANCHORED]` (based on data/evidence), `[INFERRED]` (logical deduction), or `[SPECULATIVE]` (opinion/gut feel). This surfaces when the council is confidently agreeing on something nobody actually has evidence for.

**Evidence Audit.** The synthesis includes an audit section. If consensus rests primarily on speculative claims, it gets flagged: "consensus is speculative — no advisor provided anchored evidence." This is the system watching itself for overconfidence.

**Disagreement Matrix.** A table showing each advisor's 2-5 word position on each key issue, side by side. Makes it immediately obvious where they agree and where they diverge, without reading paragraphs. Also notes when disagreements stem from persona framing vs genuine analytical divergence.

**What To Do Next.** 2-3 concrete action items, each starting with a verb. Not summaries — things the user should actually go do. This was the biggest quality-of-life improvement. Previous briefings would end with a nuanced synthesis that left the user thinking "okay but what do I actually do?"

**Key Tension.** A single paragraph framing the core unresolved trade-off as a clear choice. Not "it depends" — a decision the user needs to make, with the stakes clearly stated.

**RECOMMENDATION lines.** Each advisor ends with a single sentence starting with "RECOMMENDATION: I recommend..." Forces each agent to commit to a position rather than hedging.

### Closing the Feedback Loop

The historian was surfacing past sessions, but had no way to know which ones were actually useful. Bad advice surfaced with the same weight as good advice.

**Session ratings.** Users can rate sessions 1-5 after a briefing. The historian weights relevance by rating — a 5-star session with keyword matches ranks above a 1-star session with the same matches. Unrated sessions default to 3/5.

**Outcome tracking.** After council advice plays out in practice, users annotate what happened: `followed` (advice worked), `partial` (mixed results), `ignored` (didn't follow it), or `wrong` (followed it and it failed). Outcomes feed back into historian weighting — `followed` gets a 1.2x boost, `wrong` gets a 0.5x penalty. This compounds with ratings, so a highly-rated session that was later proven wrong gets demoted.

**Pattern detection.** If multiple sessions on similar topics have `wrong` outcomes, the mediator flags it in the briefing. The council can confidently repeat mistakes without this.

### Similarity Detection

Running the council on straightforward questions sometimes produced three agents saying basically the same thing. Different models, same conclusion — which meant the personas weren't creating enough divergence for that topic.

**Jaccard similarity check.** Before synthesis, agent responses are compared by keyword overlap. If two advisors exceed 60% overlap, a warning is displayed suggesting more diverse personas or a rephrased question. This addresses the council's own feedback (from a meta-session about improving the council) that multi-model doesn't guarantee diverse perspectives.

### Targeted Drill-Downs

Follow-up replies were always full re-dispatches — every advisor weighing in again on the user's pushback. But often the user only cared about one specific part of the briefing.

**Targeted follow-ups.** "Tell me more about the key tension" routes all advisors to elaborate on that specific point. "I disagree with Codex" routes to just that advisor for deeper explanation. "Debate the key tension" suggests escalation to `/council-debate`. More focused prompts produce more useful responses.

### Debate Session Persistence

Debate sessions (`/council-debate`) weren't saving to disk. This meant the historian couldn't find past debates, and `/council-history` couldn't list them. If you debated "Redis vs Memcached" last week and then asked `/council` about caching, the historian had no memory of it.

**Shared storage.** Debates now save JSON checkpoints to the same `~/.claude/council/sessions/` directory as council sessions, with `"type": "debate"` to distinguish them. The historian finds both. `/council-history` lists both. Debates also gained a historian check of their own — they check for related past sessions before framing positions.

---

## CLI Helper & Plugin System — v1.0.0 (February 1, 2026)

By this point the skills were doing a lot of mechanical work that didn't need LLM intelligence: parsing flags, looking up persona definitions, building prompts from templates, doing keyword matching for the historian, managing session files. Every time the LLM did these operations, it spent tokens on work that had a deterministic correct answer and occasionally got slightly different results.

### CLI Helper (`council_cli.py`)

A single Python file (~450 lines, stdlib only) that lives alongside the skill. The skill detects if Python 3 and the file are available, then delegates mechanical operations to it. If either is missing, everything falls back to the existing LLM-based processing — the skill works identically either way.

**Subcommands:** `parse` (extract flags from command string), `topic` (classify question), `assign` (map personas to agents), `prompt` (build agent prompts from templates), `synthesis-prompt` (build the mediator prompt), `session` (create/load/append/list/rate/outcome), `historian` (find related sessions with rating/outcome weighting), `similarity` (Jaccard similarity check).

All subcommands output JSON to stdout. No pip, no venv, no dependencies. Just needs Python 3.

The CLI embeds the full persona catalog, topic-to-persona mapping, stop words, and prompt templates. When the skill calls `assign --question "Should we use Redis?"`, the CLI does the keyword matching, picks the right personas, handles `--fun` injection, maps them to agents, and returns structured JSON. Zero tokens spent.

### Plugin Marketplace Support

The project started as a manual install — clone the repo, run `install.sh`, skill files get symlinked to `~/.claude/skills/`. That works, but Claude Code has a plugin system that handles installation, updates, and discovery.

**Plugin manifest.** Added `.claude-plugin/plugin.json` with metadata and a SessionStart hook that creates session directories automatically. No post-install scripts needed.

**Marketplace catalog.** Added `.claude-plugin/marketplace.json` so the repo works as a marketplace source. Users add it with `/plugin marketplace add Erreon/claude-council` and install with `/plugin install`.

**SKILL.md rename.** The plugin system expects `SKILL.md` (uppercase), not `skill.md`. Renamed in all three skill directories.

**Dual-path CLI detection.** The skill now checks both `$CLAUDE_PLUGIN_ROOT/skills/council/council_cli.py` (plugin install) and `$HOME/.claude/skills/council/council_cli.py` (manual install) when looking for the CLI helper.

**Three install methods, same skills:**

| Method | Slash command | How it works |
|--------|-------------|--------------|
| Plugin install | `/claude-council:council` | `/plugin marketplace add` + `/plugin install` |
| Script install | `/council` | `./install.sh` (symlinks by default, `--copy` for independent files) |
| Manual copy | `/council` | Copy files yourself |

All three support natural language triggering — "ask the council about X" works regardless of install method because Claude matches intent to the skill's `description` field in the frontmatter.

### Install Script Improvements

The install script was upgraded alongside the plugin work:

- **Symlink by default.** Edits in the repo or the install directory stay in sync. Better for development.
- **`--copy` flag.** For users who don't want to keep the repo cloned.
- **Python 3 check.** Informational only — logs whether the CLI helper will be active, doesn't block installation.

---

## What's Next

The system is stable and producing useful output. Open areas for future work:

- **More agent backends.** Ollama for local models, Perplexity if they ship a CLI, any LLM with a command-line interface.
- **Confidence calibration.** Track whether `[SPECULATIVE]` claims turn out to be right or wrong over time.
- **Cross-session patterns.** Detect when the council keeps giving the same type of advice on similar topics and flag it.
- **Richer historian.** Semantic similarity instead of just keyword matching for finding related sessions.
