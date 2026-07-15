# Redis 缓存设计

Redis 不作为正式数据的最终存储，只用于缓存高频访问结果和临时状态。

## 缓存更新规则

- 高校端学生情况按 `版本号 + 页码 + 每页数量 + 状态 + 搜索词摘要` 缓存完整响应，TTL 为 5 分钟
- 学生注册、画像、技能、经历、就业期望或账号启用状态变更后，仅递增全局版本号；旧分页缓存不再读取并由 TTL 自动回收，避免使用 `KEYS` 或批量扫描删除
- 缓存失效在数据库事务提交后执行，避免把未提交数据写入新版本缓存
- Redis 查询或写入异常时自动回源 MySQL，Redis 不可用不会阻断高校端学生情况页面
- Spark 完成新岗位批次分析后，清除市场统计和高校统计缓存
- 高频统计数据可以设置 30 分钟到 1 小时的过期时间
- 学生推荐结果可以设置较长过期时间，并在学生信息或岗位批次变化时主动失效

## Key 规范

- 版本：`employment:university:students:version`
- 分页结果：`employment:university:students:v{version}:{page}:{size}:{status}:{keywordSha256}`
- 会话：`employment:session:{tokenHash}`

学生情况缓存只保存可重新计算的展示结果，MySQL 始终是学生资料的唯一真实来源。
