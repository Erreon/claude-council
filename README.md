# Claude Council

A multi-AI council system for [Claude Code](https://docs.anthropic.com/en/docs/claude-code). Ask a question, get independent perspectives from multiple AI models, and receive a synthesized briefing from a neutral mediator.

Each council member is assigned a **persona** that shapes their perspective, creating productive friction by design. The mediator has **institutional memory** — it checks past sessions for relevant context before each new discussion.

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
│ Agent 1│ │ Agent 2│ │ Agent 3│  ← Each gets a persona
│ as The │ │ as The │ │ as The │  ← Staggered by default
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

The council dispatches to **three AI CLI tools** running in parallel. You choose which tools to use.

### Default Configuration

The skill ships configured for three different LLMs to maximize perspective diversity:

| Agent | CLI Tool | Install |
|-------|----------|---------|
| Agent 1 | [OpenAI Codex CLI](https://github.com/openai/codex) | `npm install -g @openai/codex` |
| Agent 2 | [Google Gemini CLI](https://github.com/google-gemini/gemini-cli) | `npm install -g @google/gemini-cli` |
| Agent 3 | [Claude CLI](https://docs.anthropic.com/en/docs/claude-code) | Included with Claude Code |

Each CLI tool requires its own account and authentication. See their respective docs for setup.

### Using Different Tools

The agents are defined by their CLI commands in `skills/council/skill.md`. You can swap any agent for a different tool by editing the dispatch commands:

```bash
# Default: OpenAI Codex
echo "<PROMPT>" | codex exec - 2>/dev/null

# Default: Google Gemini
gemini -p '<PROMPT>' -o text 2>/dev/null

# Default: Claude CLI
claude -p '<PROMPT>' --no-session-persistence 2>/dev/null
```

Replace any of these with whatever CLI tools you have available. Some options:

- **Ollama** (local models): `ollama run llama3.1 "<PROMPT>"`
- **Perplexity**: If a CLI becomes available
- **Any LLM with a CLI interface**: As long as it accepts a prompt and returns text

### Claude-Only Mode

You don't need three different LLMs. If you only have Claude Code installed, you can run all three agents as separate Claude CLI calls — the personas will still create meaningful diversity since each agent gets a different role and system prompt. Edit the skill to use `claude -p` for all three dispatch commands. You'll lose the benefit of different model architectures producing genuinely different reasoning patterns, but the persona system still works.

### Minimum Requirements

- **Claude Code** — Required. This is what runs the skills and acts as mediator.
- **At least one other CLI tool** — The council needs agents to dispatch to. With only one tool, you'll get one perspective instead of three. The skill notes failures and proceeds with available agents.
- **Best experience** — Three different CLI tools from different providers. Different models have different training data, reasoning patterns, and blind spots. That diversity is the whole point.

## Installation

### Quick Install (macOS/Linux)

```bash
git clone https://github.com/yourusername/claude-council.git
cd claude-council
./install.sh
```

The install script:
- Checks which CLI tools are installed
- Copies skill files to `~/.claude/skills/`
- Creates session and archive directories
- Reports what's ready and what's missing

### Manual Installation

If you prefer not to use the script, or you're on a platform where it doesn't work:

**1. Copy the skill files to your Claude Code skills directory:**

```bash
# Create the skill directories
mkdir -p ~/.claude/skills/council
mkdir -p ~/.claude/skills/council-debate
mkdir -p ~/.claude/skills/council-history

# Copy the files
cp skills/council/skill.md ~/.claude/skills/council/skill.md
cp skills/council-debate/skill.md ~/.claude/skills/council-debate/skill.md
cp skills/council-history/skill.md ~/.claude/skills/council-history/skill.md
```

**2. Create the session storage directories:**

```bash
mkdir -p ~/.claude/council/sessions
mkdir -p ~/Documents/council
```

**3. Install the CLI tools you want to use:**

```bash
# OpenAI Codex (requires OpenAI account)
npm install -g @openai/codex

# Google Gemini (requires Google AI account)
npm install -g @google/gemini-cli

# Claude CLI is included with Claude Code
```

**4. Authenticate each CLI tool** according to its own documentation.

**5. Verify** by opening Claude Code and typing `/council test` — you should see the skill activate.

### Windows

The skills haven't been tested on Windows. The skill files themselves are just Markdown instructions — they should work if:

1. Your CLI tools are available in your terminal (PowerShell, WSL, etc.)
2. The shell commands in the skill files work in your environment
3. The file paths (`~/.claude/`, `~/Documents/`) resolve correctly

If you're using WSL, it should work the same as Linux. Native Windows may require editing the CLI commands in the skill files to use Windows-compatible quoting and paths.

## Usage

### `/council` — Ask the Council

```
/council Should we use Postgres or SQLite for this project?
```

The mediator will:
1. Check past sessions for relevant history
2. Auto-assign personas based on the topic
3. Dispatch agents (staggered by default)
4. Synthesize a briefing with agreement, disagreement, and key tensions

**Manual persona override:**
```
/council --personas "Contrarian, Economist, Radical" Should we raise prices?
```

**Dispatch mode** — Control how agents are launched:
```
/council --mode parallel Should we use Redis?     # All 3 at once
/council --mode staggered Should we use Redis?    # Codex+Gemini, then Claude (default)
/council --mode sequential Should we use Redis?   # One at a time
```

| Mode | Behavior | Best for |
|------|----------|----------|
| **parallel** | All 3 agents simultaneously | Fast machines, short prompts |
| **staggered** (default) | Codex + Gemini together, Claude after | Balanced — avoids heaviest overlap |
| **sequential** | One at a time | Slower machines, or when parallel locks up |

**Fun mode** — Add chaotic energy:
```
/council --fun Should we rewrite the backend in Rust?
```

Randomly replaces one council seat with a fun persona (see [Fun Personas](#fun-personas) below).

**Follow-up replies:** After a briefing, just reply normally — the council will re-dispatch with your pushback included and note any position shifts.

### `/council-debate` — Structured Debate

```
/council-debate Monolith vs microservices for a 3-person team
```

Assigns two agents to argue opposing positions and one as independent analyst. Runs two rounds (opening arguments + rebuttals), then delivers a verdict.

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

**Auto-save** happens after every synthesis. Each JSON file contains full agent responses, persona assignments, prior context references, and mediator synthesis.

**Archive** with "save this" or "archive this" after a session. Creates a formatted Markdown file and marks the JSON as archived.

**Browse sessions** with `/council-history` — recap, view full transcripts, archive, delete, or resume past discussions.

## The Mediator

The running Claude Code instance acts as a neutral mediator with two responsibilities:

1. **Synthesizer** — Presents agreement, disagreement, and key tensions without injecting its own opinion. The separate Claude CLI call is the council member; the mediator is not.

2. **Historian** — Before each session, checks past sessions for relevant context and includes it in agent prompts. This gives the council institutional memory across conversations.

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

## Customization

The skills are just Markdown files that instruct Claude Code what to do. You can:

- **Swap agents** — Change the CLI commands in `skills/council/skill.md` to use different LLM tools
- **Add personas** — Edit the persona catalog in `skills/council/skill.md`
- **Change auto-assignment** — Edit the topic-to-persona mapping
- **Add more agents** — Expand from 3 to 4+ by adding more dispatch commands and updating the synthesis format
- **Change storage paths** — Edit the directory paths in the skill files
- **Adjust for your OS** — Edit CLI commands for Windows compatibility if needed

## License

MIT
