import os

os.environ["CLOUDORDER_OPS_API_KEY"] = "test-key"

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)
HEADERS = {"X-CloudOrder-API-Key": "test-key"}


def test_health_does_not_require_auth() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_diagnostic_requires_auth() -> None:
    response = client.get("/v1/diagnostics/orders/ORD-20260702-1001")
    assert response.status_code == 401


def test_retrying_consumer_diagnosis() -> None:
    response = client.get(
        "/v1/diagnostics/orders/ORD-20260702-1001", headers=HEADERS
    )
    assert response.status_code == 200
    body = response.json()
    assert body["read_only"] is True
    assert body["event_trace"]["consumer_status"] == "RETRYING"
    assert any("retrying" in item for item in body["findings"])


def test_amount_mismatch_stays_in_manual_review() -> None:
    response = client.get(
        "/v1/diagnostics/orders/ORD-20260702-1003", headers=HEADERS
    )
    assert response.status_code == 200
    body = response.json()
    assert body["order"]["status"] == "MANUAL_REVIEW"
    assert any("does not match" in item for item in body["findings"])


def test_unknown_order_returns_404() -> None:
    response = client.get("/v1/orders/ORD-NOT-FOUND", headers=HEADERS)
    assert response.status_code == 404

