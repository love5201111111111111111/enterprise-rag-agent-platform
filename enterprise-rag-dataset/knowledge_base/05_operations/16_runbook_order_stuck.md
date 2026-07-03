#ONYX_METADATA={"link":"https://kb.nebula.example/runbooks/order-stuck","primary_owners":["trade@nebula.example"],"doc_updated_at":"2026-06-30T09:20:00+08:00","department":"operations","status":"active","version":"2.2"}
# Runbook：订单长时间停留在 PENDING_INVENTORY

## 判断标准

订单处于 `PENDING_INVENTORY` 超过 2 分钟视为异常候选；同一租户 5 分钟内超过 20 笔时触发 P1 候选告警。

## 排查步骤

1. 使用订单号查询 `trace_id`，确认 `order.created.v2` 是否成功发布。
2. 检查 Kafka 主题的 Consumer Lag。Lag 超过 10,000 或最老消息超过 60 秒时，检查 Inventory Consumer。
3. 检查 Inventory Service 错误率、数据库连接池和 Redis 延迟。
4. 若消费者健康但单条事件失败，查询死信队列原因。

## 止损与恢复

积压且消费者资源饱和时，可将消费者从 6 个扩至 12 个；扩容前确认数据库 CPU 低于 70%。不得直接在数据库把订单改为成功。

单条事件可通过受控重放工具按 `event_id` 重放。重放前确认库存预占接口幂等。恢复后核对订单数、预占记录数和事件数，并观察 15 分钟。

