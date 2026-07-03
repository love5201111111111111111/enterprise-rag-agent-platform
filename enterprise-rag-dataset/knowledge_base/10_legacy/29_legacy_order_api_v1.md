#ONYX_METADATA={"link":"https://kb.nebula.example/legacy/order-api-v1","primary_owners":["trade@nebula.example"],"doc_updated_at":"2024-08-10T09:00:00+08:00","department":"api","status":"deprecated","version":"1.4","deprecated_by":"order-api-v2"}
# 【已弃用】订单 API v1

> 本文档仅用于兼容历史客户。新集成必须使用订单 API v2。

旧接口为 `POST /api/v1/order/create`，使用 `X-API-Key` 鉴权。旧版本的 `request_no` 只保留 2 小时，金额字段采用小数字符串。

API v1 不支持标准 `Idempotency-Key`、异步库存状态和统一错误码。该版本已于 2026-01-15 停止新增功能，计划于 2026-12-31 下线。

若用户询问当前订单创建方式，应引用 v2 文档，而不是本文档。迁移时将金额转换为最小货币单位整数，并将 `request_no` 映射为 16 至 64 字符的 `Idempotency-Key`。

