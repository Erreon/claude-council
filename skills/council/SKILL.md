---
name: council
description: Use when the user wants multiple AI perspectives on a decision, architecture question, strategy, or any topic worth deliberation. Invoked with /council or when the user says "ask the council", "get other opinions", "what do others think", etc.
---

# Council

Consult three external AI agents for independent perspectives — each assigned a distinct persona — then synthesize their responses into an actionable briefing that preserves disagreement, surfaces tensions, and gives the user concrete next steps. The mediator has institutional memory and weights past sessions by user ratings.

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

To add more advisors, add more rows (Advisor 4, Advisor 5, etc.) and use `--seats N` to match. The dispatch, synthesis, and JSON checkpoint will adapt automatically.

### Switching Configurations

The user can ask you to switch configurations at any time. When they do, edit the Agent Configuration table above by commenting/uncommenting the appropriate block. Examples of what the user might say:

- **"Switch the council to all Claude"** or **"Use Claude for all 3 agents"** → Comment out the multi-provider table, uncomment the Claude-only table
- **"Switch back to multi-provider"** or **"Use Codex, Gemini, and Claude"** → Comment out the Claude-only table, uncomment the multi-provider table
- **"Use staggered mode"** or **"Switch to staggered dispatch"** → The user wants `--mode staggered` (recommended for multi-provider to avoid resource contention)
- **"Use parallel mode"** or **"Switch to parallel dispatch"** → The user wants `--mode parallel` (works well for Claude-only since there's no cross-CLI contention)
- **"Add Ollama as an advisor"** → Add a row: `| Advisor 4 | Ollama (Local) | \`ollama run llama3 '<PROMPT>' 2>/dev/null\` |`

When switching, edit this file directly using the Edit tool. The change takes effect on the next `/council` invocation.

### Labeling Logic

Before producing the briefing, check the Agent Configuration table above:
- If **all three labels are identical** (e.g., all "Claude") → use **persona names only** in the briefing (e.g., "The Contrarian", "The Pragmatist")
- If **labels differ** → use **"Label as Persona"** format (e.g., "Codex (OpenAI) as The Contrarian", "Gemini (Google) as The Pragmatist")

## When to Use

- Architecture or design decisions
- Strategy questions (technical or product)
- Debugging when stuck — fresh eyes from different models
- Brainstorming where diverse perspectives add value
- Any time the user explicitly asks for council input

## CLI Acceleration (Optional)

A Python CLI helper (`council_cli.py`) can offload deterministic logic (parsing, persona assignment, prompt building, session management) to save tokens and improve consistency. It lives alongside this skill file.

**Detection + Agent Availability — run this SINGLE block once at the start of every `/council` session. Do NOT split into multiple Bash calls — run the entire block as one command to avoid repeated permission prompts:**

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

If `COUNCIL_CLI` is set, pass it to the subagent so it can use the CLI commands listed below. If empty, the subagent follows the prose instructions — the skill works identically without the CLI.

**CLI commands used by the subagent (NOT the main conversation):**

> The main conversation never calls these directly. They are listed here as a reference for building the subagent prompt.

- **Step 0 (Historian):** `python3 "$COUNCIL_CLI" historian --question "..."`
- **Step 1 (Parse):** `python3 "$COUNCIL_CLI" parse --raw "/council ..."`
- **Step 1 (Assign):** `python3 "$COUNCIL_CLI" assign --question "..." --topic "<topic>" [--personas "X,Y,Z"] [--fun]`
- **Step 1 (Prompt):** `python3 "$COUNCIL_CLI" prompt --persona "The Contrarian" --question "..." [--prior-context "..."]` (repeat per agent)
- **Follow-up prompts:** `python3 "$COUNCIL_CLI" prompt --persona "..." --question "..." --followup --previous-position "..." --other-positions "..." --user-followup "..."`
- **Synthesis prompt:** `echo '{...}' | python3 "$COUNCIL_CLI" synthesis-prompt --question "..." --personas-json '{...}' --agent-status "$AGENT_STATUS" --mode "parallel" [--compact] --stdin`
- **Session create:** `python3 "$COUNCIL_CLI" session create --question "..." --topic "..." --personas-json '{...}'`
- **Session append:** `echo '{...}' | python3 "$COUNCIL_CLI" session append --id "..." --stdin`
- **Similarity check:** `echo '{...}' | python3 "$COUNCIL_CLI" similarity --stdin`
- **Rating:** `python3 "$COUNCIL_CLI" session rate --id "..." --rating N`
- **Outcome:** `python3 "$COUNCIL_CLI" session outcome --id "..." --status "..." --note "..."`
- **Agents check:** `python3 "$COUNCIL_CLI" agents`
- **Full diagnostics:** `python3 "$COUNCIL_CLI" doctor`
- **Random tip:** `python3 "$COUNCIL_CLI" tip`

## Agent Availability

**Adapt dispatch based on the detection results above:**

| Scenario | Behavior |
|----------|----------|
| **All 3 available** | Normal dispatch using the Agent Configuration table as-is |
| **Only Claude available** | Auto-switch to Claude-only: use `claude -p '<PROMPT>' --no-session-persistence 2>/dev/null` for all 3 advisor slots. Set all labels to "Claude". No config change needed — just dispatch all 3 to Claude. |
| **2 of 3 available** | Dispatch to the available agents only. Note the missing agent in the briefing: *"Note: [Agent] was unavailable for this session."* Fill the missing slot with one of the available agents (prefer Claude as fallback). |
| **0 available** | Do NOT dispatch. Instead, show: *"No agent CLIs found. Install at least one to use the council. Run `python3 council_cli.py doctor` for setup help, or see the install commands in the README."* |

This means a user who only has Claude installed never needs to manually "switch to all-Claude mode" — the skill detects it and adapts. The `AGENT_STATUS` JSON (when available) is passed to the synthesis-prompt for the status header line.

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
| **The Curator** | Opinionated and taste-driven. Makes specific, ranked picks with clear reasoning. Allergic to generic top-10 lists and tourist-trap recommendations. | Food, drink, travel, entertainment, any recommendation query |
| **The Insider** | Deep domain and local knowledge. Knows what's real vs. hype, what locals actually do, and what the algorithms won't surface. Seasonal and context-aware. | Travel, food, local exploration, niche hobbies |
| **The Experience Designer** | Thinks about the full arc of an experience — timing, pairings, atmosphere, transitions. Not just what to do, but how to sequence it for maximum impact. | Travel itineraries, dining, events, gift-giving |

**Fun personas** (never auto-assigned — activated with `--fun` or manual `--personas` override):

These personas add chaos, humor, or adversarial energy. They still try to be *useful* — just through an unhinged lens. One fun persona replaces one of the three council seats (randomly chosen) when `--fun` is used.

| Persona | Description |
|---------|-------------|
| **The Jokester** | Treats everything like a comedy roast. Will mock bad ideas mercilessly but always lands on an actual recommendation buried in the bit. Thinks the best way to stress-test an idea is to make fun of it. |
| **The Trickster** | Gives advice that sounds wrong but might be genius. Proposes the lateral, counterintuitive, "wait, actually..." approach. Loves misdirection that accidentally leads somewhere useful. |
| **The Cheater** | Finds every shortcut, hack, and loophole. Why build it when you can fake it? Why solve the problem when you can redefine it? Ethically flexible but surprisingly effective. |
| **The Conspiracy Theorist** | Sees hidden connections everywhere. "What if the REAL reason this isn't working is..." Paranoid but occasionally spots patterns everyone else missed. |
| **The Time Traveler** | Answers from 10 years in the future. "Oh, you're still doing THAT? That's adorable." Annoyingly smug but sometimes genuinely prescient. |
| **The Intern** | Enthusiastic, slightly confused, asks "dumb" questions that turn out to be devastatingly insightful. "Wait, why DO we need a database for this?" |

### Persona Assignment

**Automatic (default):** The mediator selects 3 personas based on the topic — always including at least one Core persona and The Contrarian. Assignment logic:

- Architecture/technical questions → Contrarian + Pragmatist + Systems Thinker
- Product/feature questions → Contrarian + User Advocate + Growth Hacker
- Business/pricing questions → Contrarian + Economist + Risk Analyst
- Career/life decisions → Contrarian + Pragmatist + Outsider
- Marketing/growth questions → Contrarian + User Advocate + Growth Hacker
- Debugging/stuck → Contrarian + Pragmatist + Systems Thinker
- Strategic/big-picture → Contrarian + Visionary + Radical
- Travel questions → Contrarian + Insider + Experience Designer
- Food/drink recommendations → Contrarian + Curator + Insider
- Home/pet/garden questions → Contrarian + Pragmatist + Craftsperson
- Wellness/fitness questions → Contrarian + Pragmatist + Outsider
- Personal finance questions → Contrarian + Economist + Risk Analyst
- Learning/skill-building → Contrarian + Outsider + Pragmatist

If the topic spans multiple categories, mix accordingly. Use judgment.

**Manual override:** The user can specify personas in the command:

```
/council --personas "Contrarian, Economist, Radical" [question]
```

When manually specified, use exactly those personas. No substitution. Fun personas can be included in manual lists (e.g., `--personas "Contrarian, Jokester, Pragmatist"`).

**Fun mode (`--fun`):** When `--fun` is passed, randomly select ONE fun persona and assign it to a randomly chosen agent, replacing whatever persona that agent would have received. The other two agents keep their normal personas. Example:

```
/council --fun What database should I use?
```

Might produce: Advisor 1 as The Contrarian, Advisor 2 as The Time Traveler, Advisor 3 as The Pragmatist.

### Output Mode

By default, the council returns a **compact synthesis** — a 5-8 line summary with action items. The full briefing (per-advisor positions, disagreement matrix, evidence audit, key tension) is still generated and saved to the JSON checkpoint, but not shown unless requested.

```
/council --full [question]
```

| Flag | Behavior |
|------|----------|
| *(no flag)* | Returns compact synthesis. Full briefing saved to JSON checkpoint. |
| `--full` | Returns the complete briefing with per-advisor positions, disagreement matrix, evidence audit, and key tension. |

After receiving a compact synthesis, the user can say **"show full brief"** to retrieve the full version from the JSON checkpoint without re-running the council.

### Dispatch Mode

Controls how agents are launched. Can be specified with `--mode`:

```
/council --mode sequential [question]
/council --mode staggered [question]
/council --mode parallel [question]
```

| Mode | Behavior | Best for |
|------|----------|----------|
| **parallel** (default) | All 3 agents launch simultaneously | Default — works well when all agents are the same CLI |
| **staggered** | Advisor 1 + Advisor 2 launch together, Advisor 3 launches after they finish | Mixed providers — avoids the heaviest overlap |
| **sequential** | Agents launch one at a time (Advisor 1 → Advisor 2 → Advisor 3) | Slow machines, or when parallel is locking up |

Default is **parallel**. If you configure mixed providers (e.g., Codex + Gemini + Claude), consider using `--mode staggered` to avoid resource contention.

**Each agent gets ONE persona per session.** Assign them round-robin (Advisor 1 gets persona 1, Advisor 2 gets persona 2, Advisor 3 gets persona 3). Note the assignment in the briefing header so the user knows who played what role.

## Flow

> **ONE-BASH-CALL RULE:** Only ONE Bash call happens in the main conversation: the CLI detection block (above). Everything else — historian lookup, persona assignment, prompt building, agent dispatch — runs inside the Task subagent. The mediator does LLM reasoning only (topic classification, context gathering, flag parsing) then immediately launches the subagent.

### 0. Historian Check (Mediator's Memory) — Delegated to Subagent

The mediator does **NOT** run the historian CLI command itself. Instead, the mediator passes the question and CLI path to the subagent (Step 2), which runs the historian lookup internally. This avoids a Bash permission prompt in the main conversation.

The historian logic is unchanged — sessions with higher user ratings (from `/rate`) are weighted more heavily in relevance scoring. A 5-star session with keyword matches ranks above a 1-star session with the same matches. Unrated sessions default to 3/5.

The subagent will:
1. Run `python3 "$COUNCIL_CLI" historian --question "..."` (or read session files manually if no CLI)
2. Scan topic names and questions for relevance to the current question, weighted by rating
3. If a related session exists, include a **Prior Council Context** block in the agent prompts:

```
PRIOR COUNCIL CONTEXT:
On [date], the council discussed "[topic]". Key outcome: [1-2 sentence summary of the synthesis/final position]. [Note any decisions made or positions that shifted.]
[If outcome annotation exists: "Result: [status] — [note]"]
```

If no related sessions exist, skip this block. Don't force connections where there aren't any. If a related session has an outcome annotation, always include it — this is the most valuable historical signal.

This gives the council institutional memory — agents can build on, challenge, or reference past discussions rather than starting from zero every time.

### 1. Frame the Question (Mediator — No Bash Calls)

Take the user's question or topic and craft a clear, self-contained prompt. The prompt must include enough context that an agent with no prior conversation history can give a useful answer. If the question is about code, read relevant files and include their contents or summaries in the prompt.

**No CLI calls here.** The mediator does LLM reasoning only in this step: topic classification, context gathering (via Read/Glob), and flag parsing. The `assign`, `prompt`, and `historian` CLI commands are called by the subagent in Step 2, not by the main conversation.

**Classify the topic yourself** before assigning personas. You (the mediator LLM) understand intent far better than keyword matching. Pick the best-fit topic from this list and pass it to the subagent (which will call `assign --topic`):

| Topic key | Use when the question is about... |
|-----------|----------------------------------|
| `architecture` | System design, infrastructure, databases, APIs, deployment |
| `product` | Features, UX, onboarding, design, MVPs, roadmaps |
| `business` | Pricing, revenue, funding, hiring, contracts, compliance |
| `personal` | Career, life decisions, relationships, freelancing |
| `travel` | Trips, destinations, itineraries, hotels, sightseeing |
| `food_drink` | Restaurants, dining, cooking, bars, coffee, cuisine |
| `home_life` | Pets, gardening, home improvement, DIY, decor |
| `wellness` | Fitness, health, meditation, sleep, nutrition, mental health |
| `personal_finance` | Budgeting, investing, retirement, taxes, insurance |
| `learning` | Courses, skills, certifications, hobbies, creative pursuits |
| `marketing` | Growth, SEO, content, social media, branding, launches |
| `debugging` | Bugs, errors, crashes, performance issues, stuck |
| `strategic` | Vision, direction, pivots, competitive positioning, long-term |

If the question spans multiple categories, pick the dominant one. The CLI will fall back to keyword matching if `--topic` is omitted, but LLM classification is preferred.

Select personas (automatic or from manual override) and note the assignments.

Do NOT ask the user to confirm the prompt. Just dispatch immediately. Speed matters more than perfect framing — the user already said what they want.

### 2. Dispatch via Subagent (Context Isolation)

> **NEVER USE `run_in_background`.** Background task completion notifications leak into the main conversation after the briefing is delivered, creating noise and confusing the user. Every Bash call and every Task tool call inside the subagent must be **foreground only**.

**IMPORTANT:** The entire council dispatch, agent responses, and synthesis MUST run inside a Task subagent to keep raw agent outputs out of the main conversation context. This prevents long council sessions from causing early autocompaction.

Use the **Task tool** with `subagent_type: "general-purpose"` and a prompt that includes everything the subagent needs:

- The user's topic classification and framed question
- The CLI path (`COUNCIL_CLI`) and agent status JSON from the detection block
- Any codebase context (file contents, summaries)
- The CLI commands for each agent (from the Agent Configuration table)
- The synthesis format to follow
- The JSON checkpoint save instructions
- Flags: dispatch mode, `--fun`, `--full`, `--personas`, etc.
- Whether this is a new session or a follow-up round (include previous round context if follow-up)

**The subagent prompt must include the CRITICAL RULES preamble** (see next section) and instruct it to:

0. Run `mkdir -p ~/.claude/council/sessions && mkdir -p ~/Documents/council` first to ensure save directories exist (silent no-op if they already exist)

1. **Historian lookup:** Run `python3 "$COUNCIL_CLI" historian --question "..."` (or scan session files manually if no CLI) and incorporate any prior context into the agent prompts

2. **Persona assignment:** Run `python3 "$COUNCIL_CLI" assign --question "..." --topic "<topic>" [--personas "X,Y,Z"] [--fun]` (or assign manually using the topic-persona mapping if no CLI)

3. **Prompt building:** Run `python3 "$COUNCIL_CLI" prompt --persona "..." --question "..." [--prior-context "..."]` per agent (or build prompts manually using the template below if no CLI)

4. Run the three agents according to the **dispatch mode** (default: parallel), using the CLI commands from the **Agent Configuration** table at the top of this file. Replace `<PROMPT>` with the built prompt for each advisor.

   **Dispatch modes (NEVER use `run_in_background` in any mode):**
   - **parallel** (default): Launch all 3 Bash calls as **foreground** parallel calls in a single message (multiple Bash tool calls without `run_in_background`).
   - **staggered**: Launch Advisor 1 + Advisor 2 as foreground parallel calls in one message, wait for both to finish, then launch Advisor 3 alone as a foreground call
   - **sequential**: Launch Advisor 1, wait for it to finish, then Advisor 2, wait, then Advisor 3. All foreground calls.

5. Synthesize the three responses. Generate BOTH the full briefing AND the compact version in a single synthesis call. When using the CLI, pass `--compact` to `synthesis-prompt` — this instructs the LLM to output both formats separated by `===COMPACT===`. Preserve disagreements, surface tensions, and produce actionable next steps (not a fourth opinion, not a bland average).

6. Save the JSON checkpoint to `~/.claude/council/sessions/`. Store the **full** briefing (everything before `===COMPACT===`) in the `synthesis` field — this is the archival copy.

7. Return the output to the mediator:
   - If `--full` was passed: return the **full** briefing
   - Otherwise (default): return the **compact** version (everything after `===COMPACT===`)

### CRITICAL RULES Preamble (copy verbatim into every subagent prompt)

The mediator must include this block at the **top** of every Task subagent prompt (initial dispatch and follow-ups). Copy it verbatim:

```
CRITICAL RULES — read before doing anything:
1. NEVER use run_in_background on ANY tool call (Bash or Task). All calls must be foreground. Background task notifications leak to the user's main conversation and create noise.
2. Return ONLY the formatted briefing as your final output. Do not return raw agent responses, debug logs, or intermediate state.
3. If an agent times out (60s) or fails, note it in the briefing and proceed with the others. Do not retry or block.

CLI COMMAND REFERENCE (use these, the main conversation does not):
- Historian: python3 "$COUNCIL_CLI" historian --question "..."
- Assign: python3 "$COUNCIL_CLI" assign --question "..." --topic "<topic>" [--personas "X,Y,Z"] [--fun]
- Prompt: python3 "$COUNCIL_CLI" prompt --persona "..." --question "..." [--prior-context "..."]
- Follow-up prompt: python3 "$COUNCIL_CLI" prompt --persona "..." --question "..." --followup --previous-position "..." --other-positions "..." --user-followup "..."
- Synthesis prompt: echo '{...}' | python3 "$COUNCIL_CLI" synthesis-prompt --question "..." --personas-json '{...}' --agent-status "$AGENT_STATUS" --mode "parallel" [--compact] --stdin
- Session create: python3 "$COUNCIL_CLI" session create --question "..." --topic "..." --personas-json '{...}'
- Session append: echo '{...}' | python3 "$COUNCIL_CLI" session append --id "..." --stdin
- Similarity check: echo '{...}' | python3 "$COUNCIL_CLI" similarity --stdin
- Tip: python3 "$COUNCIL_CLI" tip
```

Replace `$COUNCIL_CLI` with the actual path detected in the main conversation. If `COUNCIL_CLI` is empty, the subagent follows prose instructions instead.

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

For each key claim, tag it with one of:
- [ANCHORED] — based on specific data, evidence, or established fact
- [INFERRED] — logical deduction from known information
- [SPECULATIVE] — opinion, gut feel, or hypothesis without direct evidence

End your response with a single sentence starting with "RECOMMENDATION: I recommend..." that captures your core advice.
```

**Agent prompt template (for follow-up rounds):**

```
You are a member of a council of AI advisors in an ongoing discussion.

YOUR ROLE: You are playing **[Persona Name]** — [one-sentence persona description].
Stay in character for this follow-up as well.

PREVIOUS QUESTION: [original question]

YOUR PREVIOUS POSITION: [summary of this agent's last response]

THE OTHER ADVISORS SAID:
- [Advisor 2 label/persona]: [summary of their position]
- [Advisor 3 label/persona]: [summary of their position]

THE MEDIATOR SAID: [mediator's synthesis from the briefing]

THE USER NOW SAYS: [user's follow-up or pushback]

Respond to the user's follow-up. You may revise your position if the user raises a good point, or defend it if you still disagree. Stay concise (under 300 words).

Tag key claims as [ANCHORED], [INFERRED], or [SPECULATIVE].

End with a single sentence starting with "RECOMMENDATION: I recommend..." that captures your updated core advice.
```

**Synthesis formats — the subagent produces BOTH, separated by `===COMPACT===`:**

The subagent always generates both formats in a single LLM call. The full briefing is saved to the JSON checkpoint's `synthesis` field. The compact version is what gets returned to the mediator (and shown to the user) unless `--full` was passed.

**Full format (saved to JSON checkpoint, shown with `--full`):**

---

**Council Briefing: [Topic]**

Apply the **Labeling Logic** from the Agent Configuration section:
- If all labels are the same → *Personas: [Persona 1], [Persona 2], [Persona 3]*
- If labels differ → *Personas: [Label 1] as [Persona 1], [Label 2] as [Persona 2], [Label 3] as [Persona 3]*
*Agents: [Agent1] OK, [Agent2] OK, [Agent3] Missing | CLI Helper: Active | Mode: [mode]*

[*Prior context: On [date], the council discussed "[topic]" — [1 sentence outcome]*]  ← only if historian found relevant history

For each advisor, use the appropriate header:
- Same labels → **[Persona]:** [2-3 sentence summary + RECOMMENDATION]
- Different labels → **[Label] as [Persona]:** [2-3 sentence summary + RECOMMENDATION]

**Evidence Audit:** [If any consensus point or action item rests primarily on [SPECULATIVE] claims from multiple advisors, flag it here: "⚠ [topic] — consensus is speculative (no advisor provided anchored evidence)." If all key claims are anchored or inferred, write "All key claims grounded." Keep to 1-2 sentences.]

**What To Do Next:**
- [ ] [Concrete action item starting with a verb — the single most important next step]
- [ ] [Second action item — verb-first, specific and actionable]
- [ ] [Third action item (optional) — only if genuinely distinct from the first two]

These should be the 2-3 things the user should actually do based on the council's input. Not summaries — actions.

**Disagreement Matrix:**

Use persona names (or "Label (Persona)" if labels differ) as column headers:

| Topic | [Advisor 1 header] | [Advisor 2 header] | [Advisor 3 header] |
|-------|-------------------|--------------------|--------------------|
| [Key issue 1] | [2-5 word position] | [2-5 word position] | [2-5 word position] |
| [Key issue 2] | [position] | [position] | [position] |

Note which disagreements stem from persona framing vs genuine analytical divergence.

**Consensus:** [What the council agrees on. 2-4 sentences maximum. Don't inflate thin agreement — if consensus is weak, say so.]

**Key Tension:** [The single most important unresolved trade-off. One paragraph. This is the decision the user actually needs to make. Frame it as a clear choice, not a hedge.]

---

> **Tip:** [random tip from the list below]

**Compact format (default output, shown without `--full`):**

---

**Council Briefing: [Topic]**
*Personas: [list] | Mode: [mode]*

[3-5 sentence synthesis: the core recommendation, where advisors agree, and the key tension as one sentence. Do NOT list individual advisor positions — synthesize into a unified narrative.]

**Do Next:**
- [ ] [Most important action item — verb-first]
- [ ] [Second action item — verb-first]

> Say "show full brief" or use `--full` for per-advisor positions, disagreement matrix, and evidence audit.

---

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
- Say "show full brief" or use --full to see the complete briefing with per-advisor positions and disagreement matrix

Rotate tips — don't repeat the same tip in back-to-back sessions.

### 3. Present the Briefing

Take the subagent's returned output and present it directly to the user. The subagent returns either the compact synthesis (default) or the full briefing (when `--full` is passed). The main context only ever sees this final output — never the raw agent responses.

### 4. Consensus Check

If all three agents broadly agree and the Disagreement section is thin or trivial, flag it:

> "The council reached consensus on this one. Want me to run a `/council-debate` to stress-test the recommendation? Sometimes unanimous agreement means we're all missing something."

Only suggest this when agreement is genuinely strong. If there are meaningful disagreements, skip this — the council already did its job.

### 5. Follow-Up Replies

After a council briefing, the user may reply with follow-up questions, pushback, or new angles without invoking `/council` again. When this happens, treat it as a continuation of the council session:

1. Take the user's reply and build the follow-up context (original question, previous positions from the JSON checkpoint, the user's new input)
2. Dispatch a new Task subagent with this context — same process as step 2. **Include the CRITICAL RULES preamble** at the top of the subagent prompt (same as the initial dispatch — no `run_in_background`, return only the briefing, handle timeouts gracefully).
3. The subagent reads the existing JSON checkpoint, appends the new round, saves it, and returns only the briefing
4. Present the returned briefing to the user

This keeps the council conversational while keeping all raw responses out of the main context. The user can go back and forth as many rounds as they want.

#### Targeted Drill-Down

When the user's follow-up references a specific section of the briefing — a disagreement row, the key tension, an action item, or an individual advisor's position — treat it as a **targeted drill-down** rather than a full re-dispatch:

- **"Tell me more about the key tension"** or **"Expand on action item 2"** → Ask all three advisors to elaborate specifically on that point, staying in persona. The follow-up prompt should quote the relevant section and ask for deeper analysis.
- **"I disagree with Advisor 1 on [topic]"** or **"Why does Advisor 2 think X?"** → Route to only that advisor for a deeper explanation. Other advisors can optionally respond if the mediator judges their perspective is relevant.
- **"Debate the key tension"** → Escalate to `/council-debate` with the tension as the motion. Suggest this option but don't auto-escalate.

The drill-down follow-up uses the same subagent dispatch and JSON checkpoint flow. The difference is in the prompt framing — targeted prompts produce more focused, useful responses than repeating the full question.

### 6. Show Full Brief (On-Demand)

When the user says "show full brief", "show the full briefing", "full brief", or uses `--full` after receiving a compact synthesis, this is **NOT** a follow-up round — do NOT re-dispatch agents. Instead:

1. Read the JSON checkpoint for the current session from `~/.claude/council/sessions/`
2. Extract the `synthesis` field from the latest round
3. Present the full briefing text to the user

This retrieves the already-generated full briefing from disk. No LLM calls needed.

### 7. Optional: Deep Dive

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
    "advisor_1": "The Contrarian",
    "advisor_2": "The Pragmatist",
    "advisor_3": "The User Advocate"
  },
  "labels": {
    "advisor_1": "Claude",
    "advisor_2": "Claude",
    "advisor_3": "Claude"
  },
  "prior_context": "Reference to related past session, if any (null if none)",
  "rating": null,
  "outcome": null,
  "rounds": [
    {
      "round": 1,
      "advisor_1": "Full advisor 1 response text",
      "advisor_2": "Full advisor 2 response text",
      "advisor_3": "Full advisor 3 response text",
      "synthesis": "The full mediator synthesis text",
      "user_followup": null
    },
    {
      "round": 2,
      "user_followup": "What the user said",
      "advisor_1": "Full advisor 1 response text",
      "advisor_2": "Full advisor 2 response text",
      "advisor_3": "Full advisor 3 response text",
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

## Rating Sessions

After any council briefing, the user can rate the session's usefulness:

```
/rate 5
/rate 3 2026-01-31-1430-local-llm
```

- Rating is 1-5 (clamped). If no session ID is given, rates the most recent active session.
- The rating is stored in the session JSON as `"rating": N`.
- Higher-rated sessions are weighted more heavily by the historian when retrieving prior context. This closes the feedback loop — good advice surfaces more, bad advice fades.
- Unrated sessions default to 3/5 for scoring purposes.

When the user rates a session, read the JSON, set `"rating"` to the value, and save it back.

## Outcome Tracking

After a council session has played out in practice, the user can annotate what actually happened:

```
/council-outcome followed "We went with microservices and it's working well"
/council-outcome partial 2026-01-31-1430-local-llm "Set up Ollama but haven't added it to the council yet"
/council-outcome wrong "The consensus recommendation failed — should have listened to the Contrarian"
```

**Format:** `/council-outcome <status> [session_id] "<note>"`

**Statuses:**
- `followed` — Took the council's advice, it worked
- `partial` — Partially followed, mixed results
- `ignored` — Didn't follow the advice (record why)
- `wrong` — Followed the advice and it was bad

If no session ID is given, annotates the most recent active session.

**Storage:** Add to the session JSON:

```json
{
  "outcome": {
    "status": "followed",
    "note": "We went with microservices and it's working well",
    "date": "2026-02-15"
  }
}
```

**How outcomes feed back into the system:**

1. **Historian weighting:** Sessions with `followed` outcomes get a boost (×1.2) in relevance scoring. Sessions with `wrong` outcomes get a penalty (×0.5). This compounds with the rating weight — a 5-star session that was later proven wrong gets demoted. A 2-star session that turned out to be prescient gets promoted.
2. **Prior context enrichment:** When the historian surfaces a related past session that has an outcome annotation, include it in the PRIOR COUNCIL CONTEXT block: `"The council recommended X. Outcome: followed — [note]."`
3. **Pattern detection:** If multiple sessions on similar topics have `wrong` outcomes, the mediator should flag this in the briefing: "Note: past council advice on similar topics has not aged well. Consider extra scrutiny."

This closes the loop between advice and results. Without it, the council can confidently repeat mistakes.

## Similarity Detection

After collecting all agent responses (before synthesis), compare them for excessive overlap. If two advisors gave highly similar responses (>60% word overlap via Jaccard similarity on word sets), insert a warning before the synthesis:

> **Similarity Warning:** The following advisors gave highly overlapping responses:
> - **The Pragmatist** and **The Systems Thinker**: 72% overlap
>
> Consider using more diverse personas or rephrasing the question.

This addresses the council's own feedback that multi-model doesn't guarantee diverse perspectives — sometimes different agents converge on the same heuristics. The warning helps the user decide whether to re-run with different personas.

## Important Notes

- **Timeout:** Give each agent up to 60 seconds. If one times out, note it and proceed with the others. The previous 120-second timeout caused resource contention and lockups on some machines.
- **Failures:** If a CLI fails (not installed, auth expired, etc.), note it and proceed with available agents. Don't block on one agent being down.
- **Context limits:** Keep the prompt self-contained. Don't assume the other agents have access to local files — include relevant snippets directly in the prompt.
- **No code execution:** This skill is for consultation only. Don't ask the other agents to write or modify files. If the council reaches a conclusion that involves code changes, the mediator handles implementation after the session.
- **Privacy:** Don't send sensitive data (API keys, credentials, personal info) to other agents. Strip these from any context before dispatching.
- **Mediator role:** The current Claude instance is the mediator. It does NOT add its own opinion as a council member. The separate Claude CLI call is the council member. Keep these roles distinct. The mediator's job is to preserve and surface disagreement, not to smooth it into bland consensus — the most valuable output is often where advisors diverge.
- **Mediator as Historian:** The mediator also serves as the council's institutional memory. Before each session, it checks past sessions for relevant context (weighted by user rating) and includes it in agent prompts. This is a factual role (reporting what was previously discussed), not an opinion role — the mediator still does not advocate for any position.
- **Persona consistency:** Once personas are assigned for a session, they persist across all follow-up rounds. Don't reassign personas mid-session.
