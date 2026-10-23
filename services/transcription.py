"""
AssemblyAI Live Transcription Service (Sponsor 1).
Uses the current v3 Python SDK for streaming audio with a typed fallback.
"""
import os
from dotenv import load_dotenv

load_dotenv()


def check_assemblyai_availability() -> dict:
    """Verifies whether AssemblyAI API key is properly configured."""
    api_key = os.getenv("ASSEMBLYAI_API_KEY", "").strip()
    if not api_key or api_key == "replace_with_assemblyai_key" or len(api_key) < 10:
        return {
            "enabled": False,
            "mode": "fallback_typed_input",
            "message": "AssemblyAI API key not configured. Using Fallback Mode (Typed Input)."
        }
    
    try:
        from assemblyai.streaming.v3 import RealTimeTranscriber
        return {
            "enabled": True,
            "mode": "assemblyai_streaming_v3",
            "message": "AssemblyAI v3 Streaming Client ready."
        }
    except Exception as e:
        return {
            "enabled": False,
            "mode": "fallback_typed_input",
            "message": f"AssemblyAI SDK status: {str(e)}. Using Fallback Mode."
        }