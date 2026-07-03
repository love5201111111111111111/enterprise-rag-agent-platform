# 企业研发知识库与智能故障处理助手数据集

这是为大模型 RAG/Agent 项目设计的仿真企业数据集。虚构公司为“星云科技”，核心产品为多租户 SaaS 订单平台 CloudOrder。所有公司、账号、域名和事件均为虚构，适合公开展示。

## 数据集目标

- 验证中文企业文档的检索、生成与引用能力。
- 测试版本冲突、过期资料、跨文档推理和无答案拒答。
- 为后续 GitHub Connector、Agent 工具、权限过滤和 RAG 评测提供基线。

## 目录

- `knowledge_base/`：可上传至 Onyx 的知识文档。
- `evaluation/golden_questions.csv`：50 条问题与标准答案。
- `evaluation/evaluation_guide.md`：评测方法和指标。

## 使用原则

1. 首次基线应上传 `knowledge_base` 下全部文档，包括 `10_legacy` 中的过期文档。
2. Agent 必须优先采用状态为 `active` 且更新时间更新的规则。
3. 对知识库没有依据的问题应明确拒答，不得编造。
4. 每个事实性回答都应给出来源文档。

