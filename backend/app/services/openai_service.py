import json
from io import BytesIO

from openai import AsyncOpenAI

from app.schemas.agent import TransactionProposal, VALID_CATEGORIES

_client: AsyncOpenAI | None = None
_transcription_client: AsyncOpenAI | None = None

_EXTRACTION_SCHEMA = {
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
                "category": {"type": "string", "enum": VALID_CATEGORIES},
                "confidence": {"type": "number"},
            },
            "required": ["amount_original", "currency_original", "description", "category", "confidence"],
            "additionalProperties": False,
        },
    },
}

_EXTRACTION_SYSTEM = (
    "Extract financial transaction details from natural language. Be precise. "
    "If currency is not specified, assume JOD. "
    "Categories must be one of: Food, Transport, Housing, Utilities, Entertainment, "
    "Shopping, Health, Education, Income, Other. "
    "If category is unclear, use Other. "
    "Confidence is 0.0 to 1.0 based on how clear the input was."
)

_PERSONA_SYSTEM = (
    "You are Whisper, a highly competent but slightly sarcastic financial assistant. "
    "Keep responses to 1-2 sentences. Be helpful first, then gently roast if spending is high. "
    "Never be mean or offensive. Focus on the user's actual numbers."
)


def reset_clients() -> None:
    """Clear cached clients — called when AI settings change at runtime."""
    global _client, _transcription_client
    _client = None
    _transcription_client = None


def _s(key: str, fallback=None):
    """Read from runtime AI settings."""
    from app.services import ai_settings_service
    return ai_settings_service.get(key, fallback)


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        provider = _s("ai_provider", "openai")
        if provider == "gemini":
            _client = AsyncOpenAI(
                api_key=_s("gemini_api_key"),
                base_url="https://generativelanguage.googleapis.com/openai/",
            )
        elif provider == "groq":
            _client = AsyncOpenAI(
                api_key=_s("groq_api_key"),
                base_url="https://api.groq.com/openai/v1",
            )
        else:
            _client = AsyncOpenAI(
                api_key=_s("openai_api_key"),
                base_url="https://api.openai.com/v1",
            )
    return _client


def _get_model() -> str:
    provider = _s("ai_provider", "openai")
    if provider == "gemini":
        return _s("gemini_model", "gemini-2.5-flash")
    if provider == "groq":
        return _s("groq_model", "llama-3.3-70b-versatile")
    return _s("openai_model", "gpt-4o-mini")


def _get_transcription_client() -> AsyncOpenAI:
    global _transcription_client
    if _transcription_client is None:
        groq_key = _s("groq_api_key")
        if groq_key:
            _transcription_client = AsyncOpenAI(
                api_key=groq_key,
                base_url="https://api.groq.com/openai/v1",
            )
        else:
            _transcription_client = AsyncOpenAI(
                api_key=_s("openai_api_key"),
                base_url="https://api.openai.com/v1",
            )
    return _transcription_client


def _transcription_model() -> str:
    return "whisper-large-v3" if _s("groq_api_key") else "whisper-1"


async def extract_transaction(nl_input: str) -> TransactionProposal:
    client = _get_client()
    model = _get_model()
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": _EXTRACTION_SYSTEM},
                {"role": "user", "content": nl_input},
            ],
            response_format=_EXTRACTION_SCHEMA,
        )
    except Exception as e:
        raise ValueError(f"AI extraction failed: {e}") from e

    content = response.choices[0].message.content
    data = json.loads(content)
    return TransactionProposal(**data)


async def generate_persona(category: str, spending_context: dict) -> str:
    client = _get_client()
    model = _get_model()
    user_msg = (
        f"Category: {category}. "
        f"This month total: {spending_context.get('this_month_total', 0)}. "
        f"Transaction count: {spending_context.get('transaction_count', 0)}."
    )
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": _PERSONA_SYSTEM},
                {"role": "user", "content": user_msg},
            ],
        )
        return response.choices[0].message.content
    except Exception:
        return "Got it. Transaction noted."


async def transcribe_audio(data: bytes, filename: str) -> str:
    """Transcribe audio: Groq → OpenAI → local Whisper (automatic fallback)."""
    if _s("groq_api_key") or _s("openai_api_key"):
        client = _get_transcription_client()
        model = _transcription_model()
        mime = "audio/webm" if filename.endswith(".webm") else "audio/ogg"
        try:
            response = await client.audio.transcriptions.create(
                model=model,
                file=(filename, BytesIO(data), mime),
            )
            return response.text
        except Exception as e:
            raise ValueError(f"Transcription failed: {e}") from e
    else:
        from app.services import local_whisper_service
        return await local_whisper_service.transcribe(data, filename)


def health_check() -> bool:
    provider = _s("ai_provider", "openai")
    if provider == "gemini":
        return bool(_s("gemini_api_key"))
    if provider == "groq":
        return bool(_s("groq_api_key"))
    return bool(_s("openai_api_key"))


def transcribe_health_check() -> bool:
    return True


def ai_status() -> dict:
    groq_key = _s("groq_api_key")
    openai_key = _s("openai_api_key")
    local_model = _s("local_whisper_model", "small")
    transcription_backend = "groq" if groq_key else ("openai" if openai_key else f"local:{local_model}")
    return {
        "provider": _s("ai_provider", "openai"),
        "model": _get_model(),
        "ai_ready": health_check(),
        "transcription_ready": transcribe_health_check(),
        "transcription_backend": transcription_backend,
    }
