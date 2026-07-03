#ONYX_METADATA={"link":"https://kb.nebula.example/security/secrets","primary_owners":["security@nebula.example"],"doc_updated_at":"2026-06-28T09:00:00+08:00","department":"security","status":"active","version":"3.1"}
# 密钥与凭据管理规范

API Key、数据库密码、Webhook Secret 和私钥统一存储在密钥管理系统。应用通过工作负载身份或短期凭据读取，禁止将 Secret 写入 `.env` 后提交 Git。

服务账号密钥最长 90 天轮换，生产数据库临时凭据最长 4 小时。轮换采用双密钥过渡：创建新密钥、部署验证、观察 24 小时、吊销旧密钥。

代码与 CI 对提交内容进行 Secret 扫描。发现泄露时应立即吊销，而不是等待确认是否被使用；随后检查调用日志、评估影响并更新相关系统。

日志只允许记录密钥指纹或脱敏片段。工单和即时通信中不得发送完整密钥。供应商支持需要排障时，应提供请求 ID 与错误码，不提供真实生产凭据。

