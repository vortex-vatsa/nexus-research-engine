"""LLM provider router: Ollama → Gemini → Groq."""

import logging

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


class LLMRouter:
    """Routes LLM calls to available providers with fallback logic."""

    def __init__(self, settings: Settings):
        """Initialize with settings."""
        self.settings = settings
        self._provider = None

    async def initialize(self) -> None:
        """Initialize and select the first available LLM provider."""
        # Stub implementation for Task 1.1
        # Full implementation in Task 1.3
        self._provider = "stub"
        logger.info("LLM Router initialized (stub)")


# Module singleton
llm_router = LLMRouter(get_settings())


def get_llm_router() -> LLMRouter:
    """FastAPI dependency for LLM router."""
    return llm_router
