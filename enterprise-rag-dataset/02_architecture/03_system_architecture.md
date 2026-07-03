#ONYX_METADATA={"link":"https://kb.nebula.example/architecture/system","primary_owners":["architecture@nebula.example"],"doc_updated_at":"2026-06-18T14:00:00+08:00","department":"architecture","status":"active","version":"2.4"}
# CloudOrder 系统架构

## 总体结构

客户端流量首先进入腾讯云 CLB，再由 API Gateway 完成 TLS 终止、限流、租户识别和鉴权。后端核心服务包括 Auth、Order、Inventory、Payment Callback、Fulfillment 和 Notification。

同步调用使用 HTTP/JSON；订单状态传播、库存预占结果和通知任务使用 Kafka。核心事务数据存储在 PostgreSQL，热点与幂等结果存储在 Redis，检索日志进入 OpenSearch，对象附件存储在 COS。

## 可用性设计

生产环境跨三个可用区部署。无状态服务至少 3 个副本，使用反亲和规则分散节点。PostgreSQL 采用一主两备并启用自动故障转移；Kafka 主题生产环境默认 6 分区、3 副本。Redis 使用集群模式，不允许应用执行全量 Key 扫描。

## 一致性边界

订单主状态由 Order Service 维护。库存预占与支付确认通过事件驱动实现最终一致性。禁止跨服务直接写入其他服务数据库。需要跨服务补偿时，使用 Saga 状态机和带幂等键的补偿命令。

## 关键目标

正常负载下，订单创建接口 P95 小于 300ms、P99 小于 800ms。消息从产生到消费完成的 P95 延迟小于 5 秒。单租户默认 API 限额为 100 请求/秒。

