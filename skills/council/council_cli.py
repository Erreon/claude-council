#!/usr/bin/env python3
"""council_cli.py — Optional CLI helper for the claude-council skill.

Single-file, stdlib-only tool that offloads deterministic logic from the
skill's LLM processing: parsing flags, assigning personas, building prompts,
managing session files, and checking response similarity.

Every subcommand outputs JSON to stdout. Errors go to stderr.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import random
from datetime import datetime
from pathlib import Path

__version__ = "0.3.0"

# ---------------------------------------------------------------------------
# Directories
# ---------------------------------------------------------------------------

SESSIONS_DIR = Path.home() / ".claude" / "council" / "sessions"
ARCHIVE_DIR = Path.home() / "Documents" / "council"

# ---------------------------------------------------------------------------
# Persona Catalog
# ---------------------------------------------------------------------------

CORE_PERSONAS = {
    "The Contrarian": {
        "description": "Actively challenges the premise. Looks for what everyone is assuming and attacks it. Says the uncomfortable thing.",
        "best_for": "Every session — always include one",
        "type": "core",
    },
    "The Pragmatist": {
        "description": "Grounds discussion in reality. What can actually be built, shipped, and maintained by a solo dev or small team? Cuts scope ruthlessly.",
        "best_for": "Architecture, product, any build decision",
        "type": "core",
    },
    "The User Advocate": {
        "description": "Thinks only about the end user's experience. Doesn't care about technical elegance — cares about whether real people will use this.",
        "best_for": "Product strategy, UX, features",
        "type": "core",
    },
}

SPECIALIST_PERSONAS = {
    "The Systems Thinker": {
        "description": "Focuses on second-order effects, dependencies, and how pieces interact. Asks \"what breaks if this changes?\"",
        "auto_assign": "Architecture, infrastructure, integrations",
        "type": "specialist",
    },
    "The Risk Analyst": {
        "description": "Identifies what can go wrong. Security, compliance, financial exposure, reputational risk. Worst-case scenarios.",
        "auto_assign": "Business decisions, launches, security",
        "type": "specialist",
    },
    "The Economist": {
        "description": "Thinks in costs, trade-offs, and ROI. Time vs money vs quality. Opportunity cost of every choice.",
        "auto_assign": "Pricing, resource allocation, buy-vs-build",
        "type": "specialist",
    },
    "The Growth Hacker": {
        "description": "Obsessed with distribution, speed-to-market, and what moves the needle. Impatient with perfection.",
        "auto_assign": "Marketing, launches, growth strategy",
        "type": "specialist",
    },
    "The Outsider": {
        "description": "Has zero context about the project. Approaches the question fresh. Catches insider assumptions and jargon.",
        "auto_assign": "When the team is deep in a rabbit hole",
        "type": "specialist",
    },
    "The Radical": {
        "description": "Proposes the uncomfortable option. Kill the feature. Pivot entirely. Start over. Delete the code.",
        "auto_assign": "Strategic pivots, when stuck, major decisions",
        "type": "specialist",
    },
    "The Craftsperson": {
        "description": "Cares about quality, maintainability, and doing it right. Will argue for the harder path if it's the better path.",
        "auto_assign": "Code quality, tech debt, long-term architecture",
        "type": "specialist",
    },
    "The Visionary": {
        "description": "Long-horizon thinking. Where does this lead in 1-2 years? What's the bigger picture?",
        "auto_assign": "Product roadmap, strategic direction",
        "type": "specialist",
    },
    "The Curator": {
        "description": "Opinionated and taste-driven. Makes specific, ranked picks with clear reasoning. Allergic to generic top-10 lists and tourist-trap recommendations.",
        "auto_assign": "Food, drink, travel, entertainment, any recommendation query",
        "type": "specialist",
    },
    "The Insider": {
        "description": "Deep domain and local knowledge. Knows what's real vs. hype, what locals actually do, and what the algorithms won't surface. Seasonal and context-aware.",
        "auto_assign": "Travel, food, local exploration, niche hobbies",
        "type": "specialist",
    },
    "The Experience Designer": {
        "description": "Thinks about the full arc of an experience — timing, pairings, atmosphere, transitions. Not just what to do, but how to sequence it for maximum impact.",
        "auto_assign": "Travel itineraries, dining, events, gift-giving",
        "type": "specialist",
    },
}

FUN_PERSONAS = {
    "The Jokester": {
        "description": "Treats everything like a comedy roast. Will mock bad ideas mercilessly but always lands on an actual recommendation buried in the bit.",
        "type": "fun",
    },
    "The Trickster": {
        "description": "Gives advice that sounds wrong but might be genius. Proposes the lateral, counterintuitive approach.",
        "type": "fun",
    },
    "The Cheater": {
        "description": "Finds every shortcut, hack, and loophole. Why build it when you can fake it? Why solve the problem when you can redefine it?",
        "type": "fun",
    },
    "The Conspiracy Theorist": {
        "description": "Sees hidden connections everywhere. Paranoid but occasionally spots patterns everyone else missed.",
        "type": "fun",
    },
    "The Time Traveler": {
        "description": "Answers from 10 years in the future. Annoyingly smug but sometimes genuinely prescient.",
        "type": "fun",
    },
    "The Intern": {
        "description": "Enthusiastic, slightly confused, asks \"dumb\" questions that turn out to be devastatingly insightful.",
        "type": "fun",
    },
}

ALL_PERSONAS = {**CORE_PERSONAS, **SPECIALIST_PERSONAS, **FUN_PERSONAS}

# ---------------------------------------------------------------------------
# Topic Classification
# ---------------------------------------------------------------------------

TOPIC_KEYWORDS = {
    "architecture": [
        "architect", "infrastructure", "system design", "database", "schema",
        "api", "backend", "frontend", "microservice", "monolith", "deploy",
        "docker", "kubernetes", "aws", "cloud", "server", "cache", "redis",
        "postgres", "sqlite", "mongo", "queue", "websocket", "sse", "polling",
        "ci/cd", "pipeline", "migration", "refactor", "integration", "stack",
        "framework", "library", "dependency", "scaling", "performance",
    ],
    "product": [
        "feature", "user experience", "ux", "ui", "onboarding", "retention",
        "conversion", "funnel", "signup", "login", "dashboard", "notification",
        "mobile", "responsive", "accessibility", "design", "prototype", "mvp",
        "roadmap", "release", "launch", "beta", "feedback", "survey",
    ],
    "business": [
        "pricing", "revenue", "cost", "budget", "roi", "investment", "funding",
        "business model", "subscription", "saas", "b2b", "b2c", "contract",
        "negotiate", "hire", "salary", "equity", "valuation", "profit",
        "margin", "enterprise", "compliance", "legal", "license",
    ],
    "personal": [
        "career", "job", "quit", "resign", "relocate", "life",
        "decision", "family", "relationship", "freelance", "remote",
        "balance", "burnout", "motivation",
    ],
    "travel": [
        "travel", "trip", "vacation", "destination", "hotel", "flight",
        "itinerary", "visit", "explore", "tourism", "airbnb", "hostel",
        "airport", "road trip", "backpack", "cruise", "resort",
        "city guide", "sightseeing", "layover", "weekend getaway",
    ],
    "food_drink": [
        "restaurant", "food", "dining", "eat", "eating", "chef", "cuisine",
        "recipe", "cooking", "meal", "bar", "cocktail", "wine", "coffee",
        "cafe", "brunch", "dinner", "lunch", "breakfast", "tasting",
        "reservation", "michelin", "street food", "brewery", "distillery",
        "bakery", "menu",
    ],
    "home_life": [
        "pet", "dog", "cat", "puppy", "kitten", "garden", "gardening",
        "plant", "yard", "home improvement", "renovation", "decor",
        "interior design", "cleaning", "organizing", "furniture", "diy",
        "landscaping", "apartment", "house", "neighborhood", "vet", "breed",
        "train a dog", "train a puppy", "train a cat",
    ],
    "wellness": [
        "fitness", "workout", "exercise", "gym", "health", "meditation",
        "yoga", "sleep", "diet", "nutrition", "mental health", "therapy",
        "self-care", "running", "weight", "stress", "mindfulness",
        "recovery", "supplements", "habit",
    ],
    "personal_finance": [
        "budget", "savings", "invest", "investing", "retirement", "mortgage",
        "debt", "credit", "insurance", "tax", "portfolio", "stocks",
        "etf", "401k", "ira", "real estate", "net worth", "emergency fund",
        "financial planning", "compound interest",
    ],
    "learning": [
        "learn", "course", "tutorial", "skill", "certification", "degree",
        "bootcamp", "self-taught", "book", "reading list", "practice",
        "mentor", "study", "workshop", "class", "curriculum", "hobby",
        "creative", "craft", "photography", "music", "writing",
    ],
    "marketing": [
        "marketing", "brand", "growth", "seo", "content", "social media",
        "advertising", "campaign", "audience", "engagement", "viral",
        "distribution", "channel", "influencer", "newsletter", "community",
        "launch", "product hunt", "hacker news",
    ],
    "debugging": [
        "bug", "debug", "error", "fix", "broken", "crash", "stuck", "issue",
        "problem", "failing", "slow", "timeout", "memory", "leak", "race",
        "condition", "deadlock", "exception", "traceback",
    ],
    "strategic": [
        "strategy", "vision", "long-term", "big picture", "pivot", "direction",
        "mission", "goal", "objective", "competitive", "market", "trend",
        "disruption", "innovation", "future",
    ],
}

TOPIC_TO_PERSONAS = {
    "architecture": ["The Contrarian", "The Pragmatist", "The Systems Thinker"],
    "product":      ["The Contrarian", "The User Advocate", "The Growth Hacker"],
    "business":     ["The Contrarian", "The Economist", "The Risk Analyst"],
    "personal":     ["The Contrarian", "The Pragmatist", "The Outsider"],
    "marketing":    ["The Contrarian", "The User Advocate", "The Growth Hacker"],
    "debugging":    ["The Contrarian", "The Pragmatist", "The Systems Thinker"],
    "strategic":    ["The Contrarian", "The Visionary", "The Radical"],
    "travel":           ["The Contrarian", "The Insider", "The Experience Designer"],
    "food_drink":       ["The Contrarian", "The Curator", "The Insider"],
    "home_life":        ["The Contrarian", "The Pragmatist", "The Craftsperson"],
    "wellness":         ["The Contrarian", "The Pragmatist", "The Outsider"],
    "personal_finance": ["The Contrarian", "The Economist", "The Risk Analyst"],
    "learning":         ["The Contrarian", "The Outsider", "The Pragmatist"],
}

AGENT_ORDER = ["advisor_1", "advisor_2", "advisor_3"]

# ---------------------------------------------------------------------------
# Tips (rotated in briefings/verdicts to surface discoverable features)
# ---------------------------------------------------------------------------

TIPS = [
    'Say "archive this" to save a Markdown copy to ~/Documents/council/',
    "/rate 1-5 to rate this session — higher-rated advice surfaces more in future councils",
    "Use /council-debate to stress-test a decision the council agreed on",
    '/council-outcome followed "what happened" tracks whether advice worked out',
    'Say "show me the raw response from Advisor 1" for the full unabridged take',
    "/council-history to browse, recap, or resume past sessions",
    "Use --fun to add a chaotic persona like The Jokester or The Time Traveler",
    'Use --personas "Contrarian, Economist, Radical" to pick your own council',
    "The council remembers past sessions — related history is included automatically",
    "Run /council-help for a quick reference of all commands and features",
    'Say "show full brief" or use --full to see the complete briefing with per-advisor positions and disagreement matrix',
]

# Maps old provider-based keys to new advisor keys (for backward compat)
LEGACY_KEY_MAP = {"codex": "advisor_1", "gemini": "advisor_2", "claude": "advisor_3"}
LEGACY_KEYS = set(LEGACY_KEY_MAP.keys())

# ---------------------------------------------------------------------------
# Stop Words (for keyword extraction / similarity)
# ---------------------------------------------------------------------------

STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "it", "that", "this", "was", "are",
    "be", "has", "had", "have", "will", "would", "could", "should", "may",
    "might", "can", "do", "does", "did", "not", "no", "so", "if", "as",
    "we", "i", "you", "they", "he", "she", "my", "your", "our", "their",
    "its", "what", "which", "who", "how", "when", "where", "why", "all",
    "each", "every", "both", "few", "more", "most", "other", "some", "such",
    "than", "too", "very", "just", "about", "above", "after", "again",
    "also", "am", "any", "because", "been", "before", "being", "between",
    "down", "during", "even", "get", "going", "got", "here", "him", "his",
    "into", "like", "make", "me", "much", "need", "new", "now", "only",
    "one", "out", "over", "own", "really", "right", "same", "say", "see",
    "still", "take", "tell", "then", "there", "these", "thing", "think",
    "those", "through", "time", "up", "us", "use", "want", "way", "well",
    "were", "while",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def emit(data):
    """Print JSON to stdout."""
    json.dump(data, sys.stdout, indent=2, default=str)
    sys.stdout.write("\n")


def err(msg):
    """Print error to stderr and exit."""
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def read_stdin_json():
    """Read JSON from stdin."""
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError as e:
        err(f"invalid JSON on stdin: {e}")


def extract_keywords(text):
    """Extract meaningful keywords from text."""
    words = re.findall(r"[a-z]+", text.lower())
    return {w for w in words if w not in STOP_WORDS and len(w) > 2}


def slugify(text, max_len=40):
    """Create a kebab-case slug from text."""
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    if len(slug) > max_len:
        slug = slug[:max_len].rsplit("-", 1)[0]
    return slug


def ensure_dirs():
    """Create session and archive directories if needed."""
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)


def normalize_legacy_keys(data):
    """Normalize session data in-memory: legacy keys, field names, response formats."""
    # Normalize personas dict
    personas = data.get("personas", {})
    if any(k in LEGACY_KEYS for k in personas):
        new_personas = {}
        for old, new in LEGACY_KEY_MAP.items():
            if old in personas:
                new_personas[new] = personas[old]
        data["personas"] = new_personas

    # Add labels from legacy keys if not present
    if "labels" not in data and any(k in LEGACY_KEYS for k in personas):
        data["labels"] = {
            "advisor_1": "Codex (OpenAI)",
            "advisor_2": "Gemini (Google)",
            "advisor_3": "Claude (Anthropic)",
        }

    # Normalize round data
    for rnd in data.get("rounds", []):
        # Legacy advisor key remap (codex/gemini/claude → advisor_1/2/3)
        for old, new in LEGACY_KEY_MAP.items():
            if old in rnd and new not in rnd:
                rnd[new] = rnd.pop(old)

        # Normalize "briefing" → "synthesis" (schema drift fix)
        if "briefing" in rnd and "synthesis" not in rnd:
            rnd["synthesis"] = rnd.pop("briefing")

        # Flatten "responses" array format → advisor_1/2/3 keys
        if "responses" in rnd:
            responses = rnd.pop("responses")
            if isinstance(responses, list):
                for i, resp in enumerate(responses):
                    key = f"advisor_{i + 1}"
                    if key not in rnd:
                        rnd[key] = resp.get("response", "") if isinstance(resp, dict) else resp
            elif isinstance(responses, dict):
                for key, val in responses.items():
                    if key not in rnd:
                        rnd[key] = val.get("response", "") if isinstance(val, dict) else val

        # Flatten nested advisor objects → plain strings
        for key in ["advisor_1", "advisor_2", "advisor_3"]:
            if key in rnd and isinstance(rnd[key], dict):
                rnd[key] = rnd[key].get("response", "")

    return data


def load_session(session_id):
    """Load a session by ID, searching for matching file. Normalizes schema on read."""
    for f in SESSIONS_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text())
            if data.get("id") == session_id:
                return normalize_legacy_keys(data), f
        except (json.JSONDecodeError, KeyError):
            continue
    return None, None


def list_sessions():
    """List all sessions sorted by date (most recent first)."""
    sessions = []
    for f in sorted(SESSIONS_DIR.glob("*.json"), reverse=True):
        try:
            data = json.loads(f.read_text())
            sessions.append({
                "id": data.get("id", f.stem),
                "type": data.get("type", "council"),
                "date": data.get("date", "unknown"),
                "topic": data.get("topic", "unknown"),
                "question": data.get("question", ""),
                "rounds": len(data.get("rounds", [])),
                "archived": data.get("archived", False),
                "rating": data.get("rating"),
                "outcome": data.get("outcome"),
                "file": str(f),
            })
        except (json.JSONDecodeError, KeyError):
            continue
    return sessions


def lookup_persona(name):
    """Look up a persona by name (case-insensitive, with or without 'The ')."""
    # Try exact match first
    if name in ALL_PERSONAS:
        return name, ALL_PERSONAS[name]
    # Try with "The " prefix
    with_the = f"The {name}"
    if with_the in ALL_PERSONAS:
        return with_the, ALL_PERSONAS[with_the]
    # Case-insensitive search
    lower = name.lower().strip()
    for pname, pdata in ALL_PERSONAS.items():
        if pname.lower() == lower or pname.lower().replace("the ", "") == lower:
            return pname, pdata
    return None, None


# ---------------------------------------------------------------------------
# Internal logic (shared by subcommands and pipeline/finalize)
# ---------------------------------------------------------------------------

def _historian_logic(question):
    """Find past sessions related to a question. Returns dict with 'related' and 'query_keywords'."""
    question_keywords = extract_keywords(question)
    if not question_keywords:
        return {"related": [], "query_keywords": [], "message": "no keywords extracted from question"}

    sessions = list_sessions()
    scored = []
    for s in sessions:
        session_text = f"{s['topic']} {s['question']}"
        session_keywords = extract_keywords(session_text)
        if not session_keywords:
            continue
        overlap = question_keywords & session_keywords
        if overlap:
            base_score = len(overlap) / len(question_keywords | session_keywords)

            rating = s.get("rating") or 3
            rating_weight = rating / 3.0

            outcome = s.get("outcome")
            outcome_weight = 1.0
            if outcome and isinstance(outcome, dict):
                status = outcome.get("status", "")
                if status == "followed":
                    outcome_weight = 1.2
                elif status == "wrong":
                    outcome_weight = 0.5
                elif status == "partial":
                    outcome_weight = 0.9
                elif status == "ignored":
                    outcome_weight = 0.8

            weighted_score = base_score * rating_weight * outcome_weight

            scored.append({
                **s,
                "relevance_score": round(weighted_score, 3),
                "base_score": round(base_score, 3),
                "rating_weight": round(rating_weight, 2),
                "outcome_weight": outcome_weight,
                "matching_keywords": sorted(overlap),
            })

    scored.sort(key=lambda x: x["relevance_score"], reverse=True)
    related = [s for s in scored if s["relevance_score"] > 0.05][:3]

    return {"related": related, "query_keywords": sorted(question_keywords)}


def _assign_logic(question, topic=None, personas_str=None, fun=False, seats=3):
    """Assign personas to agents. Returns dict with 'assignment', 'personas', 'agents', 'fun_applied'."""
    question_lower = question.lower()

    if personas_str:
        names = [n.strip() for n in personas_str.split(",")]
        personas = []
        for n in names:
            pname, pdata = lookup_persona(n)
            if pname:
                personas.append(pname)
            else:
                return {"error": f"unknown persona: {n}"}
    elif topic and topic in TOPIC_TO_PERSONAS:
        personas = list(TOPIC_TO_PERSONAS[topic])
    else:
        scores = {}
        for category, keywords in TOPIC_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in question_lower)
            if score > 0:
                scores[category] = score
        detected_topic = max(scores, key=scores.get) if scores else "architecture"
        personas = list(TOPIC_TO_PERSONAS.get(detected_topic, TOPIC_TO_PERSONAS["architecture"]))

    if len(personas) > seats:
        personas = personas[:seats]
    while len(personas) < seats:
        available = [p for p in SPECIALIST_PERSONAS if p not in personas]
        if available:
            personas.append(random.choice(available))
        else:
            break

    if fun:
        fun_persona = random.choice(list(FUN_PERSONAS.keys()))
        replaceable = [i for i, p in enumerate(personas) if p != "The Contrarian"]
        if replaceable:
            idx = random.choice(replaceable)
            personas[idx] = fun_persona

    agents = AGENT_ORDER[:seats]
    assignment = {}
    for i, agent in enumerate(agents):
        pname = personas[i] if i < len(personas) else personas[-1]
        assignment[agent] = {
            "persona": pname,
            "description": ALL_PERSONAS.get(pname, {}).get("description", ""),
        }

    return {
        "assignment": assignment,
        "personas": personas,
        "agents": agents,
        "fun_applied": fun,
    }


def _prompt_logic(persona_name, question, prior_context=None, context=None):
    """Build an agent prompt for a new session. Returns dict with 'prompt' and 'persona'."""
    pname, pdata = lookup_persona(persona_name)
    if not pname:
        return {"error": f"unknown persona: {persona_name}"}

    desc = pdata["description"]

    prior_block = ""
    if prior_context:
        prior_block = f"\n{prior_context}\n"

    context_block = ""
    if context:
        context_block = f"\nCONTEXT:\n{context}\n"

    prompt = f"""You are one member of a council of AI advisors being consulted on a question.

YOUR ROLE: You are playing **{pname}** — {desc}
Stay in character. Let this perspective shape your analysis, priorities, and recommendations.
Be specific and opinionated — don't hedge. If you disagree with conventional wisdom, say so.
{prior_block}{context_block}
QUESTION:
{question}

Respond concisely (under 500 words). Focus on your strongest recommendation and key reasoning, filtered through your assigned role.

For each key claim, tag it with one of:
- [ANCHORED] — based on specific data, evidence, or established fact
- [INFERRED] — logical deduction from known information
- [SPECULATIVE] — opinion, gut feel, or hypothesis without direct evidence

End your response with a single sentence starting with "RECOMMENDATION: I recommend..." that captures your core advice."""

    return {"prompt": prompt.strip(), "persona": pname}


def _session_create_logic(question, topic=None, personas_json_str=None, labels_json_str=None, prior_context=None):
    """Create a new session. Returns dict with 'id', 'file', 'session'."""
    ensure_dirs()
    now = datetime.now()
    topic_val = topic or question[:50]
    slug = slugify(topic_val)
    session_id = now.strftime(f"%Y-%m-%d-%H-%M-{slug}")
    filename = f"{session_id}.json"

    try:
        personas = json.loads(personas_json_str) if personas_json_str else {}
    except json.JSONDecodeError:
        return {"error": "invalid JSON for personas"}

    try:
        labels = json.loads(labels_json_str) if labels_json_str else {}
    except json.JSONDecodeError:
        return {"error": "invalid JSON for labels"}

    session = {
        "id": session_id,
        "topic": topic_val,
        "question": question,
        "date": now.strftime("%Y-%m-%d"),
        "personas": personas,
        "labels": labels,
        "prior_context": prior_context,
        "rounds": [],
        "archived": False,
    }

    filepath = SESSIONS_DIR / filename
    filepath.write_text(json.dumps(session, indent=2))
    return {"id": session_id, "file": str(filepath), "session": session}


def _similarity_logic(responses):
    """Check Jaccard similarity between responses. Returns dict with 'pairs', 'average_similarity', 'high_consensus'."""
    # Normalize legacy keys if present
    for old, new in LEGACY_KEY_MAP.items():
        if old in responses and new not in responses:
            responses[new] = responses.pop(old)

    keyword_sets = {}
    for agent, text in responses.items():
        keyword_sets[agent] = extract_keywords(str(text))

    pairs = []
    agents = list(keyword_sets.keys())
    for i in range(len(agents)):
        for j in range(i + 1, len(agents)):
            a, b = agents[i], agents[j]
            sa, sb = keyword_sets[a], keyword_sets[b]
            if sa or sb:
                union = sa | sb
                intersection = sa & sb
                jaccard = len(intersection) / len(union) if union else 0
            else:
                jaccard = 0
            pairs.append({
                "agents": [a, b],
                "jaccard": round(jaccard, 3),
                "shared_keywords": sorted(sa & sb) if sa and sb else [],
            })

    scores = [p["jaccard"] for p in pairs]
    avg_similarity = round(sum(scores) / len(scores), 3) if scores else 0
    high_consensus = avg_similarity > 0.6

    return {
        "pairs": pairs,
        "average_similarity": avg_similarity,
        "high_consensus": high_consensus,
    }


def _synthesis_prompt_logic(responses, question, personas_json_str=None, labels_json_str=None,
                            prior_context=None, agent_status=None, mode=None, compact=False):
    """Build a synthesis prompt from agent responses. Returns dict with 'prompt'."""
    # Normalize legacy keys
    for old, new in LEGACY_KEY_MAP.items():
        if old in responses and new not in responses:
            responses[new] = responses.pop(old)

    try:
        personas_map = json.loads(personas_json_str) if isinstance(personas_json_str, str) and personas_json_str else {}
    except json.JSONDecodeError:
        personas_map = {}

    try:
        labels_map = json.loads(labels_json_str) if isinstance(labels_json_str, str) and labels_json_str else {}
    except json.JSONDecodeError:
        labels_map = {}

    label_values = [labels_map.get(a, "") for a in AGENT_ORDER if a in responses]
    all_same_label = len(set(label_values)) <= 1 and all(label_values)

    responses_block = ""
    advisor_headers = []
    for agent in AGENT_ORDER:
        if agent in responses:
            resp = responses[agent]
            if isinstance(resp, dict):
                persona = resp.get("persona", personas_map.get(agent, "Unknown"))
                text = resp.get("response", "")
            else:
                persona = personas_map.get(agent, "Unknown")
                text = str(resp)
            label = labels_map.get(agent, agent)
            if all_same_label:
                header = f"**{persona}**"
            else:
                header = f"**{label} as {persona}**"
            advisor_headers.append((header, persona, label))
            responses_block += f"\n{header}:\n{text}\n"

    prior_line = ""
    if prior_context:
        prior_line = f"\nPrior context: {prior_context}\n"

    if all_same_label:
        personas_line = ", ".join(h[1] for h in advisor_headers)
        advisor_lines = "\n\n".join(
            f"{h[0]}: [2-3 sentence summary of their position + their RECOMMENDATION]"
            for h in advisor_headers
        )
        matrix_headers = " | ".join(h[1] for h in advisor_headers)
    else:
        personas_line = ", ".join(f"{h[2]} as {h[1]}" for h in advisor_headers)
        advisor_lines = "\n\n".join(
            f"{h[0]}: [2-3 sentence summary of their position + their RECOMMENDATION]"
            for h in advisor_headers
        )
        matrix_headers = " | ".join(f"{h[2]} ({h[1]})" for h in advisor_headers)

    matrix_positions = " | ".join("[2-5 word position]" for _ in advisor_headers)

    status_line = ""
    if agent_status:
        try:
            agent_status_obj = json.loads(agent_status) if isinstance(agent_status, str) else agent_status
            status_parts = []
            for cli in ["codex", "gemini", "claude"]:
                if cli in agent_status_obj.get("agents", {}):
                    info = agent_status_obj["agents"][cli]
                    status_parts.append(f"{info['label'].split(' ')[0]} {'OK' if info['available'] else 'Missing'}")
            cli_helper = "Active" if agent_status_obj.get("cli_helper_active", True) else "Inactive"
            mode_val = mode or "parallel"
            status_line = f"\n*Agents: {', '.join(status_parts)} | CLI Helper: {cli_helper} | Mode: {mode_val}*"
        except (json.JSONDecodeError, KeyError):
            pass

    tip = random.choice(TIPS)

    full_format = f"""Produce a briefing in this EXACT format:

---

**Council Briefing: [Topic]**
*Personas: {personas_line}*{status_line}

{advisor_lines}

**Evidence Audit:** [If any consensus point rests primarily on [SPECULATIVE] claims from multiple advisors, flag it. If all key claims are anchored or inferred, write "All key claims grounded." 1-2 sentences.]

**What To Do Next:**
- [ ] [Concrete action item starting with a verb — the single most important next step]
- [ ] [Second action item — verb-first, specific and actionable]
- [ ] [Third action item (optional) — only if genuinely distinct from the first two]

**Disagreement Matrix:**

| Topic | {matrix_headers} |
|-------|{"|".join("---" for _ in advisor_headers)}|
| [Key issue 1] | {matrix_positions} |
| [Key issue 2] | {matrix_positions} |

Note which disagreements stem from persona framing vs genuine analytical divergence.

**Consensus:** [What the council agrees on. 2-4 sentences maximum.]

**Key Tension:** [The single most important unresolved trade-off. Frame it as a clear choice, not a hedge.]

---

> **Tip:** {tip}"""

    compact_block = ""
    if compact:
        compact_block = f"""

After the full briefing above, output the exact delimiter line:

===COMPACT===

Then output a compact version of the briefing in this EXACT format:

**Council Briefing: [Topic]**
*Personas: {personas_line} | Mode: {mode or "parallel"}*

[3-5 sentence synthesis: the core recommendation, where advisors agree, and the key tension as one sentence. Do NOT list individual advisor positions — synthesize into a unified narrative.]

**Do Next:**
- [ ] [Most important action item — verb-first]
- [ ] [Second action item — verb-first]

> Say "show full brief" or use `--full` for per-advisor positions, disagreement matrix, and evidence audit."""

    prompt = f"""You are the neutral mediator for a council of AI advisors. Synthesize their responses.

QUESTION: {question}
{prior_line}
AGENT RESPONSES:
{responses_block}

{full_format}{compact_block}"""

    return {"prompt": prompt.strip()}


def _session_append_logic(session_id, round_data):
    """Append round data to a session. Returns dict with 'id', 'round', 'session'."""
    data, filepath = load_session(session_id)
    if not data:
        return {"error": f"session not found: {session_id}"}

    round_data["round"] = len(data.get("rounds", [])) + 1
    data.setdefault("rounds", []).append(round_data)
    filepath.write_text(json.dumps(data, indent=2))
    return {"id": session_id, "round": round_data["round"], "session": data}


# ---------------------------------------------------------------------------
# Subcommand: parse
# ---------------------------------------------------------------------------

def cmd_parse(args):
    """Parse a /council command string into structured flags."""
    raw = args.raw
    # Strip leading /council if present
    raw = re.sub(r"^/council\s*", "", raw).strip()

    result = {
        "fun": False,
        "full": False,
        "mode": "parallel",
        "personas": None,
        "question": "",
    }

    # Extract --full
    if re.search(r"--full\b", raw):
        result["full"] = True
        raw = re.sub(r"--full\s*", "", raw).strip()

    # Extract --fun
    if re.search(r"--fun\b", raw):
        result["fun"] = True
        raw = re.sub(r"--fun\s*", "", raw).strip()

    # Extract --mode
    mode_match = re.search(r"--mode\s+(parallel|staggered|sequential)", raw)
    if mode_match:
        result["mode"] = mode_match.group(1)
        raw = raw[:mode_match.start()] + raw[mode_match.end():]
        raw = raw.strip()

    # Extract --personas (quoted string)
    personas_match = re.search(r'--personas\s+"([^"]+)"', raw)
    if not personas_match:
        personas_match = re.search(r"--personas\s+'([^']+)'", raw)
    if personas_match:
        names = [n.strip() for n in personas_match.group(1).split(",")]
        resolved = []
        for n in names:
            pname, _ = lookup_persona(n)
            resolved.append(pname if pname else n)
        result["personas"] = resolved
        raw = raw[:personas_match.start()] + raw[personas_match.end():]
        raw = raw.strip()

    # Extract --seats N
    seats_match = re.search(r"--seats\s+(\d+)", raw)
    if seats_match:
        result["seats"] = int(seats_match.group(1))
        raw = raw[:seats_match.start()] + raw[seats_match.end():]
        raw = raw.strip()

    result["question"] = raw
    emit(result)


# ---------------------------------------------------------------------------
# Subcommand: topic
# ---------------------------------------------------------------------------

def cmd_topic(args):
    """Classify the topic of a question."""
    question = args.question.lower()
    scores = {}
    for category, keywords in TOPIC_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in question)
        if score > 0:
            scores[category] = score

    if not scores:
        topic = "architecture"  # default fallback
    else:
        topic = max(scores, key=scores.get)

    emit({
        "topic": topic,
        "scores": scores,
        "personas": TOPIC_TO_PERSONAS.get(topic, TOPIC_TO_PERSONAS["architecture"]),
    })


# ---------------------------------------------------------------------------
# Subcommand: assign
# ---------------------------------------------------------------------------

def cmd_assign(args):
    """Assign personas to agents for a session."""
    seats = getattr(args, "seats", 3) or 3
    result = _assign_logic(args.question, topic=args.topic, personas_str=args.personas, fun=args.fun, seats=seats)
    if "error" in result:
        err(result["error"])
    emit(result)


# ---------------------------------------------------------------------------
# Subcommand: prompt
# ---------------------------------------------------------------------------

def cmd_prompt(args):
    """Build an agent prompt."""
    if args.followup:
        # Follow-up round prompt — not handled by _prompt_logic
        pname, pdata = lookup_persona(args.persona)
        if not pname:
            err(f"unknown persona: {args.persona}")
        if not args.previous_position:
            err("--previous-position required for follow-up prompts")

        desc = pdata["description"]
        other_positions = args.other_positions or "No other positions provided."
        mediator_synthesis = args.mediator_synthesis or ""
        user_followup = args.user_followup or ""

        prompt = f"""You are a member of a council of AI advisors in an ongoing discussion.

YOUR ROLE: You are playing **{pname}** — {desc}
Stay in character for this follow-up as well.

PREVIOUS QUESTION: {args.question}

YOUR PREVIOUS POSITION: {args.previous_position}

THE OTHER ADVISORS SAID:
{other_positions}

{f"THE MEDIATOR SAID: {mediator_synthesis}" if mediator_synthesis else ""}

THE USER NOW SAYS: {user_followup}

Respond to the user's follow-up. You may revise your position if the user raises a good point, or defend it if you still disagree. Stay concise (under 300 words).

Tag key claims as [ANCHORED], [INFERRED], or [SPECULATIVE].

End with a single sentence starting with "RECOMMENDATION: I recommend..." that captures your updated core advice."""

        emit({"prompt": prompt.strip(), "persona": pname})
    else:
        # New session prompt
        result = _prompt_logic(args.persona, args.question, prior_context=args.prior_context, context=args.context)
        if "error" in result:
            err(result["error"])
        emit(result)


# ---------------------------------------------------------------------------
# Subcommand: synthesis-prompt
# ---------------------------------------------------------------------------

def cmd_synthesis_prompt(args):
    """Build a synthesis prompt from agent responses."""
    if args.stdin:
        data = read_stdin_json()
    else:
        err("--stdin required: pipe agent responses as JSON")

    result = _synthesis_prompt_logic(
        data, args.question,
        personas_json_str=args.personas_json,
        labels_json_str=args.labels_json,
        prior_context=args.prior_context,
        agent_status=args.agent_status,
        mode=args.mode,
        compact=args.compact,
    )
    emit(result)


# ---------------------------------------------------------------------------
# Subcommand: session
# ---------------------------------------------------------------------------

def cmd_session(args):
    """Manage council sessions."""
    ensure_dirs()
    action = args.session_action

    if action == "create":
        if not args.question:
            err("--question required for session create")
        now = datetime.now()
        topic = args.topic or args.question[:50]
        slug = slugify(topic)
        session_id = now.strftime(f"%Y-%m-%d-%H-%M-{slug}")
        filename = f"{session_id}.json"

        try:
            personas = json.loads(args.personas_json) if args.personas_json else {}
        except json.JSONDecodeError:
            err("invalid JSON for --personas")

        try:
            labels = json.loads(args.labels_json) if args.labels_json else {}
        except json.JSONDecodeError:
            err("invalid JSON for --labels")

        session = {
            "id": session_id,
            "topic": topic,
            "question": args.question,
            "date": now.strftime("%Y-%m-%d"),
            "personas": personas,
            "labels": labels,
            "prior_context": args.prior_context,
            "rounds": [],
            "archived": False,
        }

        filepath = SESSIONS_DIR / filename
        filepath.write_text(json.dumps(session, indent=2))
        emit({"id": session_id, "file": str(filepath), "session": session})

    elif action == "load":
        if not args.id:
            err("--id required for session load")
        data, filepath = load_session(args.id)
        if not data:
            err(f"session not found: {args.id}")
        emit({"session": data, "file": str(filepath)})

    elif action == "append":
        if not args.id:
            err("--id required for session append")
        data, filepath = load_session(args.id)
        if not data:
            err(f"session not found: {args.id}")

        if args.stdin:
            round_data = read_stdin_json()
        else:
            err("--stdin required: pipe round data as JSON")

        # Assign round number
        round_data["round"] = len(data.get("rounds", [])) + 1
        data.setdefault("rounds", []).append(round_data)
        filepath.write_text(json.dumps(data, indent=2))
        emit({"id": args.id, "round": round_data["round"], "session": data})

    elif action == "list":
        sessions = list_sessions()
        emit({"sessions": sessions, "count": len(sessions)})

    elif action == "rate":
        if not args.id:
            err("--id required for session rate")
        if args.rating is None:
            err("--rating required (1-5)")
        data, filepath = load_session(args.id)
        if not data:
            err(f"session not found: {args.id}")
        data["rating"] = args.rating
        filepath.write_text(json.dumps(data, indent=2))
        emit({"id": args.id, "rating": args.rating})

    elif action == "outcome":
        if not args.id:
            err("--id required for session outcome")
        if not args.status:
            err("--status required")
        data, filepath = load_session(args.id)
        if not data:
            err(f"session not found: {args.id}")
        data["outcome"] = {
            "status": args.status,
            "note": args.note or "",
            "date": datetime.now().strftime("%Y-%m-%d"),
        }
        filepath.write_text(json.dumps(data, indent=2))
        emit({"id": args.id, "outcome": data["outcome"]})

    else:
        err(f"unknown session action: {action}")


# ---------------------------------------------------------------------------
# Subcommand: historian
# ---------------------------------------------------------------------------

def cmd_historian(args):
    """Find past sessions related to a question, weighted by rating and outcome."""
    emit(_historian_logic(args.question))


# ---------------------------------------------------------------------------
# Subcommand: similarity
# ---------------------------------------------------------------------------

def cmd_similarity(args):
    """Check Jaccard similarity between agent responses."""
    if args.stdin:
        data = read_stdin_json()
    else:
        err("--stdin required: pipe responses as JSON object")

    emit(_similarity_logic(data))


# ---------------------------------------------------------------------------
# Subcommand: agents (fast PATH check)
# ---------------------------------------------------------------------------

AGENT_CLIS = {
    "codex": {"label": "Codex (OpenAI)", "install": "npm install -g @openai/codex"},
    "gemini": {"label": "Gemini (Google)", "install": "npm install -g @google/gemini-cli"},
    "claude": {"label": "Claude (Anthropic)", "install": "https://docs.anthropic.com/en/docs/claude-code"},
}


def cmd_agents(args):
    """Fast check: which agent CLIs are on PATH (shutil.which only)."""
    agents = {}
    for cli, info in AGENT_CLIS.items():
        path = shutil.which(cli)
        agents[cli] = {
            "available": path is not None,
            "path": path,
            "label": info["label"],
            "install": info["install"],
        }

    available = [c for c, a in agents.items() if a["available"]]
    missing = [c for c, a in agents.items() if not a["available"]]

    if len(available) == 3:
        mode_suggestion = "all-3"
    elif len(available) == 0:
        mode_suggestion = "none"
    elif available == ["claude"]:
        mode_suggestion = "claude-only"
    else:
        mode_suggestion = "partial"

    emit({
        "agents": agents,
        "available": available,
        "missing": missing,
        "count": len(available),
        "mode_suggestion": mode_suggestion,
    })


# ---------------------------------------------------------------------------
# Subcommand: doctor (thorough health check)
# ---------------------------------------------------------------------------

def cmd_doctor(args):
    """Thorough health check: run --version on each CLI, verify dirs, check helpers."""
    # Agent CLI checks (actually run --version)
    agents = {}
    for cli, info in AGENT_CLIS.items():
        path = shutil.which(cli)
        version = None
        healthy = False
        error = None
        if path:
            try:
                result = subprocess.run(
                    [cli, "--version"],
                    capture_output=True, text=True, timeout=10,
                )
                version = result.stdout.strip() or result.stderr.strip()
                healthy = result.returncode == 0
                if not healthy:
                    error = f"exit code {result.returncode}"
            except subprocess.TimeoutExpired:
                error = "timed out"
            except FileNotFoundError:
                error = "not found"
            except Exception as e:
                error = str(e)
        else:
            error = "not on PATH"

        agents[cli] = {
            "available": path is not None,
            "healthy": healthy,
            "path": path,
            "version": version,
            "label": info["label"],
            "install": info["install"],
            "error": error,
        }

    # Directory checks
    dirs = {
        "sessions": {
            "path": str(SESSIONS_DIR),
            "exists": SESSIONS_DIR.exists(),
            "is_dir": SESSIONS_DIR.is_dir() if SESSIONS_DIR.exists() else False,
            "file_count": len(list(SESSIONS_DIR.glob("*.json"))) if SESSIONS_DIR.is_dir() else 0,
        },
        "archive": {
            "path": str(ARCHIVE_DIR),
            "exists": ARCHIVE_DIR.exists(),
            "is_dir": ARCHIVE_DIR.is_dir() if ARCHIVE_DIR.exists() else False,
        },
    }

    # CLI helper checks
    cli_helper = {}
    # Check all known locations
    locations = [
        ("plugin_env", os.environ.get("CLAUDE_PLUGIN_ROOT", "") + "/skills/council/council_cli.py" if os.environ.get("CLAUDE_PLUGIN_ROOT") else ""),
        ("symlink", str(Path.home() / ".claude" / "skills" / "council" / "council_cli.py")),
        ("self", os.path.abspath(__file__)),
    ]
    for name, path in locations:
        if path:
            p = Path(path)
            cli_helper[name] = {
                "path": path,
                "exists": p.exists(),
                "is_symlink": p.is_symlink() if p.exists() else False,
            }

    # Python check
    python_path = shutil.which("python3")
    python_version = None
    if python_path:
        try:
            result = subprocess.run(
                ["python3", "--version"],
                capture_output=True, text=True, timeout=5,
            )
            python_version = result.stdout.strip()
        except Exception:
            pass

    available = [c for c, a in agents.items() if a["healthy"]]
    missing = [c for c, a in agents.items() if not a["available"]]
    unhealthy = [c for c, a in agents.items() if a["available"] and not a["healthy"]]

    emit({
        "agents": agents,
        "available": available,
        "missing": missing,
        "unhealthy": unhealthy,
        "directories": dirs,
        "cli_helper": cli_helper,
        "python": {"path": python_path, "version": python_version},
        "healthy": len(unhealthy) == 0 and dirs["sessions"]["exists"] and dirs["archive"]["exists"],
    })


# ---------------------------------------------------------------------------
# Subcommand: tip
# ---------------------------------------------------------------------------

def cmd_tip(args):
    """Return a random tip."""
    emit({"tip": random.choice(TIPS)})


# ---------------------------------------------------------------------------
# Subcommand: pipeline (pre-dispatch: historian + assign + prompts + session create)
# ---------------------------------------------------------------------------

def cmd_pipeline(args):
    """Single call replacing historian + assign + prompt (x3) + session create + mkdir."""
    ensure_dirs()

    question = args.question
    topic = args.topic
    personas_str = args.personas
    fun = args.fun
    seats = args.seats or 3
    prior_context = args.prior_context
    context = args.context
    labels_json_str = args.labels_json

    # 1. Historian lookup
    historian_result = _historian_logic(question)

    # Build prior context block from historian results
    historian_context = prior_context or ""
    for related in historian_result.get("related", []):
        date = related.get("date", "unknown")
        rtopic = related.get("topic", "unknown")
        rquestion = related.get("question", "")
        outcome = related.get("outcome")
        outcome_line = ""
        if outcome and isinstance(outcome, dict):
            outcome_line = f" Result: {outcome.get('status', 'unknown')} — {outcome.get('note', '')}"
        block = f"PRIOR COUNCIL CONTEXT:\nOn {date}, the council discussed \"{rtopic}\": \"{rquestion}\".{outcome_line}"
        if historian_context:
            historian_context += "\n\n" + block
        else:
            historian_context = block

    # 2. Assign personas
    assign_result = _assign_logic(question, topic=topic, personas_str=personas_str, fun=fun, seats=seats)
    if "error" in assign_result:
        err(assign_result["error"])

    assignment = assign_result["assignment"]
    personas_list = assign_result["personas"]

    # 3. Build prompts for each advisor
    prompts = {}
    for agent, info in assignment.items():
        prompt_result = _prompt_logic(
            info["persona"], question,
            prior_context=historian_context if historian_context else None,
            context=context,
        )
        if "error" in prompt_result:
            err(prompt_result["error"])
        prompts[agent] = prompt_result["prompt"]

    # 4. Create session
    personas_json_map = {agent: info["persona"] for agent, info in assignment.items()}
    session_result = _session_create_logic(
        question,
        topic=topic,
        personas_json_str=json.dumps(personas_json_map),
        labels_json_str=labels_json_str,
        prior_context=historian_context if historian_context else None,
    )
    if "error" in session_result:
        err(session_result["error"])

    emit({
        "session_id": session_result["id"],
        "session_file": session_result["file"],
        "historian": historian_result,
        "assignment": assignment,
        "prompts": prompts,
        "personas": personas_list,
        "fun_applied": assign_result["fun_applied"],
    })


# ---------------------------------------------------------------------------
# Subcommand: finalize (post-dispatch: similarity + synthesis-prompt + session append)
# ---------------------------------------------------------------------------

def cmd_finalize(args):
    """Single call replacing similarity + synthesis-prompt + session append."""
    if not args.stdin:
        err("--stdin required: pipe agent responses as JSON")

    data = read_stdin_json()

    # Normalize: accept both plain text and {persona, response} objects
    responses = {}
    for key, val in data.items():
        if isinstance(val, dict) and "response" in val:
            responses[key] = val["response"]
        else:
            responses[key] = str(val)

    # 1. Similarity check
    similarity_result = _similarity_logic(dict(responses))

    # 2. Build synthesis prompt
    synth_result = _synthesis_prompt_logic(
        dict(data),  # pass original data (may have persona info)
        args.question,
        personas_json_str=args.personas_json,
        labels_json_str=args.labels_json,
        prior_context=args.prior_context,
        agent_status=args.agent_status,
        mode=args.mode,
        compact=args.compact,
    )

    # 3. Session append — save raw responses
    round_data = dict(data)  # raw advisor responses
    append_result = _session_append_logic(args.session_id, round_data)
    if "error" in append_result:
        err(append_result["error"])

    emit({
        "synthesis_prompt": synth_result["prompt"],
        "similarity": similarity_result,
        "session_updated": True,
        "round": append_result["round"],
    })


# ---------------------------------------------------------------------------
# Main: argparse setup
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        prog="council_cli",
        description="CLI helper for the claude-council skill",
    )
    parser.add_argument("--version", action="version", version=f"council_cli {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # parse
    p_parse = subparsers.add_parser("parse", help="Parse /council command string")
    p_parse.add_argument("--raw", required=True, help="Raw command string")

    # topic
    p_topic = subparsers.add_parser("topic", help="Classify question topic")
    p_topic.add_argument("--question", required=True)

    # assign
    p_assign = subparsers.add_parser("assign", help="Assign personas to agents")
    p_assign.add_argument("--question", required=True)
    p_assign.add_argument("--personas", default=None, help="Comma-separated persona names")
    p_assign.add_argument("--topic", default=None, help="LLM-classified topic (e.g. food_drink, travel, architecture). Skips keyword matching.")
    p_assign.add_argument("--fun", action="store_true")
    p_assign.add_argument("--seats", type=int, default=3)

    # prompt
    p_prompt = subparsers.add_parser("prompt", help="Build agent prompt")
    p_prompt.add_argument("--persona", required=True)
    p_prompt.add_argument("--question", required=True)
    p_prompt.add_argument("--prior-context", default=None)
    p_prompt.add_argument("--context", default=None, help="Codebase or background context")
    p_prompt.add_argument("--followup", action="store_true")
    p_prompt.add_argument("--previous-position", default=None)
    p_prompt.add_argument("--other-positions", default=None)
    p_prompt.add_argument("--mediator-synthesis", default=None)
    p_prompt.add_argument("--user-followup", default=None)

    # synthesis-prompt
    p_synth = subparsers.add_parser("synthesis-prompt", help="Build synthesis prompt")
    p_synth.add_argument("--question", required=True)
    p_synth.add_argument("--personas-json", default=None, help="JSON map of agent->persona")
    p_synth.add_argument("--labels-json", default=None, help="JSON map of agent->label (e.g. 'Claude', 'Codex (OpenAI)')")
    p_synth.add_argument("--prior-context", default=None)
    p_synth.add_argument("--agent-status", default=None, help="JSON agent status from 'agents' subcommand for briefing header")
    p_synth.add_argument("--mode", default=None, help="Dispatch mode (parallel/staggered/sequential) for briefing header")
    p_synth.add_argument("--compact", action="store_true", help="Include compact format delimited by ===COMPACT===")
    p_synth.add_argument("--stdin", action="store_true")

    # session (with sub-actions)
    p_session = subparsers.add_parser("session", help="Session CRUD operations")
    p_session.add_argument("session_action", choices=["create", "load", "append", "list", "rate", "outcome"])
    p_session.add_argument("--id", default=None)
    p_session.add_argument("--question", default=None)
    p_session.add_argument("--topic", default=None)
    p_session.add_argument("--personas-json", default=None, help="JSON map of agent->persona")
    p_session.add_argument("--labels-json", default=None, help="JSON map of agent->label")
    p_session.add_argument("--prior-context", default=None)
    p_session.add_argument("--rating", type=int, choices=[1, 2, 3, 4, 5], default=None)
    p_session.add_argument("--status", default=None)
    p_session.add_argument("--note", default=None)
    p_session.add_argument("--stdin", action="store_true")

    # historian
    p_hist = subparsers.add_parser("historian", help="Find related past sessions")
    p_hist.add_argument("--question", required=True)

    # similarity
    p_sim = subparsers.add_parser("similarity", help="Check response similarity")
    p_sim.add_argument("--stdin", action="store_true")

    # agents (fast PATH check)
    subparsers.add_parser("agents", help="Check which agent CLIs are on PATH")

    # doctor (thorough health check)
    subparsers.add_parser("doctor", help="Run thorough health check on all components")

    # tip
    subparsers.add_parser("tip", help="Return a random tip")

    # pipeline (pre-dispatch: historian + assign + prompts + session create)
    p_pipeline = subparsers.add_parser("pipeline", help="Pre-dispatch: historian + assign + prompts + session create")
    p_pipeline.add_argument("--question", required=True)
    p_pipeline.add_argument("--topic", default=None)
    p_pipeline.add_argument("--personas", default=None, help="Comma-separated persona overrides")
    p_pipeline.add_argument("--fun", action="store_true")
    p_pipeline.add_argument("--seats", type=int, default=3)
    p_pipeline.add_argument("--prior-context", default=None)
    p_pipeline.add_argument("--context", default=None, help="Codebase or background context for prompts")
    p_pipeline.add_argument("--labels-json", default=None, help="JSON map of agent->label")

    # finalize (post-dispatch: similarity + synthesis-prompt + session append)
    p_final = subparsers.add_parser("finalize", help="Post-dispatch: similarity + synthesis-prompt + session append")
    p_final.add_argument("--session-id", required=True)
    p_final.add_argument("--question", required=True)
    p_final.add_argument("--personas-json", required=True, help="JSON map of agent->persona")
    p_final.add_argument("--labels-json", default=None, help="JSON map of agent->label")
    p_final.add_argument("--agent-status", default=None, help="JSON agent status for briefing header")
    p_final.add_argument("--mode", default=None, help="Dispatch mode for briefing header")
    p_final.add_argument("--compact", action="store_true", help="Include compact format delimited by ===COMPACT===")
    p_final.add_argument("--prior-context", default=None)
    p_final.add_argument("--stdin", action="store_true")

    args = parser.parse_args()

    dispatch = {
        "parse": cmd_parse,
        "topic": cmd_topic,
        "assign": cmd_assign,
        "prompt": cmd_prompt,
        "synthesis-prompt": cmd_synthesis_prompt,
        "session": cmd_session,
        "historian": cmd_historian,
        "similarity": cmd_similarity,
        "agents": cmd_agents,
        "doctor": cmd_doctor,
        "tip": cmd_tip,
        "pipeline": cmd_pipeline,
        "finalize": cmd_finalize,
    }

    dispatch[args.command](args)


if __name__ == "__main__":
    main()
