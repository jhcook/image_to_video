"""Common exception types for the video_gen package."""

class InsufficientCreditsError(RuntimeError):
    """Raised when a provider indicates the account does not have enough credits.

    This should be treated as a non-retryable, user-actionable error.
    """

    def __init__(self, message: str = "Insufficient credits", provider: str | None = None):
        self.provider = provider
        super().__init__(message)
