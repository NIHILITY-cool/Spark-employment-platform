# Redis 缓存键规范

## 学生端

| 缓存键 | 说明 | 过期策略 |
|--------|------|----------|
| `student:{studentId}:recommendations` | 学生 Top10 推荐结果 | 学生信息变化时失效 |
| `student:{studentId}:match-summary` | 学生匹配摘要 | 学生信息变化时失效 |
| `student:{studentId}:skill-gap` | 学生技能差距 | 学生技能变化时失效 |

## 高校端

| 缓存键 | 说明 | 过期策略 |
|--------|------|----------|
| `university:overview:{graduationYear}` | 高校总览统计 | 30 分钟过期 |
| `university:major:{majorId}:statistics` | 专业统计 | 1 小时过期 |

## 市场统计

| 缓存键 | 说明 | 过期策略 |
|--------|------|----------|
| `market:hot-jobs` | 热门岗位 | 岗位批次更新时失效 |
| `market:hot-skills` | 热门技能 | 岗位批次更新时失效 |
| `market:city-distribution` | 城市分布 | 岗位批次更新时失效 |

## 认证

| 缓存键 | 说明 | 过期策略 |
|--------|------|----------|
| `auth:jwt:blacklist:{tokenId}` | JWT 黑名单 | 按 JWT 过期时间 |
