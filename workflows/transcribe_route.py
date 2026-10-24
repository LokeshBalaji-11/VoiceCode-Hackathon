import os
import tempfile

from fastapi import APIRouter, File, HTTPException, UploadFile

from services.transcription import transcribe_audio_file
from services.transcription import check_assemblyai_availability, transcribe_audio_file

router = APIRouter()

@router.get("/api/status/assemblyai")
def assemblyai_status():
    return check_assemblyai_availability()
router = APIRouter()
@router.post("/api/transcribe")
def transcribe(audio: UploadFile = File(...)):
    suffix = os.path.splitext(audio.filename or "")[1] or ".webm"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(audio.file.read())
        path = tmp.name
    try:
        return transcribe_audio_file(path)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    finally:
        try:
            os.remove(path)
        except OSError:
            pass