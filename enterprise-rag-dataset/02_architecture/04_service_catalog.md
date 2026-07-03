#ONYX_METADATA={"link":"https://kb.nebula.example/architecture/services","primary_owners":["architecture@nebula.example"],"doc_updated_at":"2026-06-18T15:00:00+08:00","department":"architecture","status":"active","version":"2.2"}
# 服务目录与所有权

| 服务 | 职责 | 数据存储 | SLO | 所有团队 |
|---|---|---|---|---|
| api-gateway | 路由、鉴权、限流、追踪号 | Redis | 99.95% | 平台组 |
| auth-service | 用户、角色、Token | PostgreSQL | 99.95% | 身份组 |
| order-service | 订单生命周期、幂等 | PostgreSQL/Redis | 99.95% | 交易组 |
| inventory-service | 库存查询、预占与释放 | PostgreSQL/Redis | 99.90% | 履约组 |
| payment-callback | 验签、支付状态事件 | PostgreSQL/Kafka | 99.95% | 交易组 |
| fulfillment-service | 拣货、发货、物流状态 | PostgreSQL/Kafka | 99.90% | 履约组 |
| notification-service | 短信、邮件和 Webhook | Kafka | 99.50% | 增长组 |

## 依赖原则

Gateway 不承载业务逻辑。Order Service 可以调用 Inventory 的公开 API，但不能访问库存数据库。Notification 故障不得阻塞订单主流程。Payment Callback 必须先持久化去重记录，再发布支付事件。

服务告警应路由至所有团队；无法在 10 分钟内定位时升级 SRE。修改公共事件 Schema 必须兼容至少两个发布周期。

