"""
AssemblyAI transcription service (Sponsor 1).

Transcribes a recorded audio clip with AssemblyAI. If the key is missing or
the call fails, the caller (the API route / frontend) falls back to browser
speech recognition or typed input.

Quick self-test from the project root:
    python -m services.transcription path/to/sample.wav
After it prints text, check your AssemblyAI dashboard: Speech-to-Text usage
should be above 0 hours.
"""
import os
import sys

from dotenv import load_dotenv
load_dotenv(override=True)
def _get_key() -> str:
    """Return the configured key, or an empty string if missing/placeholder."""
    key = os.getenv("ASSEMBLYAI_API_KEY", "").strip()
    if not key or key == "replace_with_assemblyai_key" or len(key) < 10:
        return ""
    return key


def check_assemblyai_availability() -> dict:
    """Status check used by the dashboard / webhook handler."""
    if not _get_key():
        return {
            "enabled": False,
            "mode": "fallback",
            "message": "AssemblyAI key not configured. Using browser speech / typed input.",
        }
    try:
        import assemblyai  # noqa: F401
        return {
            "enabled": True,
            "mode": "assemblyai_recorded_clip",
            "message": "AssemblyAI transcription ready.",
        }
    except ImportError as e:
        return {
            "enabled": False,
            "mode": "fallback",
            "message": f"AssemblyAI SDK not installed ({e}). Run: pip install assemblyai",
        }


def transcribe_audio_file(path: str) -> dict:
    """Send an audio file to AssemblyAI and return {"text": ..., "engine": ...}.

    Raises RuntimeError on any failure so the API route can return an error
    and the frontend can switch to fallback mode.
    """
    key = _get_key()
    if not key:
        raise RuntimeError("AssemblyAI key not configured")

    import assemblyai as aai

    aai.settings.api_key = key
    aai.settings.polling_interval = 0.5  # Check every 0.5s instead of waiting 3.0s
    config = aai.TranscriptionConfig(
        language_code="en",
        punctuate=True,
        format_text=True,
    )
    transcript = aai.Transcriber(config=config).transcribe(path)

    if transcript.status == aai.TranscriptStatus.error:
        raise RuntimeError(transcript.error or "AssemblyAI transcription failed")

    return {"text": transcript.text or "", "engine": "assemblyai"}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python -m services.transcription <audio_file>")
    print(transcribe_audio_file(sys.argv[1]))