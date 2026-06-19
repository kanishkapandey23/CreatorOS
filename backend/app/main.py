import logging
import uuid
import json

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
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.database import init_db, get_db, Memory, StrategyKB, ContentOpportunity, StoryDraft, ReflectionSession, ReflectionAnswer, ChatSession, ChatMessage
from app.agents import (
    process_memory_extraction,
    seed_kb_frameworks,
    start_strategy_chat,
    process_strategy_chat_message,
    retrieve_relevant_memories,
    retrieve_relevant_kb
)
from app.llm import get_llm

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

# CORS Setup to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For local beta, allow all origins. Can be restricted to localhost:3000 in production.
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
    title: str
    summary: str
    category: str
    emotion: str
    potential: int
    tags: List[str]
    suggestedFormats: List[str]
    lesson: Optional[str] = None

class DraftPayload(BaseModel):
    storyId: str
    sections: dict

class PreviewPayload(BaseModel):
    sections: dict

class AnswerPayload(BaseModel):
    promptId: str
    promptTitle: Optional[str] = None
    value: str

class FeedbackPayload(BaseModel):
    feedback: str

# ----------------------------------------------------
# Endpoints
# ----------------------------------------------------

@app.get("/api/workspace")
def get_workspace_home(db: Session = Depends(get_db)):
    """
    Returns home dashboard details (recent opportunities, weekly plans, etc.)
    """
    # 1. Active reflection session
    active_ref = db.query(ReflectionSession).filter(ReflectionSession.status == "active").first()
    ref_data = None
    if active_ref:
        ans_count = db.query(ReflectionAnswer).filter(ReflectionAnswer.session_id == active_ref.id).count()
        ref_data = {
            "id": active_ref.id,
            "title": active_ref.title,
            "progress": ans_count,
            "total": 6
        }
    else:
        # Create a default active session if none exists
        import uuid
        session_id = f"ref_{uuid.uuid4().hex[:8]}"
        active_ref = ReflectionSession(id=session_id, title="Tuesday Reflection", status="active")
        db.add(active_ref)
        db.commit()
        ref_data = {
            "id": session_id,
            "title": "Tuesday Reflection",
            "progress": 0,
            "total": 6
        }
        
    # 2. Recent opportunities (Story Bank drafts/ideas)
    opps = db.query(ContentOpportunity).order_by(ContentOpportunity.created_at.desc()).limit(3).all()
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
                id=item["id"], content_type=item["content_type"], topic=item["topic"], status=item["status"]
            )
            opp.hook_options = item["hook_options"]
            opp.structure = item["structure"]
            opp.creator_inputs_used = item["creator_inputs_used"]
            db.add(opp)
            
            # Preseed draft
            draft = StoryDraft(story_id=item["id"], sections={sec: "" for sec in opp.structure})
            if opp.hook_options:
                draft.sections = {**draft.sections, "hook": opp.hook_options[0]}
            db.add(draft)
        db.commit()
        opps = db.query(ContentOpportunity).order_by(ContentOpportunity.created_at.desc()).limit(3).all()

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
REFLECTION_PROMPTS = [
  {"id": "p1", "title": "What made you pause this week?", "hint": "A small moment is enough. A line someone said. A thought during a walk."},
  {"id": "p2", "title": "What did you change your mind about?", "hint": "Even a tiny shift in opinion is a story worth telling."},
  {"id": "p3", "title": "What did you build, ship or finish?", "hint": "No accomplishment is too small. Describe how it felt."},
  {"id": "p4", "title": "Where did you struggle?", "hint": "Friction makes the best stories. Be honest with yourself."},
  {"id": "p5", "title": "Who taught you something?", "hint": "A mentor, a stranger, a child, a book — anyone."},
  {"id": "p6", "title": "If you could share one thing this week, what would it be?", "hint": "Trust your instinct. The first answer is usually the truest."}
]

@app.get("/api/reflections/active")
def get_active_reflection(db: Session = Depends(get_db)):
    session = db.query(ReflectionSession).filter(ReflectionSession.status == "active").first()
    if not session:
        import uuid
        session_id = f"ref_{uuid.uuid4().hex[:8]}"
        session = ReflectionSession(id=session_id, title="Weekly Reflection Nudge", status="active")
        db.add(session)
        db.commit()
        db.refresh(session)
        
    # Get creator profile and recent memories to make prompts dynamic
    from app.database import CreatorProfile
    profile = db.query(CreatorProfile).first()
    recent_memories = db.query(Memory).order_by(Memory.created_at.desc()).limit(5).all()
    
    niche = profile.niche if profile else "Engineering & Tech Storytelling"
    interests = profile.interests if profile else ["coding", "indie hacking", "creative writing"]
    
    llm = get_llm()
    system_prompt = (
        "You are Agent 1: Creator Memory Engine.\n"
        "Your task is to generate 6 personalized, non-repetitive reflection prompts for the creator.\n"
        "These prompts must be tailored to their niche and interests, and reference their recent memory history (to avoid duplicate questions and help them dive deeper into recent events).\n"
        "You must output ONLY valid JSON matching this schema:\n"
        "[\n"
        "  { \"id\": \"p1\", \"title\": \"question text?\", \"hint\": \"helpful hints...\" },\n"
        "  { \"id\": \"p2\", \"title\": \"question text?\", \"hint\": \"helpful hints...\" },\n"
        "  { \"id\": \"p3\", \"title\": \"question text?\", \"hint\": \"helpful hints...\" },\n"
        "  { \"id\": \"p4\", \"title\": \"question text?\", \"hint\": \"helpful hints...\" },\n"
        "  { \"id\": \"p5\", \"title\": \"question text?\", \"hint\": \"helpful hints...\" },\n"
        "  { \"id\": \"p6\", \"title\": \"question text?\", \"hint\": \"helpful hints...\" }\n"
        "]"
    )
    user_prompt = (
        f"Creator Niche: {niche}\n"
        f"Creator Interests: {', '.join(interests)}\n"
        f"Recent Memory Events:\n" + "\n".join([f"- {m.event} ({', '.join(m.topic)})" for m in recent_memories])
    )
    
    prompts = REFLECTION_PROMPTS
    try:
        llm_output = llm.generate(system_prompt, user_prompt)
        cleaned_json = llm_output
        if "```json" in llm_output:
            cleaned_json = llm_output.split("```json")[-1].split("```")[0].strip()
        elif "```" in llm_output:
            cleaned_json = llm_output.split("```")[-1].split("```")[0].strip()
        
        parsed = json.loads(cleaned_json)
        if isinstance(parsed, list) and len(parsed) == 6:
            prompts = parsed
    except Exception as e:
        logger.error(f"Error generating dynamic reflection prompts: {e}. Falling back to default prompts.")
        
    return {
        "id": session.id,
        "title": session.title,
        "prompts": prompts
    }

@app.post("/api/reflections/answer")
def save_reflection_answer(payload: AnswerPayload, db: Session = Depends(get_db)):
    # Get active session
    session = db.query(ReflectionSession).filter(ReflectionSession.status == "active").first()
    if not session:
        raise HTTPException(status_code=400, detail="No active reflection session found.")
        
    # Find matching prompt title by getting active prompts (bypass LLM call if promptTitle is supplied directly)
    prompt_title = payload.promptTitle
    if not prompt_title:
        active_res = get_active_reflection(db)
        prompt_title = next((p["title"] for p in active_res["prompts"] if p["id"] == payload.promptId), "Reflection")
    
    # Save or update answer
    existing = db.query(ReflectionAnswer).filter(
        ReflectionAnswer.session_id == session.id,
        ReflectionAnswer.prompt_id == payload.promptId
    ).first()
    
    if existing:
        existing.answer_text = payload.value
    else:
        ans_id = f"ans_{uuid.uuid4().hex[:8]}"
        new_ans = ReflectionAnswer(
            id=ans_id,
            session_id=session.id,
            prompt_id=payload.promptId,
            prompt_title=prompt_title,
            answer_text=payload.value
        )
        db.add(new_ans)
        
    db.commit()
    return {"success": True}

@app.post("/api/reflections/complete/{session_id}")
def complete_reflection(session_id: str, db: Session = Depends(get_db)):
    session = db.query(ReflectionSession).filter(ReflectionSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Reflection session not found.")
        
    session.status = "completed"
    db.commit() # Commit session status immediately to protect it from loop rollbacks
    
    # Retrieve all answers
    answers = db.query(ReflectionAnswer).filter(ReflectionAnswer.session_id == session_id).all()
    stories_discovered = 0
    
    for ans in answers:
        if ans.answer_text.strip() and len(ans.answer_text.strip()) > 3:
            # Trigger Agent 1 Memory Engine pipeline on each meaningful answer
            try:
                # Use a nested transaction (savepoint) to isolate commits/rollbacks per answer
                with db.begin_nested():
                    # 1. Extract Memory (Agent 1)
                    memory = process_memory_extraction(db, ans.answer_text)
                    stories_discovered += 1
                    
                    # 2. Immediately generate Content Opportunity (Agent 2 RAG)
                    # Retrieve dynamic framework or trend using dynamic RAG (semantic search)
                    query_str = f"{memory.event} {' '.join(memory.topic)} {' '.join(memory.emotion)} {memory.memory_type}"
                    kb_items = retrieve_relevant_kb(db, query=query_str, limit=1)
                    kb_item = kb_items[0] if kb_items else db.query(StrategyKB).filter(StrategyKB.kb_type != "pattern").first()
                    framework_content = kb_item.content if kb_item else "Storytelling Framework"
                    
                    llm = get_llm()
                    system_prompt = (
                        "You are Agent 2: Creative Strategy Agent.\n"
                        "You must structure an initial content opportunity from this creator memory.\n"
                        f"Use this storytelling structure or trend layout:\n{framework_content}\n\n"
                        "Rely ONLY on the provided memory details. Output ONLY valid JSON matching this schema:\n"
                        "{\n"
                        "  \"content_type\": \"story_reel\" | \"linkedin_post\" | \"newsletter\",\n"
                        "  \"topic\": \"summarized topic\",\n"
                        "  \"hook_options\": [\"hook1\", \"hook2\"],\n"
                        "  \"structure\": [\"context\", \"problem\", \"realization\", \"lesson\"],\n"
                        "  \"creator_inputs_used\": [\"input1\", \"input2\"]\n"
                        "}"
                    )
                    user_prompt = (
                        f"Active Memory Event: {memory.event}\n"
                        f"Active Memory Turning Point: {memory.turning_point or 'None'}\n"
                        f"Active Memory Emotions: {', '.join(memory.emotion)}\n"
                        f"Active Memory Topics: {', '.join(memory.topic)}\n"
                        f"Raw Text Context: {ans.answer_text}"
                    )
                    
                    opp_json_str = llm.generate(system_prompt, user_prompt)
                    
                    # Clean formatting
                    cleaned_json = opp_json_str
                    if "```json" in opp_json_str:
                        cleaned_json = opp_json_str.split("```json")[-1].split("```")[0].strip()
                    elif "```" in opp_json_str:
                        cleaned_json = opp_json_str.split("```")[-1].split("```")[0].strip()
                        
                    try:
                        opportunity_data = json.loads(cleaned_json)
                    except Exception:
                        # Fallback to mock structuring using the memory details
                        from app.llm import mock_llm_client
                        fallback_json = mock_llm_client._structure_opportunity(user_prompt)
                        opportunity_data = json.loads(fallback_json)
                    
                    # Save the new opportunity directly to the database
                    opp_id = f"st_{uuid.uuid4().hex[:8]}"
                    opportunity = ContentOpportunity(
                        id=opp_id,
                        memory_id=memory.id,
                        content_type=opportunity_data.get("content_type", "linkedin_post"),
                        topic=opportunity_data.get("topic", memory.event),
                        status="idea"
                    )
                    opportunity.hook_options = opportunity_data.get("hook_options", [])
                    opportunity.structure = opportunity_data.get("structure", ["context", "problem", "lesson"])
                    opportunity.creator_inputs_used = opportunity_data.get("creator_inputs_used", memory.topic)
                    db.add(opportunity)
                    
                    # Seed draft
                    draft = StoryDraft(
                        story_id=opp_id,
                        sections={sec: "" for sec in opportunity.structure}
                    )
                    if opportunity.hook_options:
                        draft.sections = {**draft.sections, "hook": opportunity.hook_options[0]}
                    db.add(draft)
                db.commit()
                
            except Exception as e:
                logger.error(f"Error processing Agent 1/2 pipeline: {e}")
                
    return {
        "success": True,
        "storiesDiscovered": max(stories_discovered, 1) # guarantees at least 1 discovery count for UI response
    }

# --- MEMORIES ---
@app.get("/api/memories")
def list_memories(db: Session = Depends(get_db)):
    """
    Returns list of memories to populate the timeline.
    """
    memories = db.query(Memory).order_by(Memory.created_at.desc()).all()
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
def list_stories(db: Session = Depends(get_db)):
    opps = db.query(ContentOpportunity).order_by(ContentOpportunity.created_at.desc()).all()
    results = []
    for o in opps:
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
            else:
                category = "General"
                emotion = "Growth"
                potential = 78
                tags = o.creator_inputs_used
                summary = f"A structured opportunity detailing: {o.topic}."
                lesson = "Focus on authentic insights."

        results.append({
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
            "suggestedFormats": [o.content_type.replace("_", " ").capitalize()],
            "hooks": o.hook_options
        })
    return results

@app.get("/api/stories/{story_id}")
def get_story(story_id: str, db: Session = Depends(get_db)):
    o = db.query(ContentOpportunity).filter(ContentOpportunity.id == story_id).first()
    if not o:
        raise HTTPException(status_code=404, detail="Story not found")
        
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
        else:
            category = "General"
            emotion = "Growth"
            potential = 78
            tags = o.creator_inputs_used
            summary = f"A structured opportunity detailing: {o.topic}."
            lesson = "Focus on authentic insights."

    return {
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
        "suggestedFormats": [o.content_type.replace("_", " ").capitalize()],
        "hooks": o.hook_options
    }

@app.post("/api/stories")
def create_story(payload: CreateStoryPayload, db: Session = Depends(get_db)):
    """
    Manually creates a story idea in the Story Bank.
    """
    import uuid
    opp_id = f"st_{uuid.uuid4().hex[:8]}"
    opp = ContentOpportunity(
        id=opp_id,
        content_type="linkedin_post",
        topic=payload.title,
        status="idea"
    )
    opp.hook_options = payload.suggestedFormats
    opp.structure = ["context", "problem", "lesson"]
    opp.creator_inputs_used = payload.tags
    
    db.add(opp)
    
    # Save a draft
    draft = StoryDraft(
        story_id=opp_id,
        sections={
            "hook": payload.title,
            "experience": payload.summary,
            "conflict": "",
            "lesson": payload.lesson or "",
            "cta": ""
        }
    )
    db.add(draft)
    
    db.commit()
    return {"id": opp_id, "title": payload.title}

# --- WORKSPACE DRAFTS ---
@app.get("/api/stories/{story_id}/draft")
def get_story_draft(story_id: str, db: Session = Depends(get_db)):
    draft = db.query(StoryDraft).filter(StoryDraft.story_id == story_id).first()
    if not draft:
        # Preseed empty sections
        sections = {"hook": "", "experience": "", "conflict": "", "lesson": "", "cta": ""}
        return {
            "storyId": story_id,
            "sections": sections,
            "updatedAt": None
        }
    return {
        "storyId": draft.story_id,
        "sections": draft.sections,
        "updatedAt": draft.updated_at.isoformat()
    }

@app.post("/api/stories/draft")
def save_story_draft(payload: DraftPayload, db: Session = Depends(get_db)):
    draft = db.query(StoryDraft).filter(StoryDraft.story_id == payload.storyId).first()
    if not draft:
        draft = StoryDraft(story_id=payload.storyId)
        db.add(draft)
    
    draft.sections = payload.sections
    db.commit()
    return {"ok": True, "savedAt": draft.updated_at.isoformat()}

@app.post("/api/stories/{story_id}/preview")
def get_story_preview(story_id: str, payload: PreviewPayload, db: Session = Depends(get_db)):
    opportunity = db.query(ContentOpportunity).filter(ContentOpportunity.id == story_id).first()
    if not opportunity:
        raise HTTPException(status_code=404, detail="Story opportunity not found")
        
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
def get_story_suggestions(story_id: str, db: Session = Depends(get_db)):
    opportunity = db.query(ContentOpportunity).filter(ContentOpportunity.id == story_id).first()
    draft = db.query(StoryDraft).filter(StoryDraft.story_id == story_id).first()
    
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

# --- AGENT 2: CREATIVE STRATEGY CHAT FLOWS ---
@app.get("/api/strategy/chat/sessions")
def list_chat_sessions(db: Session = Depends(get_db)):
    sessions = db.query(ChatSession).order_by(ChatSession.created_at.desc()).all()
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
def start_chat_session(payload: StartChatPayload, db: Session = Depends(get_db)):
    session = start_strategy_chat(db, payload.memoryId)
    return {
        "id": session.id,
        "title": session.title,
        "memoryId": session.memory_id,
        "status": session.status
    }

@app.get("/api/strategy/chat/sessions/{session_id}")
def get_chat_session_details(session_id: str, db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
        
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
def post_chat_message(session_id: str, payload: MessagePayload, db: Session = Depends(get_db)):
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
def submit_story_feedback(story_id: str, payload: FeedbackPayload, db: Session = Depends(get_db)):
    """
    Receives user feedback on a content opportunity. Agent 2 updates the opportunity hooks
    or structure parameters based on feedback.
    """
    opp = db.query(ContentOpportunity).filter(ContentOpportunity.id == story_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Content opportunity not found")
        
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
