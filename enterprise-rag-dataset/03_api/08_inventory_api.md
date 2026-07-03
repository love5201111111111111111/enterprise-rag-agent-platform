#ONYX_METADATA={"link":"https://developer.nebula.example/inventory/v1","primary_owners":["fulfillment@nebula.example"],"doc_updated_at":"2026-06-16T13:00:00+08:00","department":"api","status":"active","version":"1.6"}
# 库存 API v1

## 查询可售库存

`GET /api/v1/inventory/{sku}?warehouse_id={id}` 返回 `available`、`reserved` 和 `updated_at`。结果可能存在最多 2 秒缓存，不适合作为最终扣减依据。

## 预占库存

`POST /api/v1/reservations` 需要 `order_id`、`warehouse_id`、`items` 和 `Idempotency-Key`。预占默认有效期 15 分钟；订单支付后转为正式占用，超时任务会释放未确认预占。

## 常见错误

- `INV_001`：SKU 不存在。
- `INV_002`：库存不足。
- `INV_003`：仓库不可用。
- `INV_006`：幂等键冲突。

批量预占最多包含 100 个 SKU。禁止客户端通过并发拆单绕过该限制。库存不足时不得自动选择其他仓库，除非租户已开启跨仓路由策略。

