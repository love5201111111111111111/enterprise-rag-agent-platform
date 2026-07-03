import json
import logging
import os
import secrets
import time
import uuid
from collections import defaultdict, deque
from typing import Annotated, Any

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

from app.data import EVENT_TRACES, ORDERS, PAYMENT_CALLBACKS


logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(message)s")
logger = logging.getLogger("cloudorder-ops-api")

API_KEY = os.getenv("CLOUDORDER_OPS_API_KEY", "")
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
_request_windows: dict[str, deque[float]] = defaultdict(deque)

app = FastAPI(
    title="CloudOrder Read-Only Operations API",
    version="1.0.0",
    description=(
        "Read-only diagnostic tools for the fictional CloudOrder platform. "
        "All records are synthetic. The API never modifies production state."
    ),
    docs_url="/docs",
    redoc_url=None,
)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class HealthResponse(StrictModel):
    status: str
    service: str
    version: str


class OrderResponse(StrictModel):
    order_id: str
    tenant_id: str
    status: str
    amount: int
    currency: str
    updated_at: str
    trace_id: str
    channel_transaction_id: str


class PaymentCallbackResponse(StrictModel):
    channel_transaction_id: str
    received: bool
    signature_valid: bool
    deduplicated: bool
    amount: int
    currency: str
    received_at: str


class EventTraceResponse(StrictModel):
    trace_id: str
    event_name: str
    published: bool
    published_at: str | None
    consumer: str
    consumer_status: str
    retry_count: int
    last_error_code: str | None


class DiagnosticResponse(StrictModel):
    order: OrderResponse
    payment_callback: PaymentCallbackResponse | None
    event_trace: EventTraceResponse | None
    findings: list[str]
    safe_next_steps: list[str]
    read_only: bool = True


def _require_api_key(
    x_cloudorder_api_key: Annotated[str | None, Header()] = None,
) -> None:
    if not API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API authentication is not configured",
        )
    if not x_cloudorder_api_key or not secrets.compare_digest(
        x_cloudorder_api_key, API_KEY
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )


def _not_found(entity: str, identifier: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"{entity} '{identifier}' was not found in the synthetic dataset",
    )


@app.middleware("http")
async def request_controls(request: Request, call_next):  # type: ignore[no-untyped-def]
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    client = request.client.host if request.client else "unknown"
    now = time.monotonic()
    window = _request_windows[client]
    while window and now - window[0] >= 60:
        window.popleft()
    if len(window) >= RATE_LIMIT_PER_MINUTE:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded", "request_id": request_id},
            headers={"X-Request-ID": request_id},
        )
    window.append(now)

    started = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - started) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    logger.info(
        json.dumps(
            {
                "event": "api_request",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": duration_ms,
                "client": client,
            },
            ensure_ascii=False,
        )
    )
    return response


@app.get(
    "/health",
    response_model=HealthResponse,
    operation_id="getHealth",
    tags=["system"],
)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="cloudorder-ops-api", version="1.0.0")


@app.get(
    "/v1/orders/{order_id}",
    response_model=OrderResponse,
    operation_id="getOrder",
    tags=["diagnostics"],
    dependencies=[Depends(_require_api_key)],
    summary="Read an order's current state",
)
def get_order(order_id: str) -> OrderResponse:
    """Return synthetic order state. This operation is read-only."""
    order = ORDERS.get(order_id)
    if not order:
        raise _not_found("Order", order_id)
    return OrderResponse.model_validate(order)


@app.get(
    "/v1/payment-callbacks/{channel_transaction_id}",
    response_model=PaymentCallbackResponse,
    operation_id="getPaymentCallback",
    tags=["diagnostics"],
    dependencies=[Depends(_require_api_key)],
    summary="Read payment callback verification state",
)
def get_payment_callback(channel_transaction_id: str) -> PaymentCallbackResponse:
    """Return callback receipt, signature and deduplication facts."""
    callback = PAYMENT_CALLBACKS.get(channel_transaction_id)
    if not callback:
        raise _not_found("Payment callback", channel_transaction_id)
    return PaymentCallbackResponse.model_validate(callback)


@app.get(
    "/v1/event-traces/{trace_id}",
    response_model=EventTraceResponse,
    operation_id="getEventTrace",
    tags=["diagnostics"],
    dependencies=[Depends(_require_api_key)],
    summary="Trace a payment event through its consumer",
)
def get_event_trace(trace_id: str) -> EventTraceResponse:
    """Return synthetic event publication and consumer status."""
    trace = EVENT_TRACES.get(trace_id)
    if not trace:
        raise _not_found("Event trace", trace_id)
    return EventTraceResponse.model_validate(trace)


@app.get(
    "/v1/diagnostics/orders/{order_id}",
    response_model=DiagnosticResponse,
    operation_id="diagnoseOrder",
    tags=["diagnostics"],
    dependencies=[Depends(_require_api_key)],
    summary="Run a read-only order and payment diagnostic",
)
def diagnose_order(order_id: str) -> DiagnosticResponse:
    """Combine order, callback and event facts into a safe read-only diagnosis."""
    order_data = ORDERS.get(order_id)
    if not order_data:
        raise _not_found("Order", order_id)

    order = OrderResponse.model_validate(order_data)
    callback_data = PAYMENT_CALLBACKS.get(order.channel_transaction_id)
    trace_data = EVENT_TRACES.get(order.trace_id)
    callback = (
        PaymentCallbackResponse.model_validate(callback_data) if callback_data else None
    )
    trace = EventTraceResponse.model_validate(trace_data) if trace_data else None

    findings: list[str] = []
    next_steps: list[str] = []
    if callback is None:
        findings.append("No payment callback record was found")
        next_steps.append("Ask the payment channel to safely resend the callback")
    elif not callback.signature_valid:
        findings.append("The payment callback signature is invalid")
        next_steps.append("Escalate to payment security; do not publish a payment event")
    elif callback.amount != order.amount or callback.currency != order.currency:
        findings.append("Payment amount or currency does not match the order")
        next_steps.append("Keep the order in manual review; do not force it to PAID")
    elif trace is None or not trace.published:
        findings.append("The verified callback did not produce a payment event")
        next_steps.append("Escalate for an audited event replay with dual review")
    elif trace.consumer_status == "RETRYING":
        findings.append(
            f"The payment event is published but the consumer is retrying: {trace.last_error_code}"
        )
        next_steps.append("Check consumer logs and dependency health using read-only access")
    elif trace.consumer_status == "SUCCEEDED":
        findings.append("The payment event was consumed successfully")
        next_steps.append("Verify order projection and fulfillment consistency")
    else:
        findings.append(f"Event consumer state is {trace.consumer_status}")
        next_steps.append("Escalate to L2 support for read-only investigation")

    return DiagnosticResponse(
        order=order,
        payment_callback=callback,
        event_trace=trace,
        findings=findings,
        safe_next_steps=next_steps,
    )

