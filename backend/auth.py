"""Emergent Google Auth (deferred) + dev-login bypass for Khova AI.

Deferred login: anonymous users can run Discover -> Research -> Opportunities ->
Positioning -> Transformation -> Format. Auth is required only for product
generation / save / export endpoints.
"""
import os
import uuid
import logging
from datetime import datetime, timezone, timedelta

import httpx
from fastapi import APIRouter, Request, Response, HTTPException, Depends
from pydantic import BaseModel

from db import db, serialize_doc

logger = logging.getLogger("khova.auth")

auth_router = APIRouter(prefix="/api/auth", tags=["auth"])

EMERGENT_SESSION_URL = "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data"
SESSION_DAYS = 7


async def _create_or_update_user(email: str, name: str, picture: str = "") -> dict:
    existing = await db.users.find_one({"email": email}, {"_id": 0})
    if existing:
        await db.users.update_one(
            {"email": email},
            {"$set": {"name": name or existing.get("name"), "picture": picture or existing.get("picture")}},
        )
        return existing
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    doc = {
        "user_id": user_id,
        "email": email,
        "name": name or email.split("@")[0],
        "picture": picture or "",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.users.insert_one(dict(doc))
    return doc


async def _new_session(user_id: str) -> str:
    token = f"sess_{uuid.uuid4().hex}"
    await db.user_sessions.insert_one({
        "user_id": user_id,
        "session_token": token,
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return token


def _set_cookie(response: Response, token: str):
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=SESSION_DAYS * 24 * 3600,
    )


async def _get_user_from_request(request: Request):
    token = request.cookies.get("session_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.lower().startswith("bearer "):
            token = auth_header[7:].strip()
    if not token:
        return None
    session = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if not session:
        return None
    expires_at = session["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        return None
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    return user


async def get_current_user(request: Request):
    user = await _get_user_from_request(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


async def get_optional_user(request: Request):
    return await _get_user_from_request(request)


class SessionExchange(BaseModel):
    session_id: str


class DevLogin(BaseModel):
    email: str
    name: str = "Tester"


@auth_router.post("/session")
async def exchange_session(payload: SessionExchange, response: Response):
    """Exchange Emergent session_id for a persistent session_token (server-side)."""
    async with httpx.AsyncClient(timeout=20) as http:
        r = await http.get(EMERGENT_SESSION_URL, headers={"X-Session-ID": payload.session_id})
    if r.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid session")
    data = r.json()
    user = await _create_or_update_user(data["email"], data.get("name", ""), data.get("picture", ""))
    token = await _new_session(user["user_id"])
    _set_cookie(response, token)
    return {"user": serialize_doc(user), "session_token": token}


@auth_router.post("/dev-login")
async def dev_login(payload: DevLogin, response: Response):
    """TEST-ONLY bypass. REMIND USER TO REMOVE BEFORE PRODUCTION."""
    user = await _create_or_update_user(payload.email, payload.name, "")
    token = await _new_session(user["user_id"])
    _set_cookie(response, token)
    return {"user": serialize_doc(user), "session_token": token}


@auth_router.get("/me")
async def me(request: Request):
    user = await _get_user_from_request(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return serialize_doc(user)


@auth_router.post("/logout")
async def logout(request: Request, response: Response):
    token = request.cookies.get("session_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.lower().startswith("bearer "):
            token = auth_header[7:].strip()
    if token:
        await db.user_sessions.delete_one({"session_token": token})
    response.delete_cookie("session_token", path="/")
    return {"ok": True}
