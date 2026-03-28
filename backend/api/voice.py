# backend/api/voice.py

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import Response
from services.voice_service import VoiceService
from core.orchestrator import Orchestrator
import asyncio

router = APIRouter()
voice_svc = VoiceService()
orchestrator = Orchestrator()

@router.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    audio_bytes = await file.read()
    if len(audio_bytes) > 25 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 25MB)")
    try:
        transcript = voice_svc.transcribe_audio(audio_bytes, file.filename)
        parsed = voice_svc.parse_voice_command(transcript)
        return {"transcript": transcript, "parsed": parsed}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/command")
async def voice_command(file: UploadFile = File(...), workspace_id: str = "", session_id: str = ""):
    audio_bytes = await file.read()
    transcript = voice_svc.transcribe_audio(audio_bytes, file.filename)
    parsed = voice_svc.parse_voice_command(transcript)

    result = {"transcript": transcript, "parsed": parsed}

    if parsed["intent"] == "create_campaign":
        agent_result = await orchestrator.run({
            "message": parsed["message"],
            "workspace_id": workspace_id,
            "session_id": session_id,
            "budget": parsed.get("budget"),
            "platform": parsed.get("platform", "google"),
            "goal": parsed.get("goal", "conversions"),
        })
        result["agent_result"] = {
            "ad_copy": agent_result.get("ad_copy"),
            "approved": agent_result.get("approved"),
        }
        reply_text = f"Campaign created successfully. Here is your ad copy: {agent_result.get('ad_copy', '')[:200]}"
    elif parsed["intent"] == "get_stats":
        reply_text = "Fetching your campaign statistics now."
    else:
        reply_text = f"Got it. Processing your request: {transcript}"

    result["audio_reply"] = None
    try:
        audio_bytes_reply = voice_svc.text_to_speech(reply_text)
        result["has_audio"] = True
    except:
        result["has_audio"] = False

    return result

@router.post("/speak")
async def text_to_speech(text: str, voice: str = "alloy"):
    try:
        audio = voice_svc.text_to_speech(text, voice)
        return Response(content=audio, media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Add to main.py:
# from api.voice import router as voice_router
# app.include_router(voice_router, prefix="/voice", tags=["Voice"])