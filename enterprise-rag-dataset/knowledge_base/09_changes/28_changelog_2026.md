#ONYX_METADATA={"link":"https://kb.nebula.example/changes/2026","primary_owners":["release@nebula.example"],"doc_updated_at":"2026-06-30T18:00:00+08:00","department":"changes","status":"active","version":"2026.06"}
# CloudOrder 2026 变更记录

## 2026.06

- 订单 API v2.3：幂等键保留时间从 12 小时延长到 24 小时。
- Webhook v2.1：重试次数统一为 5 次，新增 600 分钟末次重试。
- 企业版 SLA 提升至 99.95%。
- 生产应用基线升级到 Java 21 与 Python 3.12。

## 2026.05

- 报表查询迁移至只读副本，最大查询范围 31 天。
- 支付补偿工具增加金额、币种与双人复核校验。

## 2026.03

- 发布门禁新增 Kafka Lag 和最老消息年龄指标。
- Inventory Service 引入仓库配置批量读取与缓存。

## 2026.01

- 订单 API v1 进入弃用期；停止新增功能。
- Webhook 签名统一为 HMAC-SHA256。

