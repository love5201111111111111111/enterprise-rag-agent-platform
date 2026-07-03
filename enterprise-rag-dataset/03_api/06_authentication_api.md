#ONYX_METADATA={"link":"https://developer.nebula.example/auth","primary_owners":["identity@nebula.example"],"doc_updated_at":"2026-06-22T09:30:00+08:00","department":"api","status":"active","version":"2.0"}
# API 鉴权规范 v2

## 请求头

外部 API 使用 Bearer Token：`Authorization: Bearer <token>`。每个请求还必须带 `X-Tenant-ID`；写接口必须带 `X-Request-ID`。创建订单等需要防重复的接口必须带 `Idempotency-Key`。

Token 默认有效期 60 分钟，刷新令牌有效期 30 天。服务账号密钥每 90 天轮换一次。系统允许新旧密钥并存 24 小时，便于无中断轮换。

## 签名 Webhook

平台发送 Webhook 时使用 `X-CloudOrder-Timestamp` 与 `X-CloudOrder-Signature`。签名内容为 `timestamp + "." + raw_body`，算法为 HMAC-SHA256。接收方必须拒绝时间偏差超过 5 分钟的请求，并按事件 ID 去重。

## 错误码

- `AUTH_001`：Token 缺失或格式错误。
- `AUTH_002`：Token 过期。
- `AUTH_003`：租户不匹配。
- `AUTH_004`：权限不足。
- `RATE_001`：超过限流阈值。

日志禁止记录完整 Token，只能记录前 6 位、后 4 位和不可逆指纹。

