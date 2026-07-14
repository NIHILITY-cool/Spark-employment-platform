# 后端模块

## 模块职责

基于 Spring Boot 的 RESTful API 后端，提供学生端和高校端的业务接口。

## 环境要求

- Java 17
- Maven 3.8+
- MySQL 8.x
- Redis

## 启动

```bash
cd backend
mvn spring-boot:run
```

在虚拟机运行时先加载仅本机可读的 MySQL 连接配置：

```bash
source ~/employment-platform/mysql.env
cd ~/employment-platform/backend
mvn spring-boot:run
```

Spark Master 已占用虚拟机 8080，因此 API 默认监听 `http://192.168.64.2:8082`；本机前端默认访问
`http://192.168.64.2:8082/api`，Swagger 页面为 `http://192.168.64.2:8082/swagger-ui.html`。

首次部署时，先执行数据库结构脚本（脚本可重复执行）：

```bash
mysql -u root -p < ../database/schema.sql
```

## 主要接口

### 服务状态
- `GET /api/health` - 服务与 MySQL 岗位数据连通性

### 学生画像
- `POST /api/students` - 创建学生画像
- `GET /api/students/{studentId}/profile` - 获取画像、技能、实践经历和期望
- `PUT /api/students/{studentId}/profile` - 更新基本信息
- `POST /api/students/{studentId}/skills` - 新增或更新技能等级（1-5）
- `DELETE /api/students/{studentId}/skills/{skillId}` - 删除技能
- `POST /api/students/{studentId}/experiences` - 新增项目、实习或获奖经历
- `PUT /api/students/{studentId}/experiences/{experienceId}` - 编辑经历
- `DELETE /api/students/{studentId}/experiences/{experienceId}` - 删除经历
- `PUT /api/students/{studentId}/preference` - 保存就业期望

### 岗位
- `GET /api/jobs` - 岗位搜索
- `GET /api/jobs/{jobKey}` - 岗位详情
- `GET /api/jobs/filters` - 当前有效岗位的城市、岗位类别筛选项

查询参数：`page`、`size`、`keyword`、`city`、`category`、`minSalary`、`maxSalary`。参数会校验范围，分页最大 100 条。

### 市场统计
- `GET /api/market/statistics/{type}?date=2026-07-11` - 读取 Spark 导出的市场统计
- `GET /api/market/overview?date=2026-07-11` - 一次获取城市、行业、学历、经验、热门岗位与热门技能

支持的统计类型：`city_distribution`、`industry_distribution`、`education_distribution`、`experience_distribution`、`hot_jobs`、`hot_skills`、`source_distribution`。

### 推荐
- `GET /api/recommendations/top10?studentId={id}` - 实时 Top10 推荐
- `GET /api/recommendations/{jobKey}/match?studentId={id}` - 单岗位匹配详情
- `GET /api/recommendations/skill-gap?studentId={id}` - 根据 Top10 计算技能差距

推荐从 MySQL 中稳定抽样至多 1500 个有效岗位，先按学生学历做硬过滤，再按实践经历、期望方向、城市、最低期望薪资、行业和岗位时效计算。方向证据不足的岗位不会进入有明确方向的 Top10；结果实时计算，不写回正式表。

推荐响应保留兼容字段，但总分只采用六个维度和 `matchedExperienceTerms` 经历命中词。技能与学历不进入分数：学历是硬门槛，技能只保留在画像中。薪资只填写最低期望，高薪岗位不会因此扣分。

### 高校培养参考

- `GET /api/university/market-dashboard` - 高校端市场看板聚合，返回总览 KPI、岗位大类、地区类别结构、城市行业热力、薪资学历、技能需求和数据质量
- `GET /api/university/training-alignment?major={专业}&city={地区}` - 读取专业对应的公开岗位样本、低经验门槛岗位、薪资、行业、学历、技能和地区岗位方向矩阵
- `GET /api/university/industry-salary-distribution?city={地区}` - 按岗位文本规则聚合十大行业薪资档位、有效薪资样本和平均月薪

当前支持数据科学与大数据技术、计算机科学与技术、软件工程、统计学和人工智能五个专业方向。接口基于 Spark 清洗并写入 MySQL 的岗位数据做即席聚合，不使用毕业生去向数据，也不输出培养质量结论。

认证仍未接入；项目、实习和获奖经历由学生自主维护，不使用未经授权的外部学生数据。

## 测试方法

```bash
cd backend
mvn test
```

## 当前负责人

待分配

## 当前进度

参见 `docs/11-progress-log.md`
