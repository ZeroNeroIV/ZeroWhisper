"""
AIProvider port — strategy interface for LLM-backed features.

Why a Strategy pattern instead of if/elif in _get_client()?
- The old openai_service.py had an if/elif chain selecting provider init
- Adding a new provider required editing that chain
- Testing was impossible without real API keys
- Transcription and extraction shared the same client but used different logic

Each provider (OpenAI, Gemini, Groq, local) implements this interface.
The application layer picks the implementation at runtime via a factory.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

# Intents the Whisper agent understands. "record_*" and "transfer" produce
# confirmable proposals; "query_*" are answered immediately from local data;
# "unknown" yields a clarification reply.
AGENT_INTENTS = (
    "record_expense",
    "record_income",
    "transfer",
    "query_balance",
    "query_spending",
    "unknown",
)


class AIProvider(ABC):
    """Abstract interface for AI-powered action extraction and persona generation."""

    @abstractmethod
    async def extract_action(
        self,
        text: str,
        categories: list[dict],
        wallets: list[dict],
    ) -> dict:
        """Extract a financial action from natural language text.

        `categories` is a list of {name, type} dicts; `wallets` is a list of
        {name, type, currency} dicts — both are offered to the model so it can
        ground its answer in the user's actual setup.

        Returns a dict with keys: intent (one of AGENT_INTENTS), amount,
        currency, description, category, wallet, from_wallet, to_wallet,
        transaction_date, confidence, reply. Unused fields are None.
        Raises AIServiceError on failure.
        """
        ...

    @abstractmethod
    async def generate_persona(
        self,
        category: str,
        this_month_total: float,
        transaction_count: int,
    ) -> str:
        """Generate a short (1-2 sentence) persona message about a spending category.

        The persona has a slightly sarcastic but helpful tone.
        Returns a fallback message on failure.
        """
        ...


class TranscriptionProvider(ABC):
    """Abstract interface for audio transcription (separate from AI extraction)."""

    @abstractmethod
    async def transcribe(self, data: bytes, filename: str) -> str:
        """Transcribe audio data to text. Raises AIServiceError on failure."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """True if this provider can accept transcription requests."""
        ...


class AIProviderFactory(ABC):
    """Creates AIProvider and TranscriptionProvider instances based on runtime config.

    The factory reads the current 'ai_provider' setting and returns the
    appropriate implementation. This keeps provider selection logic in one place.
    """

    @abstractmethod
    def create_provider(self) -> AIProvider:
        """Create an AIProvider for action extraction and personas."""
        ...

    @abstractmethod
    def create_transcription_provider(self) -> TranscriptionProvider:
        """Create a TranscriptionProvider with automatic fallback chain.

        Fallback order: Groq -> OpenAI -> local faster-whisper.
        """
        ...
