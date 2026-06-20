"""
Reminder processing, smart nudges, and in-app notification creation.
"""
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.database import (
    ContentDraft, ContentOpportunity, Notification, User,
    Memory, ReflectionSession,
)
from app.india_trends import IST
from app.notifications.channels import get_channel, CHANNEL_IN_APP, CHANNEL_EMAIL

logger = logging.getLogger("creatoros.notifications")

REMINDER_OFFSETS = {
    "1d": timedelta(days=1),
    "6h": timedelta(hours=6),
    "1h": timedelta(hours=1),
    "15m": timedelta(minutes=15),
}

DEFAULT_OFFSETS = ["1d", "1h"]
FORMAT_LABELS = {
    "linkedin_post": "LinkedIn",
    "instagram_reel": "Reel",
    "carousel": "Carousel",
    "twitter_thread": "Thread",
}


def _parse_json(val, default):
    if not val:
        return default
    try:
        return json.loads(val)
    except Exception:
        return default


def _draft_progress(draft: ContentDraft) -> int:
    sections = draft.sections or {}
    if not sections:
        return 0
    filled = sum(1 for v in sections.values() if v and str(v).strip())
    return int((filled / max(len(sections), 1)) * 100)


def _story_title(db: Session, story_id: str) -> str:
    opp = db.query(ContentOpportunity).filter(ContentOpportunity.id == story_id).first()
    return opp.topic if opp else "your story"


def _create_notification(
    db: Session,
    user_id: str,
    ntype: str,
    title: str,
    body: str,
    action_type: str,
    action_href: str,
    action_label: str,
    draft_id: str = None,
    story_id: str = None,
    email_subject: str = None,
    email_body: str = None,
    channels: list = None,
) -> Notification:
    """Create in-app notification and optionally dispatch email."""
    notif = Notification(
        id=f"ntf_{uuid.uuid4().hex[:10]}",
        user_id=user_id,
        type=ntype,
        title=title,
        body=body,
        action_type=action_type,
        action_href=action_href,
        action_label=action_label,
        draft_id=draft_id,
        story_id=story_id,
    )
    db.add(notif)

    user = db.query(User).filter(User.id == user_id).first()
    payload = {
        "title": title,
        "body": body,
        "emailSubject": email_subject or title,
        "emailBody": email_body or body,
        "actionHref": action_href,
    }
    for ch in (channels or [CHANNEL_IN_APP]):
        if ch == CHANNEL_IN_APP:
            continue
        channel = get_channel(ch)
        if channel and user:
            channel.send(user, payload)

    return notif


def _human_reminder_message(draft: ContentDraft, story_title: str, offset_key: str) -> tuple[str, str]:
    fmt = FORMAT_LABELS.get(draft.format, "draft")
    progress = _draft_progress(draft)

    if offset_key == "1d":
        title = f"Tomorrow: {story_title}"
        body = (
            f"You planned to work on \"{story_title}\" tomorrow. "
            f"Even 15 minutes tonight to review your {fmt} draft counts as progress."
        )
    elif offset_key in ("6h", "1h"):
        title = f"Coming up: {fmt} for {story_title}"
        body = (
            f"Your {fmt} draft is on the calendar soon. "
            + (f"You already have the hook — finishing the ending might take less than 10 minutes." if progress >= 30 else "A small push now will make publish day feel easy.")
        )
    elif offset_key == "15m":
        title = f"Almost time: {story_title}"
        body = f"Your {fmt} draft is scheduled shortly. Open it now and do one final read-through."
    else:
        title = f"Still on your list: {story_title}"
        body = f"Your {fmt} draft is waiting. You set a reminder to keep going until it's done — no pressure, just a gentle nudge."

    return title, body


def process_draft_reminders(db: Session, user_id: str):
    """Check scheduled drafts and fire due reminders."""
    now = datetime.now(IST)
    drafts = db.query(ContentDraft).filter(
        ContentDraft.user_id == user_id,
        ContentDraft.reminder_enabled == True,
        ContentDraft.scheduled_at.isnot(None),
        ContentDraft.status.in_(["draft", "scheduled"]),
    ).all()

    for draft in drafts:
        scheduled = draft.scheduled_at
        if scheduled.tzinfo is None:
            scheduled = scheduled.replace(tzinfo=IST)
        else:
            scheduled = scheduled.astimezone(IST)

        offsets = _parse_json(draft.reminder_offsets_json, DEFAULT_OFFSETS)
        sent = _parse_json(draft.reminder_sent_json, {})
        channels = _parse_json(draft.reminder_channels_json, [CHANNEL_IN_APP])
        story_title = _story_title(db, draft.story_id)

        if "until_complete" in offsets:
            key = "until_complete"
            last = sent.get(key)
            if not last or (now - datetime.fromisoformat(last)).days >= 1:
                title, body = _human_reminder_message(draft, story_title, key)
                _create_notification(
                    db, user_id, "reminder", title, body,
                    "continue_draft", f"/stories/{draft.story_id}/studio/{draft.id}",
                    "Continue draft", draft.id, draft.story_id,
                    email_subject=f"Your {FORMAT_LABELS.get(draft.format, 'draft')} is waiting",
                    email_body=body, channels=channels,
                )
                sent[key] = now.isoformat()
        else:
            for offset_key in offsets:
                if offset_key not in REMINDER_OFFSETS:
                    continue
                fire_at = scheduled - REMINDER_OFFSETS[offset_key]
                sent_key = f"{offset_key}_{scheduled.isoformat()}"
                if sent.get(sent_key):
                    continue
                if now >= fire_at and now < scheduled + timedelta(hours=2):
                    title, body = _human_reminder_message(draft, story_title, offset_key)
                    email_subj = f"Your {FORMAT_LABELS.get(draft.format, 'draft')} is scheduled for "
                    if offset_key == "1d":
                        email_subj += "tomorrow"
                    else:
                        email_subj += "soon"
                    email_body = (
                        f"You planned to publish \"{story_title}\".\n\n"
                        f"Checklist:\n"
                        f"□ Review caption\n"
                        f"□ Finalize visuals\n"
                        f"□ Publish\n\n"
                        f"Open CreatorOS to continue editing."
                    )
                    _create_notification(
                        db, user_id, "reminder", title, body,
                        "continue_draft", f"/stories/{draft.story_id}/studio/{draft.id}",
                        "Continue draft", draft.id, draft.story_id,
                        email_subject=email_subj, email_body=email_body, channels=channels,
                    )
                    sent[sent_key] = now.isoformat()

        draft.reminder_sent_json = json.dumps(sent)


def generate_smart_nudges(db: Session, user_id: str):
    """Gentle accountability nudges — no guilt."""
    now = datetime.now(IST)

    # Skip if we already nudged today
    existing_today = db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.type == "nudge",
        Notification.created_at >= now.replace(hour=0, minute=0, second=0),
    ).first()
    if existing_today:
        return

    stories = db.query(ContentOpportunity).filter(
        ContentOpportunity.user_id == user_id,
    ).count()

    recent_reflection = db.query(ReflectionSession).filter(
        ReflectionSession.user_id == user_id,
        ReflectionSession.status == "completed",
        ReflectionSession.created_at >= now - timedelta(days=7),
    ).count()

    if stories >= 2 and recent_reflection == 0:
        unused = stories - db.query(ContentDraft).filter(ContentDraft.user_id == user_id).count()
        if unused > 0:
            _create_notification(
                db, user_id, "nudge",
                "Stories waiting in your bank",
                f"You haven't captured a new moment this week. Your Story Bank has {stories} stories ready to explore.",
                "open_strategy", "/strategy", "Get a recommendation",
            )
            return

    stale_drafts = db.query(ContentDraft).filter(
        ContentDraft.user_id == user_id,
        ContentDraft.status.in_(["draft", "scheduled"]),
        ContentDraft.updated_at < now - timedelta(days=5),
    ).all()

    for draft in stale_drafts[:1]:
        progress = _draft_progress(draft)
        if progress >= 50:
            title = _story_title(db, draft.story_id)
            fmt = FORMAT_LABELS.get(draft.format, "draft")
            _create_notification(
                db, user_id, "nudge",
                f"Your {fmt} is {progress}% complete",
                f"\"{title}\" is almost there. Finishing it today might take less than 10 minutes.",
                "continue_draft", f"/stories/{draft.story_id}/studio/{draft.id}",
                "Continue editing", draft.id, draft.story_id,
            )
            return

    overdue = db.query(ContentDraft).filter(
        ContentDraft.user_id == user_id,
        ContentDraft.scheduled_at.isnot(None),
        ContentDraft.scheduled_at < now - timedelta(days=1),
        ContentDraft.status.in_(["draft", "scheduled"]),
    ).first()

    if overdue:
        title = _story_title(db, overdue.story_id)
        _create_notification(
            db, user_id, "overdue",
            f"Missed slot: {title}",
            "Life happens. Want to reschedule this draft or pick it back up?",
            "open_planner", "/planner", "Reschedule",
            overdue.id, overdue.story_id,
        )


def get_weekly_digest(db: Session, user_id: str) -> dict:
    now = datetime.now(IST)
    week_ago = now - timedelta(days=7)

    drafts_done = db.query(ContentDraft).filter(
        ContentDraft.user_id == user_id,
        ContentDraft.status == "published",
        ContentDraft.updated_at >= week_ago,
    ).count()

    stories_captured = db.query(ReflectionSession).filter(
        ReflectionSession.user_id == user_id,
        ReflectionSession.status == "completed",
        ReflectionSession.created_at >= week_ago,
    ).count()

    scheduled = db.query(ContentDraft).filter(
        ContentDraft.user_id == user_id,
        ContentDraft.scheduled_at.isnot(None),
        ContentDraft.scheduled_at >= week_ago,
    ).count()

    completed_scheduled = db.query(ContentDraft).filter(
        ContentDraft.user_id == user_id,
        ContentDraft.status == "published",
        ContentDraft.scheduled_at.isnot(None),
        ContentDraft.updated_at >= week_ago,
    ).count()

    rate = int((completed_scheduled / scheduled * 100)) if scheduled else 0
    bank_count = db.query(ContentOpportunity).filter(ContentOpportunity.user_id == user_id).count()

    focus = "Capture one honest moment in Reflection."
    if bank_count >= 3:
        focus = "Pick one Story Bank memory and turn it into a Reel or LinkedIn post."
    if drafts_done >= 2:
        focus = "Keep your streak — schedule next week's drafts in Planner."

    return {
        "period": f"{week_ago.strftime('%d %b')} – {now.strftime('%d %b')}",
        "draftsCompleted": drafts_done,
        "storiesCaptured": stories_captured,
        "published": drafts_done,
        "plannerCompletionRate": rate,
        "suggestedFocus": focus,
        "message": (
            f"This week you captured {stories_captured} {'story' if stories_captured == 1 else 'stories'} "
            f"and completed {drafts_done} {'draft' if drafts_done == 1 else 'drafts'}. "
            f"{'Nice rhythm — ' if drafts_done else ''}{focus}"
        ),
    }


def _maybe_weekly_digest_notification(db: Session, user_id: str):
    now = datetime.now(IST)
    if now.weekday() != 6 or now.hour < 17:
        return
    week_key = now.strftime("%Y-W%W")
    exists = db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.type == "digest",
        Notification.title.like(f"%{week_key}%"),
    ).first()
    if exists:
        return
    digest = get_weekly_digest(db, user_id)
    _create_notification(
        db, user_id, "digest",
        f"Weekly digest · {week_key}",
        digest["message"],
        "open_planner", "/planner", "View planner",
        email_subject="Your CreatorOS week in review",
        email_body=digest["message"],
        channels=[CHANNEL_IN_APP, CHANNEL_EMAIL],
    )


def sync_notifications(db: Session, user_id: str) -> list:
    """Process reminders + nudges, return active notifications."""
    process_draft_reminders(db, user_id)
    generate_smart_nudges(db, user_id)
    _maybe_weekly_digest_notification(db, user_id)
    db.commit()

    notifs = db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.dismissed == False,
    ).order_by(Notification.created_at.desc()).limit(30).all()

    return [_notif_to_dict(n) for n in notifs]


def _notif_to_dict(n: Notification) -> dict:
    return {
        "id": n.id,
        "type": n.type,
        "title": n.title,
        "body": n.body,
        "actionType": n.action_type,
        "actionHref": n.action_href,
        "actionLabel": n.action_label,
        "draftId": n.draft_id,
        "storyId": n.story_id,
        "read": n.read,
        "createdAt": n.created_at.isoformat() if n.created_at else None,
    }
