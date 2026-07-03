# 简历项目描述

## 项目名称

企业级 RAG 与只读运维 Agent 平台

## 一句话介绍

基于 Onyx 与 DeepSeek 构建并部署企业知识库 RAG/Agent 平台，融合可控仿真企业文档与真实 GitHub 研发数据，通过可复现评测、Embedding 优化、幻觉治理和受控工具调用，实现可追溯问答与只读故障诊断。

## 推荐简历版本

- 在腾讯云 Ubuntu 环境部署 Onyx v4.2.2 Standard，编排 PostgreSQL、Redis、MinIO、OpenSearch、索引服务和模型服务等多容器组件，接入 DeepSeek V4 Flash。
- 构建覆盖架构、API、运维、安全、产品与事故复盘的中文企业知识库，并设计 50 道黄金检索题和 10 道高风险生成题，建立 Hit@K、MRR、P95、引用率与拒答率评测流程。
- 对 `nomic-embed-text-v1` 与 `multilingual-e5-base` 进行控制变量 A/B 测试，将 Hit@5 从 95.8% 提升至 100%，MRR 从 0.797 提升至 0.866，检索 P95 从 1.201 秒降至 0.783 秒。
- 针对未检索时虚构认证资料的问题，实施“事实问题强制检索、无来源拒答、版本冲突优先有效文档”等 Prompt 约束，使高风险题来源命中率、引用存在率和无答案拒答率均达到 100%。
- 自研 FastAPI 只读运维诊断服务，通过 OpenAPI Action 接入 Agent，实现 `知识库检索 → 订单诊断 → 政策/运行时事实分离`；加入 API Key 鉴权、审计日志、限流、健康检查、非 root 与只读容器。
- 发现并修复 Onyx Embedding 迁移中“任务成功但新索引写入 0 chunk”的问题；通过检查索引任务字段定位增量检查点与文件去重问题，原位替换文件 ID 后完成全量重新摄取。
- 编写服务器健康检查和 PostgreSQL 备份脚本，支持 JSON 状态输出、文件锁、gzip 校验、SHA-256 与保留策略，并完成临时数据库恢复演练。
- 接入 `macrozheng/mall` 真实 GitHub 仓库的文档、Issue 与 PR，完成 674 条数据、900 个检索分块的首次摄取和 6 小时增量同步；建立隔离的 Mall 研发 Agent 与 20 题真实评测集，实现预期来源命中率 100%、可回答题引用率 100%、拒答通过率 100%。
- 编写可复现并发压测工具，分离本地 Retrieval 与完整 Agent 链路并同步采集容器资源；检索链路在 32 并发下实现 100% 成功、P95 0.94 秒，完整 Agent 在 6 并发突发下实现 100% 成功、P95 15.44 秒，据此识别生成/编排为主要延迟并给出有界队列与限流方案。
- 设计 GitHub Actions CI/CD，自动执行 FastAPI 单测、70 道评测数据校验、凭据扫描和受限容器健康检查；CD 采用 Environment 人工审批、Runner 构建镜像、生产机加载制品、健康门禁与旧镜像回滚，避免生产服务器现场下载依赖。

## 技术栈

Python、FastAPI、Docker Compose、GitHub Actions、Onyx、DeepSeek API、OpenSearch、PostgreSQL、Redis、MinIO、RAG、Embedding、OpenAPI、GitHub Connector、Linux、腾讯云

## 不建议使用的表述

- “独立开发了 Onyx”——实际是基于 Onyx 二次开发。
- “训练了 DeepSeek V4”——实际使用 DeepSeek API 作为生成模型。
- “已达到生产级”——目前是可运行、可评测、可审计的企业工程化 MVP。
- “拥有海量企业数据”——当前是 30 份可控仿真文档和 674 条公开 GitHub 研发数据，重点是评测和工程闭环。
