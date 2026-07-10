# 基于 Spark 的高校智慧就业大数据分析平台

本项目面向高校毕业生就业场景，围绕"毕业生求职信息—招聘岗位需求—高校就业指导"建立数据闭环。

## 项目整体架构

```text
公开岗位数据采集
        ↓
HDFS 原始数据存储
        ↓
Pandas / Spark 清洗与分析
        ↓
岗位画像与市场需求统计
        ↓
毕业生画像与人岗匹配
        ↓
岗位推荐与技能差距分析
        ↓
高校就业指导与培养建议
```

## 项目目录结构

```
spark-employment-platform/
├── data_source/          # 数据来源：岗位数据采集
├── infrastructure/       # 虚拟机、Hadoop、HDFS、Hive 环境
├── data_processing/      # Pandas、Spark 数据处理和统计分析
├── recommendation/       # 人岗匹配与岗位推荐
├── backend/              # Flask 后端
├── frontend/             # Vue 前端
├── shared/               # 各组共享内容
├── database/             # 数据库表结构和种子数据
├── deployment/           # Docker 部署配置
├── docs/                 # 项目文档
├── tests/                # 集成测试和 fixtures
└── scripts/              # 项目脚本
```

## 技术栈

| 层级 | 技术 |
|------|------|
| 数据采集 | Python、Requests、BeautifulSoup、Scrapy |
| 数据存储 | Hadoop 3.5.0、HDFS、Hive、MySQL 8.x |
| 数据处理 | Pandas、PySpark、Spark SQL、Scikit-learn |
| 后端 | Python、Flask、Flask-SQLAlchemy |
| 前端 | Vue 3、Vite、Element Plus、ECharts |
| 部署 | Docker、Docker Compose、Nginx |

## 快速开始

详见各模块 README.md 和 `docs/` 目录下的文档。

## 当前进度

参见 `docs/10-progress-log.md`

## 参与开发

参见 `docs/09-team-tasks.md`
