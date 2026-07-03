"""Deterministic demo data used by the read-only diagnostic API.

The records are fictional and intentionally contain no personal information.
"""

ORDERS = {
    "ORD-20260702-1001": {
        "order_id": "ORD-20260702-1001",
        "tenant_id": "tenant-demo-a",
        "status": "PENDING_PAYMENT_CONFIRMATION",
        "amount": 29900,
        "currency": "CNY",
        "updated_at": "2026-07-02T10:02:18+08:00",
        "trace_id": "trace-pay-7f31a9",
        "channel_transaction_id": "wx-demo-900001",
    },
    "ORD-20260702-1002": {
        "order_id": "ORD-20260702-1002",
        "tenant_id": "tenant-demo-a",
        "status": "FULFILLED",
        "amount": 8800,
        "currency": "CNY",
        "updated_at": "2026-07-02T09:21:05+08:00",
        "trace_id": "trace-ok-8402c1",
        "channel_transaction_id": "ali-demo-900002",
    },
    "ORD-20260702-1003": {
        "order_id": "ORD-20260702-1003",
        "tenant_id": "tenant-demo-b",
        "status": "MANUAL_REVIEW",
        "amount": 16800,
        "currency": "CNY",
        "updated_at": "2026-07-02T11:43:09+08:00",
        "trace_id": "trace-review-92bc11",
        "channel_transaction_id": "wx-demo-900003",
    },
}

PAYMENT_CALLBACKS = {
    "wx-demo-900001": {
        "channel_transaction_id": "wx-demo-900001",
        "received": True,
        "signature_valid": True,
        "deduplicated": False,
        "amount": 29900,
        "currency": "CNY",
        "received_at": "2026-07-02T10:02:14+08:00",
    },
    "ali-demo-900002": {
        "channel_transaction_id": "ali-demo-900002",
        "received": True,
        "signature_valid": True,
        "deduplicated": False,
        "amount": 8800,
        "currency": "CNY",
        "received_at": "2026-07-02T09:20:41+08:00",
    },
    "wx-demo-900003": {
        "channel_transaction_id": "wx-demo-900003",
        "received": True,
        "signature_valid": True,
        "deduplicated": False,
        "amount": 16600,
        "currency": "CNY",
        "received_at": "2026-07-02T11:42:55+08:00",
    },
}

EVENT_TRACES = {
    "trace-pay-7f31a9": {
        "trace_id": "trace-pay-7f31a9",
        "event_name": "payment.confirmed.v2",
        "published": True,
        "published_at": "2026-07-02T10:02:15+08:00",
        "consumer": "order-payment-consumer",
        "consumer_status": "RETRYING",
        "retry_count": 3,
        "last_error_code": "ORDER_DB_TIMEOUT",
    },
    "trace-ok-8402c1": {
        "trace_id": "trace-ok-8402c1",
        "event_name": "payment.confirmed.v2",
        "published": True,
        "published_at": "2026-07-02T09:20:42+08:00",
        "consumer": "order-payment-consumer",
        "consumer_status": "SUCCEEDED",
        "retry_count": 0,
        "last_error_code": None,
    },
    "trace-review-92bc11": {
        "trace_id": "trace-review-92bc11",
        "event_name": "payment.confirmed.v2",
        "published": False,
        "published_at": None,
        "consumer": "order-payment-consumer",
        "consumer_status": "NOT_STARTED",
        "retry_count": 0,
        "last_error_code": "AMOUNT_MISMATCH",
    },
}

