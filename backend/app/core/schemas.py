"""Pydantic V2 models for data validation and schema contract."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ComponentType(str, Enum):
    """Types of dashboard matrix components."""

    TABLE = "table"
    CHART = "chart"
    LIST = "list"


class ChartStyle(str, Enum):
    """Chart visualization styles."""

    BAR = "bar"
    LINE = "line"
    PIE = "pie"


class ExtensivenesLevel(str, Enum):
    """Research depth levels."""

    QUICK = "quick"
    DEEP = "deep"


class FormatPreference(str, Enum):
    """Dashboard layout format preferences."""

    TIMELINE = "timeline"
    SWOT = "swot"
    PROS_CONS = "pros_cons"
    COMPARISON = "comparison"


class JobStatus(str, Enum):
    """Research job status states."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"


class TopicMetadata(BaseModel):
    """Metadata about the research topic and generation."""

    topic: str = Field(..., description="The research topic")
    extensiveness: str = Field(..., description="Research depth level")
    format_preference: str = Field(
        ..., description="Dashboard layout format"
    )
    generated_at: datetime = Field(
        ..., description="Timestamp when payload was generated"
    )
    schema_version: str = Field(
        default="1.0", description="Schema version for compatibility"
    )


class MatrixComponent(BaseModel):
    """Single component in the dashboard data matrix."""

    section_title: str = Field(..., description="Title of this component")
    component_type: ComponentType = Field(
        ..., description="Type of component: table, chart, or list"
    )
    headers: list[str] | None = Field(
        default=None,
        description="Column headers for table components",
    )
    rows: list[list[str]] | None = Field(
        default=None,
        description="Row data for table components",
    )
    chart_style: ChartStyle | None = Field(
        default=None,
        description="Chart type for chart components",
    )
    data: list[dict[str, Any]] | None = Field(
        default=None,
        description="Data points for chart components",
    )
    description: str | None = Field(
        default=None,
        description="Additional description or notes",
    )


class DownloadedImage(BaseModel):
    """Image metadata for downloaded assets."""

    alt: str = Field(..., description="Alt text for image")
    local_url: str = Field(..., description="Local path or URL to image")


class DocumentSource(BaseModel):
    """Source document or article reference."""

    id: str = Field(..., description="Unique source identifier")
    title: str = Field(..., description="Source title")
    url: str = Field(..., description="Original URL")
    local_path: str = Field(..., description="Local storage path")
    snippet: str = Field(..., description="Text excerpt from source")
    downloaded_images: list[DownloadedImage] = Field(
        default_factory=list,
        description="Associated images",
    )


class DashboardPayload(BaseModel):
    """Complete research dashboard payload — contract between backend and frontend."""

    topic_metadata: TopicMetadata = Field(
        ..., description="Research topic and generation metadata"
    )
    executive_summary: str = Field(
        ..., description="High-level synthesis of findings"
    )
    matrix_data: list[MatrixComponent] = Field(
        ..., description="Structured data components"
    )
    document_library: list[DocumentSource] = Field(
        ..., description="Source documents"
    )

    @classmethod
    def get_schema_version(cls) -> str:
        """Get the schema version for frontend compatibility checking."""
        return "1.0"


class ResearchRequest(BaseModel):
    """Request to initiate a research job."""

    topic: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Research topic or question",
    )
    extensiveness: ExtensivenesLevel = Field(
        ..., description="Research depth level"
    )
    format_preference: FormatPreference = Field(
        ..., description="Dashboard layout format"
    )


class ResearchJobStatus(BaseModel):
    """Status and progress of a research job."""

    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatus = Field(..., description="Current job status")
    progress_message: str = Field(..., description="Human-readable progress update")
    workspace_slug: str | None = Field(
        default=None,
        description="Slug of generated workspace on completion",
    )
    error: str | None = Field(
        default=None,
        description="Error message if job failed",
    )
    created_at: datetime = Field(..., description="Job creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class NotebookQuery(BaseModel):
    """Query for notebook RAG Q&A service."""

    workspace_slug: str = Field(..., description="Workspace to query")
    question: str = Field(
        ...,
        min_length=1,
        description="Question to answer",
    )


class RetrievedChunk(BaseModel):
    """Text chunk retrieved from vector store."""

    content: str = Field(..., description="Text content")
    source_id: str = Field(..., description="ID of source document")
    url: str = Field(..., description="Source document URL")
    chunk_index: int = Field(..., description="Index of chunk within document")
    distance: float = Field(..., description="Vector distance score")


class NotebookResponse(BaseModel):
    """Answer from notebook RAG service."""

    answer: str = Field(..., description="Generated answer to question")
    sources: list[RetrievedChunk] = Field(
        ..., description="Retrieved supporting chunks"
    )
    confidence_score: float = Field(
        ..., description="Confidence in answer (0.0-1.0)"
    )
    needs_web_search: bool = Field(
        ...,
        description="Whether additional web search is recommended",
    )


class WorkspaceListItem(BaseModel):
    """Summary item for workspace list."""

    slug: str = Field(..., description="Workspace identifier slug")
    topic: str = Field(..., description="Research topic")
    generated_at: str = Field(..., description="Generation timestamp as ISO string")


class AuthUser(BaseModel):
    """Authenticated user from Google OAuth session."""

    google_id: str = Field(..., description="Google account ID")
    email: str = Field(..., description="User email address")
    name: str = Field(..., description="User display name")
    avatar_url: str = Field(..., description="URL to user profile picture")
