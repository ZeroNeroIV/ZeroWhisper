import json

from openai import AsyncOpenAI

from app.config import settings
from app.schemas.agent import TransactionProposal, VALID_CATEGORIES

_client: AsyncOpenAI | None = None

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


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
    return _client


async def extract_transaction(nl_input: str) -> TransactionProposal:
    client = _get_client()
    try:
        response = await client.chat.completions.create(
            model=settings.whisper_model,
            messages=[
                {"role": "system", "content": _EXTRACTION_SYSTEM},
                {"role": "user", "content": nl_input},
            ],
            response_format=_EXTRACTION_SCHEMA,
        )
    except Exception as e:
        raise ValueError(f"OpenAI extraction failed: {e}") from e

    content = response.choices[0].message.content
    data = json.loads(content)
    return TransactionProposal(**data)


async def generate_persona(category: str, spending_context: dict) -> str:
    client = _get_client()
    user_msg = (
        f"Category: {category}. "
        f"This month total: {spending_context.get('this_month_total', 0)}. "
        f"Transaction count: {spending_context.get('transaction_count', 0)}."
    )
    try:
        response = await client.chat.completions.create(
            model=settings.whisper_model,
            messages=[
                {"role": "system", "content": _PERSONA_SYSTEM},
                {"role": "user", "content": user_msg},
            ],
        )
        return response.choices[0].message.content
    except Exception:
        return "Got it. Transaction noted."


def health_check() -> bool:
    return bool(settings.openai_api_key)
