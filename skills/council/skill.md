---
name: council
description: Use when the user wants multiple AI perspectives on a decision, architecture question, strategy, or any topic worth deliberation. Invoked with /council or when the user says "ask the council", "get other opinions", "what do others think", etc.
---

# Council

Consult three external AI agents (Codex, Gemini, Claude) for independent perspectives — each assigned a distinct persona — then synthesize their responses as a neutral mediator with institutional memory.

## When to Use

- Architecture or design decisions
- Strategy questions (technical or product)
- Debugging when stuck — fresh eyes from different models
- Brainstorming where diverse perspectives add value
- Any time the user explicitly asks for council input

## Personas

Each council member is assigned a persona that shapes how they approach the question. This creates structural diversity — productive friction by design, not by accident.

### Persona Catalog

**Core personas** (at least 2 should always be active):

| Persona | Description | Best for |
|---------|-------------|----------|
| **The Contrarian** | Actively challenges the premise. Looks for what everyone is assuming and attacks it. Says the uncomfortable thing. | Every session — always include one |
| **The Pragmatist** | Grounds discussion in reality. What can actually be built, shipped, and maintained by a solo dev or small team? Cuts scope ruthlessly. | Architecture, product, any build decision |
| **The User Advocate** | Thinks only about the end user's experience. Doesn't care about technical elegance — cares about whether real people will use this. | Product strategy, UX, features |

**Specialist personas** (auto-selected or manually assigned based on topic):

| Persona | Description | Auto-assign when |
|---------|-------------|-----------------|
| **The Systems Thinker** | Focuses on second-order effects, dependencies, and how pieces interact. Asks "what breaks if this changes?" | Architecture, infrastructure, integrations |
| **The Risk Analyst** | Identifies what can go wrong. Security, compliance, financial exposure, reputational risk. Worst-case scenarios. | Business decisions, launches, security |
| **The Economist** | Thinks in costs, trade-offs, and ROI. Time vs money vs quality. Opportunity cost of every choice. | Pricing, resource allocation, buy-vs-build |
| **The Growth Hacker** | Obsessed with distribution, speed-to-market, and what moves the needle. Impatient with perfection. | Marketing, launches, growth strategy |
| **The Outsider** | Has zero context about the project. Approaches the question fresh. Catches insider assumptions and jargon. | When the team is deep in a rabbit hole |
| **The Radical** | Proposes the uncomfortable option. Kill the feature. Pivot entirely. Start over. Delete the code. | Strategic pivots, when stuck, major decisions |
| **The Craftsperson** | Cares about quality, maintainability, and doing it right. Will argue for the harder path if it's the better path. | Code quality, tech debt, long-term architecture |
| **The Visionary** | Long-horizon thinking. Where does this lead in 1-2 years? What's the bigger picture? | Product roadmap, strategic direction |

### Persona Assignment

**Automatic (default):** The mediator selects 3 personas based on the topic — always including at least one Core persona and The Contrarian. Assignment logic:

- Architecture/technical questions → Contrarian + Pragmatist + Systems Thinker
- Product/feature questions → Contrarian + User Advocate + Growth Hacker
- Business/pricing questions → Contrarian + Economist + Risk Analyst
- Personal/life decisions → Contrarian + Pragmatist + Outsider
- Marketing/growth questions → Contrarian + User Advocate + Growth Hacker
- Debugging/stuck → Contrarian + Pragmatist + Systems Thinker
- Strategic/big-picture → Contrarian + Visionary + Radical

If the topic spans multiple categories, mix accordingly. Use judgment.

**Manual override:** The user can specify personas in the command:

```
/council --personas "Contrarian, Economist, Radical" [question]
```

When manually specified, use exactly those personas. No substitution.

**Each agent gets ONE persona per session.** Assign them round-robin (Codex gets persona 1, Gemini gets persona 2, Claude gets persona 3). Note the assignment in the briefing header so the user knows who played what role.

## Flow

### 0. Historian Check (Mediator's Memory)

Before framing the question, the mediator checks for relevant past council sessions:

1. Read the list of JSON files in `~/.claude/council/sessions/`
2. Scan topic names and questions for relevance to the current question
3. If a related session exists, read its synthesis/outcome and include a **Prior Council Context** block in the agent prompts:

```
PRIOR COUNCIL CONTEXT:
On [date], the council discussed "[topic]". Key outcome: [1-2 sentence summary of the synthesis/final position]. [Note any decisions made or positions that shifted.]
```

If no related sessions exist, skip this block. Don't force connections where there aren't any.

This gives the council institutional memory — agents can build on, challenge, or reference past discussions rather than starting from zero every time.

### 1. Frame the Question

Take the user's question or topic and craft a clear, self-contained prompt. The prompt must include enough context that an agent with no prior conversation history can give a useful answer. If the question is about code, read relevant files and include their contents or summaries in the prompt.

Select personas (automatic or from manual override) and note the assignments.

Do NOT ask the user to confirm the prompt. Just dispatch immediately. Speed matters more than perfect framing — the user already said what they want.

### 2. Dispatch via Subagent (Context Isolation)

**IMPORTANT:** The entire council dispatch, agent responses, and synthesis MUST run inside a Task subagent to keep raw agent outputs out of the main conversation context. This prevents long council sessions from causing early autocompaction.

Use the **Task tool** with `subagent_type: "general-purpose"` and a prompt that includes everything the subagent needs:

- The framed question and any codebase context
- The CLI commands for each agent
- The synthesis format to follow
- The JSON checkpoint save instructions
- Whether this is a new session or a follow-up round (include previous round context if follow-up)

**The subagent prompt must instruct it to:**

0. Run `mkdir -p ~/.claude/council/sessions && mkdir -p ~/Documents/council` first to ensure save directories exist (silent no-op if they already exist)

1. Run all three agents in parallel using Bash:

   **Codex (OpenAI):**
   ```bash
   echo "<PROMPT>" | codex exec - 2>/dev/null
   ```

   **Gemini (Google):**
   ```bash
   gemini -p '<PROMPT>' -o text 2>/dev/null
   ```

   **Claude (Anthropic):**
   ```bash
   claude -p '<PROMPT>' --no-session-persistence 2>/dev/null
   ```

2. Synthesize the three responses as a neutral mediator (not a fourth opinion)

3. Save the JSON checkpoint to `~/.claude/council/sessions/`

4. Return ONLY the formatted briefing as its final output

**Agent prompt template (for new sessions):**

```
You are one member of a council of AI advisors being consulted on a question.

YOUR ROLE: You are playing **[Persona Name]** — [one-sentence persona description].
Stay in character. Let this perspective shape your analysis, priorities, and recommendations.
Be specific and opinionated — don't hedge. If you disagree with conventional wisdom, say so.

[PRIOR COUNCIL CONTEXT (if any):
On [date], the council discussed "[topic]". Key outcome: [summary]. ]

CONTEXT:
[any relevant codebase context, file contents, or background]

QUESTION:
[the user's question]

Respond concisely (under 500 words). Focus on your strongest recommendation and key reasoning, filtered through your assigned role.
```

**Agent prompt template (for follow-up rounds):**

```
You are a member of a council of AI advisors in an ongoing discussion.

YOUR ROLE: You are playing **[Persona Name]** — [one-sentence persona description].
Stay in character for this follow-up as well.

PREVIOUS QUESTION: [original question]

YOUR PREVIOUS POSITION: [summary of this agent's last response]

THE OTHER ADVISORS SAID:
- [Agent 2 name] as [Persona]: [summary of their position]
- [Agent 3 name] as [Persona]: [summary of their position]

THE MEDIATOR SAID: [mediator's synthesis from the briefing]

THE USER NOW SAYS: [user's follow-up or pushback]

Respond to the user's follow-up. You may revise your position if the user raises a good point, or defend it if you still disagree. Stay concise (under 300 words).
```

**Synthesis format (the subagent must use this exactly):**

---

**Council Briefing: [Topic]**
*Personas: Codex as [Persona], Gemini as [Persona], Claude as [Persona]*
[*Prior context: On [date], the council discussed "[topic]" — [1 sentence outcome]*]  ← only if historian found relevant history

**Codex (OpenAI) as [Persona]:** [2-3 sentence summary of their position]

**Gemini (Google) as [Persona]:** [2-3 sentence summary of their position]

**Claude (Anthropic) as [Persona]:** [2-3 sentence summary of their position]

**Agreement:** [What they agree on]

**Disagreement:** [Where they diverge and why — note when disagreements stem from persona differences vs genuine analytical divergence]

**Mediator's summary:** [Neutral synthesis of the strongest points from each side. Highlight the key tension or trade-off the user needs to decide on. Do NOT pick a winner — present the decision clearly so the user can choose.]

---

### 3. Present the Briefing

Take the subagent's returned briefing and present it directly to the user. The main context only ever sees this final briefing — never the raw agent responses.

### 4. Consensus Check

If all three agents broadly agree and the Disagreement section is thin or trivial, flag it:

> "The council reached consensus on this one. Want me to run a `/council-debate` to stress-test the recommendation? Sometimes unanimous agreement means we're all missing something."

Only suggest this when agreement is genuinely strong. If there are meaningful disagreements, skip this — the council already did its job.

### 5. Follow-Up Replies

After a council briefing, the user may reply with follow-up questions, pushback, or new angles without invoking `/council` again. When this happens, treat it as a continuation of the council session:

1. Take the user's reply and build the follow-up context (original question, previous positions from the JSON checkpoint, the user's new input)
2. Dispatch a new Task subagent with this context — same process as step 2
3. The subagent reads the existing JSON checkpoint, appends the new round, saves it, and returns only the briefing
4. Present the returned briefing to the user

This keeps the council conversational while keeping all raw responses out of the main context. The user can go back and forth as many rounds as they want.

### 6. Optional: Deep Dive

If the user wants to see a full raw agent response, read it from the JSON checkpoint file in `~/.claude/council/sessions/` using the Read tool. This pulls it from disk on-demand rather than keeping it in context.

## Saving Results

Council sessions are automatically saved at each checkpoint (after each synthesis).

### Auto-Save (Working Data)

**Before writing any file**, always run `mkdir -p ~/.claude/council/sessions` and `mkdir -p ~/Documents/council` via Bash first. This ensures the directories exist without prompting. Do this silently every time — it's a no-op if they already exist.

After every synthesis (initial briefing or follow-up round), save a JSON checkpoint to `~/.claude/council/sessions/`:

**Filename:** `YYYY-MM-DD-HH-MM-[slug].json` (slug is a short kebab-case topic, e.g., `meeting-agent`, `backyard-chickens`)

**Structure:**

```json
{
  "id": "YYYY-MM-DD-HH-MM-slug",
  "topic": "Short topic title",
  "question": "The original user question",
  "date": "YYYY-MM-DD",
  "personas": {
    "codex": "The Contrarian",
    "gemini": "The Pragmatist",
    "claude": "The User Advocate"
  },
  "prior_context": "Reference to related past session, if any (null if none)",
  "rounds": [
    {
      "round": 1,
      "codex": "Full codex response text",
      "gemini": "Full gemini response text",
      "claude": "Full claude response text",
      "synthesis": "The full mediator synthesis text",
      "user_followup": null
    },
    {
      "round": 2,
      "user_followup": "What the user said",
      "codex": "Full codex response text",
      "gemini": "Full gemini response text",
      "claude": "Full claude response text",
      "synthesis": "The full mediator synthesis text"
    }
  ],
  "archived": false
}
```

Use the Write tool to save/update this file after each round. If the session already has a file (follow-up round), read it first and append the new round.

### Archive (Safe Place)

When the user says "save this", "archive this", or "keep this", export the current session as a formatted Markdown file to `~/Documents/council/`:

**Filename:** `YYYY-MM-DD-[slug].md`

The Markdown file should contain:
- The original question
- Each round's briefing (formatted as it was presented to the user)
- Any follow-up rounds and how positions shifted

Also update the JSON checkpoint to set `"archived": true`.

## Important Notes

- **Timeout:** Give each agent up to 120 seconds. If one times out, note it and proceed with the others.
- **Failures:** If a CLI fails (not installed, auth expired, etc.), note it and proceed with available agents. Don't block on one agent being down.
- **Context limits:** Keep the prompt self-contained. Don't assume the other agents have access to local files — include relevant snippets directly in the prompt.
- **No code execution:** This skill is for consultation only. Don't ask the other agents to write or modify files. If the council reaches a conclusion that involves code changes, the mediator handles implementation after the session.
- **Privacy:** Don't send sensitive data (API keys, credentials, personal info) to other agents. Strip these from any context before dispatching.
- **Mediator neutrality:** The current Claude instance is the mediator. It does NOT add its own opinion as a council member. The separate Claude CLI call is the council member. Keep these roles distinct.
- **Mediator as Historian:** The mediator also serves as the council's institutional memory. Before each session, it checks past sessions for relevant context and includes it in agent prompts. This is a factual role (reporting what was previously discussed), not an opinion role — the mediator still does not advocate for any position.
- **Persona consistency:** Once personas are assigned for a session, they persist across all follow-up rounds. Don't reassign personas mid-session.
