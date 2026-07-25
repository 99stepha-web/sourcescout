"""
SourceScout Affiliate Exceptions

Custom exceptions used throughout the affiliate integration layer.
"""


class AffiliateError(Exception):
    """
    Base exception for all affiliate-related errors.
    """

    pass


class NetworkError(AffiliateError):
    """
    Raised when an HTTP request fails due to network problems.
    """

    pass


class AuthenticationError(AffiliateError):
    """
    Raised when API authentication fails.
    Examples:
        - Invalid App Key
        - Invalid Secret Key
        - Invalid Signature
    """

    pass


class APIError(AffiliateError):
    """
    Raised when the affiliate API returns a business-level error.
    """

    def __init__(self, status: str, message: str):
        self.status = status
        self.message = message
        super().__init__(f"[{status}] {message}")


class RateLimitError(APIError):
    """
    Raised when the API rate limit has been exceeded.
    """

    pass


class InvalidResponseError(AffiliateError):
    """
    Raised when the API response cannot be parsed
    or is missing required fields.
    """

    pass
