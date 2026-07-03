#ONYX_METADATA={"link":"https://kb.nebula.example/deployment/environments","primary_owners":["sre@nebula.example"],"doc_updated_at":"2026-06-26T09:00:00+08:00","department":"deployment","status":"active","version":"3.2"}
# 环境与发布矩阵

| 环境 | 用途 | 数据 | 发布策略 | 访问限制 |
|---|---|---|---|---|
| dev | 日常开发 | 合成数据 | 自动覆盖 | 公司网络 |
| test | 集成测试 | 脱敏样本 | 每日构建 | 公司网络 |
| staging | 上线验证 | 合成+脱敏 | 与生产同配置 | VPN+MFA |
| production | 客户业务 | 真实数据 | 金丝雀+审批 | 堡垒机+MFA |

生产环境位于腾讯云南京，Kubernetes 版本为 1.32，应用基线运行时为 Java 21 和 Python 3.12。所有镜像必须使用不可变 SHA256 摘要，禁止在生产部署 `latest` 标签。

发布窗口为工作日 10:00 至 16:00。周五 15:00 后、法定节假日前一天禁止常规发布。紧急安全修复需事故指挥官与研发负责人共同批准。

Staging 验证至少包括核心 API 冒烟、数据库迁移演练、回滚演练和告警检查。测试通过不代表可以跳过生产审批。

