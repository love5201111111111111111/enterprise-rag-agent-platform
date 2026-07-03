# CloudOrder Agent 工具调用验证

## 目标

验证 CloudOrder 研发运维助手能否在不执行写操作的前提下，将知识库 Runbook 与实时只读诊断结果结合。

## 工具服务

- 服务：`cloudorder-ops-api:1.0.0`
- 网络：仅加入 `onyx_default` 内部 Docker 网络，不映射公网端口
- 鉴权：`X-CloudOrder-API-Key`
- 安全：非 root、只读根文件系统、capabilities 全部移除、内存上限、健康检查
- 审计：每次请求记录 request ID、路径、状态码、耗时和调用方地址

## 初始工具面

最初暴露四个操作：

- `getOrder`
- `getPaymentCallback`
- `getEventTrace`
- `diagnoseOrder`

Agent 依次调用前三个底层接口，能够定位 `ORDER_DB_TIMEOUT`，但回答加入了“单条毒消息”等未完全证明的推断，并提出了不必要的渠道重发建议。

## 安全收敛

将 Agent 可见工具缩减为单一 `diagnoseOrder` 聚合接口。底层接口仍保留供人工只读排查，但不再暴露给模型。新增规则：

1. 先检索与当前事件类型精确匹配的 Runbook；
2. 再调用 `diagnoseOrder`；
3. 运行时事实与知识库政策分开呈现；
4. 建议只允许来自工具的 `safe_next_steps` 和当前事件 Runbook；
5. 禁止引入其他 Runbook 的阈值和操作；
6. 明确声明仅执行只读查询、未修改数据。

## 回归结果

- 调用链：`internal_search → diagnoseOrder`
- 最终引用数：1（与支付回调事件类型精确匹配）
- 无关“数据库 CPU 70%”阈值：未出现
- 固定只读披露：通过，回答明确声明“本次仅执行只读查询，未修改任何数据。”
- API 错误：无
- 最终单次端到端延迟：18.55 秒
- 工具接口：全部为 GET，只读审计日志已确认

普通 System Prompt 对固定披露格式的服从不稳定；将规则提升到每轮附加的 Reminder 后通过。相似 Runbook 的跨文档阈值污染也通过 Reminder 中的事件类型范围约束得到修复。

## 结论

该阶段验证了“RAG 提供政策、Action 提供运行时事实”的 Agent 模式，并通过收窄工具面和规则约束降低模型越权及错误建议风险。
