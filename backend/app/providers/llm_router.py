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
        self.model = "llama-3.3-70b-versatile"

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
        self._groq_provider: BaseLLMProvider | None = None
        self._ollama_provider: BaseLLMProvider | None = None

    async def initialize(self) -> None:
        """Initialize and select the primary LLM provider.

        Stores references to all available providers for fallback.
        Tries providers in order: Ollama → Gemini → Groq
        Raises RuntimeError if no provider is available.
        """
        self._groq_provider = None
        self._ollama_provider = None

        # Try Ollama (2s timeout)
        if self.settings.OLLAMA_HOST:
            try:
                async with asyncio.timeout(2):
                    provider = OllamaProvider(self.settings)
                    await provider.complete("You are helpful.", "Hello")
                    self._ollama_provider = provider
            except Exception as e:
                logger.debug(f"Ollama unavailable: {e}")

        # Try Gemini as primary
        if self.settings.GEMINI_API_KEY:
            try:
                provider = GeminiProvider(self.settings)
                await provider.complete("You are helpful.", "Hello")
                self._provider = provider
                self._provider_name = "Gemini Flash"
                logger.info("LLM: Primary = Gemini Flash")
                # Store Groq as fallback
                if self.settings.GROQ_API_KEY:
                    try:
                        self._groq_provider = GroqProvider(self.settings)
                        logger.info("LLM: Fallback = Groq")
                    except Exception as e:
                        logger.debug(f"Groq fallback unavailable: {e}")
                return
            except Exception as e:
                logger.warning(f"Gemini unavailable: {type(e).__name__}: {e}")

        # Try Groq as primary if Gemini not available
        if self.settings.GROQ_API_KEY:
            try:
                provider = GroqProvider(self.settings)
                await provider.complete("You are helpful.", "Hello")
                self._provider = provider
                self._provider_name = "Groq Llama3"
                logger.info("LLM: Primary = Groq Llama3")
                return
            except Exception as e:
                logger.warning(f"Groq unavailable: {type(e).__name__}: {e}")

        raise RuntimeError(
            "No LLM provider available. "
            "Configure GEMINI_API_KEY, GROQ_API_KEY, or OLLAMA_HOST."
        )

    async def complete(
        self, system_prompt: str, user_prompt: str, max_tokens: int = 4096
    ) -> str:
        """Generate completion with fallback provider logic.

        Tries the primary provider first, then falls back to secondary
        providers (Groq, Ollama) if the primary fails. Applies exponential
        backoff retry logic per provider.

        Args:
            system_prompt: System prompt
            user_prompt: User message
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text

        Raises:
            ResearchAgentError: If all providers fail
        """
        if not self._provider:
            raise ResearchAgentError(
                "LLM provider not initialized",
                context={"call": "complete"},
            )

        providers_to_try = [self._provider]
        if not isinstance(self._provider, GroqProvider) and self._groq_provider:
            providers_to_try.append(self._groq_provider)
        if not isinstance(self._provider, OllamaProvider) and self._ollama_provider:
            providers_to_try.append(self._ollama_provider)

        last_error = None
        for provider in providers_to_try:
            try:
                async def _call():
                    async with asyncio.timeout(90):
                        return await provider.complete(
                            system_prompt, user_prompt, max_tokens
                        )

                result = await with_backoff(_call, retries=2, base_delay=1.0)
                return result
            except Exception as e:
                provider_name = type(provider).__name__
                logger.warning(
                    f"Provider {provider_name} failed: {type(e).__name__}: {e}. "
                    f"Trying next..."
                )
                last_error = e
                continue

        raise ResearchAgentError(
            f"All LLM providers failed. Last error: {str(last_error)}",
            context={"last_error": str(last_error)},
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
