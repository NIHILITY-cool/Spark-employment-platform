# 基于 Spark 的高校智慧就业大数据分析平台

## 1. 项目简介

本项目面向高校毕业生就业场景，围绕“毕业生求职信息—招聘岗位需求—高校就业指导”建立数据闭环。

项目首先采集公开招聘岗位数据，将原始岗位数据存入 HDFS，并使用 Pandas、Spark 完成清洗、标准化、统计分析和岗位技能提取。毕业生在系统中填写个人信息、技能和求职意愿，系统根据毕业生画像与岗位画像计算匹配度，推荐合适岗位并分析技能差距。高校端汇总毕业生求职意向、岗位需求、专业匹配度和技能缺口，为就业指导、技能培训和培养方向调整提供参考。

项目第一阶段不实现完整招聘网站，不涉及企业在线招聘、在线面试和正式签约，重点完成以下主线：

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

---

## 2. 当前分工

项目暂时分为五个主要方向。

| 模块 | 主要工作 | 核心技术 |
|---|---|---|
| 数据来源 | 爬取公开岗位数据，保存原始文件和采集日志 | Python、Requests、BeautifulSoup、Scrapy |
| 数据存储 | 配置 Ubuntu 虚拟机、Hadoop、HDFS，管理原始与处理后数据 | Linux、Hadoop、HDFS、Shell |
| 数据处理与分析 | 使用 Pandas 和 Spark 清洗岗位数据、提取技能、生成统计结果 | Pandas、PySpark、Spark SQL |
| 学生端 | 学生信息、求职意愿、岗位查询、人岗匹配、岗位推荐、技能差距 | Flask、MySQL、Vue、推荐算法 |
| 高校端 | 求职意愿统计、岗位需求分析、专业匹配分析、技能缺口和培养建议 | Flask、Spark SQL、Vue、ECharts |

除以上五个模块外，项目还设置公共目录，用于存放共享数据模型、接口定义、配置文件、测试代码和项目文档。

---

## 3. 总体技术架构

```mermaid
flowchart TD
    A[公开招聘网站或公开数据集] --> B[岗位数据采集程序]
    B --> C[CSV / JSON 原始数据]
    C --> D[HDFS Raw 原始数据层]
    D --> E[Pandas 小规模检查]
    D --> F[Spark 批量清洗]
    F --> G[HDFS Cleaned 清洗数据层]
    F --> H[Hive 分析表]
    H --> I[岗位需求统计]
    H --> J[岗位画像]
    K[毕业生填写个人信息与求职意愿] --> L[MySQL 业务数据库]
    J --> M[人岗匹配与推荐服务]
    L --> M
    M --> N[岗位推荐与技能差距]
    I --> O[高校分析服务]
    N --> O
    P[Vue 前端] --> Q[Flask REST API]
    Q --> L
    Q --> M
    Q --> O
```

---

## 4. 推荐技术栈

### 4.1 数据采集

- Python 3.11
- Requests
- BeautifulSoup4
- Scrapy，可选
- Selenium 或 Playwright，仅在确实需要浏览器渲染时使用
- Pandas
- JSON、CSV
- 日志模块 logging

### 4.2 数据存储

- Ubuntu Server 24.04
- OpenJDK 17
- Hadoop 3.5.0
- HDFS
- Hive，可作为分析结果表和数据仓库
- MySQL 8.x
- Shell

### 4.3 数据处理和分析

- Pandas
- NumPy
- PySpark
- Spark SQL
- Scikit-learn
- Jieba，可用于中文岗位文本分词
- TF-IDF、余弦相似度、Jaccard 相似度

### 4.4 后端

- Python
- Flask
- Flask-JWT-Extended
- Flask-SQLAlchemy
- Flask-Migrate
- PyMySQL
- RESTful API
- Gunicorn

### 4.5 前端

- Vue 3
- Vite
- Element Plus
- Axios
- Vue Router
- Pinia
- ECharts

### 4.6 协作和部署

- Git
- GitHub
- Docker、Docker Compose，可选
- Nginx
- Postman 或 Apifox
- Markdown

---

## 5. 整体项目目录结构

建议仓库名称：

```text
spark-employment-platform
```

完整目录如下：

```text
spark-employment-platform/
├── README.md
├── LICENSE
├── .gitignore
├── .env.example
├── docker-compose.yml
│
├── data_source/                       # 数据来源：岗位数据采集
│   ├── README.md
│   ├── requirements.txt
│   ├── configs/
│   │   ├── crawler.example.yaml
│   │   ├── headers.example.json
│   │   └── field_mapping.yaml
│   ├── crawlers/
│   │   ├── __init__.py
│   │   ├── base_crawler.py
│   │   ├── public_job_crawler.py
│   │   └── dataset_loader.py
│   ├── parsers/
│   │   ├── job_parser.py
│   │   ├── salary_parser.py
│   │   ├── location_parser.py
│   │   └── text_parser.py
│   ├── pipelines/
│   │   ├── save_csv.py
│   │   ├── save_json.py
│   │   └── deduplicate.py
│   ├── scripts/
│   │   ├── run_crawler.py
│   │   ├── validate_raw_data.py
│   │   └── upload_raw_to_hdfs.sh
│   ├── tests/
│   │   ├── test_job_parser.py
│   │   └── test_salary_parser.py
│   └── logs/
│       └── .gitkeep
│
├── infrastructure/                    # 虚拟机、Hadoop、HDFS、Hive 环境
│   ├── README.md
│   ├── hadoop/
│   │   ├── core-site.xml.example
│   │   ├── hdfs-site.xml.example
│   │   ├── mapred-site.xml.example
│   │   ├── yarn-site.xml.example
│   │   └── workers.example
│   ├── hive/
│   │   ├── hive-site.xml.example
│   │   └── schema/
│   │       ├── ods_tables.sql
│   │       ├── dwd_tables.sql
│   │       ├── dws_tables.sql
│   │       └── ads_tables.sql
│   ├── scripts/
│   │   ├── install_java.sh
│   │   ├── init_hdfs_dirs.sh
│   │   ├── start_bigdata.sh
│   │   ├── stop_bigdata.sh
│   │   ├── check_services.sh
│   │   └── upload_to_hdfs.sh
│   └── docs/
│       ├── vm_setup.md
│       ├── hadoop_setup.md
│       ├── hdfs_usage.md
│       └── hive_setup.md
│
├── data_processing/                   # Pandas、Spark 数据处理和统计分析
│   ├── README.md
│   ├── requirements.txt
│   ├── pandas_jobs/
│   │   ├── inspect_raw_data.py
│   │   ├── clean_sample_data.py
│   │   ├── build_dictionaries.py
│   │   └── validate_cleaned_data.py
│   ├── spark_jobs/
│   │   ├── job_cleaning.py
│   │   ├── salary_normalization.py
│   │   ├── job_title_normalization.py
│   │   ├── skill_extraction.py
│   │   ├── job_profile_builder.py
│   │   ├── market_statistics.py
│   │   ├── student_statistics.py
│   │   ├── major_skill_gap.py
│   │   └── export_results.py
│   ├── dictionaries/
│   │   ├── skills.csv
│   │   ├── skill_aliases.csv
│   │   ├── majors.csv
│   │   ├── job_categories.csv
│   │   ├── cities.csv
│   │   ├── industries.csv
│   │   ├── education_levels.csv
│   │   └── experience_levels.csv
│   ├── sql/
│   │   ├── job_statistics.sql
│   │   ├── skill_statistics.sql
│   │   ├── salary_statistics.sql
│   │   └── university_statistics.sql
│   ├── tests/
│   │   ├── test_cleaning.py
│   │   ├── test_skill_extraction.py
│   │   └── test_statistics.py
│   └── notebooks/
│       └── exploration.ipynb
│
├── recommendation/                    # 人岗匹配与岗位推荐
│   ├── README.md
│   ├── profile/
│   │   ├── student_profile.py
│   │   └── job_profile.py
│   ├── matching/
│   │   ├── skill_match.py
│   │   ├── major_match.py
│   │   ├── education_match.py
│   │   ├── experience_match.py
│   │   ├── city_match.py
│   │   ├── salary_match.py
│   │   └── total_score.py
│   ├── ranking/
│   │   ├── topn_ranker.py
│   │   └── similar_job.py
│   ├── explanation/
│   │   ├── skill_gap.py
│   │   ├── recommendation_reason.py
│   │   └── career_suggestion.py
│   ├── evaluation/
│   │   ├── metrics.py
│   │   └── offline_evaluation.py
│   └── tests/
│       ├── test_matching.py
│       └── test_ranking.py
│
├── backend/                           # Flask 后端
│   ├── README.md
│   ├── requirements.txt
│   ├── run.py
│   ├── migrations/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── extensions.py
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── student.py
│   │   │   ├── student_skill.py
│   │   │   ├── job_preference.py
│   │   │   ├── company.py
│   │   │   ├── job.py
│   │   │   ├── job_skill.py
│   │   │   ├── favorite.py
│   │   │   ├── recommendation.py
│   │   │   └── university_statistic.py
│   │   ├── routes/
│   │   │   ├── auth.py
│   │   │   ├── student.py
│   │   │   ├── jobs.py
│   │   │   ├── recommendation.py
│   │   │   ├── university.py
│   │   │   └── admin.py
│   │   ├── services/
│   │   │   ├── auth_service.py
│   │   │   ├── student_service.py
│   │   │   ├── job_service.py
│   │   │   ├── recommendation_service.py
│   │   │   └── university_service.py
│   │   ├── schemas/
│   │   ├── utils/
│   │   └── errors/
│   └── tests/
│       ├── test_auth_api.py
│       ├── test_student_api.py
│       ├── test_job_api.py
│       └── test_university_api.py
│
├── frontend/                          # Vue 前端
│   ├── README.md
│   ├── package.json
│   ├── vite.config.js
│   ├── public/
│   └── src/
│       ├── api/
│       │   ├── auth.js
│       │   ├── student.js
│       │   ├── jobs.js
│       │   ├── recommendation.js
│       │   └── university.js
│       ├── assets/
│       ├── components/
│       │   ├── JobCard.vue
│       │   ├── MatchScore.vue
│       │   ├── SkillTags.vue
│       │   ├── FilterPanel.vue
│       │   └── ChartCard.vue
│       ├── layouts/
│       │   ├── StudentLayout.vue
│       │   ├── UniversityLayout.vue
│       │   └── AdminLayout.vue
│       ├── router/
│       ├── stores/
│       ├── utils/
│       ├── views/
│       │   ├── auth/
│       │   │   ├── LoginView.vue
│       │   │   └── RegisterView.vue
│       │   ├── student/
│       │   │   ├── StudentProfileView.vue
│       │   │   ├── JobPreferenceView.vue
│       │   │   ├── JobSearchView.vue
│       │   │   ├── JobDetailView.vue
│       │   │   ├── RecommendationView.vue
│       │   │   ├── SkillGapView.vue
│       │   │   └── FavoriteJobsView.vue
│       │   ├── university/
│       │   │   ├── UniversityDashboardView.vue
│       │   │   ├── StudentIntentionView.vue
│       │   │   ├── MarketDemandView.vue
│       │   │   ├── MajorMatchView.vue
│       │   │   ├── SkillGapAnalysisView.vue
│       │   │   └── TrainingSuggestionView.vue
│       │   └── admin/
│       │       ├── JobImportView.vue
│       │       ├── DataQualityView.vue
│       │       └── DictionaryManageView.vue
│       ├── App.vue
│       └── main.js
│
├── shared/                            # 各组共享内容
│   ├── schemas/
│   │   ├── raw_job_schema.json
│   │   ├── cleaned_job_schema.json
│   │   ├── student_schema.json
│   │   └── recommendation_schema.json
│   ├── api/
│   │   └── openapi.yaml
│   ├── constants/
│   │   ├── roles.py
│   │   ├── job_status.py
│   │   └── score_weights.py
│   └── examples/
│       ├── raw_job_sample.json
│       ├── cleaned_job_sample.json
│       └── student_sample.json
│
├── database/
│   ├── README.md
│   ├── schema.sql
│   ├── seed/
│   │   ├── majors.sql
│   │   ├── skills.sql
│   │   └── admin_user.sql
│   └── diagrams/
│       └── er_diagram.png
│
├── deployment/
│   ├── backend.Dockerfile
│   ├── frontend.Dockerfile
│   ├── nginx.conf
│   ├── docker-compose.yml
│   └── scripts/
│       ├── deploy.sh
│       └── backup_mysql.sh
│
├── docs/
│   ├── 01-requirements.md
│   ├── 02-architecture.md
│   ├── 03-database-design.md
│   ├── 04-api-design.md
│   ├── 05-data-dictionary.md
│   ├── 06-recommendation-design.md
│   ├── 07-hdfs-design.md
│   ├── 08-deployment.md
│   ├── 09-team-tasks.md
│   └── 10-progress-log.md
│
├── tests/
│   ├── integration/
│   ├── fixtures/
│   └── README.md
│
└── scripts/
    ├── init_project.sh
    ├── init_backend.sh
    ├── init_frontend.sh
    ├── run_backend.sh
    ├── run_frontend.sh
    └── run_all_tests.sh
```

---

## 6. 各部分实施计划

# 6.1 数据来源模块

目录：

```text
data_source/
```

负责人主要完成岗位数据的获取、解析、保存和质量检查。

### 第一阶段：确认数据来源

优先级如下：

1. 已公开且允许下载的招聘数据集
2. 政府公共就业服务平台公开岗位
3. 企业官方校园招聘页面
4. 明确允许访问和采集的公开招聘页面

不建议将破解验证码、绕过登录、绕过反爬作为项目目标。

### 第二阶段：确定原始岗位字段

原始岗位数据统一保存为以下结构：

```text
source_job_id
job_name
company_name
city
district
industry
company_size
company_type
salary_text
education_text
experience_text
job_description
job_requirement
publish_time
source_name
source_url
crawl_time
```

### 第三阶段：实现采集程序

需要完成：

- 请求头配置
- 请求参数配置
- 页面或接口请求
- 分页采集
- 岗位字段解析
- 异常重试
- 访问频率控制
- 采集日志
- 原始数据保存

### 第四阶段：原始数据检查

检查内容：

- 总数据量
- 字段缺失率
- 重复岗位数量
- 无岗位名称数据
- 无公司名称数据
- 无岗位描述数据
- 无薪资数据
- 采集失败页面

### 第五阶段：上传 HDFS

原始文件命名建议：

```text
jobs_数据源_日期_批次.json
jobs_数据源_日期_批次.csv
```

上传目录：

```text
/employment-platform/raw/jobs/source=数据源/date=YYYY-MM-DD/
```

### 本模块交付物

- 可运行的数据采集脚本
- 原始岗位数据
- 原始字段说明
- 数据源说明
- 采集日志
- 数据质量报告
- HDFS 上传脚本

---

# 6.2 数据存储与虚拟机模块

目录：

```text
infrastructure/
```

负责人主要完成虚拟机、大数据环境、HDFS目录和数据上传流程。

### 第一阶段：配置虚拟机

建议环境：

```text
Ubuntu Server 24.04
OpenJDK 17
Hadoop 3.5.0
Python 3.11
Spark 3.5.x
Hive 4.x，可选
```

需要完成：

- 虚拟机网络配置
- SSH远程连接
- Java环境
- Hadoop环境
- Spark环境
- Python环境
- HDFS Web UI访问

### 第二阶段：创建 HDFS 目录

```text
/employment-platform/
├── raw/
│   ├── jobs/
│   ├── students/
│   └── dictionaries/
├── cleaned/
│   ├── jobs/
│   ├── job_skills/
│   └── students/
├── warehouse/
│   ├── ods/
│   ├── dwd/
│   ├── dws/
│   └── ads/
└── output/
    ├── job_statistics/
    ├── recommendations/
    ├── skill_gaps/
    └── university_statistics/
```

### 第三阶段：建立数据分层

ODS：

保存从原始数据转换得到的结构化数据，尽量保留原始字段。

DWD：

保存完成去重、标准化、薪资解析和技能提取后的明细数据。

DWS：

保存按岗位、城市、行业、技能和专业汇总的数据。

ADS：

保存前端可直接使用的热门岗位、热门技能、专业匹配度和技能缺口结果。

### 第四阶段：编写管理脚本

至少提供：

```text
启动 Hadoop
停止 Hadoop
检查进程
创建 HDFS 目录
上传数据
查看数据
下载结果
清理测试数据
```

### 第五阶段：权限和备份

需要保证：

- 项目成员有指定目录写入权限
- 不直接写 HDFS 根目录
- 原始数据只追加、不随意覆盖
- 重要配置和脚本提交 Git
- 私密环境变量不提交 Git

### 本模块交付物

- 虚拟机配置说明
- Hadoop和Spark配置说明
- HDFS目录初始化脚本
- 数据上传下载脚本
- 服务启动停止脚本
- 大数据环境检查清单

---

# 6.3 数据处理与分析模块

目录：

```text
data_processing/
```

负责人完成从原始岗位到标准岗位、岗位画像和统计结果的处理。

### 第一阶段：Pandas探索

先用少量样本完成：

- 字段查看
- 缺失率统计
- 重复数据检查
- 薪资格式分析
- 学历格式分析
- 经验格式分析
- 城市和行业值检查
- 岗位描述文本检查

Pandas主要用于快速试验规则，不承担正式大批量任务。

### 第二阶段：建立标准字典

需要建立：

- 岗位分类字典
- 技能词典
- 技能别名表
- 专业目录
- 城市标准表
- 行业标准表
- 学历等级表
- 工作经验等级表

例如：

```text
SpringBoot → Spring Boot
mysql → MySQL
pyspark → Python、Spark
计科 → 计算机科学与技术
北上广深 → 分别保存为标准城市名
```

### 第三阶段：Spark清洗

需要完成：

- 删除完全重复岗位
- 识别相似重复岗位
- 统一空值
- 统一岗位名称
- 统一城市
- 统一行业
- 统一学历
- 统一经验
- 解析薪资上下限
- 识别应届生岗位
- 过滤明显异常数据

### 第四阶段：岗位分类和技能提取

岗位分类示例：

```text
软件开发
前端开发
后端开发
数据分析
大数据开发
人工智能
测试
运维
产品
设计
市场营销
行政管理
```

技能提取第一版采用：

```text
技能词典 + 同义词映射 + 关键词匹配
```

输出：

```text
job_id
skill_name
skill_category
source_text
```

### 第五阶段：建立岗位画像

岗位画像包含：

```text
岗位类别
城市
行业
企业类型
企业规模
薪资上下限
学历要求
经验要求
是否适合应届生
核心技能
```

### 第六阶段：市场需求分析

至少生成：

- 热门岗位排行
- 热门技能排行
- 各城市岗位数量
- 各行业岗位数量
- 各岗位平均薪资
- 学历要求分布
- 经验要求分布
- 应届生岗位占比
- 不同岗位的技能组合

### 第七阶段：输出处理结果

输出到：

- HDFS Cleaned
- Hive DWD、DWS、ADS
- MySQL业务和统计表

### 本模块交付物

- Pandas探索脚本
- Spark清洗任务
- 技能和标准字典
- 标准岗位数据
- 岗位技能数据
- 岗位画像
- 市场统计结果
- 数据处理说明文档

---

# 6.4 学生端模块

涉及目录：

```text
backend/
frontend/src/views/student/
recommendation/
```

学生端负责学生信息、求职意愿、岗位查询、匹配推荐和技能差距。

### 第一阶段：用户和学生信息

实现：

- 注册
- 登录
- 获取个人信息
- 修改个人信息
- 填写专业和学历
- 填写毕业年份
- 填写项目和实习经历
- 管理个人技能

学生技能结构：

```text
student_id
skill_name
skill_level
```

### 第二阶段：求职意愿

实现：

- 期望岗位
- 期望行业
- 期望城市
- 最低期望薪资
- 最高期望薪资
- 企业规模偏好
- 企业类型偏好
- 是否接受异地
- 是否接受实习

### 第三阶段：岗位查询

实现：

- 岗位关键词搜索
- 城市筛选
- 行业筛选
- 薪资筛选
- 学历筛选
- 经验筛选
- 应届生岗位筛选
- 岗位详情
- 岗位收藏

### 第四阶段：人岗匹配

第一版采用规则匹配：

```text
技能匹配度：40%
专业匹配度：20%
学历匹配度：10%
经验匹配度：10%
城市匹配度：10%
薪资匹配度：10%
```

输出：

- 综合匹配分数
- 已满足条件
- 未满足条件
- 已匹配技能
- 缺失技能
- 推荐理由

### 第五阶段：岗位推荐

实现：

- 推荐Top 10岗位
- 同岗位方向推荐
- 同城市岗位推荐
- 应届生友好岗位推荐
- 相似岗位推荐

### 第六阶段：技能差距

实现：

- 目标岗位高频技能
- 学生已掌握技能
- 学生缺失技能
- 缺失技能优先级
- 简单学习建议

### 学生端后端接口

```text
POST   /api/auth/register
POST   /api/auth/login

GET    /api/students/profile
PUT    /api/students/profile
GET    /api/students/skills
POST   /api/students/skills
DELETE /api/students/skills/{id}

GET    /api/students/preference
PUT    /api/students/preference

GET    /api/jobs
GET    /api/jobs/{job_id}
POST   /api/jobs/{job_id}/favorite
DELETE /api/jobs/{job_id}/favorite

GET    /api/recommendations
GET    /api/recommendations/{job_id}/match
GET    /api/recommendations/skill-gap
```

### 学生端页面

- 登录注册
- 个人信息
- 技能管理
- 求职意愿
- 岗位搜索
- 岗位详情
- 岗位推荐
- 技能差距
- 收藏岗位

### 本模块交付物

- 学生端数据库表
- 学生端后端接口
- 匹配推荐代码
- 学生端前端页面
- 接口测试
- 推荐结果示例

---

# 6.5 高校端模块

涉及目录：

```text
backend/app/routes/university.py
backend/app/services/university_service.py
frontend/src/views/university/
data_processing/spark_jobs/
```

高校端不管理单个学生的敏感详细信息，重点展示汇总分析结果。

### 第一阶段：毕业生求职意愿分析

统计：

- 各专业学生数量
- 期望岗位排行
- 期望行业排行
- 期望城市排行
- 期望薪资分布

### 第二阶段：毕业生能力分析

统计：

- 各专业高频技能
- 各技能掌握率
- 有项目经历学生比例
- 有实习经历学生比例
- 常见证书分布

### 第三阶段：人岗匹配分析

统计：

- 全校平均匹配度
- 各专业平均匹配度
- 各目标岗位平均匹配度
- 匹配度较低的岗位方向
- 常见不满足条件

### 第四阶段：市场需求分析

展示：

- 热门岗位
- 热门技能
- 热门城市
- 热门行业
- 应届生岗位数量
- 学历要求
- 经验要求
- 岗位薪资

### 第五阶段：专业与岗位分析

实现：

- 某专业对应岗位
- 岗位数量
- 岗位薪资
- 岗位高频技能
- 学生技能覆盖率
- 专业技能缺口

### 第六阶段：指导建议

第一版使用规则生成建议。

示例规则：

```text
岗位需求率 > 50%，学生掌握率 < 30%
→ 标记为重点缺失技能

某岗位招聘数量较高，专业学生匹配度较低
→ 建议增加该岗位方向的实践训练

某城市相关岗位数量较高
→ 建议加强该地区就业信息推送
```

输出：

- 就业指导建议
- 技能培训建议
- 项目实践建议
- 校企合作方向
- 专业培养方向参考

### 高校端后端接口

```text
GET /api/university/overview
GET /api/university/student-intentions
GET /api/university/student-skills
GET /api/university/major-match
GET /api/university/major-skill-gap
GET /api/university/market-demand
GET /api/university/training-suggestions
```

### 高校端页面

- 高校总览大屏
- 求职意愿分析
- 学生能力分析
- 岗位市场需求
- 专业岗位匹配
- 专业技能差距
- 就业指导建议
- 培养方向建议

### 本模块交付物

- 高校汇总统计任务
- 高校端后端接口
- ECharts数据结构
- 高校分析页面
- 建议生成规则
- 高校端演示数据和说明

---

## 7. 各模块数据接口

为了避免不同小组各自设计字段，必须统一共享数据格式。

### 7.1 原始岗位数据

```json
{
  "source_job_id": "source-10001",
  "job_name": "大数据开发工程师",
  "company_name": "示例科技公司",
  "city": "成都",
  "industry": "软件和信息技术服务业",
  "salary_text": "8K-12K",
  "education_text": "本科",
  "experience_text": "经验不限",
  "job_description": "负责数据平台开发……",
  "job_requirement": "掌握 Java、Spark、Hive……",
  "publish_time": "2026-07-10",
  "source_name": "公开数据源",
  "source_url": "https://example.com/job/10001",
  "crawl_time": "2026-07-10 10:00:00"
}
```

### 7.2 清洗后岗位数据

```json
{
  "job_id": 10001,
  "job_name": "大数据开发工程师",
  "standard_job_name": "大数据开发工程师",
  "job_category": "大数据开发",
  "company_name": "示例科技公司",
  "city": "成都",
  "industry": "软件和信息技术服务业",
  "salary_min": 8000,
  "salary_max": 12000,
  "education_requirement": "本科",
  "experience_requirement": "经验不限",
  "graduate_friendly": true,
  "skills": ["Java", "Spark", "Hive"],
  "data_source": "公开数据源"
}
```

### 7.3 学生数据

```json
{
  "student_id": 1001,
  "major": "数据科学与大数据技术",
  "education": "本科",
  "graduation_year": 2027,
  "skills": ["Python", "SQL", "Spark", "Hive"],
  "expected_jobs": ["大数据开发工程师"],
  "expected_cities": ["成都", "重庆"],
  "expected_industries": ["软件和信息技术服务业"],
  "salary_min": 8000,
  "salary_max": 12000
}
```

### 7.4 推荐结果

```json
{
  "student_id": 1001,
  "job_id": 10001,
  "total_score": 84,
  "skill_score": 75,
  "major_score": 100,
  "education_score": 100,
  "experience_score": 100,
  "city_score": 100,
  "salary_score": 90,
  "matched_skills": ["Spark", "Hive"],
  "missing_skills": ["Java"],
  "recommendation_reason": "专业、城市和薪资符合，已掌握部分核心技能"
}
```

---

## 8. 建议数据库表

第一版至少建立：

```text
user
student
student_skill
job_preference
company
job
job_skill
favorite_job
job_match
recommendation
major_statistics
major_skill_gap
market_demand_statistics
```

详细字段统一写入：

```text
docs/03-database-design.md
database/schema.sql
```

禁止不同成员在本地自行修改字段但不提交文档。

---

## 9. GitHub协作规范

### 9.1 分支

```text
main
最终稳定版本

develop
日常集成版本

feature/data-source
岗位数据采集

feature/infrastructure
Hadoop、HDFS和虚拟机

feature/data-processing
Pandas和Spark处理

feature/student
学生端

feature/university
高校端

feature/recommendation
匹配推荐

feature/frontend
前端公共组件
```

### 9.2 开发流程

```bash
git checkout develop
git pull origin develop

git checkout -b feature/data-processing

# 完成开发和测试
git add .
git commit -m "feat: 完成岗位薪资标准化"

git push origin feature/data-processing
```

随后在GitHub创建Pull Request，请其他成员检查后合并到develop。

### 9.3 提交信息

```text
feat: 新功能
fix: 修复问题
docs: 修改文档
refactor: 重构代码
test: 增加测试
chore: 环境或依赖修改
```

示例：

```text
feat: 增加学生求职意愿接口
fix: 修复8K-12K薪资解析错误
docs: 补充HDFS目录说明
```

### 9.4 禁止提交

- `.env`
- 数据库密码
- 网站Cookie
- 登录Token
- 私钥
- 大型原始数据
- `node_modules`
- Python虚拟环境
- Hadoop运行数据目录
- Spark日志

大型数据放在HDFS或共享存储中，GitHub只保存少量样例数据。

---

## 10. 第一阶段实施顺序

### 第1步：建立仓库和目录

创建完整目录，提交空目录中的 `.gitkeep` 和各模块 `README.md`。

### 第2步：确定共享字段

先完成：

- 原始岗位数据格式
- 清洗后岗位格式
- 学生信息格式
- 推荐结果格式
- 数据库初版结构
- API初版文档

### 第3步：各组并行开发

数据来源组：

- 获取第一批岗位数据
- 输出原始CSV或JSON

基础设施组：

- 配置虚拟机
- 建立HDFS目录
- 提供上传脚本

数据处理组：

- 使用样例数据调试清洗规则
- 完成标准字典

学生端组：

- 使用样例岗位数据开发页面和接口
- 完成信息填写和岗位查询

高校端组：

- 使用样例统计数据开发可视化页面

### 第4步：第一次集成

完成：

```text
原始岗位数据
→ HDFS
→ Spark清洗
→ MySQL
→ Flask岗位接口
→ Vue岗位列表
```

### 第5步：第二次集成

完成：

```text
学生信息
+ 清洗后岗位
→ 人岗匹配
→ 推荐岗位
→ 技能差距
```

### 第6步：第三次集成

完成：

```text
学生求职数据
+ 推荐结果
+ 岗位市场统计
→ 高校分析页面
```

---

## 11. 项目里程碑

### 里程碑一：目录与环境

- GitHub仓库可用
- 各成员完成克隆
- 项目目录建立
- 虚拟机可SSH连接
- HDFS正常运行

### 里程碑二：数据链路

- 已取得岗位数据
- 可上传HDFS
- Spark可读取数据
- 完成基础清洗
- 输出标准岗位表

### 里程碑三：基础系统

- 学生注册登录
- 学生填写求职信息
- 岗位查询和详情
- 高校基础看板

### 里程碑四：核心算法

- 计算匹配度
- 推荐Top-N岗位
- 输出技能差距
- 展示推荐理由

### 里程碑五：完整联调

- 数据采集到前端展示全流程跑通
- 高校端可查看统计结果
- 主要接口测试通过
- 项目可在Linux环境运行

---

## 12. 第一版验收功能

### 数据来源

- 能获取并保存一批真实岗位数据
- 有数据来源和采集时间记录
- 可重复执行采集任务

### 数据存储

- 原始岗位数据可上传HDFS
- HDFS目录结构清晰
- 能查看和下载处理结果

### 数据处理

- 岗位去重
- 薪资标准化
- 城市、学历和经验标准化
- 岗位分类
- 技能提取
- 热门岗位和热门技能统计

### 学生端

- 注册登录
- 填写个人信息和技能
- 填写求职意愿
- 查询岗位
- 查看岗位详情
- 查看推荐岗位
- 查看技能差距

### 高校端

- 查看毕业生求职意愿
- 查看热门岗位和热门技能
- 查看专业平均匹配度
- 查看专业技能差距
- 查看简单就业指导和培养建议

---

## 13. 第一版暂不实现

- 企业注册和岗位发布
- 在线投递和面试
- 正式签约管理
- 复杂简历自动解析
- 深度学习推荐模型
- 实时流数据处理
- Kafka和Flink
- Kubernetes
- 多学校复杂权限体系
- 自动修改培养方案
- 绕过招聘网站验证码或访问限制

---

## 14. 项目初始化命令

在本地执行：

```bash
mkdir -p spark-employment-platform
cd spark-employment-platform

mkdir -p \
data_source/{configs,crawlers,parsers,pipelines,scripts,tests,logs} \
infrastructure/{hadoop,hive/schema,scripts,docs} \
data_processing/{pandas_jobs,spark_jobs,dictionaries,sql,tests,notebooks} \
recommendation/{profile,matching,ranking,explanation,evaluation,tests} \
backend/app/{models,routes,services,schemas,utils,errors} \
backend/{migrations,tests} \
frontend/src/{api,assets,components,layouts,router,stores,utils} \
frontend/src/views/{auth,student,university,admin} \
shared/{schemas,api,constants,examples} \
database/{seed,diagrams} \
deployment/scripts \
docs \
tests/{integration,fixtures} \
scripts

touch README.md LICENSE .gitignore .env.example
touch data_source/logs/.gitkeep
```

初始化Git：

```bash
git init
git branch -M main
git add .
git commit -m "chore: 初始化项目目录"
```

关联GitHub仓库：

```bash
git remote add origin 你的GitHub仓库地址
git push -u origin main
```

创建开发分支：

```bash
git checkout -b develop
git push -u origin develop
```

---

## 15. README维护要求

根目录README负责说明：

- 项目是什么
- 项目整体架构
- 项目目录结构
- 如何启动
- 如何参与开发
- 当前完成进度

每个模块自己的README负责说明：

- 模块职责
- 环境安装
- 输入数据
- 输出数据
- 运行命令
- 测试方法
- 当前负责人
- 当前进度

每次接口、字段或目录发生变化，都必须同步更新文档。
