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

from app.core.domain.transaction import Transaction


class AIProvider(ABC):
    """Abstract interface for AI-powered transaction extraction and persona generation."""

    @abstractmethod
    async def extract_transaction(
        self,
        text: str,
        categories: list[str],
    ) -> dict:
        """Extract transaction details from natural language text.

        Returns dict with keys: amount_original, currency_original, description,
        category, confidence, transaction_date (optional).
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
        """Create an AIProvider for transaction extraction and personas."""
        ...

    @abstractmethod
    def create_transcription_provider(self) -> TranscriptionProvider:
        """Create a TranscriptionProvider with automatic fallback chain.

        Fallback order: Groq -> OpenAI -> local faster-whisper.
        """
        ...
