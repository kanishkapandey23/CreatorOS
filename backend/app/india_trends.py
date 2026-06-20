"""
India-focused content trends and posting windows (IST).
Practical defaults for Indian creators — not demo filler.
"""
from datetime import datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))

# Format → best day + time in IST (based on Indian audience behaviour)
POSTING_WINDOWS = {
    "linkedin_post": [
        ("Tuesday", "8:30 AM IST"),
        ("Wednesday", "10:00 AM IST"),
        ("Thursday", "12:30 PM IST"),
    ],
    "instagram_reel": [
        ("Wednesday", "7:30 PM IST"),
        ("Thursday", "8:00 PM IST"),
        ("Sunday", "7:00 PM IST"),
    ],
    "carousel": [
        ("Tuesday", "9:00 AM IST"),
        ("Thursday", "11:00 AM IST"),
    ],
    "twitter_thread": [
        ("Monday", "9:30 AM IST"),
        ("Wednesday", "6:30 PM IST"),
    ],
}

MOOD_TRENDS = {
    "reflective": {
        "formats": ["LinkedIn personal essay (short paragraphs)", "Slow-paced storytime reel"],
        "audio": ["Soft lo-fi instrumental — no lyrics", "Original voiceover only"],
        "hooks": ["Start with a quiet admission: 'Nobody talks about…'", "Open on a specific place in India — metro, chai stall, balcony"],
    },
    "happy": {
        "formats": ["GRWM / day-in-life reel", "Celebration carousel (3 slides max)"],
        "audio": ["Upbeat Bollywood acoustic (trending slowed edits)", "Feel-good indie Hindi"],
        "hooks": ["Lead with the win, then rewind to the struggle", "POV: 'The day everything finally clicked'"],
    },
    "funny": {
        "formats": ["Deadpan talking-head reel (Samay Raina-style)", "Expectation vs reality split screen"],
        "audio": ["Comedy background bed — low volume", "Trending meme audio from Indian creators"],
        "hooks": ["Blunt one-liner truth about your niche", "Start mid-conversation: 'So I did something stupid…'"],
    },
    "emotional": {
        "formats": ["Face-to-camera story reel", "Long-form LinkedIn letter"],
        "audio": ["Slowed + reverb Hindi track (nostalgic)", "Silence for first 3 seconds — then speak"],
        "hooks": ["Name the person or moment directly", "One sentence that makes people pause scrolling"],
    },
    "motivated": {
        "formats": ["Before/after transformation reel", "LinkedIn 'here's what I did' post"],
        "audio": ["High-energy phonk or gym-style beat (reels)", "No music — authority voice (LinkedIn)"],
        "hooks": ["Number in the first line: '3 months ago I…'", "Contrarian: 'Stop waiting for…'"],
    },
    "nostalgic": {
        "formats": ["Old photo + voiceover reel", "Then vs now carousel"],
        "audio": ["90s/2000s Bollywood slowed trend", "Old Hindi song clip under 15s"],
        "hooks": ["Show the old photo first", "'I found an old note that said…'"],
    },
    "random": {
        "formats": ["POV reel", "LinkedIn story post", "Quick carousel"],
        "audio": ["Whatever fits the story — trending or original", "Voiceover > trending audio"],
        "hooks": ["Specific moment > generic hook", "Ask a question Indians actually debate"],
    },
}

INDIA_TREND_PATTERNS = [
    {
        "title": "India: POV storytime reel (Hinglish)",
        "content": (
            "Instagram India — POV storytime reel\n"
            "Hook: Text on screen in Hinglish — relatable daily moment\n"
            "Format: Face cam or b-roll of your actual routine (metro, WFH, chai break)\n"
            "Audio: Trending slowed Hindi track OR your own voice\n"
            "Best time: Wed–Sun 7–9 PM IST"
        ),
    },
    {
        "title": "India: LinkedIn builder story (short paragraphs)",
        "content": (
            "LinkedIn India — personal builder story\n"
            "Hook: One bold line about a real failure or lesson\n"
            "Format: 4–6 short paragraphs, line breaks, no corporate jargon\n"
            "Best time: Tue–Thu 8:30–11 AM IST"
        ),
    },
    {
        "title": "India: 3-slide lesson carousel",
        "content": (
            "Instagram/LinkedIn carousel — 3 slides max\n"
            "Slide 1: Problem everyone in India feels\n"
            "Slide 2: What you tried\n"
            "Slide 3: One actionable takeaway\n"
            "Best time: Tuesday 9 AM IST"
        ),
    },
    {
        "title": "India: Expectation vs reality reel",
        "content": (
            "Reel format popular with Indian creators\n"
            "Split screen or quick cut: what people think vs what actually happened\n"
            "Works for career, relationships, founder life, exams, WFH\n"
            "Audio: Trending meme sound or deadpan voiceover"
        ),
    },
]


def suggest_posting_slot(fmt: str, index: int = 0) -> tuple[str, str]:
    slots = POSTING_WINDOWS.get(fmt, POSTING_WINDOWS["linkedin_post"])
    return slots[index % len(slots)]


def get_india_trends(mood: str = "reflective", fmt: str = "linkedin_post") -> dict:
    mood_data = MOOD_TRENDS.get(mood, MOOD_TRENDS["reflective"])
    day, time = suggest_posting_slot(fmt)
    return {
        "region": "India (IST)",
        "trendingFormats": mood_data["formats"] + [p["title"] for p in INDIA_TREND_PATTERNS[:2]],
        "trendingAudio": mood_data["audio"],
        "trendingHookPatterns": mood_data["hooks"],
        "trendingTopics": [p["title"].replace("India: ", "") for p in INDIA_TREND_PATTERNS],
        "suggestedDay": day,
        "suggestedTime": time,
    }


def next_posting_datetime(day_name: str, time_str: str) -> datetime:
    """Return next occurrence of e.g. Wednesday 7:30 PM IST as UTC-aware datetime."""
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    target_day = days.index(day_name) if day_name in days else 2
    hour, minute = 8, 30
    if "PM" in time_str.upper():
        parts = time_str.upper().replace("IST", "").strip().split(":")
        hour = int(parts[0].strip())
        if hour != 12:
            hour += 12
        minute = int(parts[1].replace("PM", "").strip()) if len(parts) > 1 else 0
    elif "AM" in time_str.upper():
        parts = time_str.upper().replace("IST", "").strip().split(":")
        hour = int(parts[0].strip())
        minute = int(parts[1].replace("AM", "").strip()) if len(parts) > 1 else 0

    now = datetime.now(IST)
    days_ahead = (target_day - now.weekday()) % 7
    if days_ahead == 0:
        candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if candidate <= now:
            days_ahead = 7
    target = now + timedelta(days=days_ahead)
    return target.replace(hour=hour, minute=minute, second=0, microsecond=0)


def week_days_ist(offset: int = 0) -> list[dict]:
    """Return 7 days starting from today (or offset weeks)."""
    today = datetime.now(IST).date() + timedelta(weeks=offset)
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    full = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    out = []
    for i in range(7):
        d = today + timedelta(days=i)
        out.append({
            "day": days[d.weekday()],
            "dayFull": full[d.weekday()],
            "date": d.strftime("%d %b"),
            "iso": d.isoformat(),
        })
    return out
