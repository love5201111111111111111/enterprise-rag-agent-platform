#ONYX_METADATA={"link":"https://kb.nebula.example/deployment/db-migration","primary_owners":["dba@nebula.example"],"doc_updated_at":"2026-06-17T11:00:00+08:00","department":"deployment","status":"active","version":"2.5"}
# 数据库迁移规范

所有迁移脚本必须可重复执行并带唯一版本号。生产迁移先在 staging 使用近似数据量演练，记录耗时、锁范围和磁盘增长。

新增字段先允许为空或提供默认值，应用完成双写和回填后再增加约束。删除字段至少经过两个发布周期：第一周期停止读取，第二周期停止写入，确认无访问后再删除。

单次回填任务每批不超过 5,000 行，批次间暂停并监测复制延迟。复制延迟超过 30 秒、数据库 CPU 超过 80% 持续 5 分钟或锁等待超过 10 秒时立即暂停。

禁止在业务高峰直接创建未验证的大表索引。优先使用并发建索引能力，并准备取消命令。迁移执行人和审批人不能是同一人。

