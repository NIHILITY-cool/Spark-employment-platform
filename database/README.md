# 数据库模块

## 模块职责

维护 MySQL 数据库表结构、种子数据和 ER 图。

## 文件说明

| 文件 | 用途 |
|------|------|
| `schema.sql` | 完整建表语句 |
| `seed/` | 种子数据（专业、技能、管理员等） |
| `diagrams/` | ER 图 |

## 数据库表

- `user` - 用户
- `student` - 学生信息
- `student_skill` - 学生技能
- `job_preference` - 求职意愿
- `company` - 企业
- `job` - 岗位
- `job_skill` - 岗位技能
- `favorite_job` - 收藏岗位
- `job_match` - 匹配记录
- `recommendation` - 推荐记录
- `major_statistics` - 专业统计
- `major_skill_gap` - 专业技能缺口
- `market_demand_statistics` - 市场需求统计

第一条 Spark 数据链路已使用 `schema.sql` 中的 `job`、`job_skill`、`market_statistic` 三张表：分别保存岗位画像、岗位技能和市场聚合结果。

## 初始化

```bash
mysql -u root -p < schema.sql
mysql -u root -p < seed/majors.sql
mysql -u root -p < seed/skills.sql
mysql -u root -p < seed/admin_user.sql
```

数据库账号、密码和 JDBC 地址仅通过环境变量传入 Spark 与 Spring Boot，不能写入仓库。

## 当前负责人

待分配

## 当前进度

参见 `docs/10-progress-log.md`
