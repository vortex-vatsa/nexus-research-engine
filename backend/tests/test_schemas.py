"""Tests for Pydantic schema models."""

from datetime import datetime

import pytest

from app.core.schemas import (
    AuthUser,
    ChartStyle,
    ComponentType,
    DashboardPayload,
    DocumentSource,
    DownloadedImage,
    ExtensivenesLevel,
    FormatPreference,
    JobStatus,
    MatrixComponent,
    NotebookQuery,
    NotebookResponse,
    ResearchJobStatus,
    ResearchRequest,
    RetrievedChunk,
    TopicMetadata,
    WorkspaceListItem,
)


def test_all_models_imported():
    """Verify all 17 types can be imported."""
    assert ComponentType is not None
    assert ChartStyle is not None
    assert ExtensivenesLevel is not None
    assert FormatPreference is not None
    assert JobStatus is not None
    assert TopicMetadata is not None
    assert MatrixComponent is not None
    assert DownloadedImage is not None
    assert DocumentSource is not None
    assert DashboardPayload is not None
    assert ResearchRequest is not None
    assert ResearchJobStatus is not None
    assert NotebookQuery is not None
    assert RetrievedChunk is not None
    assert NotebookResponse is not None
    assert WorkspaceListItem is not None
    assert AuthUser is not None


def test_component_type_enum():
    """Verify ComponentType has exactly TABLE, CHART, LIST."""
    assert len(ComponentType) == 3
    assert ComponentType.TABLE.value == "table"
    assert ComponentType.CHART.value == "chart"
    assert ComponentType.LIST.value == "list"


def test_chart_style_enum():
    """Verify ChartStyle enum."""
    assert ChartStyle.BAR.value == "bar"
    assert ChartStyle.LINE.value == "line"
    assert ChartStyle.PIE.value == "pie"


def test_extensiveness_level_enum():
    """Verify ExtensivenesLevel enum."""
    assert ExtensivenesLevel.QUICK.value == "quick"
    assert ExtensivenesLevel.DEEP.value == "deep"


def test_format_preference_enum():
    """Verify FormatPreference enum."""
    assert FormatPreference.TIMELINE.value == "timeline"
    assert FormatPreference.SWOT.value == "swot"
    assert FormatPreference.PROS_CONS.value == "pros_cons"
    assert FormatPreference.COMPARISON.value == "comparison"


def test_job_status_enum():
    """Verify JobStatus has exactly PENDING, RUNNING, COMPLETE, FAILED."""
    assert len(JobStatus) == 4
    assert JobStatus.PENDING.value == "pending"
    assert JobStatus.RUNNING.value == "running"
    assert JobStatus.COMPLETE.value == "complete"
    assert JobStatus.FAILED.value == "failed"


def test_research_request_validation():
    """Test ResearchRequest validation."""
    # Valid request
    req = ResearchRequest(
        topic="Artificial Intelligence",
        extensiveness=ExtensivenesLevel.QUICK,
        format_preference=FormatPreference.COMPARISON,
    )
    assert req.topic == "Artificial Intelligence"

    # Topic too short
    with pytest.raises(ValueError):
        ResearchRequest(
            topic="AI",
            extensiveness=ExtensivenesLevel.QUICK,
            format_preference=FormatPreference.COMPARISON,
        )

    # Topic too long
    with pytest.raises(ValueError):
        ResearchRequest(
            topic="a" * 501,
            extensiveness=ExtensivenesLevel.QUICK,
            format_preference=FormatPreference.COMPARISON,
        )


def test_notebook_query_validation():
    """Test NotebookQuery validation."""
    # Valid query
    query = NotebookQuery(workspace_slug="test", question="hello")
    assert query.question == "hello"

    # Empty question
    with pytest.raises(ValueError):
        NotebookQuery(workspace_slug="test", question="")


def test_notebook_query_and_response():
    """Test NotebookQuery and NotebookResponse creation."""
    query = NotebookQuery(workspace_slug="test", question="What is AI?")
    assert query.workspace_slug == "test"
    assert query.question == "What is AI?"

    chunk = RetrievedChunk(
        content="Artificial Intelligence is...",
        source_id="src1",
        url="http://example.com",
        chunk_index=0,
        distance=0.5,
    )
    response = NotebookResponse(
        answer="AI is intelligence demonstrated by machines.",
        sources=[chunk],
        confidence_score=0.8,
        needs_web_search=False,
    )
    assert response.confidence_score == 0.8
    assert len(response.sources) == 1


def test_retrieved_chunk():
    """Test RetrievedChunk creation."""
    chunk = RetrievedChunk(
        content="test content",
        source_id="s1",
        url="http://x.com",
        chunk_index=0,
        distance=0.5,
    )
    assert chunk.content == "test content"
    assert chunk.distance == 0.5


def test_workspace_list_item():
    """Test WorkspaceListItem creation."""
    item = WorkspaceListItem(
        slug="test",
        topic="Test Topic",
        generated_at="2024-01-01T00:00:00",
    )
    assert item.slug == "test"
    assert item.topic == "Test Topic"


def test_auth_user():
    """Test AuthUser creation."""
    user = AuthUser(
        google_id="123",
        email="user@gmail.com",
        name="User",
        avatar_url="http://example.com/avatar.jpg",
    )
    assert user.email == "user@gmail.com"
    assert user.google_id == "123"


def test_downloaded_image():
    """Test DownloadedImage creation."""
    img = DownloadedImage(alt="Sample image", local_url="/path/to/image.jpg")
    assert img.alt == "Sample image"
    assert img.local_url == "/path/to/image.jpg"


def test_document_source():
    """Test DocumentSource creation."""
    doc = DocumentSource(
        id="doc1",
        title="Example Article",
        url="https://example.com/article",
        local_path="/storage/doc1.md",
        snippet="This is an excerpt...",
        downloaded_images=[],
    )
    assert doc.id == "doc1"
    assert doc.title == "Example Article"
    assert len(doc.downloaded_images) == 0


def test_matrix_component():
    """Test MatrixComponent creation."""
    comp = MatrixComponent(
        section_title="Key Findings",
        component_type=ComponentType.TABLE,
        headers=["Finding", "Impact"],
        rows=[["AI Growth", "High"]],
        description="Summary of findings",
    )
    assert comp.section_title == "Key Findings"
    assert comp.component_type == ComponentType.TABLE
    assert len(comp.headers) == 2


def test_topic_metadata():
    """Test TopicMetadata creation."""
    now = datetime.utcnow()
    metadata = TopicMetadata(
        topic="AI in Healthcare",
        extensiveness="deep",
        format_preference="comparison",
        generated_at=now,
    )
    assert metadata.topic == "AI in Healthcare"
    assert metadata.schema_version == "1.0"


def test_dashboard_payload_round_trip():
    """Test complete DashboardPayload serialization/deserialization."""
    now = datetime.utcnow()

    payload = DashboardPayload(
        topic_metadata=TopicMetadata(
            topic="Test Topic",
            extensiveness="quick",
            format_preference="timeline",
            generated_at=now,
        ),
        executive_summary="This is a summary of findings.",
        matrix_data=[
            MatrixComponent(
                section_title="Overview",
                component_type=ComponentType.LIST,
                rows=[["Key Point 1"], ["Key Point 2"]],
            )
        ],
        document_library=[
            DocumentSource(
                id="src1",
                title="Source Article",
                url="https://example.com",
                local_path="/storage/src1.md",
                snippet="Article content...",
            )
        ],
    )

    # Serialize to dict
    payload_dict = payload.model_dump()
    assert isinstance(payload_dict, dict)

    # Serialize to JSON and back
    json_str = payload.model_dump_json()
    assert isinstance(json_str, str)

    # Deserialize from dict
    payload_from_dict = DashboardPayload(**payload_dict)
    assert payload_from_dict.topic_metadata.topic == "Test Topic"
    assert len(payload_from_dict.matrix_data) == 1
    assert len(payload_from_dict.document_library) == 1


def test_dashboard_payload_schema_version():
    """Test DashboardPayload.get_schema_version() returns "1.0"."""
    assert DashboardPayload.get_schema_version() == "1.0"


def test_research_job_status():
    """Test ResearchJobStatus creation."""
    now = datetime.utcnow()
    status = ResearchJobStatus(
        job_id="job-123",
        status=JobStatus.RUNNING,
        progress_message="Generating search queries...",
        created_at=now,
        updated_at=now,
    )
    assert status.job_id == "job-123"
    assert status.status == JobStatus.RUNNING
    assert status.workspace_slug is None
    assert status.error is None
