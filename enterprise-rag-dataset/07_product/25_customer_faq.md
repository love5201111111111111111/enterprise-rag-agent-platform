#ONYX_METADATA={"link":"https://kb.nebula.example/product/faq","primary_owners":["support@nebula.example"],"doc_updated_at":"2026-06-20T14:00:00+08:00","department":"product","status":"active","version":"2.8"}
# 客户常见问题

## 为什么创建订单后不是立即待支付？

库存预占采用异步处理，初始状态通常为 `PENDING_INVENTORY`。正常情况下数秒内更新。超过 2 分钟可联系支持并提供订单号。

## 重复提交会创建两笔订单吗？

正确使用 `Idempotency-Key` 时不会。相同租户、相同键和相同请求体返回首次结果；键相同但内容不同会返回冲突。

## 支付成功后多久更新？

通常在 10 秒内。若超过 2 分钟，请提供订单号、渠道交易号和支付时间，不要提供银行卡号或密码。

## 可以直接删除订单吗？

订单属于审计记录，不能物理删除。符合条件时可取消或退款；隐私删除请求按数据合规流程进行脱敏。

## Webhook 为什么重复？

平台采用至少一次投递，网络重试可能产生重复事件。客户应按事件 ID 实现幂等处理。

