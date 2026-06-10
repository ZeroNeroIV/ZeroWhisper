"""
Concrete AI provider implementations — one class per provider.

Each provider handles its own client creation, error mapping, and response
parsing. The application layer never imports `openai` directly.
"""
from __future__ import annotations

import json
from io import BytesIO

from openai import AsyncOpenAI

from app.core.exceptions import AIServiceError
from app.core.ports.ai_provider import AGENT_INTENTS, AIProvider, TranscriptionProvider


def _nullable(schema: dict) -> dict:
    return {"anyOf": [schema, {"type": "null"}]}


class OpenAIProvider(AIProvider):
    """Action extraction + persona generation via OpenAI-compatible API."""

    _PERSONA_SYSTEM = (
        "You are Whisper, a highly competent but slightly sarcastic financial assistant. "
        "Keep responses to 1-2 sentences. Be helpful first, then gently roast if spending is high. "
        "Never be mean or offensive. Focus on the user's actual numbers."
    )

    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self._model = model

    def _action_schema(self, category_names: list[str]) -> dict:
        category_schema = (
            {"type": "string", "enum": category_names}
            if category_names else {"type": "string"}
        )
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "financial_action",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "intent": {"type": "string", "enum": list(AGENT_INTENTS)},
                        "amount": _nullable({"type": "number"}),
                        "currency": _nullable({"type": "string", "enum": ["JOD", "USD"]}),
                        "description": _nullable({"type": "string"}),
                        "category": _nullable(category_schema),
                        "wallet": _nullable({"type": "string"}),
                        "from_wallet": _nullable({"type": "string"}),
                        "to_wallet": _nullable({"type": "string"}),
                        "transaction_date": _nullable({"type": "string"}),
                        "confidence": {"type": "number"},
                        "reply": _nullable({"type": "string"}),
                    },
                    "required": [
                        "intent", "amount", "currency", "description", "category",
                        "wallet", "from_wallet", "to_wallet", "transaction_date",
                        "confidence", "reply",
                    ],
                    "additionalProperties": False,
                },
            },
        }

    def _action_system(self, categories: list[dict], wallets: list[dict]) -> str:
        from datetime import date as _date
        today = _date.today().isoformat()
        cats_str = ", ".join(f"{c['name']} ({c['type']})" for c in categories) or "none"
        wallets_str = ", ".join(
            f"{w['name']} ({w['type']}, {w['currency']})" for w in wallets
        ) or "none"
        return (
            "You are Whisper, the agent of a personal finance manager. Classify the user's "
            "message into one intent and extract its fields. Be precise.\n"
            "Intents:\n"
            "- record_expense: user spent money (set amount, category, description; wallet if mentioned)\n"
            "- record_income: user received money — salary, freelance payment, gift "
            "(set amount, category, description; wallet if mentioned)\n"
            "- transfer: user moved money between two of their own wallets, e.g. from savings to cash "
            "(set amount, from_wallet, to_wallet)\n"
            "- query_balance: user asks how much money they have or what a wallet's balance is "
            "(set wallet if a specific one is named)\n"
            "- query_spending: user asks what they spent, this month's expenses, or spending per category\n"
            "- unknown: anything else — set reply to a one-sentence clarification question\n\n"
            f"The user's categories are: {cats_str}.\n"
            f"The user's wallets are: {wallets_str}.\n"
            "For record_expense pick an expense category; for record_income pick an income category. "
            "If category is unclear, use Other. Wallet fields must echo one of the user's wallet names. "
            "If currency is not specified, assume JOD. "
            "Confidence is 0.0 to 1.0 based on how clear the input was. "
            "If a date or time reference is mentioned (e.g. 'yesterday', 'last Friday', 'on May 20th'), "
            f"extract it as YYYY-MM-DD in the transaction_date field. Today is {today}."
        )

    async def extract_action(self, text: str, categories: list[dict], wallets: list[dict]) -> dict:
        category_names = [c["name"] for c in categories]
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": self._action_system(categories, wallets)},
                    {"role": "user", "content": text},
                ],
                response_format=self._action_schema(category_names),
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

        from faster_whisper import WhisperModel

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
