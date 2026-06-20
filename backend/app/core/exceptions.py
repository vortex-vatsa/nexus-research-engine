"""Custom exception hierarchy for Nexus."""


class NexusBaseError(Exception):
    """Base exception for all Nexus errors."""

    def __init__(self, message: str, context: dict | None = None):
        """Initialize exception with message and optional context.

        Args:
            message: Error message
            context: Dictionary with additional error context
        """
        super().__init__(message)
        self.context = context or {}


class SearchClientError(NexusBaseError):
    """Raised when Tavily search fails."""

    pass


class ResearchAgentError(NexusBaseError):
    """Raised when research agent fails."""

    pass


class SynthesizerError(NexusBaseError):
    """Raised when synthesizer agent fails."""

    pass


class VectorStoreError(NexusBaseError):
    """Raised when vector store operations fail."""

    pass


class NotebookError(NexusBaseError):
    """Raised when notebook service fails."""

    pass


class WorkspaceNotFoundError(NexusBaseError):
    """Raised when workspace cannot be found or accessed."""

    pass


class AuthError(NexusBaseError):
    """Raised when authentication fails."""

    pass
