import json
import uuid
import datetime
import logging
from sqlalchemy.orm import Session
from app.database import Memory, StrategyKB, ContentOpportunity, ChatSession, ChatMessage, ContentDraft
from app.llm import get_llm, embedding_engine

logger = logging.getLogger("creatoros.agents")

# 1. Agent 1: Creator Memory Engine Extraction Pipeline
def process_memory_extraction(db: Session, raw_input: str, user_id: str) -> Memory:
    """
    Takes raw creator input, calls the LLM to extract a structured memory schema,
    generates a vector embedding, and saves it to the database.
    """
    logger.info(f"Agent 1 processing memory extraction for raw input: '{raw_input[:60]}...'")
    llm = get_llm()
    
    system_prompt = (
        "You are Agent 1: Creator Memory Engine.\n"
        "Your task is to convert raw creator reflections or thoughts into a structured memory JSON.\n"
        "Do NOT invent experiences. Rely ONLY on the provided text.\n"
        "You must output ONLY valid JSON matching this schema:\n"
        "{\n"
        "  \"memory_type\": \"personal_experience\" | \"lesson\" | \"opinion\",\n"
        "  \"topic\": [\"topic1\", \"topic2\"],\n"
        "  \"event\": \"summarized event description\",\n"
        "  \"turning_point\": \"summarized turning point or None\",\n"
        "  \"emotion\": [\"emotion1\", \"emotion2\"],\n"
        "  \"potential_content_angles\": [\"angle1\", \"angle2\"],\n"
        "  \"creator_traits\": {\n"
        "    \"likes_storytelling\": true,\n"
        "    \"preferred_tone\": \"casual\",\n"
        "    \"avoid_style\": [\"generic motivation\"]\n"
        "  }\n"
        "}"
    )
    
    llm_output = llm.generate(system_prompt, f"Extract structured memory from this text:\n{raw_input}")
    
    # Clean output JSON if LLM returned markdown formatting
    cleaned_json = llm_output
    if "```json" in llm_output:
        cleaned_json = llm_output.split("```json")[-1].split("```")[0].strip()
    elif "```" in llm_output:
        cleaned_json = llm_output.split("```")[-1].split("```")[0].strip()
        
    try:
        data = json.loads(cleaned_json)
    except Exception as e:
        logger.error(f"Failed to parse LLM structured memory JSON: {e}. Output was:\n{llm_output}")
        # Fallback using our mock rules engine
        from app.llm import mock_llm_client
        fallback_json = mock_llm_client._extract_memory(raw_input)
        data = json.loads(fallback_json)
        
    # Generate vector embedding for semantic search
    embedding_bytes = embedding_engine.get_embedding(raw_input)
    
    memory_id = f"mem_{uuid.uuid4().hex[:8]}"
    memory = Memory(
        id=memory_id,
        user_id=user_id,
        memory_type=data.get("memory_type", "personal_experience"),
        event=data.get("event", "Journal reflection"),
        turning_point=data.get("turning_point"),
        raw_input=raw_input,
        embedding=embedding_bytes
    )
    memory.topic = data.get("topic", [])
    memory.emotion = data.get("emotion", [])
    memory.potential_content_angles = data.get("potential_content_angles", [])
    memory.creator_traits = data.get("creator_traits", {})
    
    db.add(memory)
    db.flush()
    db.refresh(memory)
    logger.info(f"Memory saved successfully with ID: {memory.id}")
    return memory

# 2. Pre-seed Strategy Knowledge Base (RAG Data)
DEFAULT_FRAMEWORKS = [
    {
        "id": "kb_failure_lesson",
        "title": "Failure → Lesson Storytelling Framework",
        "kb_type": "framework",
        "content": (
            "Failure → Lesson Structure:\n"
            "- Hook: Start with the vulnerability, a mistake, or a setback. (Scroll-stopping)\n"
            "- Context: Set the scene briefly. When and where did this happen?\n"
            "- Conflict: Describe the peak tension. What made it hard?\n"
            "- Realization: Explain the turning point or sudden shift in perspective.\n"
            "- Lesson: State the quiet realization or advice for others."
        )
    },
    {
        "id": "kb_scroll_stopper_reel",
        "title": "Scroll-Stopper Story Reel Structure",
        "kb_type": "structure",
        "content": (
            "Scroll-Stopper Reel (Short Video Structure):\n"
            "- Hook (0-3s): Introduce a counter-intuitive statement or peak tension.\n"
            "- Context (3-8s): Provide background on why this happened.\n"
            "- Climax (8-15s): The struggle or conflict.\n"
            "- Realization (15-22s): What changed in your head.\n"
            "- CTA (22-30s): Smooth invitation for viewers to reflect."
        )
    },
    {
        "id": "kb_growth_carousel",
        "title": "Growth Curve Carousel Structure",
        "kb_type": "structure",
        "content": (
            "Growth Curve Carousel Layout:\n"
            "- Slide 1: Bold Hook (The starting problem/state)\n"
            "- Slide 2: The Hurdle (Why it wasn't easy)\n"
            "- Slide 3: The Breakthrough (The critical pivot/advice)\n"
            "- Slide 4: The Compounding Result (Where you are now)\n"
            "- Slide 5: The Lesson & CTA (A summary of the takeaway)"
        )
    },
    {
        "id": "kb_opinion_shift",
        "title": "Opinion Shift (Perspective Swap) Framework",
        "kb_type": "framework",
        "content": (
            "Perspective Swap / Opinion Shift Framework:\n"
            "- Hook: Declare what you used to believe, and why it was wrong.\n"
            "- The Paradigm: Detail the conventional wisdom that you subscribed to.\n"
            "- The Pivot: Explain the event that shattered this belief.\n"
            "- The New View: Outline your new opinion and how it works.\n"
            "- Call to action: Ask the audience what they recently changed their mind about."
        )
    }
]

TRENDS_DATA = [
    {
        "id": "trend_april_inspiration_vs_final",
        "title": "April 2026: The Inspiration vs The Final Product",
        "kb_type": "pattern",
        "content": (
            "Instagram Trend (April 2026): The Inspiration vs The Final Product\n"
            "Niche Suitability: SaaS, AI tools, UI/UX, software development, product design.\n"
            "Pattern Outline:\n"
            "- Hook (Before): Show the original brief, wireframe, or raw code context.\n"
            "- Realization (After): Quick transition cut to the fully shipped polished interface, working feature, or outcome.\n"
            "- Trend Style: Relatable, transparent behind-the-scenes storytelling showing the authentic path from idea to shipped product."
        )
    },
    {
        "id": "trend_april_samay_raina",
        "title": "April 2026: The Samay Raina deadpan truth",
        "kb_type": "pattern",
        "content": (
            "Instagram Trend (April 2026): The Samay Raina Format\n"
            "Niche Suitability: Startups, SaaS, consulting, tech founders.\n"
            "Pattern Outline:\n"
            "- Hook: Start with a blunt, filter-less, slightly uncomfortable industry truth delivered straight to camera or in direct kinetic text (3-5 tight lines).\n"
            "- Content: Zero fluff, deadpan tone. Acknowledges what ideal customers silently agree with but corporate accounts are too scared to say.\n"
            "- CTA: No CTA needed — the raw value and authenticity earn the follow."
        )
    },
    {
        "id": "trend_april_signal_broadcast",
        "title": "April 2026: The Signal Broadcast tactile format",
        "kb_type": "pattern",
        "content": (
            "Instagram Trend (April 2026): The Signal Broadcast Format\n"
            "Niche Suitability: Hardware tech, IoT, developer tools, SaaS setups.\n"
            "Pattern Outline:\n"
            "- Hook: Tactile arrangement of physical tools, books, merch, or desk items styled like a vintage analogue broadcast console.\n"
            "- Context: Directional warm lighting, a subtle 'LIVE TRANSMISSION' or 'NOW BROADCASTING' screen/text overlay.\n"
            "- Audio: Warm lofi background noise or track. Makes the brand feel like a source of intelligence rather than a corporate feed."
        )
    },
    {
        "id": "trend_april_only_review",
        "title": "April 2026: The Only Review That Matters (Behavioral Proof)",
        "kb_type": "pattern",
        "content": (
            "Instagram Trend (April 2026): The Only Review That Matters\n"
            "Niche Suitability: SaaS, B2B software, CRM, productivity tools.\n"
            "Pattern Outline:\n"
            "- Hook: Instead of quoting a generic testimonial, show a concrete user behavior that cannot be faked.\n"
            "- Context: 'A user opening the dashboard at midnight' or 'a team completing sprint tasks 2 days early'.\n"
            "- Format: Recreate this behavioral scenario with your team in a short 15-second reel with bold overlays."
        )
    },
    {
        "id": "trend_april_four_frame_breakdown",
        "title": "April 2026: The Four-Frame Product Breakdown",
        "kb_type": "pattern",
        "content": (
            "Instagram Trend (April 2026): The Four-Frame Product Breakdown\n"
            "Niche Suitability: SaaS demo, dev platforms, cybersecurity, fintech.\n"
            "Pattern Outline:\n"
            "- Hook: A clean 4-quadrant layout with the tool dashboard in one quadrant and the presenter explaining details in the others.\n"
            "- Format: Presenter goes through: 1) What it is, 2) The core problem, 3) The standout feature, 4) One real client result."
        )
    },
    {
        "id": "trend_april_absurdist_experiment",
        "title": "April 2026: April Energy (Absurdist Experiment Format)",
        "kb_type": "pattern",
        "content": (
            "Instagram Trend (April 2026): Absurdist Experiment Format\n"
            "Niche Suitability: AI tools, design platforms, creative agency.\n"
            "Pattern Outline:\n"
            "- Hook: Do something visually unexpected or slightly unhinged with your product or workspace.\n"
            "- Context: Projecting a dashboard onto a physical brick wall, or styling code outputs inside an old retro TV screen.\n"
            "- Tone: Fun, creative mismatch that breaks standard scroll fatigue."
        )
    },
    {
        "id": "trend_april_coachella",
        "title": "April 2026: The Coachella lineup format",
        "kb_type": "pattern",
        "content": (
            "Instagram Trend (April 2026): The Coachella Format\n"
            "Niche Suitability: Marketing tech, SaaS launch events, design agencies.\n"
            "Pattern Outline:\n"
            "- Hook: Design a bold, saturated 'music festival lineup' poster where acts are replaced by product features or team roles.\n"
            "- Style: High contrast, maximum visual confidence, festival energy poster layouts."
        )
    },
    {
        "id": "trend_april_carousel_unique_edits",
        "title": "April 2026: Carousel Unique Edits",
        "kb_type": "pattern",
        "content": (
            "Instagram Trend (April 2026): Carousel Unique Edits\n"
            "Niche Suitability: Consulting, research, B2B agencies, analytics.\n"
            "Pattern Outline:\n"
            "- Hook: Carousel where every slide has a distinct design/type treatment but remains palette-cohesive.\n"
            "- Format: Swiping feels like reading a curated magazine. Slide 1 has a major visual curiosity pull."
        )
    },
    {
        "id": "trend_april_pov_overhead",
        "title": "April 2026: In Today's Episode (POV Overhead Format)",
        "kb_type": "pattern",
        "content": (
            "Instagram Trend (April 2026): POV Overhead Format\n"
            "Niche Suitability: SaaS developers, designers, writers, consultants.\n"
            "Pattern Outline:\n"
            "- Hook: Overhead camera shot showing hands, desk, and tools building/editing something in real time.\n"
            "- Title Card: 'In today's episode: how to analyze a marketing strategy in 10 minutes.' No face needed."
        )
    },
    {
        "id": "trend_april_big_font_letter",
        "title": "April 2026: The Big Font Letter Format",
        "kb_type": "pattern",
        "content": (
            "Instagram Trend (April 2026): The Big Font Letter Format\n"
            "Niche Suitability: Founders, SaaS marketing, technical writers.\n"
            "Pattern Outline:\n"
            "- Hook: Entire reel is full-screen, ultra-bold typography. No face, voiceover, or studio.\n"
            "- Content: Direct one-sentence industry hot take. E.g. 'Your product is fine. Your onboarding is broken.' Generates high shares."
        )
    },
    {
        "id": "trend_jan_flow_state",
        "title": "January 2026: Flow State POV",
        "kb_type": "pattern",
        "content": (
            "Instagram Trend (January 2026): Flow State POV\n"
            "Niche Suitability: Software engineering, writing, creative coding.\n"
            "Pattern Outline:\n"
            "- Hook: Showing a dark-themed text editor with code compiling or lines typing automatically under cozy warm lighting.\n"
            "- Context: Emphasizes focus, engineering flow state, and pure technical execution paired with ambient sounds."
        )
    },
    {
        "id": "trend_feb_penguin_narrative",
        "title": "February 2026: The Penguin Documentary Narrative",
        "kb_type": "pattern",
        "content": (
            "Instagram Trend (February 2026): The Penguin Documentary Format\n"
            "Niche Suitability: Startups, product design, marketing agencies.\n"
            "Pattern Outline:\n"
            "- Hook: A highly dramatic, cinematic voiceover (like a nature documentary) narrating standard workplace struggles.\n"
            "- Context: Overly serious narration of an engineer debug-testing at 5 PM on a Friday. Funny, lighthearted, and highly engaging."
        )
    },
    {
        "id": "trend_mar_big_boy_job",
        "title": "March 2026: Me at My Big Boy Job POV",
        "kb_type": "pattern",
        "content": (
            "Instagram Trend (March 2026): Me at My Big Boy Job POV\n"
            "Niche Suitability: Remote devs, founders, startup employees.\n"
            "Pattern Outline:\n"
            "- Hook: Humorous B2B POV reels showing real day-to-day office moments instead of perfect corporate ads.\n"
            "- Context: Relatable clips highlighting things like 'pretending to understand the client's architecture' or 'surviving another meeting'."
        )
    }
]

def seed_kb_frameworks(db: Session):
    """
    Populates default content strategy documents and Passionbits trends if not already present.
    """
    # 1. Seed frameworks if empty
    existing_frameworks = db.query(StrategyKB).filter(StrategyKB.kb_type != "pattern").count()
    if existing_frameworks == 0:
        logger.info("Pre-seeding storytelling strategy frameworks in StrategyKB...")
        for item in DEFAULT_FRAMEWORKS:
            embedding_bytes = embedding_engine.get_embedding(item["content"])
            kb = StrategyKB(
                id=item["id"],
                title=item["title"],
                kb_type=item["kb_type"],
                content=item["content"],
                embedding=embedding_bytes
            )
            db.add(kb)
        db.commit()
        logger.info("Storytelling frameworks pre-seeded successfully.")

    # 2. Seed trends if trend_april_samay_raina is missing (idempotent check)
    has_trends = db.query(StrategyKB).filter(StrategyKB.id == "trend_april_samay_raina").first()
    if not has_trends:
        logger.info("Pre-seeding Instagram trends (Jan-Apr 2026) from Passionbits...")
        for item in TRENDS_DATA:
            embedding_bytes = embedding_engine.get_embedding(item["content"])
            kb = StrategyKB(
                id=item["id"],
                title=item["title"],
                kb_type=item["kb_type"],
                content=item["content"],
                embedding=embedding_bytes
            )
            db.add(kb)
        db.commit()
        logger.info("Passionbits trends pre-seeded successfully.")

# 3. Retrieval System (Memories & KB)
def retrieve_relevant_memories(db: Session, query: str, limit: int = 3) -> list[Memory]:
    """
    Performs cosine similarity search over stored memories using sentence embeddings.
    """
    query_emb = embedding_engine.get_embedding(query)
    memories = db.query(Memory).all()
    if not memories:
        return []
        
    scored_memories = []
    for m in memories:
        sim = embedding_engine.compute_similarity(query_emb, m.embedding)
        scored_memories.append((sim, m))
        
    # Sort by similarity descending
    scored_memories.sort(key=lambda x: x[0], reverse=True)
    return [m for sim, m in scored_memories[:limit]]

def retrieve_relevant_kb(db: Session, query: str, limit: int = 1) -> list[StrategyKB]:
    """
    Performs cosine similarity search over strategy knowledge base articles.
    """
    query_emb = embedding_engine.get_embedding(query)
    kb_items = db.query(StrategyKB).all()
    if not kb_items:
        return []
        
    scored_items = []
    for item in kb_items:
        sim = embedding_engine.compute_similarity(query_emb, item.embedding)
        scored_items.append((sim, item))
        
    scored_items.sort(key=lambda x: x[0], reverse=True)
    return [item for sim, item in scored_items[:limit]]

# 4. Agent 2: Creative Strategy Agent question state machine
def start_strategy_chat(db: Session, memory_id: str = None, user_id: str = None) -> ChatSession:
    """
    Starts a strategy chat session linked to a memory, seeds the first question.
    """
    session_id = f"session_{uuid.uuid4().hex[:8]}"
    memory = None
    if memory_id:
        memory = db.query(Memory).filter(Memory.id == memory_id, Memory.user_id == user_id).first()
        
    title = f"Strategizing on: {memory.event}" if memory else "Creative brainstorming"
    
    session = ChatSession(
        id=session_id,
        user_id=user_id,
        title=title,
        memory_id=memory_id,
        status="active"
    )
    db.add(session)
    db.commit()
    
    # Retrieve framework/trend context dynamically based on memory details (RAG)
    query_str = ""
    if memory:
        query_str = f"{memory.event} {' '.join(memory.topic)} {' '.join(memory.emotion)} {memory.memory_type}"
    
    kb_items = retrieve_relevant_kb(db, query=query_str, limit=1) if query_str else []
    kb_item = kb_items[0] if kb_items else db.query(StrategyKB).filter(StrategyKB.kb_type != "pattern").first()
    if not kb_item:
        kb_item = db.query(StrategyKB).first()
        
    framework_info = kb_item.content if kb_item else "Storytelling Framework"
    
    # Generate the first message
    first_text = (
        f"I've retrieved your memory about **'{memory.event if memory else 'your experience'}'** "
        f"and matched it with the **{kb_item.title if kb_item else 'story structure'}**.\n\n"
        "Let's extract the storytelling details. First question:\n"
        "**What exactly happened during this event? What was the moment of peak tension or frustration?**"
    )
    
    msg = ChatMessage(
        id=f"msg_{uuid.uuid4().hex[:8]}",
        session_id=session_id,
        role="assistant",
        content=first_text
    )
    db.add(msg)
    db.commit()
    db.refresh(session)
    return session

def process_strategy_chat_message(db: Session, session_id: str, message_text: str) -> tuple[ChatMessage, bool, dict]:
    """
    Processes the user's chat message, progress the state machine,
    asks the next question (or generates content opportunity JSON when finished).
    """
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise ValueError("Chat session not found.")
        
    # Save user message
    user_msg_id = f"msg_{uuid.uuid4().hex[:8]}"
    user_msg = ChatMessage(
        id=user_msg_id,
        session_id=session_id,
        role="user",
        content=message_text
    )
    db.add(user_msg)
    db.commit()
    
    # Retrieve chat history
    history_messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc()).all()
    
    user_replies = [m for m in history_messages if m.role == "user"]
    reply_count = len(user_replies)
    
    memory = session.memory
    
    # Retrieve strategy framework/trend dynamically based on memory details (RAG)
    query_str = ""
    if memory:
        query_str = f"{memory.event} {' '.join(memory.topic)} {' '.join(memory.emotion)} {memory.memory_type}"
        
    kb_items = retrieve_relevant_kb(db, query=query_str, limit=1) if query_str else []
    kb_item = kb_items[0] if kb_items else db.query(StrategyKB).filter(StrategyKB.kb_type != "pattern").first()
    if not kb_item:
        kb_item = db.query(StrategyKB).first()
        
    framework_content = kb_item.content if kb_item else "Failure -> Lesson storytelling"
    
    llm = get_llm()
    is_completed = False
    opportunity_data = None
    
    if reply_count < 3:
        # Build prompt for LLM to ask next question
        history_prompt = "\n".join([f"{m.role.capitalize()}: {m.content}" for m in history_messages])
        system_prompt = (
            "You are Agent 2: Creative Strategy Agent.\n"
            "Your job is to ask the creator questions to discover stories hidden inside their memories.\n"
            "Rules:\n"
            "- NEVER write fake stories or invent details.\n"
            "- Rely ONLY on the creator's answers.\n"
            "- Be brief and casual.\n"
            f"- We are applying the following storytelling framework:\n{framework_content}\n"
            f"- Active memory event: {memory.event if memory else 'creator experience'}.\n"
            f"- This is answer {reply_count} of 3. Ask the next logical question to complete the structure."
        )
        
        reply_text = llm.generate(system_prompt, history_prompt)
        
    else:
        # We have completed the 3 questions. It is time to structure the opportunity!
        is_completed = True
        session.status = "completed"
        
        # Build prompt to generate the opportunity JSON
        history_prompt = "\n".join([f"{m.role.capitalize()}: {m.content}" for m in history_messages])
        system_prompt = (
            "You are Agent 2: Creative Strategy Agent.\n"
            "The interactive questioning is complete. You must now structure the content opportunity.\n"
            "Based strictly on the creator's inputs, generate a structured output JSON.\n"
            "Rules:\n"
            "- Output ONLY valid JSON matching this schema:\n"
            "{\n"
            "  \"content_type\": \"story_reel\" | \"linkedin_post\" | \"newsletter\",\n"
            "  \"topic\": \"summarized topic\",\n"
            "  \"hook_options\": [\"hook1\", \"hook2\"],\n"
            "  \"structure\": [\"context\", \"problem\", \"realization\", \"lesson\"],\n"
            "  \"creator_inputs_used\": [\"input1\", \"input2\"]\n"
            "}\n"
            "- Hook options must represent authentic hooks derived directly from their answers.\n"
            "- Do not make up fake stories.\n"
            f"- Active memory event: {memory.event if memory else 'creator experience'}.\n"
            f"- Active memory turning point: {memory.turning_point if memory else 'None'}.\n"
            f"- Active memory emotions: {', '.join(memory.emotion) if memory else 'None'}.\n"
            f"- Active memory topics: {', '.join(memory.topic) if memory else 'None'}."
        )
        
        opportunity_json_str = llm.generate(system_prompt, history_prompt)
        
        # Clean formatting
        cleaned_json = opportunity_json_str
        if "```json" in opportunity_json_str:
            cleaned_json = opportunity_json_str.split("```json")[-1].split("```")[0].strip()
        elif "```" in opportunity_json_str:
            cleaned_json = opportunity_json_str.split("```")[-1].split("```")[0].strip()
            
        try:
            opportunity_data = json.loads(cleaned_json)
        except Exception as e:
            logger.error(f"Failed to parse opportunity JSON from LLM: {e}. Output was:\n{opportunity_json_str}")
            # Fallback
            from app.llm import mock_llm_client
            fallback_json = mock_llm_client._structure_opportunity(history_prompt)
            opportunity_data = json.loads(fallback_json)
            
        # Create and save content opportunity in database
        opp_id = f"st_{uuid.uuid4().hex[:8]}"
        opportunity = ContentOpportunity(
            id=opp_id,
            user_id=session.user_id,
            memory_id=memory.id if memory else None,
            content_type=opportunity_data.get("content_type", "story_reel"),
            topic=opportunity_data.get("topic", "personal reflection"),
            status="idea"
        )
        opportunity.hook_options = opportunity_data.get("hook_options", [])
        opportunity.structure = opportunity_data.get("structure", ["context", "problem", "lesson"])
        opportunity.creator_inputs_used = opportunity_data.get("creator_inputs_used", [])
        db.add(opportunity)
        
        # Update session linking to the generated opportunity
        session.opportunity_id = opp_id
        
        # Pre-seed empty draft sections for the workspace editor
        draft = ContentDraft(
            id=f"dr_{uuid.uuid4().hex[:8]}",
            story_id=opp_id,
            user_id=session.user_id,
            format=opportunity.content_type or "linkedin_post",
            status="draft",
            sections={sec: "" for sec in opportunity.structure},
        )
        if opportunity.hook_options:
            draft.sections = {**draft.sections, "hook": opportunity.hook_options[0]}
        db.add(draft)
        db.commit()
        
        reply_text = (
            "Thanks for sharing! I've structured this into a content opportunity for you.\n\n"
            f"**Content Type:** {opportunity.content_type.replace('_', ' ').capitalize()}\n"
            f"**Topic:** {opportunity.topic}\n\n"
            "Click **Save to Story Bank** or **Open Workspace** to write the post!"
        )
        
        # Attach the saved opportunity ID to the response dictionary
        opportunity_data["opportunity_id"] = opp_id
        
    # Save Assistant Message
    assistant_msg_id = f"msg_{uuid.uuid4().hex[:8]}"
    assistant_msg = ChatMessage(
        id=assistant_msg_id,
        session_id=session_id,
        role="assistant",
        content=reply_text
    )
    db.add(assistant_msg)
    db.commit()
    
    return assistant_msg, is_completed, opportunity_data
