"""Notebook service for RAG Q&A with confidence scoring."""

import logging

from app.core.config import email_to_slug
from app.core.exceptions import NotebookError
from app.core.schemas import NotebookQuery, NotebookResponse

logger = logging.getLogger(__name__)


class NotebookService:
    """Provides RAG Q&A capability via vector store + LLM."""

    def __init__(self, llm_router, vector_store):
        """Initialize notebook service.

        Args:
            llm_router: LLM router for answer generation
            vector_store: VectorStoreService for retrieval
        """
        self.llm_router = llm_router
        self.vector_store = vector_store

    async def answer(
        self, query: NotebookQuery, user_email: str
    ) -> NotebookResponse:
        """Answer a question using RAG over a workspace.

        Steps:
        1. Retrieve relevant chunks from vector store
        2. Calculate confidence from chunk distances
        3. Query LLM for answer using context
        4. Determine if web search is needed
        5. Return response with sources

        Args:
            query: NotebookQuery with workspace_slug and question
            user_email: User email (for workspace isolation)

        Returns:
            NotebookResponse with answer and sources

        Raises:
            NotebookError: If answer generation fails
        """
        try:
            email_slug = email_to_slug(user_email)

            # Step 1: Retrieve relevant chunks
            chunks = await self.vector_store.query(
                question=query.question,
                email_slug=email_slug,
                workspace_slug=query.workspace_slug,
                n_results=5,
            )

            # Step 2: Handle empty results
            if not chunks:
                return NotebookResponse(
                    answer="No relevant information found in the workspace.",
                    sources=[],
                    confidence_score=0.0,
                    needs_web_search=True,
                )

            # Step 3: Calculate confidence from distances
            # Distance is typically 0-2 in cosine space, invert to get confidence
            confidence_scores = [
                max(0, 1 - chunk.distance / 2) for chunk in chunks
            ]
            avg_confidence = (
                sum(confidence_scores) / len(confidence_scores)
                if confidence_scores
                else 0.0
            )

            # Step 4: Build context from chunks
            context_parts = []
            for chunk in chunks:
                source_line = (
                    f"**{chunk.source_id}** (Distance: {chunk.distance:.2f}):"
                )
                context_parts.append(f"{source_line}\n{chunk.content}\n")
            context = "\n".join(context_parts)

            # Step 5: Query LLM with context
            system = (
                "You are a helpful research assistant. Answer questions "
                "ONLY using the provided context. If the context is "
                "insufficient to answer, respond with exactly: "
                "INSUFFICIENT_CONTEXT"
            )
            user = (
                f"Context from research:\n\n{context}\n\n"
                f"Question: {query.question}\n\n"
                f"Answer based only on the context above."
            )

            try:
                answer_text = await self.llm_router.complete(
                    system, user, max_tokens=1024
                )
            except Exception as e:
                logger.error(f"LLM query failed: {e}")
                raise NotebookError(
                    "Failed to generate answer",
                    context={"error": str(e), "question": query.question},
                )

            # Step 6: Determine if web search is needed
            needs_web_search = (
                "INSUFFICIENT_CONTEXT" in answer_text or avg_confidence < 0.3
            )

            if "INSUFFICIENT_CONTEXT" in answer_text:
                answer_text = (
                    "The available information is insufficient to answer this "
                    "question. Please consider searching the web for more "
                    "current information."
                )

            # Step 7: Return response
            return NotebookResponse(
                answer=answer_text,
                sources=chunks,
                confidence_score=avg_confidence,
                needs_web_search=needs_web_search,
            )

        except NotebookError:
            raise
        except Exception as e:
            raise NotebookError(
                "Failed to answer question",
                context={
                    "workspace": query.workspace_slug,
                    "question": query.question[:100],
                    "error": str(e),
                },
            )
