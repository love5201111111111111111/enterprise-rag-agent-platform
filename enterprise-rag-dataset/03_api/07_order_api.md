#ONYX_METADATA={"link":"https://developer.nebula.example/orders/v2","primary_owners":["trade@nebula.example"],"doc_updated_at":"2026-06-24T16:00:00+08:00","department":"api","status":"active","version":"2.3"}
# 订单 API v2

## 创建订单

`POST /api/v2/orders`

必填头：`Authorization`、`X-Tenant-ID`、`X-Request-ID`、`Idempotency-Key`。幂等键长度 16 至 64 字符，在同一租户内保留 24 小时。相同幂等键和相同请求体会返回首次结果；相同键但不同请求体返回 HTTP 409 与 `ORDER_009`。

请求体主要字段：`external_order_no`、`currency`、`items[]`、`shipping_address`。金额使用最小货币单位整数表示，例如人民币 1050 表示 10.50 元。

成功返回 HTTP 201。库存处理是异步的，因此初始状态通常为 `PENDING_INVENTORY`。

## 查询订单

`GET /api/v2/orders/{order_id}` 返回订单状态、金额、商品和履约摘要。客户端轮询频率不得高于每个订单每 2 秒一次，推荐订阅 Webhook。

## 取消订单

`POST /api/v2/orders/{order_id}/cancel` 仅允许 `PENDING_INVENTORY` 或 `AWAITING_PAYMENT` 状态。已支付订单必须走退款流程，不能直接取消。

