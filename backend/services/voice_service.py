# backend/services/voice_service.py

import openai
import tempfile
import os
from core.config import settings

class VoiceService:
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

    def transcribe_audio(self, audio_bytes: bytes, filename: str = "audio.webm") -> str:
        with tempfile.NamedTemporaryFile(suffix=f".{filename.split('.')[-1]}", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        try:
            with open(tmp_path, "rb") as f:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
                    language="en"
                )
            return transcript.text
        finally:
            os.unlink(tmp_path)

    def text_to_speech(self, text: str, voice: str = "alloy") -> bytes:
        response = self.client.audio.speech.create(
            model="tts-1",
            voice=voice,          # alloy, echo, fable, onyx, nova, shimmer
            input=text[:4096]
        )
        return response.content

    def parse_voice_command(self, transcript: str) -> dict:
        import json
        from langchain_openai import ChatOpenAI
        from langchain.schema import SystemMessage, HumanMessage

        llm = ChatOpenAI(model=settings.OPENAI_MODEL, openai_api_key=settings.OPENAI_API_KEY)
        prompt = f"""
        Parse this voice command from an advertiser and extract structured intent.
        Voice command: "{transcript}"

        Return JSON only:
        {{
            "intent": "create_campaign | pause_campaign | get_stats | optimize | chat | unknown",
            "platform": "google | meta | both | null",
            "budget": number or null,
            "goal": "conversions | traffic | awareness | leads | null",
            "campaign_name": "string or null",
            "message": "cleaned natural language version of the command"
        }}
        """
        response = llm([
            SystemMessage(content="You extract structured intents from ad manager voice commands. Return only valid JSON."),
            HumanMessage(content=prompt)
        ])
        try:
            return json.loads(response.content)
        except:
            return {"intent": "chat", "message": transcript}