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
- `GET /api/students/{studentId}/profile` - 获取画像、技能和期望
- `PUT /api/students/{studentId}/profile` - 更新基本信息
- `POST /api/students/{studentId}/skills` - 新增或更新技能等级（1-5）
- `DELETE /api/students/{studentId}/skills/{skillId}` - 删除技能
- `PUT /api/students/{studentId}/preference` - 保存就业期望

### 岗位
- `GET /api/jobs` - 岗位搜索
- `GET /api/jobs/{jobKey}` - 岗位详情与 Spark 提取技能
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

推荐首版从 MySQL 中筛选至多 300 个有效候选岗位，综合技能、经历要求、期望岗位方向、学历、城市和薪资区间进行计算；岗位技能证据不足 3 个时会折减技能分。结果实时计算，不写回正式表。

认证、项目/实习经历和高校聚合接口依赖尚未采集的学生业务数据，暂不对外宣称已实现，后续应在对应数据表与批处理结果准备后再接入。

## 测试方法

```bash
cd backend
mvn test
```

## 当前负责人

待分配

## 当前进度

参见 `docs/11-progress-log.md`
