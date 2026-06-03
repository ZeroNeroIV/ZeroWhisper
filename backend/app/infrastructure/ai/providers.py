"""
Concrete AI provider implementations — one class per provider.

Each provider handles its own client creation, error mapping, and response
parsing. The application layer never imports `openai` directly.
"""
from __future__ import annotations

import json
from io import BytesIO

from openai import AsyncOpenAI

from app.core.config import settings
from app.core.exceptions import AIServiceError
from app.core.ports.ai_provider import AIProvider, TranscriptionProvider


class OpenAIProvider(AIProvider):
    """Transaction extraction + persona generation via OpenAI-compatible API."""

    _PERSONA_SYSTEM = (
        "You are Whisper, a highly competent but slightly sarcastic financial assistant. "
        "Keep responses to 1-2 sentences. Be helpful first, then gently roast if spending is high. "
        "Never be mean or offensive. Focus on the user's actual numbers."
    )

    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self._model = model

    def _extraction_schema(self, categories: list[str]) -> dict:
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "transaction_extraction",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "amount_original": {"type": "number"},
                        "currency_original": {"type": "string", "enum": ["JOD", "USD"]},
                        "description": {"type": "string"},
                        "category": {"type": "string", "enum": categories},
                        "confidence": {"type": "number"},
                        "transaction_date": {"type": "string"},
                    },
                    "required": ["amount_original", "currency_original", "description", "category", "confidence"],
                    "additionalProperties": False,
                },
            },
        }

    def _extraction_system(self, categories: list[str]) -> str:
        from datetime import date as _date
        cats_str = ", ".join(categories)
        today = _date.today().isoformat()
        return (
            "Extract financial transaction details from natural language. Be precise. "
            "If currency is not specified, assume JOD. "
            f"Categories must be one of: {cats_str}. "
            "If category is unclear, use Other. "
            "Confidence is 0.0 to 1.0 based on how clear the input was. "
            f"If a date or time reference is mentioned (e.g. 'yesterday', 'last Friday', 'on May 20th'), "
            f"extract it as YYYY-MM-DD in the transaction_date field. Today is {today}."
        )

    async def extract_transaction(self, text: str, categories: list[str]) -> dict:
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": self._extraction_system(categories)},
                    {"role": "user", "content": text},
                ],
                response_format=self._extraction_schema(categories),
            )
        except Exception as e:
            raise AIServiceError("AI extraction failed", wrapped=e) from e

        content = response.choices[0].message.content
        if not content:
            raise AIServiceError("AI returned empty response")
        return json.loads(content)

    async def generate_persona(self, category: str, this_month_total: float, transaction_count: int) -> str:
        user_msg = (
            f"Category: {category}. "
            f"This month total: {this_month_total}. "
            f"Transaction count: {transaction_count}."
        )
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": self._PERSONA_SYSTEM},
                    {"role": "user", "content": user_msg},
                ],
            )
            return response.choices[0].message.content
        except Exception:
            return "Got it. Transaction noted."


class OpenAITranscriptionProvider(TranscriptionProvider):

    def __init__(self, api_key: str, base_url: str, model: str = "whisper-1") -> None:
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self._model = model

    async def transcribe(self, data: bytes, filename: str) -> str:
        mime = "audio/webm" if filename.endswith(".webm") else "audio/ogg"
        try:
            response = await self._client.audio.transcriptions.create(
                model=self._model,
                file=(filename, BytesIO(data), mime),
            )
            return response.text
        except Exception as e:
            raise AIServiceError("Transcription failed", wrapped=e) from e

    def is_available(self) -> bool:
        return True


class GroqTranscriptionProvider(TranscriptionProvider):

    def __init__(self, api_key: str) -> None:
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
        )
        self._model = "whisper-large-v3"

    async def transcribe(self, data: bytes, filename: str) -> str:
        mime = "audio/webm" if filename.endswith(".webm") else "audio/ogg"
        try:
            response = await self._client.audio.transcriptions.create(
                model=self._model,
                file=(filename, BytesIO(data), mime),
            )
            return response.text
        except Exception as e:
            raise AIServiceError("Groq transcription failed", wrapped=e) from e

    def is_available(self) -> bool:
        return True


class LocalWhisperTranscriptionProvider(TranscriptionProvider):
    """Local transcription via faster-whisper (CPU, int8). Model loaded lazily."""

    def __init__(self, model_size: str, cache_dir: str) -> None:
        self._model_size = model_size
        self._cache_dir = cache_dir
        self._model = None

    async def transcribe(self, data: bytes, filename: str) -> str:
        import asyncio
        import tempfile
        import logging

        from faster_whisper import WhisperModel

        logger = logging.getLogger(__name__)

        if self._model is None:
            self._model = await asyncio.to_thread(
                WhisperModel,
                self._model_size,
                device="cpu",
                compute_type="int8",
                download_root=self._cache_dir,
            )

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(data)
            tmp_path = f.name

        try:
            segments, _ = await asyncio.to_thread(self._model.transcribe, tmp_path)
            text = " ".join(seg.text for seg in segments)
            return text.strip() or ""
        except Exception as e:
            raise AIServiceError("Local transcription failed", wrapped=e) from e
        finally:
            import os
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    def is_available(self) -> bool:
        return True
