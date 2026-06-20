import logging
import uuid
import json
import os

from dotenv import load_dotenv
load_dotenv()

# Workaround for FastAPI/Starlette version compatibility issue
# TypeError: Router.__init__() got an unexpected keyword argument 'on_startup'
import starlette.routing
original_router_init = starlette.routing.Router.__init__
def patched_router_init(self, *args, **kwargs):
    kwargs.pop("on_startup", None)
    kwargs.pop("on_shutdown", None)
    original_router_init(self, *args, **kwargs)
starlette.routing.Router.__init__ = patched_router_init

from fastapi import FastAPI, Depends, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.database import (
    init_db, get_db, User, CreatorProfile, Memory, StrategyKB, ContentOpportunity,
    StoryDraft, ContentDraft, ReflectionSession, ReflectionAnswer, ChatSession, ChatMessage,
    Notification,
)
from app.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    OAuthProvidersResponse,
    TokenResponse,
    UserLogin,
    UserProfileResponse,
    UserRegister,
    create_access_token,
    find_or_create_oauth_user,
    get_current_user,
    get_password_hash,
    user_to_profile,
    verify_password,
)
from app.oauth import (
    build_authorize_url,
    create_oauth_state,
    fetch_oauth_profile,
    frontend_callback_url,
    get_configured_providers,
    is_provider_configured,
    verify_oauth_state,
)
from app.agents import (
    process_memory_extraction,
    seed_kb_frameworks,
    start_strategy_chat,
    process_strategy_chat_message,
    retrieve_relevant_memories,
    retrieve_relevant_kb
)
from app.llm import get_llm
from app.strategy_engine import get_trend_intelligence, generate_recommendations
from app.reflection_engine import get_reflection_state, append_prompt_after_answer, MAX_REFLECTION_QUESTIONS
from app.planner import get_planner_week
from app.notifications.reminder_service import sync_notifications, get_weekly_digest

from contextlib import asynccontextmanager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("creatoros.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database and seeding storytelling templates...")
    init_db()
    db = next(get_db())
    seed_kb_frameworks(db)
    logger.info("Startup sequence complete.")
    yield

app = FastAPI(title="CreatorOS API", version="1.0.0", lifespan=lifespan)

# CORS — origins from env (comma-separated), defaults to local Next.js dev server
_cors_raw = os.environ.get("CORS_ORIGINS", "http://localhost:3000,http://localhost:3001")
_cors_origins = [o.strip() for o in _cors_raw.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------------------------------
# Pydantic Schemas
# ----------------------------------------------------
class AnswerPayload(BaseModel):
    promptId: str
    value: str

class MessagePayload(BaseModel):
    message: str

class StartChatPayload(BaseModel):
    memoryId: Optional[str] = None

class CreateStoryPayload(BaseModel):
    title: str = "Untitled story"
    summary: str = ""
    category: str = "General"
    emotion: str = "Growth"
    potential: int = 75
    tags: List[str] = []
    suggestedFormats: List[str] = ["Linkedin post"]
    lesson: Optional[str] = None

class UpdateStoryPayload(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None

class DraftPayload(BaseModel):
    storyId: str
    sections: dict

class CreateDraftPayload(BaseModel):
    format: str = "linkedin_post"

class UpdateDraftPayload(BaseModel):
    sections: Optional[dict] = None
    status: Optional[str] = None
    scheduledAt: Optional[str] = None

class SaveDraftPayload(BaseModel):
    sections: dict

class PreviewPayload(BaseModel):
    sections: dict

class AnswerPayload(BaseModel):
    promptId: str
    promptTitle: Optional[str] = None
    value: str

class FeedbackPayload(BaseModel):
    feedback: str

class VibeCheckPayload(BaseModel):
    mood: str = "reflective"
    contentPreference: str = "personal_story"
    goal: str = "build_connection"
    intent: str = "recommend_from_bank"
    storyId: Optional[str] = None

class StartReflectionPayload(BaseModel):
    mood: Optional[str] = None
    goal: Optional[str] = None

class ScheduleDraftPayload(BaseModel):
    scheduledAt: Optional[str] = None
    scheduledDay: Optional[str] = None
    dayIso: Optional[str] = None
    reminderEnabled: Optional[bool] = True
    reminderOffsets: Optional[List[str]] = None
    reminderChannels: Optional[List[str]] = None

class ReminderPayload(BaseModel):
    reminderEnabled: bool = True
    reminderOffsets: List[str] = ["1d", "1h"]
    reminderChannels: List[str] = ["in_app", "email"]

# ----------------------------------------------------
# Auth helpers
# ----------------------------------------------------

def _get_creator_profile(db: Session, user_id: str) -> CreatorProfile:
    profile = db.query(CreatorProfile).filter(CreatorProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Creator profile not found")
    return profile


def _get_user_opportunity(db: Session, story_id: str, user_id: str) -> ContentOpportunity:
    opp = db.query(ContentOpportunity).filter(
        ContentOpportunity.id == story_id,
        ContentOpportunity.user_id == user_id,
    ).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Story not found")
    return opp


def _get_user_chat_session(db: Session, session_id: str, user_id: str) -> ChatSession:
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == user_id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return session


DRAFT_FORMAT_LABELS = {
    "linkedin_post": "LinkedIn Post",
    "instagram_reel": "Instagram Reel",
    "carousel": "Carousel",
    "twitter_thread": "Twitter Thread",
}


def _enrich_story(opportunity: ContentOpportunity) -> dict:
    linked_mem = opportunity.memory
    category = "Storyteller"
    emotion = "Insight"
    potential = 85
    tags = []
    summary = ""
    lesson = ""

    if linked_mem:
        category = linked_mem.topic[0].capitalize() if linked_mem.topic else "Journey"
        emotion = linked_mem.emotion[0].capitalize() if linked_mem.emotion else "Growth"
        potential = 90 if linked_mem.turning_point else 75
        tags = linked_mem.topic
        summary = linked_mem.event
        lesson = linked_mem.turning_point or "Learn through persistence"
    else:
        if "gave up" in opportunity.topic.lower():
            category = "Founder Journey"
            emotion = "Vulnerability"
            potential = 92
            tags = ["founder", "resilience"]
            summary = "A quiet morning where I sat with the idea of walking away — and what made me stay."
            lesson = "Conviction is rebuilt in small moments, not big speeches."
        elif "100 users" in opportunity.topic.lower():
            category = "Product"
            emotion = "Curiosity"
            potential = 81
            tags = ["product", "users"]
            summary = "Patterns I noticed when I stopped reading dashboards and started reading messages."
            lesson = "Listen at the edges. The middle of your data already agrees with you."
        else:
            category = "General"
            emotion = "Growth"
            potential = 78
            tags = opportunity.creator_inputs_used
            summary = f"A structured opportunity detailing: {opportunity.topic}."
            lesson = "Focus on authentic insights."

    return {
        "category": category,
        "emotion": emotion,
        "potential": potential,
        "tags": tags,
        "summary": summary or opportunity.topic,
        "lesson": lesson,
    }


def _draft_to_response(draft: ContentDraft) -> dict:
    return {
        "id": draft.id,
        "storyId": draft.story_id,
        "format": draft.format,
        "formatLabel": DRAFT_FORMAT_LABELS.get(draft.format, draft.format.replace("_", " ").title()),
        "status": draft.status,
        "sections": draft.sections,
        "scheduledAt": draft.scheduled_at.isoformat() if draft.scheduled_at else None,
        "reminderEnabled": bool(draft.reminder_enabled),
        "reminderOffsets": json.loads(draft.reminder_offsets_json or '["1d","1h"]'),
        "reminderChannels": json.loads(draft.reminder_channels_json or '["in_app","email"]'),
        "reminderActive": bool(draft.reminder_enabled and draft.scheduled_at),
        "createdAt": draft.created_at.isoformat() if draft.created_at else None,
        "updatedAt": draft.updated_at.isoformat() if draft.updated_at else None,
    }


def _get_user_draft(db: Session, draft_id: str, user_id: str) -> ContentDraft:
    draft = db.query(ContentDraft).filter(
        ContentDraft.id == draft_id,
        ContentDraft.user_id == user_id,
    ).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return draft


def _draft_count(db: Session, story_id: str, user_id: str) -> int:
    return db.query(ContentDraft).filter(
        ContentDraft.story_id == story_id,
        ContentDraft.user_id == user_id,
    ).count()

# ----------------------------------------------------
# Auth routes
# ----------------------------------------------------

@app.post("/api/auth/register", response_model=TokenResponse)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user_id = f"user_{uuid.uuid4().hex[:12]}"
    user = User(
        id=user_id,
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        name=payload.name,
    )
    profile = CreatorProfile(
        user_id=user_id,
        niche=payload.niche,
        interests=["coding", "indie hacking", "creative writing", "startups"],
        preferred_tone="casual",
        goals=["build in public", "write authentic stories", "explain simple technical lessons"],
    )
    db.add(user)
    db.add(profile)
    db.commit()

    token = create_access_token(user.id)
    return TokenResponse(access_token=token, expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60)


@app.post("/api/auth/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not user.hashed_password or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(user.id)
    return TokenResponse(access_token=token, expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60)


@app.get("/api/auth/oauth/providers", response_model=OAuthProvidersResponse)
def list_oauth_providers():
    return OAuthProvidersResponse(providers=get_configured_providers())


@app.get("/api/auth/oauth/{provider}")
def oauth_login(provider: str):
    if not is_provider_configured(provider):
        return RedirectResponse(frontend_callback_url(error="oauth_not_configured"))
    state = create_oauth_state(provider)
    return RedirectResponse(build_authorize_url(provider, state))


@app.get("/api/auth/oauth/{provider}/callback")
async def oauth_callback(provider: str, code: str = None, state: str = None, db: Session = Depends(get_db)):
    if not is_provider_configured(provider):
        return RedirectResponse(frontend_callback_url(error="oauth_not_configured"))
    if not code or not state:
        return RedirectResponse(frontend_callback_url(error="oauth_missing_params"))

    try:
        verify_oauth_state(state, provider)
        profile_data = await fetch_oauth_profile(provider, code)
        user = find_or_create_oauth_user(db, profile_data)
        token = create_access_token(user.id)
        return RedirectResponse(frontend_callback_url(token=token))
    except HTTPException as exc:
        logger.error(f"OAuth callback failed for {provider}: {exc.detail}")
        return RedirectResponse(frontend_callback_url(error="oauth_failed"))
    except Exception as exc:
        logger.error(f"OAuth callback error for {provider}: {exc}")
        return RedirectResponse(frontend_callback_url(error="oauth_failed"))


@app.get("/api/auth/me", response_model=UserProfileResponse)
def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(CreatorProfile).filter(CreatorProfile.user_id == current_user.id).first()
    return user_to_profile(current_user, profile)

# ----------------------------------------------------
# Endpoints
# ----------------------------------------------------

@app.get("/api/workspace")
def get_workspace_home(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user.id
    # 1. Active reflection session
    active_ref = db.query(ReflectionSession).filter(
        ReflectionSession.user_id == user_id,
        ReflectionSession.status == "active",
    ).first()
    ref_data = None
    if active_ref:
        ans_count = db.query(ReflectionAnswer).filter(ReflectionAnswer.session_id == active_ref.id).count()
        ref_data = {
            "id": active_ref.id,
            "title": active_ref.title,
            "progress": ans_count,
            "total": 4
        }
    else:
        # Create a default active session if none exists
        import uuid
        session_id = f"ref_{uuid.uuid4().hex[:8]}"
        active_ref = ReflectionSession(id=session_id, user_id=user_id, title="Tuesday Reflection", status="active")
        db.add(active_ref)
        db.commit()
        ref_data = {
            "id": session_id,
            "title": "Tuesday Reflection",
            "progress": 0,
            "total": 4
        }
        
    # 2. Recent opportunities (Story Bank drafts/ideas)
    opps = db.query(ContentOpportunity).filter(
        ContentOpportunity.user_id == user_id,
    ).order_by(ContentOpportunity.created_at.desc()).limit(3).all()
    recent_stories = []
    
    # If database is empty, seed some default mock opportunities
    if not opps:
        # Add basic dummy items so dashboard looks premium
        dummy_data = [
            {
                "id": "st_dummy1", "content_type": "story_reel", "topic": "The Tuesday I almost gave up", 
                "hook_options": ["I almost shut down the company on a Tuesday morning."],
                "structure": ["context", "problem", "lesson"], "creator_inputs_used": ["founder burnout"],
                "status": "draft"
            },
            {
                "id": "st_dummy2", "content_type": "linkedin_post", "topic": "What my first 100 users taught me", 
                "hook_options": ["What my first 100 users taught me by breaking the product."],
                "structure": ["context", "realization", "lesson"], "creator_inputs_used": ["product design"],
                "status": "idea"
            }
        ]
        for item in dummy_data:
            opp = ContentOpportunity(
                id=item["id"], user_id=user_id, content_type=item["content_type"], topic=item["topic"], status=item["status"]
            )
            opp.hook_options = item["hook_options"]
            opp.structure = item["structure"]
            opp.creator_inputs_used = item["creator_inputs_used"]
            db.add(opp)
            
            # Preseed content draft
            draft = ContentDraft(
                id=f"dr_{uuid.uuid4().hex[:8]}",
                story_id=item["id"],
                user_id=user_id,
                format=item["content_type"],
                status="draft",
                sections={sec: "" for sec in opp.structure},
            )
            if opp.hook_options:
                draft.sections = {**draft.sections, "hook": opp.hook_options[0]}
            db.add(draft)
        db.commit()
        opps = db.query(ContentOpportunity).filter(
            ContentOpportunity.user_id == user_id,
        ).order_by(ContentOpportunity.created_at.desc()).limit(3).all()

    for o in opps:
        # Resolve category/emotion/potential to match Next.js MOCK_STORIES schema
        linked_mem = o.memory
        category = "Storyteller"
        emotion = "Insight"
        potential = 85
        tags = []
        summary = ""
        lesson = ""
        
        if linked_mem:
            category = linked_mem.topic[0].capitalize() if linked_mem.topic else "Journey"
            emotion = linked_mem.emotion[0].capitalize() if linked_mem.emotion else "Growth"
            potential = 90 if linked_mem.turning_point else 75
            tags = linked_mem.topic
            summary = linked_mem.event
            lesson = linked_mem.turning_point or "Learn through persistence"
        else:
            # Dummy mappings
            if "gave up" in o.topic.lower():
                category = "Founder Journey"
                emotion = "Vulnerability"
                potential = 92
                tags = ["founder", "resilience"]
                summary = "A quiet morning where I sat with the idea of walking away — and what made me stay."
                lesson = "Conviction is rebuilt in small moments, not big speeches."
            elif "100 users" in o.topic.lower():
                category = "Product"
                emotion = "Curiosity"
                potential = 81
                tags = ["product", "users"]
                summary = "Patterns I noticed when I stopped reading dashboards and started reading messages."
                lesson = "Listen at the edges. The middle of your data already agrees with you."
                
        recent_stories.append({
            "id": o.id,
            "title": o.topic,
            "emotion": emotion,
            "category": category,
            "status": o.status,
            "potential": potential,
            "createdAt": o.created_at.strftime("%Y-%m-%d"),
            "summary": summary or o.topic,
            "lesson": lesson,
            "tags": tags,
            "suggestedFormats": [o.content_type.replace("_", " ").capitalize()]
        })

    # 3. Weekly plan mapping
    weekly_plan = [
        {"day": "Mon", "title": "Founder coffee story", "status": "draft"},
        {"day": "Wed", "title": "Lessons from 0→1", "status": "scheduled"},
        {"day": "Fri", "title": "Why I quit my job", "status": "idea"}
    ]
    if len(recent_stories) > 0:
        weekly_plan[0]["title"] = recent_stories[0]["title"]
        weekly_plan[0]["status"] = recent_stories[0]["status"]

    return {
        "continueReflection": ref_data,
        "recentStories": recent_stories,
        "weeklyPlan": weekly_plan,
        "balance": {"story": 60, "lesson": 25, "opinion": 15}
    }

# --- REFLECTION FLOWS ---
REFLECTION_OPENER_FALLBACK = {
    "id": "p1",
    "sectionTitle": "Checking in",
    "title": "What's been sitting with you lately?",
    "hint": "A feeling, a conversation, a moment you keep replaying. No need to have it figured out.",
}


def _derive_section_title(prompt_title: str) -> str:
    """Generate a concise section label from a reflection prompt question."""
    title = (prompt_title or "").strip().rstrip("?").strip()
    if not title:
        return "Reflection"
    lower = title.lower()
    keyword_map = [
        (("feel", "mood", "emotion", "heart"), "How you're feeling"),
        (("moment", "when", "where", "happened"), "The moment"),
        (("change", "shift", "realize", "learn"), "What shifted"),
        (("relationship", "friend", "family", "person"), "Someone who mattered"),
        (("struggle", "stuck", "hard", "difficult"), "What was hard"),
        (("grateful", "thankful", "appreciate"), "Gratitude"),
        (("memory", "remember", "childhood", "past"), "A memory"),
        (("conversation", "talk", "said", "told"), "A conversation"),
        (("week", "lately", "recent", "today"), "Checking in"),
    ]
    for keywords, label in keyword_map:
        if any(k in lower for k in keywords):
            return label
    words = [w for w in title.split() if w.lower() not in {"what", "how", "why", "when", "where", "did", "you", "your", "the", "a", "an", "is", "are", "was", "were", "about", "this", "that", "can"}]
    if not words:
        words = title.split()[:4]
    label = " ".join(words[:4]).strip()
    return label[:48] if label else "Reflection"


def _enrich_prompt(prompt: dict) -> dict:
    item = dict(prompt)
    item["sectionTitle"] = item.get("sectionTitle") or _derive_section_title(item.get("title", ""))
    return item

@app.post("/api/reflections/start")
def start_reflection(
    payload: StartReflectionPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Start a fresh reflection — optionally seeded from Strategist vibe check."""
    user_id = current_user.id
    active = db.query(ReflectionSession).filter(
        ReflectionSession.user_id == user_id,
        ReflectionSession.status == "active",
    ).all()
    for s in active:
        s.status = "completed"

    vibe = None
    if payload.mood:
        vibe = {"mood": payload.mood, "goal": payload.goal or "express_myself"}

    session = ReflectionSession(
        id=f"ref_{uuid.uuid4().hex[:8]}",
        user_id=user_id,
        title="Life Reflection",
        status="active",
        vibe_json=json.dumps(vibe) if vibe else None,
        detected_mood=payload.mood,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    profile = _get_creator_profile(db, user_id)
    state = get_reflection_state(db, session, profile)
    current = state.get("currentPrompt")
    if current:
        state["currentPrompt"] = _enrich_prompt(current)
    return state

@app.get("/api/reflections/active")
def get_active_reflection(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user.id
    session = db.query(ReflectionSession).filter(
        ReflectionSession.user_id == user_id,
        ReflectionSession.status == "active",
    ).first()
    if not session:
        session_id = f"ref_{uuid.uuid4().hex[:8]}"
        session = ReflectionSession(id=session_id, user_id=user_id, title="Life Reflection", status="active")
        db.add(session)
        db.commit()
        db.refresh(session)

    profile = _get_creator_profile(db, user_id)
    state = get_reflection_state(db, session, profile)
    current = state.get("currentPrompt")
    if current:
        state["currentPrompt"] = _enrich_prompt(current)
    return state

@app.post("/api/reflections/answer")
def save_reflection_answer(
    payload: AnswerPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = current_user.id
    session = db.query(ReflectionSession).filter(
        ReflectionSession.user_id == user_id,
        ReflectionSession.status == "active",
    ).first()
    if not session:
        raise HTTPException(status_code=400, detail="No active reflection session found.")

    prompt_title = payload.promptTitle or "Reflection"

    existing = db.query(ReflectionAnswer).filter(
        ReflectionAnswer.session_id == session.id,
        ReflectionAnswer.prompt_id == payload.promptId
    ).first()

    if existing:
        existing.answer_text = payload.value
        existing.prompt_title = prompt_title
    else:
        ans_id = f"ans_{uuid.uuid4().hex[:8]}"
        db.add(ReflectionAnswer(
            id=ans_id,
            session_id=session.id,
            prompt_id=payload.promptId,
            prompt_title=prompt_title,
            answer_text=payload.value,
        ))

    db.commit()

    answers = db.query(ReflectionAnswer).filter(
        ReflectionAnswer.session_id == session.id,
    ).order_by(ReflectionAnswer.created_at.asc()).all()

    profile = _get_creator_profile(db, user_id)
    result = append_prompt_after_answer(db, session, profile, answers)

    next_prompt = result.get("nextPrompt")
    if next_prompt:
        result["nextPrompt"] = _enrich_prompt(next_prompt)

    return {"success": True, **result}

@app.post("/api/reflections/complete/{session_id}")
def complete_reflection(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(ReflectionSession).filter(
        ReflectionSession.id == session_id,
        ReflectionSession.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Reflection session not found.")
        
    session.status = "completed"
    db.commit() # Commit session status immediately to protect it from loop rollbacks
    
    # Retrieve all answers
    answers = db.query(ReflectionAnswer).filter(ReflectionAnswer.session_id == session_id).all()
    stories_discovered = 0
    
    for ans in answers:
        if stories_discovered >= 3:
            break
        if ans.answer_text.strip() and len(ans.answer_text.strip()) > 3:
            try:
                with db.begin_nested():
                    memory = process_memory_extraction(db, ans.answer_text, current_user.id)
                    opp_id = f"st_{uuid.uuid4().hex[:8]}"
                    opportunity = ContentOpportunity(
                        id=opp_id,
                        user_id=current_user.id,
                        memory_id=memory.id,
                        content_type="story",
                        topic=memory.event[:120] if memory.event else "Untitled moment",
                        status="idea",
                    )
                    opportunity.hook_options = []
                    opportunity.structure = []
                    opportunity.creator_inputs_used = memory.topic
                    db.add(opportunity)
                    stories_discovered += 1
                db.commit()
            except Exception as e:
                logger.error(f"Error processing memory extraction: {e}")

    return {
        "success": True,
        "storiesDiscovered": stories_discovered,
    }

# --- MEMORIES ---
@app.get("/api/memories")
def list_memories(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    memories = db.query(Memory).filter(Memory.user_id == current_user.id).order_by(Memory.created_at.desc()).all()
    results = []
    for m in memories:
        results.append({
            "id": m.id,
            "memory_type": m.memory_type,
            "topic": m.topic,
            "event": m.event,
            "turning_point": m.turning_point,
            "emotion": m.emotion,
            "potential_content_angles": m.potential_content_angles,
            "creator_traits": m.creator_traits,
            "raw_input": m.raw_input,
            "createdAt": m.created_at.strftime("%Y-%m-%d %H:%M")
        })
    return results

# --- STORIES (STORY BANK) ---
@app.get("/api/stories")
def list_stories(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    opps = db.query(ContentOpportunity).filter(
        ContentOpportunity.user_id == current_user.id,
    ).order_by(ContentOpportunity.created_at.desc()).all()
    results = []
    for o in opps:
        meta = _enrich_story(o)
        results.append({
            "id": o.id,
            "title": o.topic,
            "emotion": meta["emotion"],
            "category": meta["category"],
            "status": o.status,
            "potential": meta["potential"],
            "createdAt": o.created_at.strftime("%Y-%m-%d"),
            "summary": meta["summary"],
            "lesson": meta["lesson"],
            "tags": meta["tags"],
            "draftCount": _draft_count(db, o.id, current_user.id),
            "suggestedFormats": [o.content_type.replace("_", " ").capitalize()],
            "hooks": o.hook_options,
        })
    return results

@app.get("/api/stories/{story_id}")
def get_story(story_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    o = _get_user_opportunity(db, story_id, current_user.id)
    meta = _enrich_story(o)
    return {
        "id": o.id,
        "title": o.topic,
        "emotion": meta["emotion"],
        "category": meta["category"],
        "status": o.status,
        "potential": meta["potential"],
        "createdAt": o.created_at.strftime("%Y-%m-%d"),
        "summary": meta["summary"],
        "lesson": meta["lesson"],
        "tags": meta["tags"],
        "draftCount": _draft_count(db, o.id, current_user.id),
        "suggestedFormats": [o.content_type.replace("_", " ").capitalize()],
        "hooks": o.hook_options,
        "structure": o.structure,
    }

@app.post("/api/stories")
def create_story(
    payload: CreateStoryPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    import uuid
    opp_id = f"st_{uuid.uuid4().hex[:8]}"
    opp = ContentOpportunity(
        id=opp_id,
        user_id=current_user.id,
        content_type="linkedin_post",
        topic=payload.title,
        status="idea"
    )
    opp.hook_options = payload.suggestedFormats
    opp.structure = ["context", "problem", "lesson"]
    opp.creator_inputs_used = payload.tags
    
    db.add(opp)

    draft = ContentDraft(
        id=f"dr_{uuid.uuid4().hex[:8]}",
        story_id=opp_id,
        user_id=current_user.id,
        format="linkedin_post",
        status="draft",
        sections={
            "hook": payload.title,
            "experience": payload.summary,
            "conflict": "",
            "lesson": payload.lesson or "",
            "cta": "",
        },
    )
    db.add(draft)
    
    db.commit()
    return {"id": opp_id, "title": payload.title}

@app.patch("/api/stories/{story_id}")
def update_story(
    story_id: str,
    payload: UpdateStoryPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    opp = _get_user_opportunity(db, story_id, current_user.id)
    if payload.title is not None:
        opp.topic = payload.title.strip() or "Untitled story"
    if payload.status is not None:
        opp.status = payload.status
    db.commit()
    db.refresh(opp)
    return {"ok": True, "id": opp.id, "title": opp.topic, "status": opp.status}

@app.delete("/api/stories/{story_id}")
def delete_story(
    story_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    opp = _get_user_opportunity(db, story_id, current_user.id)
    db.query(ContentDraft).filter(
        ContentDraft.story_id == story_id,
        ContentDraft.user_id == current_user.id,
    ).delete()
    db.query(StoryDraft).filter(
        StoryDraft.story_id == story_id,
        StoryDraft.user_id == current_user.id,
    ).delete()
    db.delete(opp)
    db.commit()
    return {"ok": True, "id": story_id}

# --- CONTENT DRAFTS (Studio) ---
@app.get("/api/stories/{story_id}/drafts")
def list_story_drafts(story_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _get_user_opportunity(db, story_id, current_user.id)
    drafts = db.query(ContentDraft).filter(
        ContentDraft.story_id == story_id,
        ContentDraft.user_id == current_user.id,
    ).order_by(ContentDraft.updated_at.desc()).all()
    return [_draft_to_response(d) for d in drafts]


@app.post("/api/stories/{story_id}/drafts")
def create_content_draft(
    story_id: str,
    payload: CreateDraftPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_user_opportunity(db, story_id, current_user.id)
    fmt = payload.format if payload.format in DRAFT_FORMAT_LABELS else "linkedin_post"
    draft = ContentDraft(
        id=f"dr_{uuid.uuid4().hex[:8]}",
        story_id=story_id,
        user_id=current_user.id,
        format=fmt,
        status="draft",
        sections={"hook": "", "experience": "", "conflict": "", "lesson": "", "cta": ""},
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return _draft_to_response(draft)


@app.get("/api/drafts/{draft_id}")
def get_content_draft(draft_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _draft_to_response(_get_user_draft(db, draft_id, current_user.id))


@app.patch("/api/drafts/{draft_id}")
def update_content_draft(
    draft_id: str,
    payload: UpdateDraftPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    draft = _get_user_draft(db, draft_id, current_user.id)
    if payload.sections is not None:
        draft.sections = payload.sections
    if payload.status is not None:
        draft.status = payload.status
    if payload.scheduledAt is not None:
        from datetime import datetime
        draft.scheduled_at = datetime.fromisoformat(payload.scheduledAt.replace("Z", "+00:00")) if payload.scheduledAt else None
        if draft.scheduled_at and draft.status == "draft":
            draft.status = "scheduled"
    db.commit()
    db.refresh(draft)
    return _draft_to_response(draft)


@app.delete("/api/drafts/{draft_id}")
def delete_content_draft(draft_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    draft = _get_user_draft(db, draft_id, current_user.id)
    db.delete(draft)
    db.commit()
    return {"ok": True, "id": draft_id}


# --- LEGACY WORKSPACE DRAFTS (compat) ---
@app.get("/api/stories/{story_id}/draft")
def get_story_draft(story_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _get_user_opportunity(db, story_id, current_user.id)
    draft = db.query(ContentDraft).filter(
        ContentDraft.story_id == story_id,
        ContentDraft.user_id == current_user.id,
    ).order_by(ContentDraft.updated_at.desc()).first()
    if not draft:
        sections = {"hook": "", "experience": "", "conflict": "", "lesson": "", "cta": ""}
        return {"storyId": story_id, "sections": sections, "updatedAt": None}
    return {
        "storyId": draft.story_id,
        "draftId": draft.id,
        "sections": draft.sections,
        "updatedAt": draft.updated_at.isoformat() if draft.updated_at else None,
    }


@app.post("/api/stories/draft")
def save_story_draft(
    payload: DraftPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_user_opportunity(db, payload.storyId, current_user.id)
    draft = db.query(ContentDraft).filter(
        ContentDraft.story_id == payload.storyId,
        ContentDraft.user_id == current_user.id,
    ).order_by(ContentDraft.updated_at.desc()).first()
    if not draft:
        draft = ContentDraft(
            id=f"dr_{uuid.uuid4().hex[:8]}",
            story_id=payload.storyId,
            user_id=current_user.id,
            format="linkedin_post",
            status="draft",
        )
        db.add(draft)
    draft.sections = payload.sections
    db.commit()
    db.refresh(draft)
    return {"ok": True, "savedAt": draft.updated_at.isoformat(), "draftId": draft.id}


@app.post("/api/drafts/{draft_id}/save")
def save_content_draft(
    draft_id: str,
    payload: SaveDraftPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    draft = _get_user_draft(db, draft_id, current_user.id)
    draft.sections = payload.sections
    db.commit()
    db.refresh(draft)
    return {"ok": True, "savedAt": draft.updated_at.isoformat(), "draftId": draft.id}


# --- WORKSPACE DRAFTS (deprecated alias) ---

@app.post("/api/stories/{story_id}/preview")
def get_story_preview(
    story_id: str,
    payload: PreviewPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    opportunity = _get_user_opportunity(db, story_id, current_user.id)
        
    sections = payload.sections
    
    # Retrieve dynamic trend or framework via RAG for strategy grounding
    query_str = f"{opportunity.topic} {opportunity.content_type} {', '.join(opportunity.creator_inputs_used)}"
    kb_items = retrieve_relevant_kb(db, query=query_str, limit=1)
    kb_item = kb_items[0] if kb_items else db.query(StrategyKB).filter(StrategyKB.kb_type != "pattern").first()
    framework_content = kb_item.content if kb_item else "General Storytelling Format"
    
    llm = get_llm()
    system_prompt = (
        "You are Agent 2: Creative Strategy Agent.\n"
        "Your task is to take the creator's raw section draft inputs and polish them into a high-converting, trendy, and polished social media post.\n"
        f"Ground your polish in this strategy/trend template:\n{framework_content}\n\n"
        "Make it visually stunning with engaging spacing, bold hooks, bullet points, and appropriate emojis.\n"
        "Rely ONLY on the facts in the user draft sections. Do NOT invent fake experiences or make up details outside their input."
    )
    user_prompt = (
        f"Content Type: {opportunity.content_type}\n"
        f"Topic: {opportunity.topic}\n"
        f"Draft Sections:\n" + "\n".join([f"[{sec.upper()}]: {text}" for sec, text in sections.items() if text])
    )
    
    polished_text = llm.generate(system_prompt, user_prompt)
    return {"polishedText": polished_text}

@app.get("/api/stories/{story_id}/suggestions")
def get_story_suggestions(story_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    opportunity = _get_user_opportunity(db, story_id, current_user.id)
    draft = db.query(ContentDraft).filter(
        ContentDraft.story_id == story_id,
        ContentDraft.user_id == current_user.id,
    ).order_by(ContentDraft.updated_at.desc()).first()
    
    if not draft or not any(draft.sections.values()):
        return {
            "suggestions": [
                "Create a scroll-stopping hook referencing a specific setback.",
                "Detail the emotional pivot point clearly in the realization section.",
                "Keep the CTA focused on prompting high audience comments."
            ]
        }
        
    # Analyze the sections and generate 3 dynamic suggestions!
    llm = get_llm()
    system_prompt = (
        "You are Agent 2: Creative Strategy Agent.\n"
        "Your task is to review the creator's draft sections and output exactly 3 bullet-point suggestions for improving their copy.\n"
        "Each suggestion must be short (under 12 words), direct, and focus on style, pacing, clarity, or emotional resonance.\n"
        "Output ONLY valid JSON matching this schema:\n"
        "{\n"
        "  \"suggestions\": [\"suggestion 1\", \"suggestion 2\", \"suggestion 3\"]\n"
        "}"
    )
    user_prompt = f"Topic: {opportunity.topic if opportunity else 'Draft'}\nDraft Sections:\n" + "\n".join([f"[{sec.upper()}]: {val}" for sec, val in draft.sections.items() if val])
    
    try:
        reply = llm.generate(system_prompt, user_prompt)
        cleaned_json = reply
        if "```json" in reply:
            cleaned_json = reply.split("```json")[-1].split("```")[0].strip()
        elif "```" in reply:
            cleaned_json = reply.split("```")[-1].split("```")[0].strip()
        data = json.loads(cleaned_json)
        return {"suggestions": data.get("suggestions", [])[:3]}
    except Exception as e:
        logger.error(f"Error generating dynamic suggestions: {e}")
        return {
            "suggestions": [
                "Shorten the hook by 3 words to increase impact.",
                "Insert a specific sensory detail in your experience.",
                "Ensure the call to action invites simple organic replies."
            ]
        }

@app.get("/api/strategy/trends")
def get_strategy_trends(
    mood: str = "reflective",
    format: str = "linkedin_post",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_trend_intelligence(db, mood=mood, fmt=format)

@app.get("/api/planner/week")
def get_planner_week_view(
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_planner_week(db, current_user.id, offset)

@app.post("/api/drafts/{draft_id}/schedule")
def schedule_draft(
    draft_id: str,
    payload: ScheduleDraftPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from datetime import datetime
    from app.india_trends import next_posting_datetime, IST

    draft = _get_user_draft(db, draft_id, current_user.id)
    if payload.dayIso:
        from datetime import datetime
        from app.india_trends import IST
        d = datetime.fromisoformat(payload.dayIso).date()
        draft.scheduled_at = datetime(d.year, d.month, d.day, 19, 30, tzinfo=IST)
    elif payload.scheduledAt:
        from datetime import datetime
        draft.scheduled_at = datetime.fromisoformat(payload.scheduledAt.replace("Z", "+00:00"))
    elif payload.scheduledDay:
        day, time = payload.scheduledDay.split("|") if "|" in payload.scheduledDay else (payload.scheduledDay, "7:30 PM IST")
        draft.scheduled_at = next_posting_datetime(day.strip(), time.strip())
    else:
        draft.scheduled_at = None
    draft.status = "scheduled" if draft.scheduled_at else "draft"
    if payload.reminderEnabled is not False and draft.scheduled_at:
        draft.reminder_enabled = True
        if payload.reminderOffsets:
            draft.reminder_offsets_json = json.dumps(payload.reminderOffsets)
        if payload.reminderChannels:
            draft.reminder_channels_json = json.dumps(payload.reminderChannels)
        draft.reminder_sent_json = "{}"
    elif payload.reminderEnabled is False:
        draft.reminder_enabled = False
    db.commit()
    db.refresh(draft)
    return _draft_to_response(draft)

@app.patch("/api/drafts/{draft_id}/reminders")
def update_draft_reminders(
    draft_id: str,
    payload: ReminderPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    draft = _get_user_draft(db, draft_id, current_user.id)
    draft.reminder_enabled = payload.reminderEnabled
    draft.reminder_offsets_json = json.dumps(payload.reminderOffsets)
    draft.reminder_channels_json = json.dumps(payload.reminderChannels)
    draft.reminder_sent_json = "{}"
    db.commit()
    db.refresh(draft)
    return _draft_to_response(draft)

# --- NOTIFICATIONS & ACCOUNTABILITY ---
@app.get("/api/notifications")
def list_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items = sync_notifications(db, current_user.id)
    unread = sum(1 for n in items if not n.get("read"))
    return {"notifications": items, "unreadCount": unread}

@app.post("/api/notifications/{notif_id}/read")
def mark_notification_read(
    notif_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    n = db.query(Notification).filter(
        Notification.id == notif_id,
        Notification.user_id == current_user.id,
    ).first()
    if n:
        n.read = True
        db.commit()
    return {"ok": True}

@app.post("/api/notifications/{notif_id}/dismiss")
def dismiss_notification(
    notif_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    n = db.query(Notification).filter(
        Notification.id == notif_id,
        Notification.user_id == current_user.id,
    ).first()
    if n:
        n.dismissed = True
        n.read = True
        db.commit()
    return {"ok": True}

@app.post("/api/notifications/{notif_id}/complete")
def complete_from_notification(
    notif_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    n = db.query(Notification).filter(
        Notification.id == notif_id,
        Notification.user_id == current_user.id,
    ).first()
    if n and n.draft_id:
        draft = _get_user_draft(db, n.draft_id, current_user.id)
        draft.status = "published"
        draft.reminder_enabled = False
    if n:
        n.dismissed = True
        n.read = True
        db.commit()
    return {"ok": True}

@app.get("/api/notifications/digest")
def weekly_digest(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_weekly_digest(db, current_user.id)

@app.get("/api/notifications/channels")
def list_notification_channels():
    from app.notifications.channels import AVAILABLE_CHANNELS, FUTURE_CHANNELS
    return {
        "available": AVAILABLE_CHANNELS,
        "comingSoon": FUTURE_CHANNELS,
    }

# --- STRATEGY: VIBE CHECK + RECOMMENDATIONS ---
@app.post("/api/strategy/recommendations")
def get_strategy_recommendations(
    payload: VibeCheckPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return generate_recommendations(
        db=db,
        user_id=current_user.id,
        mood=payload.mood,
        content_preference=payload.contentPreference,
        goal=payload.goal,
        intent=payload.intent,
        focus_story_id=payload.storyId,
    )

# --- AGENT 2: CREATIVE STRATEGY CHAT FLOWS (legacy) ---
@app.get("/api/strategy/chat/sessions")
def list_chat_sessions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sessions = db.query(ChatSession).filter(
        ChatSession.user_id == current_user.id,
    ).order_by(ChatSession.created_at.desc()).all()
    results = []
    for s in sessions:
        results.append({
            "id": s.id,
            "title": s.title,
            "memoryId": s.memory_id,
            "status": s.status,
            "createdAt": s.created_at.strftime("%Y-%m-%d %H:%M")
        })
    return results

@app.post("/api/strategy/chat/sessions")
def start_chat_session(
    payload: StartChatPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = start_strategy_chat(db, payload.memoryId, current_user.id)
    return {
        "id": session.id,
        "title": session.title,
        "memoryId": session.memory_id,
        "status": session.status
    }

@app.get("/api/strategy/chat/sessions/{session_id}")
def get_chat_session_details(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = _get_user_chat_session(db, session_id, current_user.id)
        
    messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc()).all()
    msg_data = []
    for m in messages:
        msg_data.append({
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "createdAt": m.created_at.isoformat()
        })
        
    # Retrieve framework & memory details for context panel
    memory_info = None
    if session.memory:
        memory_info = {
            "id": session.memory.id,
            "event": session.memory.event,
            "turning_point": session.memory.turning_point,
            "topic": session.memory.topic,
            "emotion": session.memory.emotion
        }
        
    framework_title = "Failure → Lesson Framework"
    if session.memory and session.memory.memory_type == "opinion":
        framework_title = "Perspective Swap Framework"
    kb_item = db.query(StrategyKB).filter(StrategyKB.title.like(f"%{framework_title[:10]}%")).first()
    
    return {
        "id": session.id,
        "title": session.title,
        "status": session.status,
        "memory": memory_info,
        "opportunity_id": getattr(session, "opportunity_id", None),
        "framework": {
            "title": kb_item.title if kb_item else "Storytelling Framework",
            "content": kb_item.content if kb_item else "General framework guidelines"
        },
        "messages": msg_data
    }

@app.post("/api/strategy/chat/sessions/{session_id}/message")
def post_chat_message(
    session_id: str,
    payload: MessagePayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_user_chat_session(db, session_id, current_user.id)
    try:
        assistant_msg, is_completed, opp_data = process_strategy_chat_message(
            db, session_id, payload.message
        )
        return {
            "message": {
                "id": assistant_msg.id,
                "role": assistant_msg.role,
                "content": assistant_msg.content,
                "createdAt": assistant_msg.created_at.isoformat()
            },
            "isCompleted": is_completed,
            "opportunity": opp_data
        }
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.error(f"Error processing chat message: {e}")
        raise HTTPException(status_code=500, detail="Internal server error in strategy agent processing.")

# --- FEEDBACK LOOP ---
@app.post("/api/stories/{story_id}/feedback")
def submit_story_feedback(
    story_id: str,
    payload: FeedbackPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    opp = _get_user_opportunity(db, story_id, current_user.id)
        
    opp.feedback = payload.feedback
    
    # Process feedback loop using LLM
    llm = get_llm()
    system_prompt = (
        "You are Agent 2: Creative Strategy Agent.\n"
        "The creator has provided feedback on their generated hooks and opportunity topic.\n"
        "You must update the list of scroll-stopping hooks to incorporate their feedback.\n"
        "Output ONLY valid JSON matching this schema:\n"
        "{\n"
        "  \"hook_options\": [\"updated hook 1\", \"updated hook 2\"]\n"
        "}"
    )
    user_prompt = (
        f"Original Topic: {opp.topic}\n"
        f"Original Hooks: {json.dumps(opp.hook_options)}\n"
        f"Creator Feedback: {payload.feedback}"
    )
    
    reply = llm.generate(system_prompt, user_prompt)
    
    cleaned_json = reply
    if "```json" in reply:
        cleaned_json = reply.split("```json")[-1].split("```")[0].strip()
    elif "```" in reply:
        cleaned_json = reply.split("```")[-1].split("```")[0].strip()
        
    try:
        data = json.loads(cleaned_json)
        opp.hook_options = data.get("hook_options", opp.hook_options)
    except Exception as e:
        logger.error(f"Failed to process feedback JSON: {e}")
        # Default simple fallback modification
        opp.hook_options = [f"{h} (Refined: {payload.feedback[:30]})" for h in opp.hook_options]
        
    db.commit()
    return {"success": True, "hook_options": opp.hook_options}
