#ONYX_METADATA={"link":"https://kb.nebula.example/runbooks/kafka-backlog","primary_owners":["platform@nebula.example"],"doc_updated_at":"2026-06-30T11:00:00+08:00","department":"operations","status":"active","version":"2.4"}
# Runbook：Kafka 消费积压

## 诊断

记录主题、Consumer Group、总 Lag、最老消息年龄和增长速度。区分生产突增、消费者变慢、分区不均和毒消息。仅看总 Lag 不能判断恢复时间。

检查消费者重启、处理耗时、外部依赖、GC 和分区分配。若只有一个分区积压，增加超过分区数的消费者不会提升吞吐。

## 处理

消费者无错误且资源饱和时逐步扩容，每次不超过当前副本数的 100%。扩容后观察数据库与下游限流。毒消息应进入死信队列，不得无限重试阻塞分区。

禁止通过直接跳过 Offset 来“清空”核心业务消息。确需调整 Offset 时必须由服务负责人和 SRE 双重批准，先导出受影响 Offset 范围并准备重放方案。

恢复标准：Lag 持续下降至 1,000 以下，最老消息小于 30 秒，下游错误率正常并稳定 15 分钟。

