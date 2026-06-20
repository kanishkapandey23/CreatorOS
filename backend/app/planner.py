"""Simple weekly planner — schedules content drafts."""
import json
from sqlalchemy.orm import Session

from app.database import ContentDraft, ContentOpportunity
from app.india_trends import week_days_ist, IST

DRAFT_FORMAT_LABELS = {
    "linkedin_post": "LinkedIn",
    "instagram_reel": "Reel",
    "carousel": "Carousel",
    "twitter_thread": "Thread",
}


def _draft_item(draft: ContentDraft, story_title: str) -> dict:
    scheduled = None
    if draft.scheduled_at:
        scheduled = draft.scheduled_at.astimezone(IST) if draft.scheduled_at.tzinfo else draft.scheduled_at
    return {
        "id": draft.id,
        "storyId": draft.story_id,
        "title": story_title,
        "type": DRAFT_FORMAT_LABELS.get(draft.format, draft.format),
        "format": draft.format,
        "status": draft.status,
        "scheduledAt": scheduled.isoformat() if scheduled else None,
        "reminderEnabled": bool(draft.reminder_enabled),
        "reminderActive": bool(draft.reminder_enabled and draft.scheduled_at),
        "reminderOffsets": json.loads(draft.reminder_offsets_json or '["1d","1h"]'),
    }


def get_planner_week(db: Session, user_id: str, offset: int = 0) -> dict:
    days = week_days_ist(offset)
    day_isos = {d["iso"] for d in days}

    drafts = db.query(ContentDraft).filter(
        ContentDraft.user_id == user_id,
    ).order_by(ContentDraft.updated_at.desc()).all()

    story_titles = {}
    for d in drafts:
        if d.story_id not in story_titles:
            opp = db.query(ContentOpportunity).filter(ContentOpportunity.id == d.story_id).first()
            story_titles[d.story_id] = opp.topic if opp else "Untitled story"

    scheduled_by_day = {d["iso"]: [] for d in days}
    unscheduled = []

    for draft in drafts:
        item = _draft_item(draft, story_titles.get(d.story_id, "Untitled story"))
        if draft.scheduled_at:
            local = draft.scheduled_at
            if local.tzinfo is None:
                local = local.replace(tzinfo=IST)
            else:
                local = local.astimezone(IST)
            iso = local.date().isoformat()
            if iso in scheduled_by_day:
                scheduled_by_day[iso].append(item)
            else:
                unscheduled.append(item)
        else:
            unscheduled.append(item)

    week = []
    for d in days:
        week.append({
            "day": d["day"],
            "dayFull": d["dayFull"],
            "date": d["date"],
            "iso": d["iso"],
            "items": scheduled_by_day[d["iso"]],
        })

    return {"week": week, "unscheduled": unscheduled}
