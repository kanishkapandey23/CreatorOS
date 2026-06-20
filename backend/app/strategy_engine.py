"""
Content Strategy recommendation engine.
Combines Story Bank, vibe check, trend intelligence, and creator profile.
"""
import json
import logging
import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.database import ContentOpportunity, ContentDraft, CreatorProfile
from app.india_trends import get_india_trends, suggest_posting_slot, next_posting_datetime
from app.llm import get_llm

logger = logging.getLogger("creatoros.strategy")

DRAFT_FORMAT_LABELS = {
    "linkedin_post": "LinkedIn Post",
    "instagram_reel": "Instagram Reel",
    "carousel": "Carousel",
    "twitter_thread": "Twitter Thread",
}

MOOD_FORMAT_MAP = {
    "reflective": ["linkedin_post", "carousel"],
    "happy": ["instagram_reel", "carousel"],
    "funny": ["instagram_reel", "twitter_thread"],
    "emotional": ["linkedin_post", "instagram_reel"],
    "motivated": ["linkedin_post", "instagram_reel"],
    "nostalgic": ["instagram_reel", "carousel"],
    "random": ["linkedin_post", "instagram_reel", "carousel", "twitter_thread"],
}

PREFERENCE_FORMAT_MAP = {
    "personal_story": ["linkedin_post", "instagram_reel"],
    "educational": ["carousel", "linkedin_post"],
    "storytime": ["instagram_reel", "linkedin_post"],
    "opinion": ["linkedin_post", "twitter_thread"],
    "lifestyle": ["instagram_reel", "carousel"],
    "career": ["linkedin_post", "carousel"],
    "surprise_me": ["linkedin_post", "instagram_reel", "carousel", "twitter_thread"],
}


def get_trend_intelligence(db: Session, mood: str = "reflective", fmt: str = "linkedin_post", **_kwargs) -> dict:
    """India-focused trends and posting windows (IST)."""
    return get_india_trends(mood=mood, fmt=fmt)


def _suggest_format(mood: str, preference: str) -> str:
    mood_fmts = MOOD_FORMAT_MAP.get(mood, ["linkedin_post"])
    pref_fmts = PREFERENCE_FORMAT_MAP.get(preference, ["linkedin_post"])
    for fmt in pref_fmts:
        if fmt in mood_fmts:
            return fmt
    return pref_fmts[0]


def _rule_based_recommendations(
    stories: list,
    drafts_by_story: dict,
    mood: str,
    preference: str,
    goal: str,
    trends: dict,
    focus_story_id: Optional[str] = None,
) -> list:
    """Fallback when LLM unavailable."""
    recs = []
    ranked = stories
    if focus_story_id:
        ranked = sorted(stories, key=lambda s: 0 if s["id"] == focus_story_id else 1)

    for i, story in enumerate(ranked[:4]):
        fmt = _suggest_format(mood, preference)
        story_drafts = drafts_by_story.get(story["id"], [])
        existing = next((d for d in story_drafts if d["format"] == fmt), None)
        day, time = suggest_posting_slot(fmt, i)

        if existing:
            action = "continue_draft"
            draft_id = existing["id"]
            reason = (
                f"You already have a {existing['formatLabel']} draft for this story. "
                f"Your {mood} mood pairs well with continuing rather than starting over."
            )
        else:
            action = "create_draft"
            draft_id = None
            reason = (
                f"This story aligns with your {mood} mood. "
                f"Try '{trends['trendingFormats'][0]}' — popular with Indian audiences right now."
            )

        recs.append({
            "id": f"rec_{uuid.uuid4().hex[:8]}",
            "storyId": story["id"],
            "storyTitle": story["title"],
            "format": fmt,
            "formatLabel": DRAFT_FORMAT_LABELS.get(fmt, fmt),
            "reason": reason,
            "priority": max(95 - i * 12, 60),
            "bestPostingDay": day,
            "bestPostingTime": time,
            "trendingFormat": trends["trendingFormats"][i % len(trends["trendingFormats"])],
            "trendingAudio": trends["trendingAudio"][i % len(trends["trendingAudio"])],
            "suggestedHookStyle": trends["trendingHookPatterns"][i % len(trends["trendingHookPatterns"])],
            "action": action,
            "draftId": draft_id,
            "scheduledAt": next_posting_datetime(day, time).isoformat(),
            "publishConfidence": "high",
            "publishWindowNote": "Weekday evenings work well for this format in India.",
        })
    return recs


def _enrich_story(opportunity: ContentOpportunity) -> dict:
    linked_mem = opportunity.memory
    if linked_mem:
        return {
            "category": linked_mem.topic[0].capitalize() if linked_mem.topic else "Journey",
            "emotion": linked_mem.emotion[0].capitalize() if linked_mem.emotion else "Growth",
            "tags": linked_mem.topic,
            "summary": linked_mem.event,
        }
    return {
        "category": "General",
        "emotion": "Growth",
        "tags": opportunity.creator_inputs_used or [],
        "summary": opportunity.topic,
    }


def _draft_count(db: Session, story_id: str, user_id: str) -> int:
    return db.query(ContentDraft).filter(
        ContentDraft.story_id == story_id,
        ContentDraft.user_id == user_id,
    ).count()


def generate_recommendations(
    db: Session,
    user_id: str,
    mood: str,
    content_preference: str,
    goal: str,
    intent: str = "recommend_from_bank",
    focus_story_id: Optional[str] = None,
) -> dict:
    """Generate personalized content recommendations from Story Bank + trends + vibe."""
    opps = db.query(ContentOpportunity).filter(
        ContentOpportunity.user_id == user_id,
    ).order_by(ContentOpportunity.created_at.desc()).all()

    stories = []
    for o in opps:
        meta = _enrich_story(o)
        stories.append({
            "id": o.id,
            "title": o.topic,
            "emotion": meta["emotion"],
            "category": meta["category"],
            "summary": meta["summary"],
            "tags": meta["tags"],
            "draftCount": _draft_count(db, o.id, user_id),
        })

    profile = db.query(CreatorProfile).filter(CreatorProfile.user_id == user_id).first()
    niche = profile.niche if profile else "General creator"
    interests = profile.interests if profile else []

    fmt_default = _suggest_format(mood, content_preference)
    trends = get_trend_intelligence(db, mood=mood, fmt=fmt_default)

    if intent == "new_story" or not stories:
        return {
            "recommendations": [],
            "trends": trends,
            "suggestReflection": True,
            "message": "Start a reflection to capture new experiences for your Story Bank.",
        }

    drafts_by_story = {}
    for o in opps:
        drafts = db.query(ContentDraft).filter(
            ContentDraft.story_id == o.id,
            ContentDraft.user_id == user_id,
        ).all()
        drafts_by_story[o.id] = [
            {
                "id": d.id,
                "format": d.format,
                "formatLabel": DRAFT_FORMAT_LABELS.get(d.format, d.format),
                "status": d.status,
            }
            for d in drafts
        ]

    # Build context for LLM
    story_lines = "\n".join([
        f"- [{s['id']}] {s['title']} (emotion: {s['emotion']}, category: {s['category']}, drafts: {s['draftCount']})"
        for s in stories[:12]
    ])
    trend_lines = "\n".join([f"- {t}" for t in trends["trendingFormats"][:4]])

    llm = get_llm()
    system_prompt = (
        "You are a personal content strategist for Indian creators (IST timezone).\n"
        "Recommend what to work on TODAY from their Story Bank.\n"
        "Use India-relevant posting times (e.g. Wed 7:30 PM IST for reels, Tue 8:30 AM IST for LinkedIn).\n"
        "NEVER encourage copying trends — adapt authentically.\n"
        "If a story already has a matching draft, recommend continuing it (action: continue_draft).\n"
        "Output ONLY valid JSON:\n"
        "{\n"
        '  "recommendations": [\n'
        "    {\n"
        '      "storyId": "st_xxx",\n'
        '      "format": "linkedin_post|instagram_reel|carousel|twitter_thread",\n'
        '      "reason": "2-3 sentences explaining WHY — mood fit, trend alignment, content balance",\n'
        '      "priority": 85,\n'
        '      "bestPostingDay": "Wednesday",\n'
        '      "bestPostingTime": "7:30 PM",\n'
        '      "trendingFormat": "trend name",\n'
        '      "trendingAudio": "audio suggestion or N/A for LinkedIn",\n'
        '      "suggestedHookStyle": "hook style tip",\n'
        '      "action": "continue_draft|create_draft",\n'
        '      "draftId": null\n'
        "    }\n"
        "  ]\n"
        "}"
    )
    user_prompt = (
        f"Creator niche: {niche}\n"
        f"Interests: {', '.join(interests)}\n"
        f"Today's mood: {mood}\n"
        f"Content preference: {content_preference}\n"
        f"Goal: {goal}\n"
        f"Region: India (IST)\n"
        f"Suggested slot: {trends.get('suggestedDay')} {trends.get('suggestedTime')}\n"
        f"Focus story (if any): {focus_story_id or 'none — pick from full Story Bank'}\n\n"
        f"Story Bank:\n{story_lines}\n\n"
        f"Trending formats:\n{trend_lines}\n\n"
        f"Return 2-4 recommendations ranked by priority. Always explain why."
    )

    recommendations = []
    try:
        raw = llm.generate(system_prompt, user_prompt)
        cleaned = raw
        if "```json" in raw:
            cleaned = raw.split("```json")[-1].split("```")[0].strip()
        elif "```" in raw:
            cleaned = raw.split("```")[-1].split("```")[0].strip()
        parsed = json.loads(cleaned)
        for i, rec in enumerate(parsed.get("recommendations", [])[:4]):
            story = next((s for s in stories if s["id"] == rec.get("storyId")), None)
            if not story and stories:
                story = stories[i % len(stories)]
                rec["storyId"] = story["id"]
            fmt = rec.get("format", _suggest_format(mood, content_preference))
            story_drafts = drafts_by_story.get(rec.get("storyId"), [])
            existing = next((d for d in story_drafts if d["format"] == fmt), None)
            if existing and rec.get("action") != "create_draft":
                rec["action"] = "continue_draft"
                rec["draftId"] = existing["id"]
            elif not rec.get("draftId"):
                rec["action"] = rec.get("action", "create_draft")
                rec["draftId"] = None
            day, time = suggest_posting_slot(fmt, i)
            recommendations.append({
                "id": f"rec_{uuid.uuid4().hex[:8]}",
                "storyId": rec.get("storyId"),
                "storyTitle": story["title"] if story else "Your story",
                "format": fmt,
                "formatLabel": DRAFT_FORMAT_LABELS.get(fmt, fmt),
                "reason": rec.get("reason", "A strong match for today."),
                "priority": rec.get("priority", 80 - i * 5),
                "bestPostingDay": rec.get("bestPostingDay", trends.get("suggestedDay", "Wednesday")),
                "bestPostingTime": rec.get("bestPostingTime", trends.get("suggestedTime", "7:30 PM IST")),
                "trendingFormat": rec.get("trendingFormat", trends["trendingFormats"][0] if trends["trendingFormats"] else ""),
                "trendingAudio": rec.get("trendingAudio", trends["trendingAudio"][0] if trends["trendingAudio"] else "N/A"),
                "suggestedHookStyle": rec.get("suggestedHookStyle", trends["trendingHookPatterns"][0] if trends["trendingHookPatterns"] else ""),
                "action": rec.get("action", "create_draft"),
                "draftId": rec.get("draftId"),
                "scheduledAt": next_posting_datetime(
                    rec.get("bestPostingDay", trends.get("suggestedDay", "Wednesday")),
                    rec.get("bestPostingTime", trends.get("suggestedTime", "7:30 PM IST")),
                ).isoformat(),
                "publishConfidence": "high",
                "publishWindowNote": "Weekday evenings perform well for storytime reels in India.",
            })
    except Exception as e:
        logger.error(f"LLM recommendations failed: {e}")
        recommendations = _rule_based_recommendations(
            stories, drafts_by_story, mood, content_preference, goal, trends, focus_story_id
        )

    if focus_story_id and recommendations:
        recommendations = sorted(
            recommendations,
            key=lambda r: 0 if r["storyId"] == focus_story_id else 1,
        )

    return {
        "recommendations": recommendations,
        "trends": trends,
        "suggestReflection": False,
        "vibe": {"mood": mood, "contentPreference": content_preference, "goal": goal},
    }
