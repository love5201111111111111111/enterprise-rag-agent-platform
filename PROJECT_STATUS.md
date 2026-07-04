# 项目状态

更新时间：2026-07-03

| 模块 | 状态 | 说明 |
|---|---|---|
| 云服务器与 Onyx 部署 | 完成 | Standard 多容器运行正常 |
| DeepSeek 模型接入 | 完成 | DeepSeek V4 Flash |
| 企业仿真知识库 | 完成 | 30 文档、版本冲突与安全分类 |
| RAG Agent | 完成 | 知识库强制检索、引用与拒答 |
| 黄金评测集 | 完成 | 50 检索题、10 高风险生成题 |
| Embedding A/B | 完成 | E5 最终 Hit@5=100%、MRR=0.866 |
| 只读诊断 API | 完成 | 鉴权、审计、限流、健康检查 |
| OpenAPI Agent Action | 完成 | `internal_search → diagnoseOrder` |
| Agent 安全收敛 | 完成 | 聚合接口、禁止跨 Runbook 阈值、只读披露 |
| 真实 GitHub 数据源 | 完成 | macrozheng/mall，674 条文档、900 chunks，6 小时增量同步 |
| Mall 独立知识库与 Agent | 完成 | 文档集 ID 2、Agent ID 2，与 CloudOrder 数据隔离 |
| GitHub 黄金评测 | 完成 | 20 题，来源命中 100%、可回答题引用 100%、拒答 100% |
| 并发压力测试 | 完成 | 检索 32 并发 P95=0.94s；Agent 6 并发突发 P95=15.44s；均 100% 成功 |
| HTTPS 与公网收敛 | 待完成 | 需要域名或确定访问方案 |
| 基础健康检查 | 完成 | JSON 输出，覆盖 HTTP、容器、磁盘和内存 |
| PostgreSQL 备份 | 完成 | gzip、SHA-256、保留策略和临时库恢复演练 |
| 异地备份与完整灾备 | 待完成 | 需接入腾讯云 COS，并覆盖 MinIO/OpenSearch |
| CI/CD 流水线 | CI 完成 / CD 待激活 | GitHub Actions 双 Job 已通过，Dependabot PR 均通过；待配置主分支规则、production 环境与部署 Secrets |
| 求职材料 | 进行中 | README 已建立，待补演示与面试材料 |

当前判断：RAG/Agent MVP 已完成；完整求职项目约 90%。
