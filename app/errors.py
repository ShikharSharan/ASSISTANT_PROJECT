class AssistantDataError(Exception):
    """Base error for task and money persistence issues."""


class ValidationError(AssistantDataError):
    """Raised when user data is incomplete or invalid."""


class RecordNotFoundError(AssistantDataError):
    """Raised when an expected task or money entry is missing."""
