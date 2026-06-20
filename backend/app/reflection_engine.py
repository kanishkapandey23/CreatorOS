"""
Adaptive reflection flow — life-focused prompts with mood-aware follow-ups.
"""
import json
import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.database import CreatorProfile, Memory, ReflectionAnswer, ReflectionSession
from app.llm import get_llm

logger = logging.getLogger("creatoros.reflection")

MAX_REFLECTION_QUESTIONS = 3

LIFE_OPENER = {
    "id": "p1",
    "sectionTitle": "Checking in",
    "title": "What's been sitting with you lately?",
    "hint": "A feeling, a conversation, a moment you keep replaying. No need to have it figured out.",
}

LIFE_FOLLOWUPS = [
    {
        "id": "p2",
        "sectionTitle": "The moment",
        "title": "Can you walk me through the exact moment it hit you?",
        "hint": "Where were you? What did you see or hear? Small details make stories real.",
    },
    {
        "id": "p3",
        "sectionTitle": "What shifted",
        "title": "What changed for you after that — even if it was subtle?",
        "hint": "A belief, a feeling, a decision. The turning point doesn't have to be dramatic.",
    },
]

MOOD_KEYWORDS = {
    "reflective": ["think", "wonder", "realize", "pause", "quiet", "alone", "journal"],
    "happy": ["happy", "joy", "excited", "grateful", "laugh", "celebrate", "win", "good"],
    "funny": ["funny", "laugh", "hilarious", "awkward", "ridiculous", "joke"],
    "emotional": ["cry", "tears", "hurt", "miss", "love", "heart", "sad", "grief", "anxious"],
    "motivated": ["motivated", "driven", "energy", "push", "goal", "ready", "fired"],
    "nostalgic": ["remember", "used to", "childhood", "back when", "miss", "old", "past"],
    "uncertain": ["unsure", "confused", "don't know", "lost", "stuck", "maybe", "uncertain"],
}

REFLECTION_SYSTEM = (
    "You are a warm, thoughtful companion helping someone capture personal life stories.\n"
    "RULES:\n"
    "- Ask about LIFE: feelings, relationships, daily moments, growth, conversations, surprises, routines, family, friends.\n"
    "- NEVER ask about code, bugs, APIs, tech stack, deployments, pull requests, or work tools unless they explicitly brought it up.\n"
    "- Questions should feel like a caring friend — not a job interview, survey, or productivity coach.\n"
    "- Reference specific details from their previous answers when generating follow-ups.\n"
    "- Output ONLY valid JSON. No markdown."
)


def _parse_llm_json(raw: str) -> dict:
    cleaned = raw.strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json")[-1].split("```")[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```")[-1].split("```")[0].strip()
    return json.loads(cleaned)


def _keyword_mood(text: str) -> str:
    lower = text.lower()
    scores = {mood: sum(1 for kw in words if kw in lower) for mood, words in MOOD_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "reflective"


def infer_mood_from_answers(answers: list[ReflectionAnswer]) -> str:
    combined = " ".join(a.answer_text for a in answers if a.answer_text)
    if not combined.strip():
        return "reflective"
    return _keyword_mood(combined)


def _session_prompts(session: ReflectionSession) -> list:
    if not session.prompts_json:
        return []
    try:
        data = json.loads(session.prompts_json)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save_session_prompts(session: ReflectionSession, prompts: list, mood: Optional[str] = None):
    session.prompts_json = json.dumps(prompts)
    if mood:
        session.detected_mood = mood


def _build_profile_context(profile: CreatorProfile, recent_memories: list) -> str:
    niche = profile.niche or "creator"
    interests = ", ".join(profile.interests or []) or "life, growth"
    memory_lines = "\n".join([f"- {m.event}" for m in recent_memories[:3]]) or "None yet"
    return (
        f"Creator context (use subtly — this is about their life, not their job):\n"
        f"Niche: {niche}\nInterests: {interests}\n"
        f"Recent stories captured:\n{memory_lines}"
    )


MOOD_OPENERS = {
    "reflective": ("What's been quietly weighing on you?", "A thought, a conversation, something you have not said out loud."),
    "happy": ("What made you smile recently — even something small?", "A person, a moment, a message you re-read."),
    "funny": ("What absurd or awkward thing happened to you lately?", "The kind of story you would tell a friend over chai."),
    "emotional": ("What touched you or caught you off guard recently?", "No need to be dramatic — honesty is enough."),
    "motivated": ("What are you pushing toward right now?", "A goal, a habit, a conversation you need to have."),
    "nostalgic": ("What from your past came back to mind recently?", "A place, a person, an old version of yourself."),
    "uncertain": ("What's feeling unclear or in-between for you?", "Transitions count. You do not need a neat answer."),
}


def generate_opener(
    db: Session,
    profile: CreatorProfile,
    recent_memories: list,
    strategy_vibe: Optional[dict] = None,
) -> dict:
    mood = (strategy_vibe or {}).get("mood")
    if mood and mood in MOOD_OPENERS:
        title, hint = MOOD_OPENERS[mood]
        return {
            "id": "p1",
            "sectionTitle": "Checking in",
            "title": title,
            "hint": hint,
        }

    llm = get_llm()
    vibe_line = ""
    if strategy_vibe:
        vibe_line = f"Strategy vibe check: mood={strategy_vibe.get('mood')}, goal={strategy_vibe.get('goal')}\n"
    user_prompt = (
        f"{vibe_line}"
        f"{_build_profile_context(profile, recent_memories)}\n\n"
        "Generate ONE gentle opening question to understand how this person is feeling lately.\n"
        "It must be about life — emotions, relationships, moments, routines — NOT work or tech.\n"
        'Output JSON: {"prompt": {"id": "p1", "sectionTitle": "short label", "title": "question?", "hint": "gentle nudge"}}'
    )
    try:
        raw = llm.generate(REFLECTION_SYSTEM, user_prompt)
        parsed = _parse_llm_json(raw)
        prompt = parsed.get("prompt", parsed)
        prompt["id"] = "p1"
        return prompt
    except Exception as e:
        logger.error(f"Opener generation failed: {e}")
        return dict(LIFE_OPENER)


def generate_followup(
    db: Session,
    profile: CreatorProfile,
    answers: list[ReflectionAnswer],
    question_index: int,
) -> tuple[dict, str]:
    """Generate next question based on prior Q&A. Returns (prompt, detected_mood)."""
    mood = infer_mood_from_answers(answers)
    history = "\n".join([
        f"Q: {a.prompt_title}\nA: {a.answer_text}"
        for a in answers
    ])
    llm = get_llm()
    user_prompt = (
        f"{_build_profile_context(profile, [])}\n\n"
        f"Detected vibe so far: {mood}\n"
        f"This is follow-up question #{question_index + 1} of {MAX_REFLECTION_QUESTIONS}.\n\n"
        f"Conversation so far:\n{history}\n\n"
        "First, confirm or refine the emotional vibe from their answers.\n"
        "Then generate ONE follow-up that digs deeper into the most story-worthy thread.\n"
        "Reference something specific they mentioned. Stay life-focused — no tech/work jargon.\n"
        'Output JSON: {"detectedMood": "reflective|happy|funny|emotional|motivated|nostalgic|uncertain", '
        f'"prompt": {{"id": "p{question_index + 1}", "sectionTitle": "short label", "title": "question?", "hint": "gentle nudge"}}}}'
    )
    try:
        raw = llm.generate(REFLECTION_SYSTEM, user_prompt)
        parsed = _parse_llm_json(raw)
        prompt = parsed.get("prompt", parsed)
        prompt["id"] = f"p{question_index + 1}"
        detected = parsed.get("detectedMood", mood)
        return prompt, detected
    except Exception as e:
        logger.error(f"Follow-up generation failed: {e}")
        fallback = LIFE_FOLLOWUPS[min(question_index - 1, len(LIFE_FOLLOWUPS) - 1)]
        return {**fallback, "id": f"p{question_index + 1}"}, mood


def _session_vibe(session: ReflectionSession) -> Optional[dict]:
    if not session.vibe_json:
        return None
    try:
        return json.loads(session.vibe_json)
    except Exception:
        return None


def get_reflection_state(
    db: Session,
    session: ReflectionSession,
    profile: CreatorProfile,
) -> dict:
    """Build current reflection UI state for an active session."""
    answers = db.query(ReflectionAnswer).filter(
        ReflectionAnswer.session_id == session.id,
    ).order_by(ReflectionAnswer.created_at.asc()).all()

    answered_count = len(answers)
    stored_prompts = _session_prompts(session)
    recent_memories = db.query(Memory).filter(
        Memory.user_id == session.user_id,
    ).order_by(Memory.created_at.desc()).limit(5).all()

    if answered_count >= MAX_REFLECTION_QUESTIONS:
        return _build_response(
            session, None, answered_count, session.detected_mood, answers, is_complete=True
        )

    # Resume in-progress session
    if answered_count < len(stored_prompts):
        current = stored_prompts[answered_count]
        mood = session.detected_mood or (infer_mood_from_answers(answers) if answers else None)
        return _build_response(session, current, answered_count, mood, answers)

    # Generate the prompt for this step
    strategy_vibe = _session_vibe(session)
    if answered_count == 0:
        prompt = generate_opener(db, profile, recent_memories, strategy_vibe)
        mood = strategy_vibe.get("mood") if strategy_vibe else None
    else:
        prompt, mood = generate_followup(db, profile, answers, answered_count)

    _save_session_prompts(session, stored_prompts + [prompt], mood)
    db.commit()
    return _build_response(session, prompt, answered_count, mood or session.detected_mood, answers)


def append_prompt_after_answer(
    db: Session,
    session: ReflectionSession,
    profile: CreatorProfile,
    answers: list[ReflectionAnswer],
) -> dict:
    """After saving an answer, generate next prompt or mark complete."""
    answered_count = len(answers)
    stored_prompts = _session_prompts(session)
    mood = infer_mood_from_answers(answers)
    session.detected_mood = mood

    if answered_count >= MAX_REFLECTION_QUESTIONS:
        db.commit()
        return {"detectedMood": mood, "nextPrompt": None, "questionIndex": answered_count, "isComplete": True}

    if answered_count < len(stored_prompts):
        next_prompt = stored_prompts[answered_count]
    else:
        next_prompt, mood = generate_followup(db, profile, answers, answered_count)
        session.detected_mood = mood
        _save_session_prompts(session, stored_prompts + [next_prompt], mood)

    db.commit()
    return {
        "detectedMood": mood,
        "nextPrompt": next_prompt,
        "questionIndex": answered_count,
        "isComplete": False,
    }


def _build_response(
    session: ReflectionSession,
    current_prompt: Optional[dict],
    question_index: int,
    mood: Optional[str],
    answers: list,
    is_complete: bool = False,
) -> dict:
    return {
        "id": session.id,
        "title": session.title or "Reflection",
        "questionIndex": question_index,
        "totalQuestions": MAX_REFLECTION_QUESTIONS,
        "detectedMood": mood,
        "currentPrompt": current_prompt,
        "isComplete": is_complete,
        "answeredCount": len(answers),
    }
