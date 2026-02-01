---
name: council-help
description: Use when the user wants help with the council plugin, asks "what can the council do", "council commands", "how do I use the council", etc.
---

# Council Quick Reference

Print this cheat sheet directly — no agents, no dispatch.

## Core Commands

| Command | What it does |
|---------|-------------|
| `/council [question]` | Consult 3 AI advisors and get a synthesized briefing |
| `/council-debate [topic]` | Structured 2-round debate with a verdict |
| `/council-history` | Browse, recap, or resume past council sessions |
| `/council-help` | This cheat sheet |

## Flags

| Flag | Example | Effect |
|------|---------|--------|
| `--fun` | `/council --fun Should I rewrite in Rust?` | Adds a chaotic persona (Jokester, Time Traveler, etc.) to one seat |
| `--mode` | `/council --mode sequential ...` | Dispatch mode: `parallel` (default), `staggered`, or `sequential` |
| `--personas` | `/council --personas "Contrarian, Economist, Radical" ...` | Pick your own council members |
| `--seats N` | `/council --seats 5 ...` | Change the number of advisors (default: 3) |

## Post-Session

| Command | What it does |
|---------|-------------|
| `/rate 1-5` | Rate the session — higher-rated advice surfaces more in future councils |
| `/rate 4 [session-id]` | Rate a specific past session |
| `/council-outcome followed "note"` | Record that you followed the advice and what happened |
| `/council-outcome wrong "note"` | Record that the advice didn't work out |
| `/council-outcome partial "note"` | Partially followed, mixed results |
| `/council-outcome ignored "note"` | Didn't follow the advice |

## Follow-Up Patterns

After a briefing, just reply naturally — no need to re-invoke `/council`:

| You say | What happens |
|---------|-------------|
| *"Tell me more about the key tension"* | All 3 advisors elaborate on that specific point |
| *"I disagree with Advisor 1 on X"* | That advisor defends or revises their position |
| *"Expand on action item 2"* | Targeted drill-down on that action |
| *"Debate the key tension"* | Escalates to `/council-debate` |
| *"Show me the raw response from Advisor 1"* | Full unabridged response pulled from the session file |
| *"Archive this"* / *"Save this"* | Exports a Markdown copy to `~/Documents/council/` |

## Diagnostics

| Command | What it does |
|---------|-------------|
| `python3 council_cli.py doctor` | Full health check — agent CLIs, directories, Python version |
| `python3 council_cli.py agents` | Quick check of which agent CLIs are on PATH |

## Configuration

You can switch agent configurations by asking naturally:

- **"Switch the council to all Claude"** — uses Claude for all 3 advisor slots
- **"Switch back to multi-provider"** — uses Codex, Gemini, and Claude
- **"Add Ollama as an advisor"** — adds a local LLM to the council
- **"Use staggered mode"** — dispatches agents with less overlap (good for mixed providers)

The council auto-detects which CLIs are installed and adapts. If only Claude is available, it runs all 3 seats on Claude automatically.

## Personas

**Core** (always available): The Contrarian, The Pragmatist, The User Advocate

**Specialist** (auto-assigned by topic): The Systems Thinker, The Risk Analyst, The Economist, The Growth Hacker, The Outsider, The Radical, The Craftsperson, The Visionary

**Fun** (via `--fun` or `--personas`): The Jokester, The Trickster, The Cheater, The Conspiracy Theorist, The Time Traveler, The Intern
