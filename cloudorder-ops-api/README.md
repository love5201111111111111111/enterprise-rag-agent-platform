# CloudOrder Read-Only Operations API

这是 CloudOrder 企业 RAG/Agent 项目的只读诊断工具层，用于演示 Onyx Agent 如何在知识库检索之后调用受控业务工具。

## 工程约束

- 所有数据均为虚构数据，不包含个人信息。
- 只提供 GET 查询，不提供修改订单、补偿支付等写操作。
- 除健康检查外，所有接口都要求 `X-CloudOrder-API-Key`。
- 使用请求 ID、JSON 审计日志、限流、非 root 容器、只读文件系统和 Docker 健康检查。
- OpenAPI 文档由 FastAPI 自动生成：`/openapi.json`。

## 演示订单

| 订单号 | 场景 |
|---|---|
| `ORD-20260702-1001` | 支付事件已发布，但订单消费者因数据库超时重试 |
| `ORD-20260702-1002` | 正常履约完成 |
| `ORD-20260702-1003` | 支付金额不一致，进入人工审核 |

## 本地测试

```bash
pip install -r requirements-dev.txt
pytest -q
```

## 部署原则

容器仅加入 `onyx_default` 内部网络，不映射公网端口。Onyx 通过容器名访问：

```text
http://cloudorder-ops-api:8080/openapi.json
```

密钥只保存在服务器 `.env`，不进入 Git 仓库。
