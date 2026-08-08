import json
import logging
import time
from functools import wraps
from typing import Callable, TypeVar, ParamSpec

log = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R")


class APIClientError(Exception):
    pass


class RateLimitError(APIClientError):
    pass


class DataParseError(APIClientError):
    def __init__(self, url: str, body: str, message: str):
        super().__init__(f"Parse error: {message} | url='{url}'")
        self.url = url
        self.body = body
        self.message = message


def retry(
    max_attempts: int = 3,
    backoff: float = 2.0,
    retriable_exceptions: tuple[type[Exception], ...] = (
        ConnectionError,
        TimeoutError,
        APIClientError,
    ),
):
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)

                except retriable_exceptions as exc:
                    if attempt == max_attempts:
                        raise

                    wait_time = backoff ** attempt

                    log.warning(
                        "Attempt %d/%d failed: %s. Retrying in %.1fs",
                        attempt,
                        max_attempts,
                        exc,
                        wait_time,
                    )

                    time.sleep(wait_time)

            raise RuntimeError("Unexpected retry failure")

        return wrapper

    return decorator


class CarrierAPIClient:
    """
    HTTP client for the carrier tracking API.

    Supports context manager usage:
        with CarrierAPIClient(base_url, api_key) as client:
            data = client.get_shipments('2024-01-20')
    """

    BASE_TIMEOUT = 30

    def __init__(self, base_url: str, api_key: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._session_open = False
        self._request_count = 0

    def __enter__(self) -> "CarrierAPIClient":
        self._session_open = True
        log.info(
            "CarrierAPIClient session opened: %s",
            self.base_url,
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self._session_open = False

        log.info(
            "CarrierAPIClient session closed. Requests made: %d",
            self._request_count,
        )

        if exc_type is not None:
            log.error(
                "Session closed due to exception: %s",
                exc_val,
            )

    def _check_session(self) -> None:
        """Raise RuntimeError if called outside a with block."""
        if not self._session_open:
            raise RuntimeError(
                "CarrierAPIClient must be used as a context manager"
            )

    def _parse_response(self, url: str, body: str) -> dict:
        """Parse JSON response body. Raise DataParseError on failure."""
        try:
            return json.loads(body)

        except json.JSONDecodeError as exc:
            raise DataParseError(
                url,
                body,
                str(exc),
            ) from exc

    def _handle_status(
        self,
        url: str,
        status_code: int,
        body: str,
    ) -> dict:
        """
        Route HTTP status codes to exceptions or return parsed body.

        200 -> success
        429 -> RateLimitError
        5xx -> APIClientError
        4xx -> ValueError
        """

        if status_code == 200:
            return self._parse_response(url, body)

        if status_code == 429:
            raise RateLimitError("Rate limit exceeded")

        if 500 <= status_code < 600:
            raise APIClientError(
                f"Server error ({status_code})"
            )

        if 400 <= status_code < 500:
            raise ValueError(
                f"Client error ({status_code})"
            )

        raise APIClientError(
            f"Unexpected status code ({status_code})"
        )

    @retry(
        max_attempts=3,
        backoff=2.0,
        retriable_exceptions=(
            ConnectionError,
            TimeoutError,
            APIClientError,
        ),
    )
    def get_shipments(self, date: str) -> list[dict]:
        self._check_session()

        url = f"{self.base_url}/v1/shipments?date={date}"

        log.debug("GET %s", url)

        status_code, body = self._simulate_http(url)

        self._request_count += 1      # <-- MOVE HERE

        return self._handle_status(
        url,
        status_code,
        body,
    ).get("shipments", [])
    _call_count = 0

    def _simulate_http(self, url: str) -> tuple[int, str]:
        """
        Simulates unreliable HTTP:
        fails first 2 calls, then succeeds.
        """

        CarrierAPIClient._call_count += 1

        if CarrierAPIClient._call_count <= 2:
            raise ConnectionError(
                f"Simulated network failure "
                f"#{CarrierAPIClient._call_count}"
            )

        return (
            200,
            json.dumps(
                {
                    "shipments": [
                        {
                            "id": "SH-001",
                            "carrier": "DHL",
                            "status": "in_transit",
                            "delay": 2,
                        },
                        {
                            "id": "SH-002",
                            "carrier": "FedEx",
                            "status": "delivered",
                            "delay": 0,
                        },
                    ]
                }
            ),
        )


if __name__ == "__main__":
    logging.basicConfig(
       level=logging.INFO,
        format="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    with CarrierAPIClient(
        base_url="https://api.carrier-platform.in",
        api_key="secret-key-123",
    ) as client:

        shipments = client.get_shipments("2024-01-20")

        print(f"Retrieved {len(shipments)} shipments:")

        for shipment in shipments:
            print(shipment)

    try:
        client.get_shipments("2024-01-20")
    except RuntimeError as exc:
        print(f"Expected RuntimeError: {exc}")

    try:
        client._session_open = True

        client._parse_response(
            "http://test",
            "not valid json []'",
        )

    except DataParseError as exc:
        print(f"Expected DataParseError: {exc}")

    finally:
        client._session_open = False