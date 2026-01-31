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

### 1. Frame the Debate

Take the user's topic and define two clear positions. If the user has a lean, assign the opposing position to be argued as well. Craft the prompt with enough context for agents with no conversation history.

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
