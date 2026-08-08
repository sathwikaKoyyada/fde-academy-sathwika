import json
import pytest
from unittest.mock import patch

from pydantic import BaseModel, Field, ValidationError

from day5_ex2_logistics_client import (
    LogisticsAPIClient,
    APIClientError,
)


class ShipmentSchema(BaseModel):
    """The contract: what a valid shipment response MUST look like."""

    shipment_id: str = Field(..., min_length=3)
    carrier: str
    status: str
    delay_days: int = Field(..., ge=0)


@pytest.fixture
def client() -> LogisticsAPIClient:
    return LogisticsAPIClient(
        base_url="https://api.carrier-platform.in",
        api_key="valid-test-key-123",
    )


@patch("day5_ex2_logistics_client.mock_http_get")
def test_get_shipment_success_returns_valid_schema(mock_get, client):
    mock_get.return_value = (
        200,
        json.dumps(
            {
                "shipment_id": "SH-100",
                "carrier": "FedEx",
                "status": "delivered",
                "delay_days": 0,
            }
        ),
    )
    result = client.get_shipment("SH-100")
    assert result["shipment_id"] == "SH-100"
    validated = ShipmentSchema.model_validate(result)
    assert validated.carrier == "FedEx"
    assert mock_get.call_count == 1


def test_shipment_schema_rejects_missing_field():
    incomplete = {"carrier": "DHL", "status": "in_transit", "delay_days": 1}
    with pytest.raises(ValidationError):
        ShipmentSchema.model_validate(incomplete)


@patch("day5_ex2_logistics_client.time.sleep")
@patch("day5_ex2_logistics_client.mock_http_get")
def test_retries_on_500_then_succeeds(mock_get, mock_sleep, client):
    mock_get.side_effect = [
        (500, json.dumps({"error": "Internal error"})),
        (
            200,
            json.dumps(
                {
                    "shipment_id": "SH-200",
                    "carrier": "DHL",
                    "status": "in_transit",
                    "delay_days": 0,
                }
            ),
        ),
    ]
    result = client.get_shipment("SH-200")
    assert result["shipment_id"] == "SH-200"
    assert mock_get.call_count == 2
    assert mock_sleep.called


@patch("day5_ex2_logistics_client.time.sleep")
@patch("day5_ex2_logistics_client.mock_http_get")
def test_rate_limit_retries_after_wait(mock_get, mock_sleep, client):
    mock_get.side_effect = [
        (429, json.dumps({"error": "Rate limited", "retry_after": 3})),
        (
            200,
            json.dumps(
                {
                    "shipment_id": "SH-300",
                    "carrier": "BlueDart",
                    "status": "delivered",
                    "delay_days": 0,
                }
            ),
        ),
    ]
    result = client.get_shipment("SH-300")
    assert result["shipment_id"] == "SH-300"
    mock_sleep.assert_called_once_with(3)


@patch("day5_ex2_logistics_client.mock_http_get")
def test_invalid_api_key_fails_without_retry(mock_get, client):
    mock_get.return_value = (401, json.dumps({"error": "Invalid API key"}))
    with pytest.raises(APIClientError):
        client.get_shipment("SH-400")
    assert mock_get.call_count == 1


@pytest.mark.parametrize("status_code", [500, 502, 503, 504])
@patch("day5_ex2_logistics_client.time.sleep")
@patch("day5_ex2_logistics_client.mock_http_get")
def test_all_5xx_codes_are_retriable(mock_get, mock_sleep, status_code, client):
    mock_get.side_effect = [
        (status_code, json.dumps({"error": "Server error"})),
        (
            200,
            json.dumps(
                {
                    "shipment_id": "SH-500",
                    "carrier": "DHL",
                    "status": "pending",
                    "delay_days": 0,
                }
            ),
        ),
    ]
    result = client.get_shipment("SH-500")
    assert result["shipment_id"] == "SH-500"
    assert mock_get.call_count == 2
