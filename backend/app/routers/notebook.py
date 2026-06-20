"""Notebook RAG Q&A API routes."""

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.auth.dependencies import get_current_user
from app.core.config import get_settings
from app.core.schemas import AuthUser, NotebookQuery, NotebookResponse
from app.providers.llm_router import get_llm_router
from app.services.notebook import NotebookService
from app.services.vector_store import VectorStoreService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/query")
async def query_notebook(
    query: NotebookQuery,
    current_user: AuthUser = Depends(get_current_user),
) -> NotebookResponse:
    """Query workspace knowledge base using RAG.

    Args:
        query: NotebookQuery with workspace_slug and question
        current_user: Authenticated user from session

    Returns:
        NotebookResponse with answer and sources

    Raises:
        HTTPException: 400 if query fails
    """
    try:
        # Initialize services
        llm_router = get_llm_router()
        settings = get_settings()
        vector_store = VectorStoreService(settings)
        notebook_service = NotebookService(llm_router, vector_store)

        # Get answer
        response = await notebook_service.answer(query, current_user.email)

        logger.info(
            f"Notebook query from {current_user.email}: "
            f"confidence={response.confidence_score:.2f}, "
            f"needs_web_search={response.needs_web_search}"
        )
        return response

    except Exception as e:
        logger.error(f"Notebook query failed: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Query failed: {str(e)}",
        )


@router.post("/search-and-answer")
async def search_and_answer(
    query: NotebookQuery,
    current_user: AuthUser = Depends(get_current_user),
):
    """Search web and answer question (V2 feature - stub).

    Args:
        query: NotebookQuery with workspace_slug and question
        current_user: Authenticated user from session

    Returns:
        501 Not Implemented
    """
    raise HTTPException(
        status_code=501,
        detail="Search and answer feature not yet implemented",
    )
