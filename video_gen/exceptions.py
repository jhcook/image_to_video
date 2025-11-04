"""
Custom exceptions for video generation.

Provides specific exception types for better error handling and debugging.
"""


class VideoGenerationError(Exception):
    """Base exception for video generation errors."""
    pass


class APIError(VideoGenerationError):
    """Base exception for API-related errors."""
    pass


class Veo3APIError(APIError):
    """Exception for Veo-3 API errors."""
    pass


class SoraAPIError(APIError):
    """Exception for Sora-2 API errors."""
    pass


class RunwayAPIError(APIError):
    """Exception for Runway API errors."""
    pass


class AuthenticationError(APIError):
    """Exception for authentication failures."""
    pass


class RateLimitError(APIError):
    """Exception for rate limiting errors."""
    pass


class VideoProcessingError(VideoGenerationError):
    """Exception for video processing errors."""
    pass


class ConfigurationError(VideoGenerationError):
    """Exception for configuration errors."""
    pass


class ValidationError(VideoGenerationError):
    """Exception for validation errors."""
    pass


class InsufficientCreditsError(APIError):
    """Exception for provider billing/credit exhaustion.

    Raised when a provider indicates the account does not have enough credits
    to perform the requested operation. Treat as non-retryable until user adds
    credits or switches provider/model.
    """
    def __init__(self, message: str = "Insufficient credits", provider: str | None = None):
        self.provider = provider
        super().__init__(message)
