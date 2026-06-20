import datetime
import json
import os
from sqlalchemy import create_engine, Column, String, DateTime, Text, LargeBinary, ForeignKey, Boolean, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./creatoros.db")

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    """Authentication identity — email, password, account metadata."""

    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)
    name = Column(String, nullable=True)
    oauth_provider = Column(String, nullable=True, index=True)
    oauth_subject = Column(String, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    profile = relationship("CreatorProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    memories = relationship("Memory", back_populates="user")
    opportunities = relationship("ContentOpportunity", back_populates="user")
    reflection_sessions = relationship("ReflectionSession", back_populates="user")
    chat_sessions = relationship("ChatSession", back_populates="user")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")


class CreatorProfile(Base):
    """
    Creator-specific preferences (niche, tone, goals).
    One-to-one with User — separate from auth so profile data can evolve independently.
    """

    __tablename__ = "creator_profile"

    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    niche = Column(String, default="Engineering & Storytelling")
    interests_json = Column(Text, default="[]")
    preferred_tone = Column(String, default="casual")
    goals_json = Column(Text, default="[]")
    content_preferences_json = Column(Text, default="{}")

    user = relationship("User", back_populates="profile")

    @property
    def interests(self):
        return json.loads(self.interests_json or "[]")

    @interests.setter
    def interests(self, val):
        self.interests_json = json.dumps(val or [])

    @property
    def goals(self):
        return json.loads(self.goals_json or "[]")

    @goals.setter
    def goals(self, val):
        self.goals_json = json.dumps(val or [])

    @property
    def content_preferences(self):
        return json.loads(self.content_preferences_json or "{}")

    @content_preferences.setter
    def content_preferences(self, val):
        self.content_preferences_json = json.dumps(val or {})


class Memory(Base):
    __tablename__ = "memories"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), index=True, nullable=False)
    memory_type = Column(String, index=True)
    topic_json = Column(Text, default="[]")
    event = Column(Text)
    turning_point = Column(Text, nullable=True)
    emotion_json = Column(Text, default="[]")
    potential_content_angles_json = Column(Text, default="[]")
    creator_traits_json = Column(Text, default="{}")
    raw_input = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    embedding = Column(LargeBinary, nullable=True)

    user = relationship("User", back_populates="memories")

    @property
    def topic(self):
        return json.loads(self.topic_json or "[]")

    @topic.setter
    def topic(self, val):
        self.topic_json = json.dumps(val or [])

    @property
    def emotion(self):
        return json.loads(self.emotion_json or "[]")

    @emotion.setter
    def emotion(self, val):
        self.emotion_json = json.dumps(val or [])

    @property
    def potential_content_angles(self):
        return json.loads(self.potential_content_angles_json or "[]")

    @potential_content_angles.setter
    def potential_content_angles(self, val):
        self.potential_content_angles_json = json.dumps(val or [])

    @property
    def creator_traits(self):
        return json.loads(self.creator_traits_json or "{}")

    @creator_traits.setter
    def creator_traits(self, val):
        self.creator_traits_json = json.dumps(val or {})


class StrategyKB(Base):
    __tablename__ = "strategy_kb"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(Text)
    kb_type = Column(String, index=True)
    embedding = Column(LargeBinary, nullable=True)


class ContentOpportunity(Base):
    __tablename__ = "content_opportunities"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), index=True, nullable=False)
    memory_id = Column(String, ForeignKey("memories.id"), nullable=True)
    content_type = Column(String)
    topic = Column(String)
    hook_options_json = Column(Text, default="[]")
    structure_json = Column(Text, default="[]")
    creator_inputs_used_json = Column(Text, default="[]")
    status = Column(String, default="idea")
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="opportunities")
    memory = relationship("Memory")

    @property
    def hook_options(self):
        return json.loads(self.hook_options_json or "[]")

    @hook_options.setter
    def hook_options(self, val):
        self.hook_options_json = json.dumps(val or [])

    @property
    def structure(self):
        return json.loads(self.structure_json or "[]")

    @structure.setter
    def structure(self, val):
        self.structure_json = json.dumps(val or [])

    @property
    def creator_inputs_used(self):
        return json.loads(self.creator_inputs_used_json or "[]")

    @creator_inputs_used.setter
    def creator_inputs_used(self, val):
        self.creator_inputs_used_json = json.dumps(val or [])


class StoryDraft(Base):
    __tablename__ = "story_drafts"

    story_id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), index=True, nullable=False)
    sections_json = Column(Text, default="{}")
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    @property
    def sections(self):
        return json.loads(self.sections_json or "{}")

    @sections.setter
    def sections(self, val):
        self.sections_json = json.dumps(val or {})


class ContentDraft(Base):
    """Content draft — one story can have many drafts (LinkedIn, Reel, etc.)."""

    __tablename__ = "content_drafts"

    id = Column(String, primary_key=True, index=True)
    story_id = Column(String, ForeignKey("content_opportunities.id"), index=True, nullable=False)
    user_id = Column(String, ForeignKey("users.id"), index=True, nullable=False)
    format = Column(String, default="linkedin_post")
    status = Column(String, default="draft")
    sections_json = Column(Text, default="{}")
    scheduled_at = Column(DateTime, nullable=True)
    reminder_enabled = Column(Boolean, default=False)
    reminder_offsets_json = Column(Text, default='["1d","1h"]')
    reminder_channels_json = Column(Text, default='["in_app","email"]')
    reminder_sent_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    @property
    def sections(self):
        return json.loads(self.sections_json or "{}")

    @sections.setter
    def sections(self, val):
        self.sections_json = json.dumps(val or {})


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), index=True, nullable=False)
    type = Column(String, default="reminder")
    title = Column(String)
    body = Column(Text)
    action_type = Column(String)
    action_href = Column(String)
    action_label = Column(String)
    draft_id = Column(String, ForeignKey("content_drafts.id"), nullable=True)
    story_id = Column(String, nullable=True)
    read = Column(Boolean, default=False)
    dismissed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="notifications")


class ReflectionSession(Base):
    __tablename__ = "reflection_sessions"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), index=True, nullable=False)
    title = Column(String)
    status = Column(String, default="active")
    prompts_json = Column(Text, nullable=True)
    detected_mood = Column(String, nullable=True)
    vibe_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="reflection_sessions")
    answers = relationship("ReflectionAnswer", back_populates="session", cascade="all, delete-orphan")


class ReflectionAnswer(Base):
    __tablename__ = "reflection_answers"

    id = Column(String, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("reflection_sessions.id"))
    prompt_id = Column(String)
    prompt_title = Column(String)
    answer_text = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    session = relationship("ReflectionSession", back_populates="answers")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), index=True, nullable=False)
    title = Column(String)
    memory_id = Column(String, ForeignKey("memories.id"), nullable=True)
    opportunity_id = Column(String, ForeignKey("content_opportunities.id"), nullable=True)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="chat_sessions")
    memory = relationship("Memory")
    opportunity = relationship("ContentOpportunity")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("chat_sessions.id"))
    role = Column(String)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    session = relationship("ChatSession", back_populates="messages")


_USER_SCOPED_COLUMNS = [
    ("memories", "user_id"),
    ("content_opportunities", "user_id"),
    ("story_drafts", "user_id"),
    ("content_drafts", "user_id"),
    ("reflection_sessions", "user_id"),
    ("chat_sessions", "user_id"),
]


def _migrate_add_user_id_columns(db):
    for table, column in _USER_SCOPED_COLUMNS:
        try:
            db.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} VARCHAR"))
            db.commit()
        except Exception:
            db.rollback()


_USER_OAUTH_COLUMNS = [
    ("oauth_provider", "VARCHAR"),
    ("oauth_subject", "VARCHAR"),
]


def _migrate_user_oauth_columns(db):
    for column, coltype in _USER_OAUTH_COLUMNS:
        try:
            db.execute(text(f"ALTER TABLE users ADD COLUMN {column} {coltype}"))
            db.commit()
        except Exception:
            db.rollback()


def _migrate_creator_profile_id_to_user_id(db):
    try:
        # Check column names
        res = db.execute(text("PRAGMA table_info(creator_profile)")).fetchall()
        columns = [row[1] for row in res]
        if "id" in columns and "user_id" not in columns:
            db.execute(text("ALTER TABLE creator_profile RENAME COLUMN id TO user_id"))
            db.commit()
    except Exception:
        db.rollback()


def _migrate_story_drafts_to_content_drafts(db):
    """One-time migration: legacy story_drafts (1:1) → content_drafts (1:many)."""
    import uuid
    try:
        if db.query(ContentDraft).count() > 0:
            return
        legacy = db.query(StoryDraft).all()
        for ld in legacy:
            opp = db.query(ContentOpportunity).filter(ContentOpportunity.id == ld.story_id).first()
            fmt = opp.content_type if opp and opp.content_type else "linkedin_post"
            db.add(ContentDraft(
                id=f"dr_{uuid.uuid4().hex[:8]}",
                story_id=ld.story_id,
                user_id=ld.user_id,
                format=fmt,
                status="draft",
                sections_json=ld.sections_json or "{}",
                updated_at=ld.updated_at or datetime.datetime.utcnow(),
            ))
        db.commit()
    except Exception:
        db.rollback()


def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        _migrate_add_user_id_columns(db)
        _migrate_user_oauth_columns(db)
        _migrate_creator_profile_id_to_user_id(db)
        try:
            db.execute(text("ALTER TABLE chat_sessions ADD COLUMN opportunity_id VARCHAR"))
            db.commit()
        except Exception:
            db.rollback()
        _migrate_story_drafts_to_content_drafts(db)
        for col, coltype in [("prompts_json", "TEXT"), ("detected_mood", "VARCHAR"), ("vibe_json", "TEXT")]:
            try:
                db.execute(text(f"ALTER TABLE reflection_sessions ADD COLUMN {col} {coltype}"))
                db.commit()
            except Exception:
                db.rollback()
        try:
            db.execute(text("ALTER TABLE content_drafts ADD COLUMN scheduled_at DATETIME"))
            db.commit()
        except Exception:
            db.rollback()
        for col, coltype in [
            ("reminder_enabled", "BOOLEAN"),
            ("reminder_offsets_json", "TEXT"),
            ("reminder_channels_json", "TEXT"),
            ("reminder_sent_json", "TEXT"),
        ]:
            try:
                db.execute(text(f"ALTER TABLE content_drafts ADD COLUMN {col} {coltype}"))
                db.commit()
            except Exception:
                db.rollback()
    finally:
        db.close()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
