# Claude Council

A multi-AI council system for [Claude Code](https://docs.anthropic.com/en/docs/claude-code). Ask a question, get independent perspectives from multiple AI models, and receive a synthesized briefing from a neutral mediator.

Each council member is assigned a **persona** that shapes their perspective, creating productive friction by design. The mediator has **institutional memory** — it checks past sessions for relevant context (weighted by user ratings) before each new discussion. Agents tag their claims by [evidence level](#evidence-tags), and the briefing includes [actionable next steps](#what-to-do-next), a [disagreement matrix](#disagreement-matrix), and an [evidence audit](#evidence-audit).

> **Platform note:** This was built and tested on macOS. The skills are Markdown files that instruct Claude Code how to call CLI tools, so they should work on Linux as-is. Windows users may need to adjust the CLI commands in the skill files (shell quoting, paths, etc.).

## How It Works

```
You → /council Should I build or buy this feature?

         ┌──────────────┐
         │   Mediator    │  ← Checks past sessions (historian role)
         │  (Claude Code) │  ← Selects personas based on topic
         └──────┬───────┘
                │
    ┌───────────┼───────────┐
    ▼           ▼           ▼
┌────────┐ ┌────────┐ ┌────────┐
│Advisor 1│ │Advisor 2│ │Advisor 3│  ← Each gets a persona
│ as The │ │ as The │ │ as The │  ← Parallel by default
│Contrarian│Pragmatist│Systems │  ← Isolated from main context
│        │ │        │ │Thinker │
└────┬───┘ └────┬───┘ └────┬───┘
     │          │          │
     └──────────┼──────────┘
                ▼
         ┌──────────────┐
         │   Briefing    │  ← Agreement, disagreement, synthesis
         │  returned to  │  ← Only this reaches your context
         │  main context  │
         └──────────────┘
```

## Agent Configuration

The council dispatches to **three AI agents** via CLI commands. By default, it uses three different providers for maximum perspective diversity — different models have different training data, reasoning patterns, and blind spots.

### Default (Multi-Provider)

| Agent | CLI Tool | Install |
|-------|----------|---------|
| Advisor 1 | [OpenAI Codex CLI](https://github.com/openai/codex) | `npm install -g @openai/codex` |
| Advisor 2 | [Google Gemini CLI](https://github.com/google-gemini/gemini-cli) | `npm install -g @google/gemini-cli` |
| Advisor 3 | [Claude CLI](https://docs.anthropic.com/en/docs/claude-code) | Included with Claude Code |

Each CLI tool requires its own account and authentication. See their respective docs for setup. With mixed providers, the briefing uses **"Label as Persona"** format (e.g., "Codex (OpenAI) as The Contrarian") so you can tell which model said what.

### Claude-Only Mode

If you only have Claude Code installed, **you don't need to do anything** — the council auto-detects which CLIs are available and adapts. With only Claude on PATH, all three advisor slots automatically dispatch to Claude. No config change needed.

The personas still create meaningful diversity — each agent gets a different role and system prompt. When all agents share the same label, the briefing shows **persona names only** (e.g., "The Contrarian", "The Pragmatist") for clean output.

You can also switch modes manually by telling Claude "switch the council to all Claude", or by editing the Agent Configuration table in `skills/council/SKILL.md` — there's a commented-out Claude-only block ready to swap in.

### Switching Configurations

You can switch between configurations and dispatch modes by talking to Claude naturally:

| What you say | What happens |
|------|------|
| "Switch the council to all Claude" | Swaps config to 3x Claude CLI |
| "Switch back to multi-provider" | Swaps config to Codex + Gemini + Claude |
| "Use staggered mode" | Sets dispatch to staggered (recommended for multi-provider) |
| "Use parallel mode" | Sets dispatch to parallel (recommended for Claude-only) |
| "Add Ollama as a 4th advisor" | Adds a row to the config table |

Claude edits the skill file directly — changes take effect on the next `/council` invocation.

### Adding More Advisors

The council supports more than 3 seats. Add rows to the Agent Configuration table and use `--seats N`:

```
/council --seats 5 Should we rewrite the backend?
```

### Other Providers

Any CLI that accepts a prompt and returns text works. Some options:

| Provider | Label | CLI Command | Install |
|----------|-------|-------------|---------|
| [Ollama](https://ollama.ai) (local) | `Ollama (Local)` | `ollama run llama3 '<PROMPT>' 2>/dev/null` | [ollama.ai](https://ollama.ai) |
| Any LLM CLI | Your label | Your command with `<PROMPT>` placeholder | Per tool docs |

### Minimum Requirements

- **Claude Code** — Required. This is what runs the skills and acts as mediator.
- **At least one agent CLI** — The default config uses Codex, Gemini, and Claude. The council auto-detects which CLIs are available at the start of each session and adapts: all 3 for full multi-provider, Claude-only if that's all you have, or a mix. Missing agents are noted in the briefing header.

## Installation

There are three ways to install. All support natural language triggering — saying "ask the council about X" or "what do others think?" works regardless of install method because Claude matches the skill's description to your intent. The difference is the slash command name:

| Method | Slash command | Best for |
|--------|-----------|----------|
| **Plugin install** | `/claude-council:council` | Easiest install, auto-updates |
| **Script install** | `/council` | Shorter commands, symlink mode for development |
| **Manual copy** | `/council` | Full control, no git needed |

### Plugin Install (Recommended)

**Prerequisites:** Claude Code plus any agent CLIs you want to use. The default config uses Codex, Gemini, and Claude — see [Agent Configuration](#agent-configuration). For Claude-only mode, no extra tools needed.

```
/plugin marketplace add Erreon/claude-council
/plugin install claude-council@claude-council
```

Skills are namespaced: `/claude-council:council`, `/claude-council:council-debate`, `/claude-council:council-history`. You can also just say "ask the council about..." and Claude will invoke the right skill automatically. Session directories are created on first use via a SessionStart hook.

Update to the latest version anytime with `/plugin marketplace update claude-council`.

### Script Install

```bash
git clone https://github.com/Erreon/claude-council.git
cd claude-council
./install.sh
```

The install script:
- Checks which CLI tools are installed
- Symlinks skill files to `~/.claude/skills/` (edits in either location stay in sync)
- Creates session and archive directories
- Checks for Python 3 (optional, for CLI helper)
- Reports what's ready and what's missing

Use `./install.sh --copy` if you prefer independent copies instead of symlinks.

Skills are available at their short names: `/council`, `/council-debate`, `/council-history`.

### Manual Installation

**1. Copy the skill files to your Claude Code skills directory:**

```bash
mkdir -p ~/.claude/skills/council
mkdir -p ~/.claude/skills/council-debate
mkdir -p ~/.claude/skills/council-history

cp skills/council/SKILL.md ~/.claude/skills/council/SKILL.md
cp skills/council/council_cli.py ~/.claude/skills/council/council_cli.py
chmod +x ~/.claude/skills/council/council_cli.py
cp skills/council-debate/SKILL.md ~/.claude/skills/council-debate/SKILL.md
cp skills/council-history/SKILL.md ~/.claude/skills/council-history/SKILL.md
```

**2. Create the session storage directories:**

```bash
mkdir -p ~/.claude/council/sessions
mkdir -p ~/Documents/council
```

**3. Install the agent CLI tools:**

```bash
# OpenAI Codex (requires OpenAI account)
npm install -g @openai/codex

# Google Gemini (requires Google AI account)
npm install -g @google/gemini-cli

# Claude CLI is included with Claude Code
```

Authenticate each tool according to its docs. If you only want Claude-only mode, skip this step and tell Claude "switch the council to all Claude".

### Windows

The skills haven't been tested on Windows. The skill files themselves are just Markdown instructions — they should work if:

1. Your CLI tools are available in your terminal (PowerShell, WSL, etc.)
2. The shell commands in the skill files work in your environment
3. The file paths (`~/.claude/`, `~/Documents/`) resolve correctly

If you're using WSL, it should work the same as Linux. Native Windows may require editing the CLI commands in the skill files to use Windows-compatible quoting and paths.

## Recommended Settings

**Without these permissions, Claude Code will ask "Do you want to proceed?" on every `/council` invocation.** The council runs CLI detection, agent dispatch, and session management commands — each can trigger a prompt. Adding these to your `~/.claude/settings.json` makes sessions seamless:

```json
{
  "permissions": {
    "allow": [
      "Bash(python3:*)",
      "Bash(codex:*)",
      "Bash(gemini:*)",
      "Bash(claude:*)",
      "Bash(echo:*)",
      "Bash(find:*)",
      "Bash(command:*)",
      "Bash(mkdir:*)"
    ]
  }
}
```

For Claude-only mode you only need `"Bash(python3:*)"`, `"Bash(claude:*)"`, and the utility entries. If you add Ollama, add `"Bash(ollama:*)"`.

The first-run hook prints this permissions block when you start your first session, so you'll see it at install time too.

> **Security note:** These permissions allow Claude to run CLI tools without asking for confirmation. The council skill is designed to never include sensitive data like API keys or credentials in agent prompts, but you should review the skill files if you have concerns. If you'd prefer to approve each dispatch manually, skip these settings — the council works fine without them, it just asks for permission before each agent call.

## Usage

### `/council` — Ask the Council

> **Note:** If installed via plugin, the slash command is `/claude-council:council` instead of `/council`. Natural language like "ask the council" works with any install method — Claude matches intent to the skill description automatically. The examples below use the short names for readability.

```
/council Should we use Postgres or SQLite for this project?
```

The mediator will:
1. Check past sessions for relevant history (weighted by rating and outcome)
2. Auto-assign personas based on the topic
3. Dispatch agents (staggered by default)
4. Check for response similarity and warn if agents converge too much
5. Synthesize a briefing with a disagreement matrix, evidence audit, and actionable next steps

**Manual persona override:**
```
/council --personas "Contrarian, Economist, Radical" Should we raise prices?
```

**Dispatch mode** — Control how agents are launched:
```
/council --mode parallel Should we use Redis?     # All 3 at once (default)
/council --mode staggered Should we use Redis?    # Advisor 1+2, then Advisor 3
/council --mode sequential Should we use Redis?   # One at a time
```

| Mode | Behavior | Best for |
|------|----------|----------|
| **parallel** (default) | All 3 agents simultaneously | Default — works well when all agents are the same CLI |
| **staggered** | Advisor 1 + 2 together, Advisor 3 after | Mixed providers — avoids heaviest overlap |
| **sequential** | One at a time | Slower machines, or when parallel locks up |

**Fun mode** — Add chaotic energy:
```
/council --fun Should we rewrite the backend in Rust?
```

Randomly replaces one council seat with a fun persona (see [Fun Personas](#fun-personas) below).

### Reading the Briefing

Every council briefing follows a consistent structure. Here's what each section means and how to use it.

#### Advisor Summaries

Each advisor's position is condensed to 2-3 sentences plus their core recommendation. These are summaries, not the full responses — if you want the raw output, ask to see the deep dive (it's stored in the session JSON).

#### Evidence Tags

Each advisor tags their claims with one of three levels:

| Tag | Meaning | How to treat it |
|-----|---------|-----------------|
| `[ANCHORED]` | Based on specific data, evidence, or established fact | High confidence — act on it |
| `[INFERRED]` | Logical deduction from known information | Reasonable — verify if stakes are high |
| `[SPECULATIVE]` | Opinion, gut feel, or hypothesis | Treat as a hypothesis to test, not a conclusion |

#### Evidence Audit

The mediator scans the advisors' tagged claims and flags when consensus rests on speculation rather than evidence. If all three agents agree on something but none has anchored evidence, you'll see a warning. This prevents the briefing from sounding authoritative when it's actually just three models guessing in the same direction.

#### What To Do Next

2-3 concrete action items distilled from across all advisor positions. These are not summaries of what was discussed — they're things you should actually go do. Each starts with a verb, and they're rendered as a markdown checklist. The mediator doesn't advocate for any single advisor; it extracts the most actionable takeaways from the full discussion, including the disagreements.

#### Disagreement Matrix

A table showing where advisors diverge on key issues, with each position condensed to 2-5 words. The mediator notes which disagreements come from persona framing (the Contrarian is being contrarian) vs. genuine analytical divergence (they identified different root causes). This is often the most valuable part — the interesting signal is where smart perspectives clash, not where they agree.

#### Consensus

What the advisors agree on. Kept short (2-4 sentences) and honest — if consensus is weak, it says so rather than inflating thin agreement.

#### Key Tension

The single most important unresolved trade-off. Framed as a clear choice you need to make, not a hedge. This is the decision the council is handing back to you.

**Follow-up replies:** After a briefing, just reply normally — the council will re-dispatch with your pushback included and note any position shifts. You can also do targeted drill-downs: reference a specific disagreement row, action item, or advisor's position to get focused follow-up instead of a full re-run.

**Rate a session:**
```
/rate 5                                    # Rate the current session
/rate 3 2026-01-31-1430-local-llm          # Rate a specific session
```
Higher-rated sessions are weighted more heavily by the historian. Unrated sessions default to 3/5.

**Track outcomes:**
```
/council-outcome followed "Went with microservices, working well"
/council-outcome wrong "Should have listened to the Contrarian"
```
Statuses: `followed`, `partial`, `ignored`, `wrong`. Outcomes feed back into historian weighting — advice that was proven wrong gets demoted in future relevance scoring.

### `/council-debate` — Structured Debate

```
/council-debate Monolith vs microservices for a 3-person team
```

Assigns two agents to argue opposing positions and one as independent analyst. Runs two rounds (opening arguments + rebuttals), then delivers a verdict. Debate sessions are saved to the same session directory as council sessions, so the historian can find them and `/council-history` can list them.

### `/council-history` — Session Management

```
/council-history
```

Browse, recap, archive, or resume past sessions. Sessions auto-save as JSON after every round.

## Personas

Each council member gets assigned a persona that shapes their analysis. Personas are auto-selected by topic or manually overridden.

### Core Personas (always available)

| Persona | Role | Always Include? |
|---------|------|----------------|
| **The Contrarian** | Challenges premises, attacks assumptions, says the uncomfortable thing | Yes — at least one per session |
| **The Pragmatist** | Grounds in reality, cuts scope ruthlessly, focuses on what ships | Recommended |
| **The User Advocate** | Thinks only about end-user experience, ignores technical elegance | For product/UX questions |

### Specialist Personas

| Persona | Role | Best For |
|---------|------|----------|
| **The Systems Thinker** | Second-order effects, dependencies, "what breaks if this changes?" | Architecture, integrations |
| **The Risk Analyst** | Security, compliance, worst-case scenarios, blast radius | Business decisions, launches |
| **The Economist** | Costs, ROI, trade-offs, opportunity cost | Pricing, buy-vs-build |
| **The Growth Hacker** | Distribution, speed-to-market, moving the needle | Marketing, launches |
| **The Outsider** | Zero context, fresh eyes, catches insider assumptions | When you're deep in a rabbit hole |
| **The Radical** | Kill the feature, pivot, start over, delete the code | Strategic pivots, when stuck |
| **The Craftsperson** | Quality, maintainability, argues for the harder-but-better path | Code quality, tech debt |
| **The Visionary** | Long-horizon thinking, bigger picture, 1-2 year view | Product roadmap, strategy |

### Auto-Assignment

The mediator picks personas based on topic:

| Topic | Default Personas |
|-------|-----------------|
| Architecture/technical | Contrarian + Pragmatist + Systems Thinker |
| Product/features | Contrarian + User Advocate + Growth Hacker |
| Business/pricing | Contrarian + Economist + Risk Analyst |
| Personal/life decisions | Contrarian + Pragmatist + Outsider |
| Marketing/growth | Contrarian + User Advocate + Growth Hacker |
| Debugging/stuck | Contrarian + Pragmatist + Systems Thinker |
| Strategic/big-picture | Contrarian + Visionary + Radical |

### Fun Personas

Fun personas are **never auto-assigned**. They're activated with `--fun` (randomly picks one to replace a council seat) or by naming them in `--personas`.

| Persona | Role |
|---------|------|
| **The Jokester** | Roasts bad ideas mercilessly, but always lands on a real recommendation buried in the bit |
| **The Trickster** | Counterintuitive advice that sounds wrong but might be genius. Loves lateral thinking. |
| **The Cheater** | Every shortcut, hack, and loophole. Why build it when you can fake it? |
| **The Conspiracy Theorist** | Sees hidden connections everywhere. Paranoid but occasionally spots what everyone missed. |
| **The Time Traveler** | Answers from 10 years in the future. Annoyingly smug but sometimes genuinely prescient. |
| **The Intern** | Enthusiastic, slightly confused, asks "dumb" questions that turn out to be devastatingly insightful. |

**Examples:**
```
/council --fun What framework should we use?
# → Might get: Contrarian + Pragmatist + The Intern

/council --personas "Contrarian, Jokester, Time Traveler" Is AI overhyped?
# → Full chaos mode
```

## Session Storage

Sessions are saved automatically and can be archived for long-term reference.

| Location | Format | Purpose |
|----------|--------|---------|
| `~/.claude/council/sessions/` | JSON | Working data — auto-saved after every round |
| `~/Documents/council/` | Markdown | Archive — human-readable, created on request |

**Auto-save** happens after every synthesis — both `/council` and `/council-debate` sessions. Each JSON file contains full agent responses, persona/position assignments, prior context references, and mediator synthesis or verdict.

**Rate** sessions 1-5 with `/rate`. Higher-rated sessions are weighted more heavily by the historian.

**Track outcomes** with `/council-outcome` after advice plays out in practice. Outcomes feed back into historian scoring.

**Archive** with "save this" or "archive this" after a session. Creates a formatted Markdown file and marks the JSON as archived.

**Browse sessions** with `/council-history` — recap, view full transcripts, archive, delete, rate, annotate outcomes, or resume past discussions.

## The Mediator

The running Claude Code instance acts as a neutral mediator with three responsibilities:

1. **Synthesizer** — Produces a structured briefing with a disagreement matrix, evidence audit, and actionable next steps. Preserves disagreement rather than smoothing it into bland consensus. The separate Claude CLI call is the council member; the mediator is not.

2. **Historian** — Before each session, checks past sessions for relevant context (weighted by user ratings and outcome annotations) and includes it in agent prompts. Sessions rated highly or with positive outcomes surface more; sessions marked `wrong` get demoted. This gives the council institutional memory that improves over time.

3. **Quality monitor** — Checks agent responses for excessive similarity before synthesis. If two advisors converge too much (>60% overlap), the mediator flags it so the user can consider re-running with more diverse personas.

## Context Efficiency

Council dispatch runs inside a subagent, so only the final briefing (~300 words) enters your main conversation context — not the three raw agent responses (~1500+ words). This prevents long council sessions from causing early context compaction.

## Examples

**Architecture decision:**
```
/council We need real-time updates. WebSockets vs SSE vs polling for a small SaaS with 500 users?
```

**Product strategy:**
```
/council --personas "User Advocate, Economist, Radical" Should we add a free tier or keep paid-only?
```

**Personal decision:**
```
/council Should I quit my job to go full-time on my side project? I have 8 months of savings.
```

**Stress-test a plan:**
```
/council-debate Building our own auth vs using Auth0
```

### Example Briefing Output

Here's what a council briefing looks like with the default all-Claude configuration. Since all agents use the same label, the briefing uses **persona names only**:

---

**Council Briefing: Real-Time Updates for Small SaaS**
*Personas: The Contrarian, The Pragmatist, The Systems Thinker*

**The Contrarian:** Challenges the assumption that real-time is even needed — most "real-time" features are fine with 5-second polling and the complexity cost of WebSockets is rarely justified at 500 users. RECOMMENDATION: I recommend starting with simple polling and only upgrading if users actually complain about latency.

**The Pragmatist:** SSE is the pragmatic middle ground — simpler than WebSockets, built on HTTP, works through proxies, and handles the one-way server-to-client push that covers 90% of real-time use cases. RECOMMENDATION: I recommend SSE with a polling fallback for older clients.

**The Systems Thinker:** WebSockets create hidden operational complexity — connection state management, reconnection logic, load balancer configuration, and debugging becomes harder since traffic doesn't show up in standard HTTP logs. RECOMMENDATION: I recommend SSE for notifications and polling for data sync, avoiding WebSockets entirely at this scale.

**Evidence Audit:** All key claims grounded. The Contrarian's "rarely justified" claim is [INFERRED] from scale analysis rather than benchmarked data, but the reasoning is sound.

**What To Do Next:**
- [ ] Prototype SSE for your highest-priority real-time feature (notifications or live updates) and measure actual latency
- [ ] Load test with 500 concurrent SSE connections on your current infrastructure to confirm it handles the connection count
- [ ] Set up a polling fallback endpoint so clients degrade gracefully if SSE connections drop

**Disagreement Matrix:**

| Topic | The Contrarian | The Pragmatist | The Systems Thinker |
|-------|----------------|----------------|---------------------|
| Best approach | Polling is enough | SSE is the sweet spot | SSE + polling hybrid |
| WebSockets | Overkill at this scale | Unnecessary complexity | Avoid entirely |
| When to upgrade | Only if users complain | When you need bidirectional | Never at 500 users |

The disagreement on polling vs SSE is genuine analytical divergence — The Contrarian questions the premise while the others accept real-time is needed but differ on implementation.

**Consensus:** All three advisors agree WebSockets are unnecessary at 500 users and would add complexity without meaningful benefit. The operational overhead (connection management, load balancer config, debugging) outweighs any latency advantage at this scale.

**Key Tension:** Do you invest in SSE now (slightly more work upfront, cleaner real-time experience) or start with polling (faster to ship, but may need replacement later if latency matters)? This is a bet on whether your users will actually notice the difference between 200ms and 5s updates.

---

<details>
<summary><strong>Example with mixed providers</strong></summary>

When different providers are configured, the briefing switches to **"Label as Persona"** format:

---

**Council Briefing: Real-Time Updates for Small SaaS**
*Personas: Codex (OpenAI) as The Contrarian, Gemini (Google) as The Pragmatist, Claude (Anthropic) as The Systems Thinker*

**Codex (OpenAI) as The Contrarian:** [position summary...]

**Gemini (Google) as The Pragmatist:** [position summary...]

**Claude (Anthropic) as The Systems Thinker:** [position summary...]

---

</details>

## CLI Helper (Optional)

The project includes an optional Python CLI tool (`council_cli.py`) that offloads deterministic logic from the skill's LLM processing. It saves tokens and improves consistency for operations like parsing flags, assigning personas, building prompts, and managing session files.

**Requirements:** Python 3 (any version). No external dependencies — stdlib only.

**How it works:** The skill detects if Python 3 and the CLI file are available at the start of each session. If present, it delegates logic operations to the CLI. If not, everything falls back to the existing LLM-based processing — the skill works identically either way.

**Installation:** Automatic. The `install.sh` script symlinks (or copies with `--copy`) `council_cli.py` alongside `SKILL.md`. No PATH changes, no pip, no venv.

### Subcommands

All subcommands output JSON to stdout. Errors go to stderr.

| Subcommand | Purpose | Example |
|---|---|---|
| `parse` | Parse `/council` command flags | `council_cli.py parse --raw "/council --fun Should we use Redis?"` |
| `topic` | Classify question topic | `council_cli.py topic --question "Should we use Redis?"` |
| `assign` | Assign personas to agents | `council_cli.py assign --question "..." [--fun] [--personas "X,Y,Z"]` |
| `prompt` | Build agent prompt | `council_cli.py prompt --persona "The Contrarian" --question "..."` |
| `synthesis-prompt` | Build synthesis prompt | `echo '{...}' \| council_cli.py synthesis-prompt --question "..." --stdin` |
| `session create` | Create new session | `council_cli.py session create --question "..." --topic "..."` |
| `session load` | Load session by ID | `council_cli.py session load --id "..."` |
| `session append` | Append round data | `echo '{...}' \| council_cli.py session append --id "..." --stdin` |
| `session list` | List all sessions | `council_cli.py session list` |
| `session rate` | Rate a session (1-5) | `council_cli.py session rate --id "..." --rating 4` |
| `session outcome` | Annotate outcome | `council_cli.py session outcome --id "..." --status "implemented"` |
| `historian` | Find related past sessions | `council_cli.py historian --question "..."` |
| `similarity` | Check response similarity | `echo '{...}' \| council_cli.py similarity --stdin` |
| `agents` | Check which agent CLIs are on PATH | `council_cli.py agents` |
| `doctor` | Full health check (versions, dirs, helpers) | `council_cli.py doctor` |

### Diagnostics

If something isn't working, the CLI helper has two diagnostic commands:

```bash
# Quick check — which agent CLIs are available?
python3 ~/.claude/skills/council/council_cli.py agents

# Full health check — versions, directories, helper paths, Python
python3 ~/.claude/skills/council/council_cli.py doctor
```

Both output structured JSON. The `agents` command is fast (PATH check only) and runs automatically before every dispatch. The `doctor` command is thorough (actually runs `--version` on each CLI) and is intended for manual troubleshooting.

## Customization

The skills are just Markdown files that instruct Claude Code what to do. You can:

- **Swap agents** — Change the CLI commands in `skills/council/SKILL.md` to use different LLM tools
- **Add personas** — Edit the persona catalog in `skills/council/SKILL.md`
- **Change auto-assignment** — Edit the topic-to-persona mapping
- **Add more agents** — Expand from 3 to 4+ by adding more dispatch commands and updating the synthesis format
- **Change storage paths** — Edit the directory paths in the skill files
- **Adjust for your OS** — Edit CLI commands for Windows compatibility if needed

## License

MIT
