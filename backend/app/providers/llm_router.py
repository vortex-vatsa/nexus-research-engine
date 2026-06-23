"""LLM provider router: Ollama → Gemini → Groq with fallback logic."""

import asyncio
import logging
from abc import ABC, abstractmethod

import httpx

from app.core.config import Settings, get_settings
from app.core.exceptions import ResearchAgentError

logger = logging.getLogger(__name__)


async def with_backoff(
    fn, retries: int = 2, base_delay: float = 1.0
):
    """Retry an async callable with exponential backoff on failure.

    Args:
        fn: Async callable to execute
        retries: Number of retries (total attempts = retries + 1)
        base_delay: Initial delay in seconds

    Returns:
        Result of successful function call

    Raises:
        The last exception if all attempts fail
    """
    for attempt in range(retries + 1):
        try:
            return await fn()
        except Exception as e:
            if attempt == retries:
                raise
            delay = base_delay * (2 ** attempt)
            logger.warning(
                f"Attempt {attempt + 1} failed: {e}. "
                f"Retrying in {delay}s."
            )
            await asyncio.sleep(delay)


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def complete(
        self, system_prompt: str, user_prompt: str, max_tokens: int = 4096
    ) -> str:
        """Generate a completion using the LLM.

        Args:
            system_prompt: System prompt to guide behavior
            user_prompt: User message
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text response
        """
        pass


class OllamaProvider(BaseLLMProvider):
    """Ollama local LLM provider."""

    def __init__(self, settings: Settings):
        """Initialize Ollama provider.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.host = settings.OLLAMA_HOST or "http://localhost:11434"
        self.model = "llama3.2"

    async def complete(
        self, system_prompt: str, user_prompt: str, max_tokens: int = 4096
    ) -> str:
        """Generate completion via Ollama API.

        Args:
            system_prompt: System prompt
            user_prompt: User message
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text

        Raises:
            ResearchAgentError: If API call fails
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.host}/api/generate",
                    json={
                        "model": self.model,
                        "system": system_prompt,
                        "prompt": user_prompt,
                        "stream": False,
                    },
                )
                response.raise_for_status()
                return response.json()["response"]
            except Exception as e:
                raise ResearchAgentError(
                    "Ollama API request failed",
                    context={"error": str(e), "host": self.host},
                )


class GeminiProvider(BaseLLMProvider):
    """Google Gemini Flash LLM provider."""

    def __init__(self, settings: Settings):
        """Initialize Gemini provider.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.model = "gemini-2.5-flash"

    async def complete(
        self, system_prompt: str, user_prompt: str, max_tokens: int = 4096
    ) -> str:
        """Generate completion via Gemini API.

        Args:
            system_prompt: System prompt
            user_prompt: User message
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text

        Raises:
            ResearchAgentError: If API call fails
        """
        try:
            import google.generativeai as genai

            genai.configure(api_key=self.settings.GEMINI_API_KEY)
            model = genai.GenerativeModel(
                self.model,
                system_instruction=system_prompt,
            )
            response = await asyncio.to_thread(
                model.generate_content, user_prompt
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini error: {type(e).__name__}: {e}")
            raise ResearchAgentError(
                "Gemini API request failed",
                context={"error": str(e), "model": self.model},
            )


class GroqProvider(BaseLLMProvider):
    """Groq Llama3 LLM provider."""

    def __init__(self, settings: Settings):
        """Initialize Groq provider.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.model = "llama-3.1-8b-instant"

    async def complete(
        self, system_prompt: str, user_prompt: str, max_tokens: int = 4096
    ) -> str:
        """Generate completion via Groq API.

        Args:
            system_prompt: System prompt
            user_prompt: User message
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text

        Raises:
            ResearchAgentError: If API call fails
        """
        try:
            from groq import AsyncGroq

            client = AsyncGroq(api_key=self.settings.GROQ_API_KEY)
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq error: {type(e).__name__}: {e}")
            raise ResearchAgentError(
                "Groq API request failed",
                context={"error": str(e), "model": self.model},
            )


class LLMRouter:
    """Routes LLM calls to available providers with fallback logic."""

    def __init__(self, settings: Settings):
        """Initialize router with settings.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self._provider: BaseLLMProvider | None = None
        self._provider_name: str | None = None

    async def initialize(self) -> None:
        """Initialize and select the first available LLM provider.

        Tries providers in order: Ollama → Gemini → Groq
        Raises RuntimeError if no provider is available.
        """
        # Try Ollama (2s timeout)
        if self.settings.OLLAMA_HOST:
            try:
                async with asyncio.timeout(2):
                    provider = OllamaProvider(self.settings)
                    # Test with a simple request
                    await provider.complete("You are helpful.", "Hello")
                    self._provider = provider
                    self._provider_name = "Ollama (local)"
                    logger.info("LLM: Using Ollama (local)")
                    return
            except Exception as e:
                logger.debug(f"Ollama unavailable: {e}")

        # Try Gemini
        if self.settings.GEMINI_API_KEY:
            try:
                provider = GeminiProvider(self.settings)
                # Test with a simple request
                await provider.complete("You are helpful.", "Hello")
                self._provider = provider
                self._provider_name = "Gemini Flash"
                logger.info("LLM: Using Gemini Flash")
                return
            except Exception as e:
                logger.warning(f"Gemini unavailable: {type(e).__name__}: {e}")

        # Try Groq
        if self.settings.GROQ_API_KEY:
            try:
                provider = GroqProvider(self.settings)
                # Test with a simple request
                await provider.complete("You are helpful.", "Hello")
                self._provider = provider
                self._provider_name = "Groq Llama3"
                logger.info("LLM: Using Groq Llama3")
                return
            except Exception as e:
                logger.warning(f"Groq unavailable: {type(e).__name__}: {e}")

        raise RuntimeError(
            "No LLM provider available. "
            "Configure OLLAMA_HOST, GEMINI_API_KEY, or GROQ_API_KEY."
        )

    async def complete(
        self, system_prompt: str, user_prompt: str, max_tokens: int = 4096
    ) -> str:
        """Generate completion with selected provider.

        Wraps the provider call in a 30-second timeout and applies
        exponential backoff retry logic.

        Args:
            system_prompt: System prompt
            user_prompt: User message
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text

        Raises:
            ResearchAgentError: On timeout or provider failure
        """
        if not self._provider:
            raise ResearchAgentError(
                "LLM provider not initialized",
                context={"call": "complete"},
            )

        async def _call():
            async with asyncio.timeout(90):
                return await self._provider.complete(
                    system_prompt, user_prompt, max_tokens
                )

        try:
            return await with_backoff(_call, retries=2, base_delay=1.0)
        except asyncio.TimeoutError:
            raise ResearchAgentError(
                "LLM request timed out after 30 seconds",
                context={"timeout_seconds": 30},
            )

    def get_provider_name(self) -> str:
        """Get the name of the current provider.

        Returns:
            Provider name (e.g., "Ollama (local)")

        Raises:
            ResearchAgentError: If provider not initialized
        """
        if not self._provider_name:
            raise ResearchAgentError(
                "LLM provider not initialized",
                context={"call": "get_provider_name"},
            )
        return self._provider_name


# Module singleton
llm_router = LLMRouter(get_settings())


def get_llm_router() -> LLMRouter:
    """FastAPI dependency for LLM router.

    Returns:
        Module-level LLMRouter instance
    """
    return llm_router
