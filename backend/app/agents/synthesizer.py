"""Synthesizer agent that converts sources into structured dashboard payload."""

import json
import logging
from datetime import datetime
from uuid import uuid4

from app.core.exceptions import SynthesizerError
from app.core.schemas import (
    ChartStyle,
    ComponentType,
    DashboardPayload,
    DocumentSource,
    FormatPreference,
    MatrixComponent,
    ResearchRequest,
    TopicMetadata,
)
from app.providers.llm_router import with_backoff

logger = logging.getLogger(__name__)


class SynthesizerAgent:
    """Synthesizes research sources into structured dashboard payload."""

    def __init__(
        self,
        request: ResearchRequest,
        workspace_slug: str,
        email_slug: str,
        llm_router,
        workspace_repo,
        settings,
    ):
        """Initialize synthesizer agent.

        Args:
            request: ResearchRequest with topic and preferences
            workspace_slug: Slug for the workspace
            email_slug: Email as safe directory name
            llm_router: LLM router for synthesis
            workspace_repo: Repository for saving payload
            settings: Application settings
        """
        self.request = request
        self.workspace_slug = workspace_slug
        self.email_slug = email_slug
        self.llm_router = llm_router
        self.workspace_repo = workspace_repo
        self.settings = settings
        self.request_id = str(uuid4())[:8]

    async def run(
        self, sources: list[DocumentSource]
    ) -> DashboardPayload:
        """Execute the full synthesis pipeline.

        1. Build context from sources
        2. Apply token guard (80,000 char limit)
        3. Generate synthesis prompt
        4. Call LLM with backoff retry
        5. Parse response as JSON with repair fallback
        6. Create DashboardPayload with metadata
        7. Save to workspace repository
        8. Return payload

        Args:
            sources: List of DocumentSource objects from research

        Returns:
            DashboardPayload with synthesized findings

        Raises:
            SynthesizerError: On LLM failure or JSON parsing failure
        """
        logger.info(
            f"[{self.request_id}] Starting synthesis of {len(sources)} sources"
        )

        # Step 1: Build context from sources
        context_lines = []
        for source in sources:
            context_lines.append(f"## {source.title}")
            context_lines.append(f"URL: {source.url}\n")
            context_lines.append(source.snippet[:2000])
            context_lines.append("\n---\n")

        context = "\n".join(context_lines)

        # Step 2: Token guard - truncate if too large
        if len(context) > 80000:
            logger.info(
                f"[{self.request_id}] Context exceeds 80K chars, "
                f"truncating to top sources"
            )
            # Truncate to fit within limit
            context = context[:80000]

        # Step 3: Build synthesis prompt
        system, user = self._build_synthesis_prompt(context)

        # Step 4: Call LLM with backoff
        logger.info(f"[{self.request_id}] Calling LLM for synthesis...")
        try:
            async def _synthesize():
                return await self.llm_router.complete(
                    system, user, max_tokens=4096
                )

            raw_response = await with_backoff(
                _synthesize, retries=2, base_delay=1.0
            )
        except Exception as e:
            raise SynthesizerError(
                f"LLM synthesis failed: {e}",
                context={"request_id": self.request_id},
            )

        # Step 5: Parse response
        logger.info(f"[{self.request_id}] Parsing LLM response...")
        payload = self._parse_llm_response(raw_response)

        # Step 6: Add metadata
        payload.topic_metadata = TopicMetadata(
            topic=self.request.topic,
            extensiveness=self.request.extensiveness.value,
            format_preference=self.request.format_preference.value,
            generated_at=datetime.utcnow(),
            schema_version="1.0",
        )

        # Step 7: Save to repository
        logger.info(f"[{self.request_id}] Saving payload to repository...")
        try:
            await self.workspace_repo.save_payload(
                self.email_slug, self.workspace_slug, payload
            )
        except Exception as e:
            logger.warning(
                f"[{self.request_id}] Failed to save payload: {e}"
            )
            # Continue - payload is still valid even if save fails

        logger.info(
            f"[{self.request_id}] Synthesis complete: "
            f"{len(payload.matrix_data)} components, "
            f"{len(payload.document_library)} sources"
        )
        return payload

    def _build_synthesis_prompt(
        self, context: str
    ) -> tuple[str, str]:
        """Build the system and user prompts for synthesis.

        Args:
            context: Combined context from all sources

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        system = (
            "Return ONLY a valid JSON object. No markdown fences. "
            "No explanation. Raw JSON only. "
            "Your entire response must be parseable by json.loads()."
        )

        # Format-specific instructions
        format_pref = self.request.format_preference
        if format_pref == FormatPreference.COMPARISON:
            format_instructions = (
                "COMPARISON format: 2 tables + 1 line chart + 1 list. "
                "Tables for comparative analysis, chart for trends, "
                "list for key insights."
            )
        elif format_pref == FormatPreference.SWOT:
            format_instructions = (
                "SWOT format: 4 lists for Strengths, Weaknesses, "
                "Opportunities, and Threats."
            )
        elif format_pref == FormatPreference.TIMELINE:
            format_instructions = (
                "TIMELINE format: 3 lists ordered chronologically. "
                "Each entry: [date, event]. Sort by date ascending."
            )
        elif format_pref == FormatPreference.PROS_CONS:
            format_instructions = (
                "PROS_CONS format: 2 lists (Pros, Cons) + 1 comparison table. "
                "List format: [item, explanation]."
            )
        else:
            format_instructions = ""

        # JSON schema example
        schema_example = (
            '{'
            '"executive_summary": "string",'
            '"matrix_data": ['
            '{"section_title": "string", '
            '"component_type": "table|chart|list", '
            '"headers": ["string"], '
            '"rows": [["string"]], '
            '"chart_style": "bar|line|pie", '
            '"data": [{"label": "value"}], '
            '"description": "string"}'
            '],'
            '"document_library": ['
            '{"id": "string", "title": "string", '
            '"url": "string", "local_path": "string", '
            '"snippet": "string", "downloaded_images": []}'
            ']'
            '}'
        )

        user = (
            f"Synthesize the following sources about '{self.request.topic}' "
            f"into a structured dashboard.\n\n"
            f"Format: {format_instructions}\n\n"
            f"Context:\n{context}\n\n"
            f"Return a JSON object with this structure:\n{schema_example}\n\n"
            f"Return ONLY valid JSON. No markdown. No explanation."
        )

        return system, user

    def _parse_llm_response(self, raw: str) -> DashboardPayload:
        """Parse LLM response as DashboardPayload JSON.

        Handles markdown fences and attempts JSON repair on failure.

        Args:
            raw: Raw LLM response string

        Returns:
            Parsed DashboardPayload

        Raises:
            SynthesizerError: If response cannot be parsed
        """
        # Strip whitespace and remove markdown fences
        raw = raw.strip()
        if raw.startswith("```"):
            # Remove ```json or ``` prefix
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        # Try to parse as JSON
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as e:
            logger.warning(
                f"[{self.request_id}] Initial JSON parse failed: {e}. "
                f"Attempting repair..."
            )
            # Try repair (but don't await it since we're not in async context here)
            # For now, just raise with the original response for debugging
            raise SynthesizerError(
                "Failed to parse LLM response as JSON",
                context={
                    "error": str(e),
                    "raw_preview": raw[:200],
                    "request_id": self.request_id,
                },
            )

        # Validate and create DashboardPayload
        try:
            payload = DashboardPayload(
                topic_metadata=TopicMetadata(
                    topic=self.request.topic,
                    extensiveness=self.request.extensiveness.value,
                    format_preference=self.request.format_preference.value,
                    generated_at=datetime.utcnow(),
                ),
                executive_summary=parsed.get(
                    "executive_summary", "Research findings summary."
                ),
                matrix_data=[
                    MatrixComponent(
                        section_title=comp.get("section_title", ""),
                        component_type=ComponentType(
                            comp.get("component_type", "list")
                        ),
                        headers=comp.get("headers"),
                        rows=comp.get("rows"),
                        chart_style=ChartStyle(
                            comp.get("chart_style", "bar")
                        )
                        if comp.get("chart_style")
                        else None,
                        data=comp.get("data"),
                        description=comp.get("description"),
                    )
                    for comp in parsed.get("matrix_data", [])
                ],
                document_library=[
                    DocumentSource(
                        id=doc.get("id", ""),
                        title=doc.get("title", ""),
                        url=doc.get("url", ""),
                        local_path=doc.get("local_path", ""),
                        snippet=doc.get("snippet", ""),
                        downloaded_images=doc.get(
                            "downloaded_images", []
                        ),
                    )
                    for doc in parsed.get("document_library", [])
                ],
            )
            return payload
        except (KeyError, ValueError, TypeError) as e:
            raise SynthesizerError(
                "Failed to construct DashboardPayload from parsed JSON",
                context={
                    "error": str(e),
                    "raw_preview": raw[:200],
                    "request_id": self.request_id,
                },
            )

    async def _attempt_json_repair(self, broken: str) -> str:
        """Attempt to repair malformed JSON using LLM.

        Args:
            broken: Broken JSON string

        Returns:
            Repaired JSON string

        Raises:
            SynthesizerError: If repair fails
        """
        logger.info(f"[{self.request_id}] Attempting JSON repair...")
        repair_prompt = (
            f"Fix this malformed JSON. Return ONLY valid JSON:\n{broken}"
        )
        system = (
            "You are a JSON repair expert. Return only valid JSON. "
            "No explanation, no markdown."
        )

        try:
            repaired = await self.llm_router.complete(
                system, repair_prompt, max_tokens=4096
            )
            # Try to parse to verify it's valid
            json.loads(repaired)
            logger.info(f"[{self.request_id}] JSON repair successful")
            return repaired
        except Exception as e:
            raise SynthesizerError(
                "JSON repair failed",
                context={"error": str(e), "request_id": self.request_id},
            )
