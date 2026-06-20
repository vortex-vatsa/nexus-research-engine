"""Research agent that generates queries and collects sources."""

import asyncio
import json
import logging
from uuid import uuid4

from app.core.exceptions import ResearchAgentError
from app.core.schemas import DocumentSource, ResearchRequest
from app.providers.llm_router import LLMRouter
from app.providers.search_client import TavilySearchClient

logger = logging.getLogger(__name__)


class ResearchAgent:
    """Autonomous agent for conducting research via web search."""

    def __init__(
        self,
        request: ResearchRequest,
        workspace_slug: str,
        email_slug: str,
        llm_router: LLMRouter,
        search_client: TavilySearchClient,
        settings,
    ):
        """Initialize research agent.

        Args:
            request: ResearchRequest with topic and preferences
            workspace_slug: Slug for the workspace being created
            email_slug: Email as safe directory name (e.g., user_gmail_com)
            llm_router: LLM router for sub-query generation
            search_client: Tavily search client
            settings: Application settings
        """
        self.request = request
        self.workspace_slug = workspace_slug
        self.email_slug = email_slug
        self.llm_router = llm_router
        self.search_client = search_client
        self.settings = settings
        self.request_id = str(uuid4())[:8]

    async def run(self) -> list[DocumentSource]:
        """Execute the full research pipeline.

        1. Generate sub-queries from topic
        2. Search each query with concurrency limit
        3. Deduplicate results by URL
        4. Create DocumentSource objects
        5. Return source list

        Returns:
            List of DocumentSource objects

        Raises:
            ResearchAgentError: On query generation or search failure
        """
        logger.info(
            f"[{self.request_id}] Starting research: {self.request.topic}"
        )

        # Step 1: Generate search sub-queries
        logger.info(f"[{self.request_id}] Generating search queries...")
        queries = await self._generate_sub_queries()
        logger.info(f"[{self.request_id}] Generated {len(queries)} queries")

        # Step 2: Search with concurrency limit
        logger.info(f"[{self.request_id}] Searching sources...")
        semaphore = asyncio.Semaphore(5)

        async def bounded_search(query: str):
            async with semaphore:
                return await self.search_client.search(query)

        search_tasks = [bounded_search(q) for q in queries]
        search_results = await asyncio.gather(
            *search_tasks, return_exceptions=True
        )

        # Handle any exceptions from search
        all_results = []
        for result in search_results:
            if isinstance(result, Exception):
                logger.warning(
                    f"[{self.request_id}] Search error: {result}"
                )
            else:
                all_results.extend(result)

        # Step 3: Deduplicate by URL, keep highest score
        seen_urls = {}
        for result in all_results:
            if result.url not in seen_urls:
                seen_urls[result.url] = result
            else:
                if result.score > seen_urls[result.url].score:
                    seen_urls[result.url] = result

        unique_results = list(seen_urls.values())
        logger.info(
            f"[{self.request_id}] "
            f"Found {len(unique_results)} unique sources"
        )

        # Step 4: Build DocumentSource list
        sources = []
        for i, result in enumerate(unique_results):
            source = DocumentSource(
                id=f"{self.workspace_slug}_src_{i}",
                title=result.title,
                url=result.url,
                local_path=f"/storage/{self.email_slug}/"
                f"{self.workspace_slug}/raw_sources/src_{i}.md",
                snippet=result.content[:500],
                downloaded_images=[],
            )
            sources.append(source)

        logger.info(
            f"[{self.request_id}] "
            f"Research complete: {len(sources)} sources"
        )
        return sources

    async def _generate_sub_queries(self) -> list[str]:
        """Generate targeted search queries using LLM.

        Prompt the LLM to generate 5 search queries based on the topic
        and format preference.

        Returns:
            List of search query strings

        Raises:
            ResearchAgentError: If LLM response is not valid JSON
        """
        system = "Return ONLY a JSON array of strings. No other text."
        user = (
            f"Generate 5 targeted search queries for: {self.request.topic} "
            f"formatted as: {self.request.format_preference.value}\n\n"
            "Return ONLY the JSON array. No markdown, no explanation."
        )

        response = await self.llm_router.complete(system, user)

        # Strip markdown fences if present
        response = response.strip()
        if response.startswith("```"):
            response = response.split("```")[1]
            if response.startswith("json"):
                response = response[4:]
        response = response.strip()

        try:
            queries = json.loads(response)
            if not isinstance(queries, list) or not all(
                isinstance(q, str) for q in queries
            ):
                raise ValueError("Response is not a list of strings")
            logger.debug(
                f"[{self.request_id}] Generated queries: {queries}"
            )
            return queries
        except (json.JSONDecodeError, ValueError) as e:
            raise ResearchAgentError(
                "Failed to parse LLM response as JSON",
                context={
                    "raw_response": response[:200],
                    "error": str(e),
                },
            )
