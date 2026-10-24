"""
FastAPI Webhook & Dashboard API Receiver.
Powers the web interface and receives external triggers.

Accounts: every agent run, upload and chat belongs to a signed-in user
(or a 24-hour guest). See core/accounts.py and workflows/account_routes.py.
"""
from workflows.transcribe_route import router as transcribe_router
import os
import re
import threading
from pathlib import Path
from typing import Optional
from evals.safety_guardrail import audit_prompt
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel

from core import accounts
from core.agent import run_agent_pipeline
from core.artifacts import build_artifacts
from core.git_ops import undo_last_changes
from services.transcription import check_assemblyai_availability
from workflows.account_routes import COOKIE_NAME, check_origin, current_user
from workflows.account_routes import router as account_router
from workflows.transcribe_route import router as transcribe_router

accounts.init_db()

app = FastAPI(title="VoiceCode Autopilot API", version="2.0.0", redirect_slashes=False)

# The studio is served from this same server, so cross-origin access is not needed.
# Keep this list explicit: never combine "*" with credentials.
ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv("VCA_ALLOWED_ORIGINS", "http://127.0.0.1:8000,http://localhost:8000").split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(transcribe_router)
app.include_router(account_router)
# Voice uploads cost AssemblyAI credit, so they require a signed-in user.
app.include_router(transcribe_router, dependencies=[Depends(current_user), Depends(check_origin)])


class AgentRequest(BaseModel):
    prompt: str
    approved: bool = False
    conversation_id: Optional[str] = None


# ------------------------------ 7-step pipeline ------------------------------
# Step 1 (prompt screening) and step 7 (artifact packaging) are added here;
# steps 2-6 are the original agent steps from core.agent.
SCREENING_STEP = "Safety Audit: Prompt Screening"
PIPELINE_STEPS = [
    "Parsing User Specification & Context",
    "Generating Architecture & Search-Replace Patches",
    "Executing Pytest Test Suite Verification",
    "Creating Isolated Feature Branch & Staging Files",
    "Committing Changes & Preparing PR Payload",
]
PACKAGING_STEP = "Packaging Download Artifacts (.patch / .py)"

# All users share one demo_repo on disk, so agent runs are serialized.
RUN_LOCK = threading.Lock()
# Remember who made the last approved change so nobody can undo someone else's work.
_last_change = {"user_id": None}


def _execute(prompt: str, approved: bool, user_id: str) -> dict:
    # Step 1 of 7: screen the prompt before the agent runs
    verdict = audit_prompt(prompt)
    screening = {"step": SCREENING_STEP, "status": "completed" if verdict["allowed"] else "failed"}
    if not verdict["allowed"]:
        skipped = [{"step": n, "status": "skipped"} for n in PIPELINE_STEPS + [PACKAGING_STEP]]
        return {"status": "blocked", "message": verdict["explanation"],
                "timeline": [screening] + skipped, "prompt_audit": verdict}

    # Steps 2-6 of 7: the existing agent pipeline (one run at a time)
    if not RUN_LOCK.acquire(timeout=120):
        raise HTTPException(status_code=503, detail="The agent is busy with another run. Please try again shortly.")
    try:
        result = run_agent_pipeline(prompt, approved=approved)
        if approved:
            _last_change["user_id"] = user_id
    finally:
        RUN_LOCK.release()

    if isinstance(result, dict):
        # Step 7 of 7: package the downloadable artifacts
        try:
            result["artifacts"] = build_artifacts((result.get("plan") or {}).get("patches", []))
            art = result["artifacts"]
            packaging = "completed" if (art["patch"] or art["files"]) else "skipped"
        except Exception as e:
            result["artifacts"] = {"patch": "", "files": [], "notes": [f"artifact build failed: {e}"]}
            packaging = "failed"
        result["prompt_audit"] = verdict
        if isinstance(result.get("timeline"), list):
            result["timeline"] = [screening] + result["timeline"] + [{"step": PACKAGING_STEP, "status": packaging}]
    return result


def _summarize(result: dict, approved: bool):
    status = str(result.get("status", "unknown")) if isinstance(result, dict) else "unknown"
    failed = bool(re.search(r"fail|error|block|reject", status, re.I))
    if failed:
        extra = f" {result.get('message')}" if isinstance(result, dict) and result.get("message") else \
            " Open the timeline to see the failed step."
        return f"Pipeline stopped (status: {status}).{extra}", "fail"
    if not approved:
        return f"Plan preview ready (status: {status}). Review the timeline and diff, then click Approve & PR.", "ok"
    return f"Pipeline finished (status: {status}). Review the diff and audit log before merging.", "ok"


def _save(user_id, conversation_id, role, content, tone=None, run=None):
    try:
        accounts.add_message(user_id, conversation_id, role, content, tone=tone, run=run)
    except accounts.AccountError:
        pass  # a full chat must never break a finished run


# ------------------------------ API routes ------------------------------
@app.get("/health")
def health_check():
    return {"status": "ok", "service": "voicecode-autopilot-api"}

@app.post("/api/run", dependencies=[Depends(check_origin)])
@app.post("/api/run/", dependencies=[Depends(check_origin)])
def run_agent(req: AgentRequest, user: dict = Depends(current_user)):
    prompt = req.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is empty.")
    if len(prompt) > 4000:
        raise HTTPException(status_code=413, detail="Prompt is too long (max 4000 characters).")

    conversation_id = req.conversation_id
    if conversation_id:
        if accounts.get_conversation(user["id"], conversation_id) is None:
            raise HTTPException(status_code=404, detail="Chat not found.")
    else:
        try:
            conversation_id = accounts.create_conversation(user["id"])["id"]
        except accounts.AccountError as e:
            raise HTTPException(status_code=e.status, detail=e.message)

    try:
        accounts.add_message(user["id"], conversation_id, "user", prompt)
    except accounts.AccountError as e:
        raise HTTPException(status_code=e.status, detail=e.message)

    try:
        result = _execute(prompt, req.approved, user["id"])
    except HTTPException:
        raise
    except Exception as e:
        _save(user["id"], conversation_id, "agent", f"Request failed: {e}", tone="fail")
        raise HTTPException(status_code=500, detail=str(e))

    text, tone = _summarize(result, req.approved)
    _save(user["id"], conversation_id, "agent", text, tone=tone, run=result)
    if isinstance(result, dict):
        result["conversation_id"] = conversation_id
        result["agent_message"] = {"text": text, "tone": tone}
    return result


@app.post("/api/undo", dependencies=[Depends(check_origin)])
@app.post("/api/undo/", dependencies=[Depends(check_origin)])
def undo_action(user: dict = Depends(current_user)):
    owner = _last_change["user_id"]
    if owner not in (None, user["id"]):
        raise HTTPException(status_code=403, detail="The last change was made by another user, so you can't roll it back.")
    with RUN_LOCK:
        message = undo_last_changes()
    _last_change["user_id"] = None
    return {"status": "success", "message": message}


# ------------------------------ pages ------------------------------
# Define templates directory
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"


def _signed_in(request: Request) -> bool:
    token = request.cookies.get(COOKIE_NAME, "")
    return bool(token and accounts.get_user_by_token(token))


def _page(name: str) -> HTMLResponse:
    f = TEMPLATES_DIR / name
    if f.exists():
        return HTMLResponse(f.read_text(encoding="utf-8"), headers={"Cache-Control": "no-store"})
    return HTMLResponse(f"<h1>{name} not found in templates directory.</h1>", status_code=500)


@app.get("/", response_class=HTMLResponse)
def serve_studio_canvas(request: Request):
    """Serves the studio UI to signed-in users; everyone else goes to /login."""
    if not _signed_in(request):
        return RedirectResponse("/login", status_code=303)
    return _page("index.html")


@app.get("/login", response_class=HTMLResponse)
def serve_login(request: Request):
    if _signed_in(request):
        return RedirectResponse("/", status_code=303)
    return _page("login.html")