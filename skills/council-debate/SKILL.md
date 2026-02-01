---
name: council-debate
description: Use when the user wants AI agents to debate a topic, argue for/against a decision, or stress-test an idea through adversarial deliberation. Invoked with /council-debate or when the user says "debate this", "argue both sides", "devil's advocate", "stress test this idea", etc.
---

# Council Debate

Run a structured debate between AI agents where they respond to and challenge each other's arguments. The current Claude instance acts as neutral judge.

## Agent Configuration

| Slot | Label | CLI Command |
|------|-------|-------------|
| Advisor 1 | Codex (OpenAI) | `echo "<PROMPT>" \| codex exec --skip-git-repo-check - 2>/dev/null` |
| Advisor 2 | Gemini (Google) | `gemini -p '<PROMPT>' -o text 2>/dev/null` |
| Advisor 3 | Claude (Anthropic) | `claude -p '<PROMPT>' --no-session-persistence 2>/dev/null` |

<!-- Claude-only alternative — uncomment this block and comment out the block above:
| Slot | Label | CLI Command |
|------|-------|-------------|
| Advisor 1 | Claude | `claude -p '<PROMPT>' --no-session-persistence 2>/dev/null` |
| Advisor 2 | Claude | `claude -p '<PROMPT>' --no-session-persistence 2>/dev/null` |
| Advisor 3 | Claude | `claude -p '<PROMPT>' --no-session-persistence 2>/dev/null` |
-->

To switch configurations, see the "Switching Configurations" section in the main council skill.

### Labeling Logic

Before producing the verdict, check the Agent Configuration table above:
- If **all three labels are identical** → use **role names only** (e.g., "Position A debater", "Independent analyst")
- If **labels differ** → use **"Label as Role"** format (e.g., "Codex (OpenAI) arguing Position A")

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

Dispatch all three agents in parallel using the CLI commands from the **Agent Configuration** table at the top. Assign two to argue opposing positions, and one as an independent analyst.

**Position A debater — Advisor 1** (or vary across invocations)
**Position B debater — Advisor 2**
**Independent analyst — Advisor 3**

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

> **Tip:** [random tip — pick one from the list below]

**Tip source:** If CLI is available, get the tip from `python3 "$COUNCIL_CLI" tip` (returns `{"tip": "..."}`). Otherwise pick one at random from this list:
- Say "archive this" to save a Markdown copy to ~/Documents/council/
- /rate 1-5 to rate this session — higher-rated advice surfaces more in future councils
- Use /council-debate to stress-test a decision the council agreed on
- /council-outcome followed "what happened" tracks whether advice worked out
- Say "show me the raw response from Advisor 1" for the full unabridged take
- /council-history to browse, recap, or resume past sessions
- Use --fun to add a chaotic persona like The Jokester or The Time Traveler
- Use --personas "Contrarian, Economist, Radical" to pick your own council
- The council remembers past sessions — related history is included automatically
- Run /council-help for a quick reference of all commands and features

Rotate tips — don't repeat the same tip in back-to-back sessions.

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
    "a": { "label": "Position A description", "agent": "advisor_1" },
    "b": { "label": "Position B description", "agent": "advisor_2" }
  },
  "analyst": "advisor_3",
  "labels": {
    "advisor_1": "Claude",
    "advisor_2": "Claude",
    "advisor_3": "Claude"
  },
  "rounds": [
    {
      "round": 1,
      "label": "Opening arguments",
      "advisor_1": "Full response text",
      "advisor_2": "Full response text",
      "advisor_3": "Full response text"
    },
    {
      "round": 2,
      "label": "Rebuttals",
      "advisor_1": "Full response text",
      "advisor_2": "Full response text",
      "advisor_3": "Full response text"
    }
  ],
  "verdict": "The full verdict text from the judge",
  "archived": false
}
```

Use the Write tool to save/update this file after the verdict. If the user requests Round 3, read the existing file, append the round, update the verdict, and re-save.

### CLI Acceleration + Agent Detection

**Run this SINGLE block once at the start of every `/council-debate` session. Do NOT split into multiple Bash calls — run the entire block as one command to avoid repeated permission prompts:**

```bash
# Detect CLI helper + agent availability in one shot
COUNCIL_CLI=""
if [ -n "$CLAUDE_PLUGIN_ROOT" ] && python3 "$CLAUDE_PLUGIN_ROOT/skills/council/council_cli.py" --version >/dev/null 2>&1; then
    COUNCIL_CLI="$CLAUDE_PLUGIN_ROOT/skills/council/council_cli.py"
elif python3 "$HOME/.claude/skills/council/council_cli.py" --version >/dev/null 2>&1; then
    COUNCIL_CLI="$HOME/.claude/skills/council/council_cli.py"
elif CACHE_CLI="$(find "$HOME/.claude/plugins/cache/claude-council" -name council_cli.py -path "*/skills/council/*" 2>/dev/null | head -1)" && [ -n "$CACHE_CLI" ] && python3 "$CACHE_CLI" --version >/dev/null 2>&1; then
    COUNCIL_CLI="$CACHE_CLI"
fi
# Agent availability (combined in same call)
if [ -n "$COUNCIL_CLI" ]; then
    AGENT_STATUS=$(python3 "$COUNCIL_CLI" agents 2>/dev/null)
    echo "COUNCIL_CLI=$COUNCIL_CLI"
    echo "$AGENT_STATUS"
else
    CODEX_OK=false; GEMINI_OK=false; CLAUDE_OK=false; AGENT_COUNT=0
    command -v codex  >/dev/null 2>&1 && CODEX_OK=true  && AGENT_COUNT=$((AGENT_COUNT + 1))
    command -v gemini >/dev/null 2>&1 && GEMINI_OK=true  && AGENT_COUNT=$((AGENT_COUNT + 1))
    command -v claude >/dev/null 2>&1 && CLAUDE_OK=true  && AGENT_COUNT=$((AGENT_COUNT + 1))
    echo "COUNCIL_CLI="
    echo "CODEX=$CODEX_OK GEMINI=$GEMINI_OK CLAUDE=$CLAUDE_OK COUNT=$AGENT_COUNT"
fi
```

**If CLI available, use these for session management:**
```bash
# Check for related past sessions/debates before starting
python3 "$COUNCIL_CLI" historian --question "the debate topic"

# Create session after verdict
python3 "$COUNCIL_CLI" session create --question "the topic" --topic "short topic" --personas-json '{"type":"debate","positions":{"a":{"label":"...","agent":"codex"},"b":{"label":"...","agent":"gemini"}},"analyst":"claude"}'

# Append round data
echo '{"label":"Opening arguments","codex":"...","gemini":"...","claude":"..."}' | python3 "$COUNCIL_CLI" session append --id "SESSION_ID" --stdin
```

### Agent Availability

**Adapt dispatch based on the detection results above:**

| Scenario | Behavior |
|----------|----------|
| **All 3 available** | Normal dispatch using the Agent Configuration table as-is |
| **Only Claude available** | Use `claude -p '<PROMPT>' --no-session-persistence 2>/dev/null` for all 3 slots (Position A debater, Position B debater, Independent analyst). Set all labels to "Claude". |
| **2 of 3 available** | Dispatch to the available agents. Fill the missing slot with one of the available agents (prefer Claude as fallback). Note in the verdict: *"Note: [Agent] was unavailable for this debate."* |
| **0 available** | Do NOT dispatch. Show: *"No agent CLIs found. Install at least one to run a debate. Run `python3 council_cli.py doctor` for setup help."* |

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
