---
name: council-debate
description: Use when the user wants AI agents to debate a topic, argue for/against a decision, or stress-test an idea through adversarial deliberation. Invoked with /council-debate or when the user says "debate this", "argue both sides", "devil's advocate", "stress test this idea", etc.
---

# Council Debate

Run a structured debate between AI agents where they respond to and challenge each other's arguments. The current Claude instance acts as neutral judge.

## When to Use

- The user is leaning toward a decision and wants it stress-tested
- There are two or more legitimate approaches and the trade-offs aren't obvious
- The user says "debate", "argue", "devil's advocate", "stress test", "challenge this"
- A regular `/council` produced agreement and the user wants deeper tension explored

## Flow

### 0. Historian Check

Before framing the debate, check for relevant past council sessions or debates:

**If CLI available:**
```bash
python3 "$COUNCIL_CLI" historian --question "the debate topic"
```

**Otherwise:** Scan `~/.claude/council/sessions/` for related topics.

If a related session or debate exists, note it when framing the debate so agents have that context. Don't force connections where there aren't any.

### 1. Frame the Debate

Take the user's topic and define two clear positions. If the user has a lean, assign the opposing position to be argued as well. Craft the prompt with enough context for agents with no conversation history. If the historian found relevant prior context, include it in the agent prompts.

Do NOT ask the user to confirm. Just dispatch immediately.

### 2. Round 1 — Opening Arguments

Dispatch all three agents in parallel. Assign two to argue opposing positions, and one as an independent analyst.

**Position A debater — one of: Codex, Gemini, or Claude CLI** (vary across invocations)
**Position B debater — another of the three**
**Independent analyst — the remaining agent**

CLI commands:

```bash
# Codex
echo "<PROMPT>" | codex exec - 2>/dev/null

# Gemini
gemini -p '<PROMPT>' -o text 2>/dev/null

# Claude
claude -p '<PROMPT>' --no-session-persistence 2>/dev/null
```

**Debater prompt template (Position A and B):**

```
You are a debater in a structured AI debate. You have been assigned a position to argue.

YOUR POSITION: [Position A or B]
You MUST argue this position convincingly, even if you personally disagree.
Be specific, use concrete examples, and anticipate counterarguments.

CONTEXT:
[relevant background, codebase context, or constraints]

TOPIC:
[the debate topic]

Give your opening argument in under 400 words. Be persuasive and specific.
```

**Independent analyst prompt template:**

```
You are an independent analyst observing a debate between two AI advisors.

CONTEXT:
[relevant background, codebase context, or constraints]

TOPIC:
[the debate topic]

POSITION A: [brief description]
POSITION B: [brief description]

Provide an independent analysis in under 400 words. You are not assigned a side. Identify what each side will likely get right and wrong. Point out factors both sides might overlook. Be specific and opinionated.
```

### 3. Round 2 — Rebuttals

Send each debater the OTHER debater's opening argument and ask them to rebut it. Send the independent analyst both arguments for a revised take. Run all three in parallel.

**Debater rebuttal prompt template:**

```
You are a debater in a structured AI debate. Here is your opponent's opening argument:

---
[Other agent's Round 1 response]
---

YOUR POSITION: [same position as Round 1]

Write a rebuttal in under 300 words. Attack their weakest points. Defend your position against their strongest points. Concede anything that's genuinely correct — concessions make you more credible.
```

**Analyst Round 2 prompt template:**

```
You are an independent analyst observing a debate. Here are both opening arguments:

POSITION A argued:
---
[Position A's Round 1 response]
---

POSITION B argued:
---
[Position B's Round 1 response]
---

Now that you've seen both arguments, give your updated analysis in under 300 words. Who made the stronger opening? What did each side miss? Where is the real crux of this decision?
```

### 4. Synthesize — The Verdict

The current Claude instance (you) acts as **neutral judge**. Present the debate outcome:

---

**Debate: [Topic]**

**Position A** (argued by [agent]): [1-2 sentence summary]

**Position B** (argued by [agent]): [1-2 sentence summary]

**Independent analysis** (by [agent]): [1-2 sentence summary of their take]

**Strongest argument for A:** [the single most compelling point]

**Strongest argument for B:** [the single most compelling point]

**Concessions made:** [anything either side admitted the other was right about — these are often the most valuable insights]

**Verdict:** [Your judgment as judge. Who made the stronger case? What's the right call given everything argued? Be decisive — don't cop out with "it depends."]

---

### 5. Optional: Round 3

If the user wants to go deeper, run a final round where each debater gives a 200-word closing statement incorporating the rebuttals. Then re-synthesize.

## Saving Results

Debate sessions save to the same location as council sessions so the historian can find them and `/council-history` can list them.

**Before writing any file**, always run `mkdir -p ~/.claude/council/sessions && mkdir -p ~/Documents/council` first.

After the verdict (and after each optional Round 3), save a JSON checkpoint to `~/.claude/council/sessions/`:

**Filename:** `YYYY-MM-DD-HH-MM-[slug].json`

**Structure:**

```json
{
  "id": "YYYY-MM-DD-HH-MM-slug",
  "type": "debate",
  "topic": "Short topic title",
  "question": "The original user topic",
  "date": "YYYY-MM-DD",
  "positions": {
    "a": { "label": "Position A description", "agent": "codex" },
    "b": { "label": "Position B description", "agent": "gemini" }
  },
  "analyst": "claude",
  "rounds": [
    {
      "round": 1,
      "label": "Opening arguments",
      "codex": "Full response text",
      "gemini": "Full response text",
      "claude": "Full response text"
    },
    {
      "round": 2,
      "label": "Rebuttals",
      "codex": "Full response text",
      "gemini": "Full response text",
      "claude": "Full response text"
    }
  ],
  "verdict": "The full verdict text from the judge",
  "archived": false
}
```

Use the Write tool to save/update this file after the verdict. If the user requests Round 3, read the existing file, append the round, update the verdict, and re-save.

### CLI Acceleration (Optional)

If the council CLI helper is available, use it for session creation and historian checks:

```bash
if [ -n "$CLAUDE_PLUGIN_ROOT" ] && python3 "$CLAUDE_PLUGIN_ROOT/skills/council/council_cli.py" --version >/dev/null 2>&1; then
    COUNCIL_CLI="$CLAUDE_PLUGIN_ROOT/skills/council/council_cli.py"
elif python3 "$HOME/.claude/skills/council/council_cli.py" --version >/dev/null 2>&1; then
    COUNCIL_CLI="$HOME/.claude/skills/council/council_cli.py"
else
    COUNCIL_CLI=""
fi
```

**If CLI available:**
```bash
# Check for related past sessions/debates before starting
python3 "$COUNCIL_CLI" historian --question "the debate topic"

# Create session after verdict
python3 "$COUNCIL_CLI" session create --question "the topic" --topic "short topic" --personas-json '{"type":"debate","positions":{"a":{"label":"...","agent":"codex"},"b":{"label":"...","agent":"gemini"}},"analyst":"claude"}'

# Append round data
echo '{"label":"Opening arguments","codex":"...","gemini":"...","claude":"..."}' | python3 "$COUNCIL_CLI" session append --id "SESSION_ID" --stdin
```

## Position Assignment

- If the user has a stated preference, assign one agent to argue FOR it and one AGAINST
- If no preference, assign positions based on what creates the most productive tension
- Randomly vary which agent gets which role across invocations — don't always make the same agent the contrarian
- The independent analyst role should also rotate

## Important Notes

- **Timeout:** Give each agent up to 120 seconds per round. If one times out, note it and proceed.
- **Failures:** If a CLI fails, note it and continue with the remaining agents. If only one debater remains, the judge can take over the failed agent's position.
- **Two rounds minimum:** Always do opening arguments + rebuttals. The rebuttals are where the real value emerges.
- **No code execution:** Consultation only. Don't ask agents to write or modify files.
- **Privacy:** Don't send sensitive data (API keys, credentials, personal info) to other agents.
- **Judge neutrality:** The current Claude instance is the judge, NOT a debater. The separate Claude CLI call is the council member. Keep these roles distinct.
