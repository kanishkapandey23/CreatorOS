import os
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Optional

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
import bcrypt
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.database import User, CreatorProfile, get_db

load_dotenv()

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

security = HTTPBearer(auto_error=False)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None
    niche: str = "Engineering & Storytelling"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserProfileResponse(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    niche: str
    created_at: str


class OAuthProvidersResponse(BaseModel):
    providers: list[str]


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def create_access_token(user_id: str, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.utcnow() + expires_delta
    return jwt.encode({"user_id": user_id, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = verify_token(credentials.credentials)
    user = db.query(User).filter(User.id == payload["user_id"]).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def user_to_profile(user: User, profile: Optional[CreatorProfile] = None) -> UserProfileResponse:
    return UserProfileResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        niche=profile.niche if profile else "Engineering & Storytelling",
        created_at=user.created_at.isoformat(),
    )


def _default_creator_profile(user_id: str, niche: str = "Engineering & Storytelling") -> CreatorProfile:
    return CreatorProfile(
        user_id=user_id,
        niche=niche,
        interests=["coding", "indie hacking", "creative writing", "startups"],
        preferred_tone="casual",
        goals=["build in public", "write authentic stories", "explain simple technical lessons"],
    )


def find_or_create_oauth_user(db: Session, profile_data: dict) -> User:
    provider = profile_data["provider"]
    subject = profile_data["subject"]
    email = profile_data["email"].lower()
    name = profile_data.get("name")

    user = db.query(User).filter(
        User.oauth_provider == provider,
        User.oauth_subject == subject,
    ).first()
    if user:
        return user

    user = db.query(User).filter(User.email == email).first()
    if user:
        if user.oauth_provider and user.oauth_provider != provider:
            raise HTTPException(
                status_code=400,
                detail=f"This email is linked to {user.oauth_provider}. Sign in with that provider instead.",
            )
        user.oauth_provider = provider
        user.oauth_subject = subject
        if name and not user.name:
            user.name = name
        db.commit()
        db.refresh(user)
        return user

    user_id = f"user_{uuid.uuid4().hex[:12]}"
    user = User(
        id=user_id,
        email=email,
        name=name,
        hashed_password=get_password_hash(secrets.token_urlsafe(32)),
        oauth_provider=provider,
        oauth_subject=subject,
    )
    db.add(user)
    db.add(_default_creator_profile(user_id))
    db.commit()
    db.refresh(user)
    return user
