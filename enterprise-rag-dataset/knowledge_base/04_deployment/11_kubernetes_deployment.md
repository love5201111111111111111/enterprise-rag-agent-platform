#ONYX_METADATA={"link":"https://kb.nebula.example/deployment/kubernetes","primary_owners":["sre@nebula.example"],"doc_updated_at":"2026-06-27T14:00:00+08:00","department":"deployment","status":"active","version":"3.1"}
# Kubernetes 部署规范

## 资源基线

每个生产服务至少 3 个副本。必须配置 readiness、liveness 与 startup 探针；Java 服务 startup 探针最长允许 180 秒。CPU request 应参考过去 14 天 P50，limit 不超过 request 的 4 倍；内存 request 参考 P95，limit 至少比 request 高 20%。

Pod 必须以非 root 用户运行、根文件系统只读，并移除不必要的 Linux capabilities。Secret 通过 External Secrets 从密钥管理系统注入，禁止写入镜像、ConfigMap 或 Git。

## 弹性与中断

核心服务 HPA 最小 3、副本上限按容量评审确定。扩容指标优先使用请求队列和延迟，CPU 作为辅助指标。PodDisruptionBudget 要保证维护期间至少 2 个副本可用。

## 变更检查

部署前检查镜像签名、依赖漏洞、迁移脚本和回滚版本。部署后观察 15 分钟，关注 5xx、P95 延迟、Pod 重启、Kafka Lag 和数据库连接数。任何核心指标超过基线 20% 应暂停放量。

