"""ChromaDB vector store service for workspace isolation."""

import asyncio
import logging
from pathlib import Path

import chromadb

from app.core.config import Settings
from app.core.exceptions import VectorStoreError
from app.core.schemas import DocumentSource, RetrievedChunk

logger = logging.getLogger(__name__)


class VectorStoreService:
    """Manages ChromaDB vector stores with per-workspace isolation."""

    def __init__(self, settings: Settings):
        """Initialize vector store service.

        Args:
            settings: Application settings with STORAGE_ROOT
        """
        self.settings = settings
        self._collections = {}

    def _get_collection(self, email_slug: str, workspace_slug: str):
        """Get or create a ChromaDB collection for a workspace.

        Collections are persistent and isolated per user+workspace.
        Stores embedding data in {STORAGE_ROOT}/{email_slug}/{workspace_slug}/chroma_db

        Args:
            email_slug: Email as safe directory name
            workspace_slug: Workspace slug

        Returns:
            ChromaDB collection object
        """
        collection_key = f"{email_slug}_{workspace_slug}"

        if collection_key not in self._collections:
            # Create persistent client
            storage_path = (
                Path(self.settings.STORAGE_ROOT)
                / email_slug
                / workspace_slug
                / "chroma_db"
            )
            storage_path.mkdir(parents=True, exist_ok=True)

            client = chromadb.PersistentClient(path=str(storage_path))
            collection_name = f"nexus_{email_slug}_{workspace_slug}"
            collection = client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            self._collections[collection_key] = collection

        return self._collections[collection_key]

    def _chunk_text(
        self, text: str, chunk_size: int = 500, overlap: int = 50
    ) -> list[str]:
        """Split text into overlapping chunks.

        Args:
            text: Text to chunk
            chunk_size: Target chunk size in characters
            overlap: Number of characters to overlap between chunks

        Returns:
            List of text chunks
        """
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - overlap

        return chunks

    async def ingest(
        self,
        documents: list[DocumentSource],
        email_slug: str,
        workspace_slug: str,
    ) -> int:
        """Ingest documents into vector store.

        Chunks each document and embeds via ChromaDB.
        Wraps all ChromaDB operations in run_in_executor.

        Args:
            documents: List of DocumentSource objects
            email_slug: Email as safe directory name
            workspace_slug: Workspace slug

        Returns:
            Total number of chunks ingested

        Raises:
            VectorStoreError: If ingestion fails
        """
        try:
            loop = asyncio.get_event_loop()
            collection = await loop.run_in_executor(
                None, self._get_collection, email_slug, workspace_slug
            )

            total_chunks = 0
            all_ids = []
            all_documents = []
            all_metadatas = []

            for doc in documents:
                # Chunk the document
                chunks = self._chunk_text(doc.snippet)
                for chunk_idx, chunk in enumerate(chunks):
                    chunk_id = f"{doc.id}_chunk_{chunk_idx}"
                    all_ids.append(chunk_id)
                    all_documents.append(chunk)
                    all_metadatas.append(
                        {
                            "source_id": doc.id,
                            "url": doc.url,
                            "chunk_index": chunk_idx,
                            "email_slug": email_slug,
                        }
                    )
                    total_chunks += 1

            # Add to collection in executor
            if all_ids:
                await loop.run_in_executor(
                    None,
                    lambda: collection.add(
                        ids=all_ids,
                        documents=all_documents,
                        metadatas=all_metadatas,
                    ),
                )

            logger.info(
                f"Ingested {total_chunks} chunks from "
                f"{len(documents)} documents into {workspace_slug}"
            )
            return total_chunks

        except Exception as e:
            raise VectorStoreError(
                "Failed to ingest documents into vector store",
                context={
                    "workspace": workspace_slug,
                    "doc_count": len(documents),
                    "error": str(e),
                },
            )

    async def query(
        self,
        question: str,
        email_slug: str,
        workspace_slug: str,
        n_results: int = 5,
    ) -> list[RetrievedChunk]:
        """Query vector store for relevant chunks.

        Args:
            question: Query question
            email_slug: Email as safe directory name
            workspace_slug: Workspace slug
            n_results: Number of results to return

        Returns:
            List of RetrievedChunk objects sorted by distance ascending

        Raises:
            VectorStoreError: If query fails
        """
        try:
            loop = asyncio.get_event_loop()
            collection = await loop.run_in_executor(
                None, self._get_collection, email_slug, workspace_slug
            )

            # Query in executor
            results = await loop.run_in_executor(
                None,
                lambda: collection.query(
                    query_texts=[question],
                    n_results=n_results,
                ),
            )

            # Parse results into RetrievedChunk objects
            chunks = []
            if results and results["documents"]:
                for i, doc in enumerate(results["documents"][0]):
                    chunk = RetrievedChunk(
                        content=doc,
                        source_id=results["metadatas"][0][i].get(
                            "source_id", ""
                        ),
                        url=results["metadatas"][0][i].get("url", ""),
                        chunk_index=results["metadatas"][0][i].get(
                            "chunk_index", 0
                        ),
                        distance=results["distances"][0][i]
                        if results["distances"]
                        else 1.0,
                    )
                    chunks.append(chunk)

            # Sort by distance ascending (closer results first)
            chunks.sort(key=lambda x: x.distance)
            return chunks

        except Exception as e:
            raise VectorStoreError(
                "Failed to query vector store",
                context={
                    "workspace": workspace_slug,
                    "question": question[:100],
                    "error": str(e),
                },
            )
