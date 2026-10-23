"""
FastAPI Webhook & Dashboard API Receiver.
Powers the web interface and receives external triggers.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from core.agent import run_agent_pipeline
from core.git_ops import undo_last_changes
from services.transcription import check_assemblyai_availability

app = FastAPI(title="VoiceCode Autopilot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



class AgentRequest(BaseModel):
    prompt: str
    approved: bool = False


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "voicecode-autopilot-api"}


@app.get("/api/voice-status")
def voice_status():
    """Returns the current status of Sponsor 1 (AssemblyAI) vs Fallback Mode."""
    return check_assemblyai_availability()


@app.post("/api/run")
def run_agent(req: AgentRequest):
    try:
        result = run_agent_pipeline(req.prompt, approved=req.approved)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/undo")
def undo_action():
    message = undo_last_changes()
    return {"status": "success", "message": message}
from fastapi.responses import HTMLResponse
from pathlib import Path

# Define templates directory
TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

@app.get("/", response_class=HTMLResponse)
async def serve_studio_canvas():
    """Serves the elite VoiceCode Autopilot Studio UI natively."""
    index_file = TEMPLATES_DIR / "index.html"
    if index_file.exists():
        return index_file.read_text(encoding="utf-8")
    return "<h1>index.html not found in templates directory.</h1>"