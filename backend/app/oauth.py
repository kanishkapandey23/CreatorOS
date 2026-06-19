import os
import secrets
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException
from jose import JWTError, jwt

from app.auth import SECRET_KEY, ALGORITHM

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "").strip()
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "").strip()
GITHUB_CLIENT_ID = os.environ.get("GITHUB_CLIENT_ID", "").strip()
GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET", "").strip()
API_BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000").rstrip("/")

OAUTH_STATE_EXPIRE_MINUTES = 10


def get_configured_providers() -> list[str]:
    providers = []
    if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
        providers.append("google")
    if GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET:
        providers.append("github")
    return providers


def is_provider_configured(provider: str) -> bool:
    return provider in get_configured_providers()


def create_oauth_state(provider: str) -> str:
    payload = {
        "provider": provider,
        "nonce": secrets.token_urlsafe(16),
        "exp": datetime.utcnow() + timedelta(minutes=OAUTH_STATE_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_oauth_state(state: str, provider: str) -> None:
    try:
        payload = jwt.decode(state, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")
    if payload.get("provider") != provider:
        raise HTTPException(status_code=400, detail="OAuth state provider mismatch")


def build_authorize_url(provider: str, state: str) -> str:
    if provider == "google":
        params = {
            "client_id": GOOGLE_CLIENT_ID,
            "redirect_uri": f"{API_BASE_URL}/api/auth/oauth/google/callback",
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "online",
            "prompt": "select_account",
        }
        return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"

    if provider == "github":
        params = {
            "client_id": GITHUB_CLIENT_ID,
            "redirect_uri": f"{API_BASE_URL}/api/auth/oauth/github/callback",
            "scope": "read:user user:email",
            "state": state,
        }
        return f"https://github.com/login/oauth/authorize?{urlencode(params)}"

    raise HTTPException(status_code=400, detail="Unsupported OAuth provider")


async def fetch_oauth_profile(provider: str, code: str) -> dict[str, Any]:
    if provider == "google":
        return await _fetch_google_profile(code)
    if provider == "github":
        return await _fetch_github_profile(code)
    raise HTTPException(status_code=400, detail="Unsupported OAuth provider")


async def _fetch_google_profile(code: str) -> dict[str, Any]:
    redirect_uri = f"{API_BASE_URL}/api/auth/oauth/google/callback"
    async with httpx.AsyncClient(timeout=20.0) as client:
        token_res = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
            headers={"Accept": "application/json"},
        )
        if token_res.status_code != 200:
            raise HTTPException(status_code=400, detail="Google token exchange failed")
        access_token = token_res.json().get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="Google access token missing")

        user_res = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if user_res.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch Google profile")
        data = user_res.json()

    email = data.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Google account has no email")

    return {
        "provider": "google",
        "subject": data.get("sub"),
        "email": email.lower(),
        "name": data.get("name"),
    }


async def _fetch_github_profile(code: str) -> dict[str, Any]:
    redirect_uri = f"{API_BASE_URL}/api/auth/oauth/github/callback"
    async with httpx.AsyncClient(timeout=20.0) as client:
        token_res = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": redirect_uri,
            },
            headers={"Accept": "application/json"},
        )
        if token_res.status_code != 200:
            raise HTTPException(status_code=400, detail="GitHub token exchange failed")
        access_token = token_res.json().get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="GitHub access token missing")

        user_res = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
            },
        )
        if user_res.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch GitHub profile")
        data = user_res.json()

        email = data.get("email")
        if not email:
            emails_res = await client.get(
                "https://api.github.com/user/emails",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                },
            )
            if emails_res.status_code == 200:
                for entry in emails_res.json():
                    if entry.get("primary") and entry.get("verified"):
                        email = entry.get("email")
                        break
                if not email:
                    for entry in emails_res.json():
                        if entry.get("verified"):
                            email = entry.get("email")
                            break

    if not email:
        raise HTTPException(status_code=400, detail="GitHub account has no verified email")

    return {
        "provider": "github",
        "subject": str(data.get("id")),
        "email": email.lower(),
        "name": data.get("name") or data.get("login"),
    }


def frontend_callback_url(token: str | None = None, error: str | None = None) -> str:
    if token:
        return f"{FRONTEND_URL}/callback?token={token}"
    return f"{FRONTEND_URL}/callback?error={error or 'oauth_failed'}"
