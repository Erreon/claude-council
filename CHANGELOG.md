# Changelog

How Claude Council evolved from a simple multi-model experiment to a full deliberation system with institutional memory. Each iteration was driven by real usage — running sessions about backyard chickens, app revenue strategy, local LLM setups, and more — and watching where the system fell short.

---

## The Beginning — v0.1.0

The initial idea was straightforward: what if you could ask the same question to Codex, Gemini, and Claude simultaneously and get a synthesized answer? Not just three separate opinions, but a briefing that identified where they agreed, where they disagreed, and what the actual decision point was.

The first version shipped with three skills — `/council` for the core dispatch-and-synthesize loop, `/council-debate` for structured adversarial deliberation, and `/council-history` for browsing past sessions.

The key design choices that stuck from day one: personas over prompts (engineering productive friction rather than hoping for it), context isolation (raw agent responses never enter the main conversation), institutional memory (the mediator checks past sessions before each new one), and a catalog of 18 personas across core, specialist, and fun categories.

The first sessions worked, but immediately exposed problems.

---

## Fixing Real-World Breakage — v0.2.0

Running actual sessions on a MacBook revealed that launching all three CLI tools simultaneously was a bad idea. The `claude` CLI is heavy — when it competed with Codex and Gemini for resources, timeouts became common and the machine would lock up.

Added dispatch modes so users can control how agents launch. Staggered mode (the new default) runs Codex and Gemini together, then Claude alone — solving most timeout issues. Also dropped per-agent timeout from 120s to 60s, which surfaced resource contention instead of masking it, and fixed Codex failing in non-git directories.

The other addition was six fun personas — The Jokester, The Trickster, The Cheater, The Conspiracy Theorist, The Time Traveler, and The Intern. They add chaos and humor while still trying to be useful. Activated with `--fun`, which randomly replaces one council seat.

At this point the system was usable. But the output format was too loose, and there was no way to close the feedback loop.

---

## Structured Output & Feedback Loops — v0.3.0

After about a dozen sessions, patterns emerged in what made a briefing useful vs forgettable. The good ones had clear disagreements and actionable next steps. The bad ones smoothed over the interesting tensions.

### Better Briefings

Added evidence tagging so agents mark claims as anchored (data-backed), inferred, or speculative. The synthesis now includes an evidence audit — if consensus rests on speculation, it gets flagged. This is the system watching itself for overconfidence.

Added a disagreement matrix (positions at a glance), concrete action items ("What To Do Next"), a key tension paragraph framing the core unresolved trade-off as a clear choice, and mandatory RECOMMENDATION lines forcing each agent to commit to a position.

### Feedback Loop

The historian was surfacing past sessions but had no way to know which ones were useful. Added session ratings (1-5) and outcome tracking (followed, partial, ignored, wrong). Both feed back into historian weighting — good advice surfaces more, proven-wrong advice fades. If multiple sessions on similar topics have `wrong` outcomes, the mediator flags it.

### Other Improvements

Added Jaccard similarity detection — if two advisors exceed 60% keyword overlap, a warning appears. Multi-model doesn't guarantee diverse perspectives, and this catches when it doesn't.

Added targeted follow-ups so users can drill into specific parts of a briefing instead of re-dispatching everyone.

Fixed debate sessions not saving to disk. Debates now share the same session storage as council sessions, so the historian finds both and `/council-history` lists both.

---

## CLI Helper & Plugin System — v1.0.0

By this point the skills were doing a lot of mechanical work that didn't need LLM intelligence: parsing flags, looking up persona definitions, building prompts from templates, keyword matching for the historian, managing session files. Every time the LLM did these operations, it spent tokens on work that had a deterministic correct answer.

### CLI Helper

Added `council_cli.py` — a single Python file (~450 lines, stdlib only) that lives alongside the skill. Handles all the deterministic operations: flag parsing, topic classification, persona assignment, prompt building, session CRUD, historian search, and similarity checking. The skill detects if Python 3 and the file are available and delegates to it. If either is missing, everything falls back to LLM-based processing — the skill works identically either way.

### Plugin Marketplace

Made the repo installable through Claude Code's plugin marketplace in addition to the existing install script. Added plugin manifest, marketplace catalog, renamed skill files to uppercase `SKILL.md` (plugin system requirement), and added dual-path CLI detection so skills find the helper regardless of install method.

### Install Script

Switched to symlinks by default (better for development), added `--copy` flag for standalone installs, and added an informational Python 3 check.

---

## Onboarding & Ease of Use — v1.1.0

The biggest complaint from new users was friction on first use: permission prompts on every `/council` invocation, no indication of what's installed, and Claude-only users having to manually switch configurations. This release fixes all of that.

### Auto-Detection

The council now auto-detects which agent CLIs are installed before every dispatch and adapts automatically:

- **All 3 available** — Normal multi-provider dispatch
- **Only Claude** — All 3 advisor slots dispatch to Claude. No config change needed.
- **2 of 3** — Uses what's available, fills the missing slot with a fallback, notes it in the briefing
- **0 available** — Shows setup instructions instead of failing silently

This means a user who installs the plugin with only Claude Code never needs to manually "switch to all-Claude mode" — it just works.

### Diagnostics

Added two new CLI helper subcommands:

- **`agents`** — Fast PATH check (`shutil.which` only). Returns which CLIs are available, their paths, and a mode suggestion. Runs automatically before every dispatch.
- **`doctor`** — Thorough health check that actually runs `--version` on each CLI, verifies session/archive directories, checks CLI helper locations, and reports Python version. For manual troubleshooting.

### Briefing Status Header

Council briefings now include an agent status line:

```
*Agents: Codex OK, Gemini OK, Claude OK | CLI Helper: Active | Mode: staggered*
```

Added `--agent-status` and `--mode` arguments to the `synthesis-prompt` subcommand to support this.

### Rich First-Run Output

Replaced the minimal "missing CLI tools" message in the SessionStart hook with a full diagnostic:

- Agent install status with checkmarks
- Mode suggestion based on what's detected
- Python and CLI helper status
- Copy-pasteable permissions block for `~/.claude/settings.json`
- Available commands quick reference
- Links to `doctor` and `agents` for future diagnostics

### Permission Prompt Reduction

The CLI detection and agent availability check are now combined into a single bash block (previously 2-3 separate calls, each triggering a permission prompt). The first-run output prominently explains which permissions to add to eliminate prompts entirely.

### Council-Debate Parity

The `/council-debate` skill now has the same auto-detection logic, so debates also adapt to whatever CLIs are installed.

---

## Tip Rotation & Quick Reference — v1.2.0

Users kept discovering features late — outcome tracking, fun mode, archiving — because they were buried in the skill files. This release surfaces those features directly in the output.

### Tip Rotation

Every council briefing and debate verdict now ends with a rotating tip:

```
> **Tip:** /rate 1-5 to rate this session — higher-rated advice surfaces more in future councils
```

Ten tips cover the features most likely to be missed: archiving, rating, outcome tracking, fun mode, custom personas, raw response viewing, and `/council-help`. The CLI helper picks tips randomly via `council_cli.py tip`; if the CLI isn't available, the mediator picks from an inline list in the skill file. Tips rotate so consecutive sessions show different ones.

### `/council-help`

New lightweight skill — no dispatch, no agents. Prints a cheat sheet covering all commands, flags, post-session actions, follow-up patterns, diagnostics, configuration switching, and the full persona catalog. Invoked with `/council-help` or by asking "how do I use the council?"

---

## Lifestyle Topics & New Personas — v1.3.0

The council was built for technical and business decisions, but users started asking it about restaurants, travel itineraries, puppy training, and workout routines. These all fell into the catch-all "personal" bucket and got assigned Contrarian + Pragmatist + Outsider — personas designed for career/life decisions, not for recommending a weekend in Portland.

### New Topic Categories

Broke the old "personal" category into meaningful lifestyle buckets:

- **travel** — trips, destinations, itineraries, hotels, road trips
- **food_drink** — restaurants, cuisine, bars, coffee, recipes, reservations
- **home_life** — pets, gardening, home improvement, decor, DIY
- **wellness** — fitness, nutrition, meditation, mental health, sleep
- **personal_finance** — budgeting, investing, retirement, debt, taxes
- **learning** — courses, certifications, hobbies, reading lists, skill-building

The original "personal" category is now narrowed to career and life decisions (quit your job, relocate, freelance vs full-time). Keywords that belonged in the new categories were moved out.

### New Specialist Personas

Three new personas designed for experiential and recommendation queries:

- **The Curator** — Opinionated and taste-driven. Makes specific, ranked picks with clear reasoning. Allergic to generic top-10 lists and tourist-trap recommendations. Auto-assigned for food, drink, travel, and entertainment queries.
- **The Insider** — Deep domain and local knowledge. Knows what's real vs. hype, what locals actually do, and what the algorithms won't surface. Seasonal and context-aware. Auto-assigned for travel, food, and local exploration.
- **The Experience Designer** — Thinks about the full arc of an experience — timing, pairings, atmosphere, transitions. Not just what to do, but how to sequence it for maximum impact. Auto-assigned for itineraries, dining, events, and gift-giving.

### Topic-to-Persona Mappings

Each new category gets its own persona triple:

| Topic | Personas |
|-------|----------|
| Travel | Contrarian + Insider + Experience Designer |
| Food/drink | Contrarian + Curator + Insider |
| Home/pets/garden | Contrarian + Pragmatist + Craftsperson |
| Wellness/fitness | Contrarian + Pragmatist + Outsider |
| Personal finance | Contrarian + Economist + Risk Analyst |
| Learning | Contrarian + Outsider + Pragmatist |

This means "best high-end restaurants in New Orleans" now gets a Curator and an Insider instead of a Pragmatist and an Outsider — personas that actually know how to think about food recommendations.

---

## What's Next

Open areas for future work:

- **More agent backends.** Ollama for local models, Perplexity if they ship a CLI, any LLM with a command-line interface.
- **Confidence calibration.** Track whether speculative claims turn out to be right or wrong over time.
- **Cross-session patterns.** Detect when the council keeps giving the same type of advice on similar topics.
- **Richer historian.** Semantic similarity instead of just keyword matching for finding related sessions.
