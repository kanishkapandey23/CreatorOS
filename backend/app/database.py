import datetime
import json
import os
from sqlalchemy import create_engine, Column, String, DateTime, Text, LargeBinary, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./creatoros.db")

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class CreatorProfile(Base):
    __tablename__ = "creator_profile"
    
    id = Column(String, primary_key=True, index=True)
    niche = Column(String, default="Engineering & Storytelling")
    interests_json = Column(Text, default="[]")  # List of strings
    preferred_tone = Column(String, default="casual")
    goals_json = Column(Text, default="[]")  # List of strings
    content_preferences_json = Column(Text, default="{}")  # Arbitrary preferences dict

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
    memory_type = Column(String, index=True)  # e.g., personal_experience, lesson, emotion, opinion
    topic_json = Column(Text, default="[]")  # List of strings
    event = Column(Text)
    turning_point = Column(Text, nullable=True)
    emotion_json = Column(Text, default="[]")  # List of strings
    potential_content_angles_json = Column(Text, default="[]")  # List of strings
    creator_traits_json = Column(Text, default="{}")  # Preferences mapping dict
    raw_input = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    embedding = Column(LargeBinary, nullable=True)  # Vector embedding stored as binary float array

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
    content = Column(Text)  # Storytelling template details
    kb_type = Column(String, index=True)  # framework, structure, pattern
    embedding = Column(LargeBinary, nullable=True)


class ContentOpportunity(Base):
    __tablename__ = "content_opportunities"
    
    id = Column(String, primary_key=True, index=True)
    memory_id = Column(String, ForeignKey("memories.id"), nullable=True)
    content_type = Column(String)  # e.g. story_reel, linkedin_post, newsletter
    topic = Column(String)
    hook_options_json = Column(Text, default="[]")  # List of hooks
    structure_json = Column(Text, default="[]")  # e.g., ["context", "problem", "lesson"]
    creator_inputs_used_json = Column(Text, default="[]")
    status = Column(String, default="idea")  # idea, draft, published
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

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
    
    story_id = Column(String, primary_key=True, index=True)  # links to opportunity or memory
    sections_json = Column(Text, default="{}")  # {hook: '', experience: '', conflict: '', lesson: '', cta: ''}
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    @property
    def sections(self):
        return json.loads(self.sections_json or "{}")
    
    @sections.setter
    def sections(self, val):
        self.sections_json = json.dumps(val or {})


class ReflectionSession(Base):
    __tablename__ = "reflection_sessions"
    
    id = Column(String, primary_key=True, index=True)
    title = Column(String)
    status = Column(String, default="active")  # active, completed
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

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
    title = Column(String)
    memory_id = Column(String, ForeignKey("memories.id"), nullable=True)
    opportunity_id = Column(String, ForeignKey("content_opportunities.id"), nullable=True)
    status = Column(String, default="active")  # active, completed (opportunity structured)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    memory = relationship("Memory")
    opportunity = relationship("ContentOpportunity")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(String, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("chat_sessions.id"))
    role = Column(String)  # user, assistant
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    session = relationship("ChatSession", back_populates="messages")


def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Check/add opportunity_id column to chat_sessions safely
    try:
        db.execute("ALTER TABLE chat_sessions ADD COLUMN opportunity_id VARCHAR")
        db.commit()
    except Exception:
        pass
        
    # Check if creator profile exists, create default if not
    profile = db.query(CreatorProfile).filter(CreatorProfile.id == "u_demo").first()
    if not profile:
        profile = CreatorProfile(
            id="u_demo",
            niche="Engineering & Tech Storytelling",
            interests=["coding", "indie hacking", "creative writing", "startups"],
            preferred_tone="casual",
            goals=["build in public", "write authentic stories", "explain simple technical lessons"]
        )
        db.add(profile)
        db.commit()
    db.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
