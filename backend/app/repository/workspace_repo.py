"""WorkspaceRepository — abstracts all file system operations."""

import logging
import shutil
from pathlib import Path

import aiofiles

from app.core.config import Settings
from app.core.exceptions import WorkspaceNotFoundError
from app.core.schemas import DashboardPayload, WorkspaceListItem

logger = logging.getLogger(__name__)


class WorkspaceRepository:
    """Abstracts all workspace file system operations.

    All file I/O goes through this class. To swap from local disk to
    Cloudflare R2, replace this implementation. No other code touches files.
    """

    def __init__(self, settings: Settings):
        """Initialize repository.

        Args:
            settings: Application settings with STORAGE_ROOT
        """
        self.settings = settings
        self.storage_root = Path(settings.STORAGE_ROOT).resolve()

    def _safe_path(self, email_slug: str, slug: str) -> Path:
        """Build and validate a safe workspace path.

        Verifies path is within STORAGE_ROOT to prevent traversal attacks.

        Args:
            email_slug: Email as safe directory name
            slug: Workspace slug

        Returns:
            Validated Path object

        Raises:
            WorkspaceNotFoundError: If path traversal detected
        """
        # Reject slug/email containing path separators or traversal sequences
        if "/" in slug or "\\" in slug or ".." in slug:
            raise WorkspaceNotFoundError(
                "Path traversal attempt detected",
                context={"email_slug": email_slug, "slug": slug},
            )
        if "/" in email_slug or "\\" in email_slug or ".." in email_slug:
            raise WorkspaceNotFoundError(
                "Path traversal attempt detected",
                context={"email_slug": email_slug, "slug": slug},
            )

        base = self.storage_root
        path = (base / email_slug / slug).resolve()

        # Verify path is within storage root (defense in depth)
        if not str(path).startswith(str(base)):
            raise WorkspaceNotFoundError(
                "Path traversal attempt detected",
                context={"email_slug": email_slug, "slug": slug},
            )

        return path

    async def ensure_workspace_dir(
        self, email_slug: str, slug: str
    ) -> Path:
        """Create workspace directory structure if not exists.

        Creates {STORAGE_ROOT}/{email_slug}/{slug}/raw_sources/

        Args:
            email_slug: Email as safe directory name
            slug: Workspace slug

        Returns:
            Base workspace path

        Raises:
            WorkspaceNotFoundError: If path traversal detected
        """
        base_path = self._safe_path(email_slug, slug)
        sources_path = base_path / "raw_sources"

        # Create directories
        try:
            sources_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Workspace directory ensured: {base_path}")
        except Exception as e:
            raise WorkspaceNotFoundError(
                "Failed to create workspace directory",
                context={
                    "path": str(base_path),
                    "error": str(e),
                },
            )

        return base_path

    async def save_payload(
        self, email_slug: str, slug: str, payload: DashboardPayload
    ) -> None:
        """Save DashboardPayload to dashboard_payload.json.

        Args:
            email_slug: Email as safe directory name
            slug: Workspace slug
            payload: DashboardPayload to save

        Raises:
            WorkspaceNotFoundError: If path traversal detected or save fails
        """
        base_path = self._safe_path(email_slug, slug)
        payload_path = base_path / "dashboard_payload.json"

        try:
            # Ensure directory exists
            base_path.mkdir(parents=True, exist_ok=True)

            # Serialize payload to JSON
            payload_json = payload.model_dump_json(indent=2)

            # Write asynchronously
            async with aiofiles.open(payload_path, "w") as f:
                await f.write(payload_json)

            logger.info(f"Payload saved: {payload_path}")
        except Exception as e:
            raise WorkspaceNotFoundError(
                "Failed to save dashboard payload",
                context={
                    "path": str(payload_path),
                    "error": str(e),
                },
            )

    async def load_payload(
        self, email_slug: str, slug: str
    ) -> DashboardPayload:
        """Load DashboardPayload from dashboard_payload.json.

        Args:
            email_slug: Email as safe directory name
            slug: Workspace slug

        Returns:
            Parsed DashboardPayload

        Raises:
            WorkspaceNotFoundError: If file not found or invalid
        """
        base_path = self._safe_path(email_slug, slug)
        payload_path = base_path / "dashboard_payload.json"

        try:
            # Read asynchronously
            async with aiofiles.open(payload_path, "r") as f:
                content = await f.read()

            # Parse JSON
            payload = DashboardPayload.model_validate_json(content)
            logger.info(f"Payload loaded: {payload_path}")
            return payload
        except FileNotFoundError:
            raise WorkspaceNotFoundError(
                "Workspace payload not found",
                context={"path": str(payload_path)},
            )
        except Exception as e:
            raise WorkspaceNotFoundError(
                "Failed to load dashboard payload",
                context={
                    "path": str(payload_path),
                    "error": str(e),
                },
            )

    async def save_source(
        self, email_slug: str, slug: str, filename: str, content: str
    ) -> str:
        """Save raw markdown source document.

        Args:
            email_slug: Email as safe directory name
            slug: Workspace slug
            filename: Filename (e.g., "src_0.md")
            content: Document content

        Returns:
            Local path string for DocumentSource.local_path

        Raises:
            WorkspaceNotFoundError: If path traversal detected or save fails
        """
        base_path = self._safe_path(email_slug, slug)
        sources_path = base_path / "raw_sources"
        file_path = sources_path / filename

        try:
            # Verify file path is within sources directory
            file_path_resolved = file_path.resolve()
            if not str(file_path_resolved).startswith(str(sources_path.resolve())):
                raise WorkspaceNotFoundError(
                    "Path traversal attempt in source file",
                    context={"filename": filename},
                )

            # Ensure directory exists
            sources_path.mkdir(parents=True, exist_ok=True)

            # Write asynchronously
            async with aiofiles.open(file_path, "w") as f:
                await f.write(content)

            local_path = f"/storage/{email_slug}/{slug}/raw_sources/{filename}"
            logger.debug(f"Source saved: {file_path}")
            return local_path
        except WorkspaceNotFoundError:
            raise
        except Exception as e:
            raise WorkspaceNotFoundError(
                "Failed to save source document",
                context={
                    "path": str(file_path),
                    "error": str(e),
                },
            )

    async def load_source(
        self, email_slug: str, slug: str, source_id: str
    ) -> str:
        """Load raw markdown source document.

        Args:
            email_slug: Email as safe directory name
            slug: Workspace slug
            source_id: Source identifier (e.g., "src_0")

        Returns:
            Raw markdown content

        Raises:
            WorkspaceNotFoundError: If file not found or invalid
        """
        base_path = self._safe_path(email_slug, slug)
        sources_path = base_path / "raw_sources"
        file_path = sources_path / f"{source_id}.md"

        try:
            # Verify file path is within sources directory
            file_path_resolved = file_path.resolve()
            if not str(file_path_resolved).startswith(str(sources_path.resolve())):
                raise WorkspaceNotFoundError(
                    "Path traversal attempt in source file",
                    context={"source_id": source_id},
                )

            # Read asynchronously
            async with aiofiles.open(file_path, "r") as f:
                content = await f.read()

            logger.debug(f"Source loaded: {file_path}")
            return content
        except FileNotFoundError:
            raise WorkspaceNotFoundError(
                "Source document not found",
                context={"source_id": source_id},
            )
        except WorkspaceNotFoundError:
            raise
        except Exception as e:
            raise WorkspaceNotFoundError(
                "Failed to load source document",
                context={
                    "source_id": source_id,
                    "error": str(e),
                },
            )

    async def list_workspaces(
        self, email_slug: str
    ) -> list[WorkspaceListItem]:
        """List all workspaces for a user.

        Scans {STORAGE_ROOT}/{email_slug}/ for directories containing
        dashboard_payload.json and returns sorted by generated_at descending.

        Args:
            email_slug: Email as safe directory name

        Returns:
            List of WorkspaceListItem sorted by recency

        Raises:
            WorkspaceNotFoundError: On scan failure
        """
        user_path = self._safe_path(email_slug, "")
        user_path = user_path.parent / email_slug  # Remove the trailing component

        try:
            workspaces = []

            # Scan user directory
            if not user_path.exists():
                return []

            for workspace_dir in user_path.iterdir():
                if not workspace_dir.is_dir():
                    continue

                payload_file = workspace_dir / "dashboard_payload.json"
                if not payload_file.exists():
                    continue

                try:
                    # Read payload to get metadata
                    async with aiofiles.open(payload_file, "r") as f:
                        content = await f.read()

                    payload = DashboardPayload.model_validate_json(content)
                    workspace = WorkspaceListItem(
                        slug=workspace_dir.name,
                        topic=payload.topic_metadata.topic,
                        generated_at=payload.topic_metadata.generated_at.isoformat(),
                    )
                    workspaces.append(workspace)
                except Exception as e:
                    logger.warning(
                        f"Failed to read workspace {workspace_dir.name}: {e}"
                    )
                    continue

            # Sort by generated_at descending (most recent first)
            workspaces.sort(
                key=lambda w: w.generated_at, reverse=True
            )
            logger.info(f"Listed {len(workspaces)} workspaces for {email_slug}")
            return workspaces
        except Exception as e:
            raise WorkspaceNotFoundError(
                "Failed to list workspaces",
                context={"email_slug": email_slug, "error": str(e)},
            )

    async def delete_workspace(
        self, email_slug: str, slug: str
    ) -> None:
        """Delete entire workspace directory tree.

        Args:
            email_slug: Email as safe directory name
            slug: Workspace slug

        Raises:
            WorkspaceNotFoundError: If workspace not found or delete fails
        """
        import asyncio

        base_path = self._safe_path(email_slug, slug)

        try:
            if not base_path.exists():
                raise WorkspaceNotFoundError(
                    "Workspace not found",
                    context={"path": str(base_path)},
                )

            # Delete asynchronously via thread executor
            def sync_delete():
                shutil.rmtree(base_path)

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, sync_delete)

            logger.info(f"Workspace deleted: {base_path}")
        except WorkspaceNotFoundError:
            raise
        except Exception as e:
            raise WorkspaceNotFoundError(
                "Failed to delete workspace",
                context={
                    "path": str(base_path),
                    "error": str(e),
                },
            )


# Module singleton
workspace_repo = WorkspaceRepository(Settings())


def get_workspace_repo() -> WorkspaceRepository:
    """FastAPI dependency for workspace repository.

    Returns:
        Module-level WorkspaceRepository instance
    """
    return workspace_repo
