#ONYX_METADATA={"link":"https://kb.nebula.example/security/data-classification","primary_owners":["security@nebula.example"],"doc_updated_at":"2026-06-27T10:00:00+08:00","department":"security","status":"active","version":"2.6"}
# 数据分类与处理规范

## 分类等级

- L1 公开：官网内容、公开 API 文档。
- L2 内部：内部流程、一般架构信息。
- L3 机密：客户业务数据、源代码、内部日志、合同和未公开漏洞。
- L4 严格机密：密码、私钥、完整 Token、支付敏感信息和加密主密钥。

L3 数据只能存储在受管系统，传输和静态存储均需加密。生产日志中的手机号和邮箱必须脱敏，订单号可用于内部排障但不得出现在公开渠道。

L4 数据禁止进入聊天、工单正文、代码仓库和普通日志。密钥只能存储在密钥管理系统。发现 L4 数据外泄时按 P0 安全事件处理。

用于测试和模型评测的数据必须合成或脱敏。生产数据不得直接复制到个人电脑。数据导出应记录申请人、目的、字段、范围和到期时间。

