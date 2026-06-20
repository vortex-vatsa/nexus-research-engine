"""Tavily web search client for research queries."""

import logging

import httpx
from pydantic import BaseModel, Field

from app.core.config import Settings
from app.core.exceptions import SearchClientError

logger = logging.getLogger(__name__)


class SearchResult(BaseModel):
    """A single search result from Tavily."""

    url: str = Field(..., description="Result URL")
    title: str = Field(..., description="Result title")
    content: str = Field(..., description="Result snippet or content")
    score: float = Field(..., description="Relevance score")


class TavilySearchClient:
    """Async client for Tavily API."""

    def __init__(self, settings: Settings):
        """Initialize search client.

        Args:
            settings: Application settings with TAVILY_API_KEY
        """
        self.settings = settings
        self.base_url = "https://api.tavily.com"
        self.client = httpx.AsyncClient(
            base_url=self.base_url, timeout=30.0
        )

    async def search(
        self, query: str, max_results: int = 8
    ) -> list[SearchResult]:
        """Search the web using Tavily API.

        Args:
            query: Search query string
            max_results: Maximum number of results to return

        Returns:
            List of SearchResult objects

        Raises:
            SearchClientError: If API request fails
        """
        try:
            response = await self.client.post(
                "/search",
                json={
                    "api_key": self.settings.TAVILY_API_KEY,
                    "query": query,
                    "max_results": max_results,
                    "search_depth": "advanced",
                    "include_raw_content": True,
                },
            )
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("results", []):
                results.append(
                    SearchResult(
                        url=item.get("url", ""),
                        title=item.get("title", ""),
                        content=item.get("content", ""),
                        score=item.get("score", 0.0),
                    )
                )
            return results
        except httpx.HTTPError as e:
            raise SearchClientError(
                "Tavily API request failed",
                context={
                    "query": query,
                    "status_code": e.response.status_code
                    if hasattr(e, "response")
                    else None,
                    "error": str(e),
                },
            )
        except Exception as e:
            raise SearchClientError(
                "Failed to parse search results",
                context={"query": query, "error": str(e)},
            )

    async def close(self) -> None:
        """Close the HTTP client connection."""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
