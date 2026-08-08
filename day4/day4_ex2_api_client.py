import logging
import time
import json
from typing import Any, Callable, TypeVar
from functools import wraps

log = logging.getLogger(__name__)
T = TypeVar('T')


# ============== TASK 1: Custom exception hierarchy ==============
class FDEBaseError(Exception):
    """Base for all TechStar FDE pipeline errors."""

    def __init__(self, message: str, context: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.context = context or {}

    def __str__(self) -> str:
        if self.context:
            ctx = ', '.join(f'{k}={v!r}' for k, v in self.context.items())
            return f'{self.message} | {ctx}'
        return self.message


class APIClientError(FDEBaseError):
    """HTTP error from an external API call."""

    def __init__(self, url: str, status_code: int, message: str) -> None:
        super().__init__(
            f'HTTP {status_code}: {message}',
            context={'url': url, 'status_code': status_code},
        )
        self.status_code = status_code
        self.url = url


class RateLimitError(APIClientError):
    """HTTP 429: API rate limit exceeded."""

    def __init__(self, url: str, retry_after: int = 60) -> None:
        super().__init__(url, 429, f'Rate limited — retry after {retry_after}s')
        self.retry_after = retry_after


class DataParseError(FDEBaseError):
    """Response body could not be parsed as expected schema."""

    def __init__(self, url: str, raw_response: str, reason: str) -> None:
        super().__init__(
            f'Parse error: {reason}',
            context={'url': url, 'response_preview': raw_response[:100]},
        )
        self.url = url
        self.raw_response = raw_response


# ============== TASK 2: Retry decorator with exponential backoff ==============
def retry(
    max_attempts: int = 3,
    backoff: float = 2.0,
    retriable_exceptions: tuple = (ConnectionError, TimeoutError, APIClientError),
) -> Callable:
    """
    Decorator: retry the wrapped function up to max_attempts times.
    Wait backoff^attempt seconds between retries (exponential backoff).
    Only retries on retriable_exceptions.
    Raises the last exception if all attempts fail.
    Does NOT retry on RateLimitError — caller should handle that separately.
    """

    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exc: Exception | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except RateLimitError as e:
                    # Don't retry rate limits — re-raise immediately
                    log.warning('Rate limited: %s', e)
                    raise
                except retriable_exceptions as e:
                    last_exc = e
                    wait = backoff ** attempt
                    log.warning(
                        'Attempt %d/%d failed: %s. Retrying in %.1fs',
                        attempt, max_attempts, e, wait,
                    )
                    if attempt < max_attempts:
                        time.sleep(wait)
            log.error('All %d attempts exhausted', max_attempts)
            raise last_exc  # type: ignore[misc]
        return wrapper
    return decorator
