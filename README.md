# 基于 Spark 的高校智慧就业大数据分析平台

本项目面向高校学生就业分析与人才培养决策场景，围绕"学生能力与就业期望—招聘岗位需求—高校就业指导与培养优化"建立数据闭环。

当前真实主数据来自公开招聘岗位，学生数据仅在学生自主填写或高校授权匿名导入后使用；无真实数据时使用明确标记的演示队列，不生成虚假的就业率或培养质量结论。项目不建设就业跟踪模块。岗位历史跨度不足时只展示近期需求信号，不包装为长期预测。

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
学生画像与候选岗位筛选
        ↓
人岗匹配与 Top10 岗位推荐
        ↓
技能差距与就业困难识别
        ↓
高校就业分析与培养建议
```

## 项目目录结构

```
spark-employment-platform/
├── data_source/          # 数据来源：岗位数据采集
├── infrastructure/       # 虚拟机、Hadoop、HDFS、Spark、MySQL、Redis
├── data_processing/      # Pandas、Spark 数据处理和统计分析
├── recommendation/       # 人岗匹配规则、解释与离线评估
├── backend/              # Spring Boot 后端
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
| 数据存储 | Hadoop 3.5.0、HDFS、MySQL 8.x、Redis |
| 数据处理 | Pandas、PySpark、Spark SQL、Scikit-learn |
| 后端 | Java 17、Spring Boot、MyBatis-Plus、JWT |
| 前端 | Vue 3、Vite、Element Plus、ECharts |
| 部署 | Docker、Docker Compose、Nginx |

## 快速开始

详见各模块 README.md 和 `docs/` 目录下的文档。

## 当前进度

参见 `docs/11-progress-log.md`

## 参与开发

参见 `docs/10-team-tasks.md`
