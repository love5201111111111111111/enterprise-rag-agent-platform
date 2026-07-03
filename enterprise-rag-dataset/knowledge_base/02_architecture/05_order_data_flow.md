#ONYX_METADATA={"link":"https://kb.nebula.example/architecture/order-flow","primary_owners":["trade@nebula.example"],"doc_updated_at":"2026-06-21T11:00:00+08:00","department":"architecture","status":"active","version":"2.0"}
# 订单创建与履约数据流

1. 客户端调用 `POST /api/v2/orders`，携带租户 Token 和 `Idempotency-Key`。
2. Gateway 校验 Token、租户限额并生成 `trace_id`。
3. Order Service 校验请求，将幂等键与请求摘要写入 Redis，并在 PostgreSQL 创建 `PENDING_INVENTORY` 订单。
4. Order Service 发布 `order.created.v2` 事件。
5. Inventory Service 预占库存，发布 `inventory.reserved.v1` 或 `inventory.rejected.v1`。
6. 成功时订单转为 `AWAITING_PAYMENT`；失败时转为 `CANCELLED` 并记录原因。
7. 支付渠道回调验签成功后，Payment Callback 发布 `payment.confirmed.v2`，订单转为 `PAID`。
8. Fulfillment Service 创建履约单，后续状态依次为 `PICKING`、`SHIPPED`、`COMPLETED`。

事件可能重复投递，所有消费者必须以 `event_id` 去重。事件在 Kafka 中至少保留 7 天。订单状态只能向允许的下一状态迁移；任何逆向修改必须走补偿流程。

