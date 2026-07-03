# Embedding A/B 对比：Nomic vs Multilingual E5

## 实验设计

- 固定 Onyx v4.2.2、知识库、Document Set、Top-K=5 和检索 API。
- 固定 50 道黄金问题，其中 48 道有预期来源文档。
- 只替换 Embedding 模型，其他变量保持不变。
- 新模型完成全量重建并预热后，再采集稳态指标。

## 结果

| 模型 | Hit@5 | MRR | Median | P95 | Misses |
|---|---:|---:|---:|---:|---|
| `nomic-ai/nomic-embed-text-v1` | 95.8% | 0.797 | 0.344s | 1.201s | Q005、Q018 |
| `intfloat/multilingual-e5-base` | **100%** | **0.866** | **0.319s** | **0.783s** | 无 |

## 结论

Multilingual E5 在当前中文企业语料上同时改善召回率、相关文档排序和 P95 延迟，因此保留为最终 Embedding。该结论仅对当前评测集有效；语料规模扩大后需要执行回归评测。

## 工程发现

1. Embedding 迁移必须检查实际写入的 chunk 数，不能只看任务 `SUCCESS`。
2. 文件连接器的增量检查点可能使新索引出现“扫描成功但写入 0 chunk”。
3. 更换文件 ID 后重新摄取，E5 索引成功写入 30 个 chunk。
4. 新模型首次并发调用存在冷启动超时，生产部署应在流量进入前执行预热查询。

## 证据文件

- Nomic：`retrieval_20260702_173916.csv`、`retrieval_20260702_173916.md`
- E5 空索引诊断：`retrieval_20260702_184113.csv`、`retrieval_20260702_184113.md`
- E5 最终稳态：`retrieval_20260702_191122.csv`、`retrieval_20260702_191122.md`
- E5 高风险生成验证：`baseline_20260702_191611.csv`、`baseline_20260702_191611.md`
