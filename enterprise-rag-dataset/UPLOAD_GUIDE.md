# Onyx 上传与配置步骤

## 首轮基线

1. 进入“管理面板 → 连接器 → File”。
2. 上传 `cloudorder_kb.zip`，连接器命名为 `CloudOrder-KB-v1`。
3. 等待所有文件完成索引，确认文档数为 30。
4. 进入“Document Sets”，创建 `CloudOrder企业知识库` 并关联该连接器。
5. 创建 Agent `CloudOrder研发运维助手`，限定使用该 Document Set。

## 建议的 Agent 指令

你是 CloudOrder 企业研发与运维助手。回答事实问题时必须基于知识库并给出引用。优先采用 status=active 且更新时间较新的文档；deprecated 或 expired 文档仅用于明确的历史问题。资料不足时直接说明无法从知识库确认。涉及生产变更、数据修复、密钥和支付信息时必须遵守审批与安全规范，不得编造命令或权限。

## 注意

不要把 `evaluation/golden_questions.csv` 上传到同一个知识库，否则模型会直接检索到标准答案，导致评测数据泄漏。评测集只保留在本地。

