"""
Account routes: sign up, sign in, guest access, sign out, delete account,
and saved chats. Sessions live in an HttpOnly cookie.

Exports for other modules:
    router         - include it in the app
    current_user   - dependency that returns the signed-in user or raises 401
    check_origin   - dependency that blocks cross-site state-changing requests
"""
import os
import time
from collections import defaultdict, deque
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field

from core import accounts

COOKIE_NAME = "vca_session"
# Set VCA_SECURE_COOKIES=1 when you deploy behind HTTPS.
SECURE_COOKIES = os.getenv("VCA_SECURE_COOKIES", "0") == "1"


# ------------------------------ guards -------------------------------
def check_origin(request: Request) -> None:
    """Defense in depth on top of SameSite=Lax: reject cross-site writes."""
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return
    origin = request.headers.get("origin")
    if origin and urlparse(origin).netloc != request.headers.get("host", ""):
        raise HTTPException(status_code=403, detail="Cross-origin request blocked.")


def current_user(request: Request) -> dict:
    token = request.cookies.get(COOKIE_NAME, "")
    user = accounts.get_user_by_token(token) if token else None
    if not user:
        raise HTTPException(status_code=401, detail="Not signed in.")
    return user


_attempts = defaultdict(deque)


def _throttle(key: str, limit: int, window: int) -> None:
    """Simple in-memory rate limit (resets when the server restarts)."""
    now = time.time()
    if len(_attempts) > 5000:  # keep memory bounded
        for k in [k for k, q in _attempts.items() if not q or now - q[-1] > window]:
            _attempts.pop(k, None)
    q = _attempts[key]
    while q and now - q[0] > window:
        q.popleft()
    if len(q) >= limit:
        raise HTTPException(status_code=429, detail="Too many attempts. Please try again in a few minutes.")
    q.append(now)


def _ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _fail(error: accounts.AccountError):
    raise HTTPException(status_code=error.status, detail=error.message)


def _start_session(response: Response, user: dict, guest: bool = False) -> None:
    ttl = accounts.GUEST_TTL if guest else accounts.SESSION_TTL
    token = accounts.create_session(user["id"], ttl=ttl)
    response.set_cookie(
        COOKIE_NAME, token, max_age=ttl, httponly=True,
        samesite="lax", secure=SECURE_COOKIES, path="/",
    )


# ------------------------------ models -------------------------------
class SignupBody(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(max_length=200)
    name: str = Field(default="", max_length=80)


class LoginBody(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(max_length=200)


class TitleBody(BaseModel):
    title: str = Field(max_length=80)


class NewConversationBody(BaseModel):
    title: str = Field(default="New chat", max_length=80)


router = APIRouter(dependencies=[Depends(check_origin)])


# ------------------------------ auth ---------------------------------
@router.post("/api/auth/signup")
def signup(body: SignupBody, request: Request, response: Response):
    _throttle(f"signup|{_ip(request)}", 10, 3600)
    try:
        user = accounts.create_user(body.email, body.password, body.name)
    except accounts.AccountError as e:
        _fail(e)
    _start_session(response, user)
    return {"user": user}


@router.post("/api/auth/login")
def login(body: LoginBody, request: Request, response: Response):
    key = f"login|{_ip(request)}|{body.email.strip().lower()}"
    _throttle(key, 8, 600)
    try:
        user = accounts.authenticate(body.email, body.password)
    except accounts.AccountError as e:
        _fail(e)
    _attempts.pop(key, None)
    _start_session(response, user)
    return {"user": user}


@router.post("/api/auth/guest")
def guest(request: Request, response: Response):
    _throttle(f"guest|{_ip(request)}", 20, 3600)
    user = accounts.create_guest()
    _start_session(response, user, guest=True)
    return {"user": user}


@router.post("/api/auth/logout")
def logout(request: Request, response: Response):
    accounts.delete_session(request.cookies.get(COOKIE_NAME, ""))
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"status": "ok"}


@router.get("/api/auth/me")
def me(user: dict = Depends(current_user)):
    return {"user": user}


@router.delete("/api/auth/account")
def delete_account(response: Response, user: dict = Depends(current_user)):
    accounts.delete_user(user["id"])
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"status": "deleted"}


# ------------------------------ chats --------------------------------
@router.get("/api/conversations")
def list_chats(user: dict = Depends(current_user)):
    return {"conversations": accounts.list_conversations(user["id"])}


@router.post("/api/conversations")
def new_chat(body: NewConversationBody, user: dict = Depends(current_user)):
    try:
        return accounts.create_conversation(user["id"], body.title)
    except accounts.AccountError as e:
        _fail(e)


@router.get("/api/conversations/{conversation_id}")
def open_chat(conversation_id: str, user: dict = Depends(current_user)):
    conv = accounts.get_conversation(user["id"], conversation_id)
    if conv is None:
        raise HTTPException(status_code=404, detail="Chat not found.")
    return conv


@router.patch("/api/conversations/{conversation_id}")
def rename_chat(conversation_id: str, body: TitleBody, user: dict = Depends(current_user)):
    try:
        ok = accounts.rename_conversation(user["id"], conversation_id, body.title)
    except accounts.AccountError as e:
        _fail(e)
    if not ok:
        raise HTTPException(status_code=404, detail="Chat not found.")
    return {"status": "ok"}


@router.delete("/api/conversations/{conversation_id}")
def delete_chat(conversation_id: str, user: dict = Depends(current_user)):
    if not accounts.delete_conversation(user["id"], conversation_id):
        raise HTTPException(status_code=404, detail="Chat not found.")
    return {"status": "deleted"}