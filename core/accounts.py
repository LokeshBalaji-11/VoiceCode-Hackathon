"""
Accounts, sessions and saved chats for VoiceCode Autopilot.

Standard library only (sqlite3 + hashlib.scrypt). What it gives you:
  - sign up / sign in with scrypt-hashed passwords (never stored in plain text)
  - random session tokens: only a SHA-256 hash of the token is stored in the DB
  - one-click guest accounts that delete themselves after 24 hours
  - per-user conversations and messages (every query is filtered by user_id,
    so one user can never read or change another user's data)

The database file is created at data/autopilot.db (override with VCA_DB_PATH).
Add `data/` to .gitignore: it contains password hashes.
"""
import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(os.getenv("VCA_DB_PATH", "data/autopilot.db"))
SESSION_TTL = 60 * 60 * 24 * 14      # 14 days
GUEST_TTL = 60 * 60 * 24             # 24 hours
MAX_CONVERSATIONS = 200
MAX_MESSAGES = 1000
PASSWORD_MIN = 8
PASSWORD_MAX = 200

_SCRYPT = {"n": 2 ** 14, "r": 8, "p": 1, "dklen": 32}
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id         TEXT PRIMARY KEY,
    email      TEXT UNIQUE,
    name       TEXT,
    pw_salt    BLOB,
    pw_hash    BLOB,
    is_guest   INTEGER NOT NULL DEFAULT 0,
    created_at REAL NOT NULL,
    expires_at REAL
);
CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT PRIMARY KEY,
    user_id    TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at REAL NOT NULL,
    expires_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS conversations (
    id         TEXT PRIMARY KEY,
    user_id    TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title      TEXT NOT NULL,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS messages (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role            TEXT NOT NULL,
    tone            TEXT,
    content         TEXT NOT NULL,
    run_json        TEXT,
    created_at      REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_conv_user ON conversations(user_id, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_msg_conv ON messages(conversation_id, id);
CREATE INDEX IF NOT EXISTS idx_sess_user ON sessions(user_id);
"""


class AccountError(Exception):
    """A user-facing error with an HTTP status code."""

    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.message = message
        self.status = status


# ------------------------------ database ------------------------------
@contextmanager
def db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with db() as conn:
        conn.executescript(SCHEMA)
    cleanup_expired()


def cleanup_expired() -> None:
    """Remove expired sessions and expired guest accounts (and all their data)."""
    now = time.time()
    with db() as conn:
        conn.execute("DELETE FROM sessions WHERE expires_at < ?", (now,))
        conn.execute("DELETE FROM users WHERE is_guest = 1 AND expires_at IS NOT NULL AND expires_at < ?", (now,))


# ------------------------------ passwords -----------------------------
def _hash_password(password: str, salt: bytes) -> bytes:
    return hashlib.scrypt(password.encode("utf-8"), salt=salt, **_SCRYPT)


_DUMMY_SALT = os.urandom(16)
_DUMMY_HASH = _hash_password("not-a-real-password", _DUMMY_SALT)


def _normalize_email(email: str) -> str:
    email = (email or "").strip().lower()
    if len(email) > 254 or not _EMAIL_RE.match(email):
        raise AccountError("Please enter a valid email address.", 422)
    return email


def _check_password_rules(password: str) -> None:
    if len(password or "") < PASSWORD_MIN:
        raise AccountError(f"Password must be at least {PASSWORD_MIN} characters.", 422)
    if len(password) > PASSWORD_MAX:
        raise AccountError("Password is too long.", 422)


def _public_user(row) -> dict:
    return {
        "id": row["id"],
        "email": row["email"],
        "name": row["name"] or (row["email"] or "Guest").split("@")[0],
        "is_guest": bool(row["is_guest"]),
        "expires_at": row["expires_at"],
    }


# ------------------------------ users ---------------------------------
def create_user(email: str, password: str, name: str = "") -> dict:
    email = _normalize_email(email)
    _check_password_rules(password)
    name = (name or "").strip()[:80]
    salt = os.urandom(16)
    pw_hash = _hash_password(password, salt)
    user_id = uuid.uuid4().hex
    try:
        with db() as conn:
            conn.execute(
                "INSERT INTO users (id, email, name, pw_salt, pw_hash, is_guest, created_at) "
                "VALUES (?, ?, ?, ?, ?, 0, ?)",
                (user_id, email, name, salt, pw_hash, time.time()),
            )
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    except sqlite3.IntegrityError:
        raise AccountError("An account with that email already exists.", 409)
    return _public_user(row)


def create_guest() -> dict:
    cleanup_expired()
    user_id = uuid.uuid4().hex
    now = time.time()
    with db() as conn:
        conn.execute(
            "INSERT INTO users (id, email, name, is_guest, created_at, expires_at) VALUES (?, NULL, 'Guest', 1, ?, ?)",
            (user_id, now, now + GUEST_TTL),
        )
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return _public_user(row)


def authenticate(email: str, password: str) -> dict:
    """Return the user, or raise a generic error (never reveals which part was wrong)."""
    generic = AccountError("Invalid email or password.", 401)
    try:
        email = _normalize_email(email)
    except AccountError:
        _hash_password(password or "", _DUMMY_SALT)  # keep timing similar
        raise generic
    with db() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ? AND is_guest = 0", (email,)).fetchone()
    if row is None:
        _hash_password(password or "", _DUMMY_SALT)  # keep timing similar
        raise generic
    candidate = _hash_password(password or "", row["pw_salt"])
    if not hmac.compare_digest(candidate, row["pw_hash"]):
        raise generic
    return _public_user(row)


def delete_user(user_id: str) -> None:
    """Delete the account and, by cascade, its sessions, chats and messages."""
    with db() as conn:
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))


# ------------------------------ sessions ------------------------------
def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_session(user_id: str, ttl: int = SESSION_TTL) -> str:
    token = secrets.token_urlsafe(32)
    now = time.time()
    with db() as conn:
        conn.execute(
            "INSERT INTO sessions (token_hash, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (_token_hash(token), user_id, now, now + ttl),
        )
    return token


def get_user_by_token(token: str):
    if not token:
        return None
    now = time.time()
    with db() as conn:
        row = conn.execute(
            "SELECT u.* FROM sessions s JOIN users u ON u.id = s.user_id "
            "WHERE s.token_hash = ? AND s.expires_at > ? "
            "AND (u.is_guest = 0 OR u.expires_at > ?)",
            (_token_hash(token), now, now),
        ).fetchone()
    return _public_user(row) if row else None


def delete_session(token: str) -> None:
    if token:
        with db() as conn:
            conn.execute("DELETE FROM sessions WHERE token_hash = ?", (_token_hash(token),))


# ---------------------------- conversations ---------------------------
def _conv_dict(row) -> dict:
    return {"id": row["id"], "title": row["title"],
            "created_at": row["created_at"], "updated_at": row["updated_at"]}


def create_conversation(user_id: str, title: str = "New chat") -> dict:
    with db() as conn:
        count = conn.execute("SELECT COUNT(*) FROM conversations WHERE user_id = ?", (user_id,)).fetchone()[0]
        if count >= MAX_CONVERSATIONS:
            raise AccountError("Chat limit reached. Delete an old chat first.", 429)
        cid, now = uuid.uuid4().hex, time.time()
        conn.execute(
            "INSERT INTO conversations (id, user_id, title, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (cid, user_id, (title or "New chat").strip()[:80] or "New chat", now, now),
        )
        row = conn.execute("SELECT * FROM conversations WHERE id = ?", (cid,)).fetchone()
    return _conv_dict(row)


def list_conversations(user_id: str) -> list:
    with db() as conn:
        rows = conn.execute(
            "SELECT * FROM conversations WHERE user_id = ? ORDER BY updated_at DESC LIMIT 200", (user_id,)
        ).fetchall()
    return [_conv_dict(r) for r in rows]


def get_conversation(user_id: str, conversation_id: str):
    """Return the conversation with its messages, or None if it is not this user's."""
    with db() as conn:
        conv = conn.execute(
            "SELECT * FROM conversations WHERE id = ? AND user_id = ?", (conversation_id, user_id)
        ).fetchone()
        if conv is None:
            return None
        rows = conn.execute(
            "SELECT role, tone, content, run_json, created_at FROM messages "
            "WHERE conversation_id = ? ORDER BY id", (conversation_id,)
        ).fetchall()
    messages = []
    for r in rows:
        run = None
        if r["run_json"]:
            try:
                run = json.loads(r["run_json"])
            except ValueError:
                run = None
        messages.append({"role": r["role"], "tone": r["tone"], "content": r["content"],
                         "run": run, "created_at": r["created_at"]})
    out = _conv_dict(conv)
    out["messages"] = messages
    return out


def rename_conversation(user_id: str, conversation_id: str, title: str) -> bool:
    title = (title or "").strip()[:80]
    if not title:
        raise AccountError("Title cannot be empty.", 422)
    with db() as conn:
        cur = conn.execute(
            "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ? AND user_id = ?",
            (title, time.time(), conversation_id, user_id),
        )
        return cur.rowcount > 0


def delete_conversation(user_id: str, conversation_id: str) -> bool:
    with db() as conn:
        cur = conn.execute(
            "DELETE FROM conversations WHERE id = ? AND user_id = ?", (conversation_id, user_id)
        )
        return cur.rowcount > 0


def add_message(user_id: str, conversation_id: str, role: str, content: str,
                tone: str = None, run: dict = None) -> None:
    if role not in ("user", "agent"):
        raise AccountError("Invalid message role.", 400)
    run_json = json.dumps(run, default=str) if run is not None else None
    now = time.time()
    with db() as conn:
        conv = conn.execute(
            "SELECT title FROM conversations WHERE id = ? AND user_id = ?", (conversation_id, user_id)
        ).fetchone()
        if conv is None:
            raise AccountError("Conversation not found.", 404)
        count = conn.execute(
            "SELECT COUNT(*) FROM messages WHERE conversation_id = ?", (conversation_id,)
        ).fetchone()[0]
        if count >= MAX_MESSAGES:
            raise AccountError("This chat is full. Start a new chat.", 429)
        conn.execute(
            "INSERT INTO messages (conversation_id, role, tone, content, run_json, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (conversation_id, role, tone, content, run_json, now),
        )
        new_title = conv["title"]
        if role == "user" and new_title == "New chat":
            new_title = " ".join(content.split())[:48] or "New chat"
        conn.execute(
            "UPDATE conversations SET updated_at = ?, title = ? WHERE id = ?",
            (now, new_title, conversation_id),
        )