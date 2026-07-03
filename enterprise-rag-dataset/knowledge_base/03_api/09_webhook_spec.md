#ONYX_METADATA={"link":"https://developer.nebula.example/webhooks/v2","primary_owners":["platform@nebula.example"],"doc_updated_at":"2026-06-23T10:00:00+08:00","department":"api","status":"active","version":"2.1"}
# Webhook 投递规范 v2

## 投递策略

Webhook 请求超时时间为 5 秒。成功必须返回任意 2xx 状态码。失败后按 1、5、30、120、600 分钟重试，最多重试 5 次；全部失败后进入死信队列，并在租户控制台显示。

每次投递带有 `X-CloudOrder-Event-ID`、`X-CloudOrder-Timestamp` 和 `X-CloudOrder-Signature`。接收端必须使用原始请求体验签，不得先格式化 JSON。

## 事件兼容

事件名采用 `domain.action.vN`，例如 `order.paid.v2`。同一大版本只增加可选字段，不删除或改变已有字段语义。消费者必须忽略未知字段。

## 排障信息

客户反馈未收到事件时，首先查询事件 ID 与投递记录，而不是重新触发支付。人工重放需要 L2 权限，单次最多 100 条，并保留操作者、原因和时间。事件重放不会改变原始 `event_id`，客户系统必须保证幂等。

