# Operations

## `healthcheck.sh`

检查 Onyx HTTP 健康状态、核心容器、CloudOrder Ops API、磁盘和可用内存，输出单行 JSON，critical 状态返回非零退出码，便于接入 cron、云监控或告警平台。

## `backup_postgres.sh`

执行 PostgreSQL 逻辑备份，使用临时文件、文件锁、gzip 完整性检查、SHA-256 和 7 天保留策略。

当前备份仅位于服务器同一块磁盘，不能抵御云盘损坏或实例误删。生产环境应继续同步到腾讯云 COS，并定期做恢复演练。MinIO/OpenSearch 的完整灾备也尚未完成。

2026-07-02 已完成一次临时数据库恢复演练：备份成功恢复，并校验 Persona、Search Settings 和 Tool 三类核心表，随后删除临时验证库。
