#ONYX_METADATA={"link":"https://kb.nebula.example/runbooks/payment-callback","primary_owners":["trade@nebula.example"],"doc_updated_at":"2026-06-30T13:00:00+08:00","department":"operations","status":"active","version":"2.3"}
# Runbook：支付成功但订单未更新

首先收集租户、订单号、渠道交易号和大致支付时间。禁止要求客户提供银行卡号、CVV 或完整支付凭据。

1. 查询 Payment Callback 是否收到渠道请求以及验签结果。
2. 检查渠道交易号的去重记录；重复回调应返回成功但不重复发布事件。
3. 查询 `payment.confirmed.v2` 是否发布，并按 `trace_id` 追踪 Order Consumer。
4. 检查订单当前状态。若已取消或金额不一致，进入人工审核，不得强制改为 PAID。

渠道支持安全重发时可请求重发；否则使用内部补偿工具重新发布已验证的支付事件。补偿前必须核对租户、订单、金额、币种和渠道交易号五项信息，并由另一名人员复核。

完成后确认订单状态、履约单和客户通知一致。所有人工补偿必须记录原因与操作人。

