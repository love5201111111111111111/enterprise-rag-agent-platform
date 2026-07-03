#ONYX_METADATA={"link":"https://kb.nebula.example/product/refunds","primary_owners":["product@nebula.example"],"doc_updated_at":"2026-06-19T10:00:00+08:00","department":"product","status":"active","version":"2.2"}
# 订单退款业务规则

已支付且未完成的订单可发起退款。整单退款使用原支付渠道；部分退款仅在渠道支持时开放。累计退款金额不得超过实付金额。

退款申请创建后状态为 `REFUND_PENDING`。渠道受理后为 `REFUND_PROCESSING`，成功为 `REFUNDED`，失败为 `REFUND_FAILED`。通常 1 至 3 个工作日到账，具体取决于支付渠道。

同一退款请求必须使用稳定的幂等键。网络超时后客户端应查询原请求，不得生成新键盲目重试。渠道返回结果不明确时进入人工对账。

客服可以创建退款申请，但无权修改渠道结果或直接调整订单支付状态。超过 5,000 元人民币的人工退款需要财务复核；疑似欺诈订单需同时通知风控。

