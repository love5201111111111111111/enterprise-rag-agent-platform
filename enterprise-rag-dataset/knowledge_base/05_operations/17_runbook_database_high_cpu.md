#ONYX_METADATA={"link":"https://kb.nebula.example/runbooks/db-high-cpu","primary_owners":["dba@nebula.example"],"doc_updated_at":"2026-06-30T10:00:00+08:00","department":"operations","status":"active","version":"2.0"}
# Runbook：PostgreSQL CPU 持续过高

## 触发条件

主库 CPU 超过 80% 持续 5 分钟，或查询 P95 延迟超过基线 2 倍。

## 排查顺序

1. 检查是否处于发布、迁移、回填或报表运行窗口。
2. 查看活动会话、等待事件和耗时最高的 SQL 指纹，不在工单中粘贴完整客户参数。
3. 检查连接数、缓存命中率、复制延迟与磁盘 IOPS。
4. 对比应用流量，识别单租户突发或缺失索引。

## 可执行措施

优先暂停回填和非核心报表；对异常租户临时限流；必要时取消明确识别出的非事务长查询。不得直接重启主库。终止业务事务前必须联系对应服务负责人。

恢复后保留 SQL 指纹、执行计划和时间线。若原因是缺失索引，应先在 staging 验证并走并发建索引流程，禁止在高峰期直接执行。

