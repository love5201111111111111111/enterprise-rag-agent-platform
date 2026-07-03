#ONYX_METADATA={"link":"https://kb.nebula.example/company/profile","primary_owners":["strategy@nebula.example"],"doc_updated_at":"2026-06-20T09:00:00+08:00","department":"company","status":"active","version":"2.1"}
# 星云科技与 CloudOrder 产品概览

## 公司与产品

星云科技是一家虚构的企业软件公司。CloudOrder 是公司的核心产品，为零售、电商和连锁门店提供订单、库存、支付回调与履约协同能力。平台采用多租户架构，生产环境部署在腾讯云南京地域。

CloudOrder 的服务等级分为标准版、专业版和企业版。标准版面向小型团队；专业版增加高级报表与自动化规则；企业版提供独立密钥、审计导出、专属支持和更高 SLA。

## 关键业务术语

- 租户：使用 CloudOrder 的独立客户组织，以 `tenant_id` 隔离数据。
- 订单：从创建到完成的业务主对象。
- 履约单：仓库或门店执行拣货、发货的任务对象。
- 幂等键：客户端用于避免重复创建订单的唯一键。
- 追踪号：贯穿网关和微服务的 `trace_id`，用于故障定位。

## 支持边界

平台不保存银行卡号或 CVV。支付由持牌支付渠道完成，CloudOrder 只保存渠道交易号、金额、状态和脱敏后的支付方式。任何要求导出明文支付凭据的请求都必须拒绝并上报安全团队。

