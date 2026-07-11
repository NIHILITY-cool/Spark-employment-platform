# ncss 岗位字段映射与清洗规则

更新时间：2026-07-11

## 当前主数据

当前只使用国家大学生就业服务平台 ncss 合并总表作为岗位主数据：

```text
data_source/data/raw/ncss_jobs/date=2026-07-11/run=20260711_160114_merged/jobs_ncss_2026-07-11_merged.jsonl
data_source/data/raw/ncss_jobs/date=2026-07-11/run=20260711_160114_merged/jobs_ncss_2026-07-11_merged.csv
```

MOHRSS、BOSS 和 `graduate_jobs` 派生集合已归档，不进入当前清洗主线。

## 组长统一字段

清洗后岗位表按以下字段输出：

```text
job_id
job_name
job_category
company_name
industry
company_scale
city
district
education
experience
salary_raw
salary_min
salary_max
job_description
job_url
crawl_date
```

## ncss 字段映射

| 统一字段 | ncss 原始字段 | 处理方式 |
| --- | --- | --- |
| `job_id` | `source_job_id` | 直接改名 |
| `job_name` | `job_name` | 直接保留 |
| `job_category` | 暂无 | 先置空，后续自动分类 |
| `company_name` | `company_name` | 直接保留 |
| `industry` | `industry` | 直接保留 |
| `company_scale` | `company_size` | 改名 |
| `city` | `city` | 拆分城市和区域，移除末尾的“市”，并将无法细分的“中国”统一为“全国” |
| `district` | `district` | 直接保留；如 `city` 中含 `-` 且本字段为空，则拆出区域 |
| `education` | `education_text` | 改名 |
| `experience` | `experience_text` | 改名；当前 ncss 合并总表该字段基本为空 |
| `salary_raw` | `salary_text` | 改名 |
| `salary_min` | `salary_text` | 从原始薪资解析 |
| `salary_max` | `salary_text` | 从原始薪资解析 |
| `job_description` | `job_description` | 直接保留 |
| `job_url` | `source_url` | 改名 |
| `crawl_date` | `crawl_time` | 取日期部分 |

## 去重规则

- 以 `job_id` 作为唯一键。
- 如果出现重复 `job_id`，保留第一次出现的记录，后续重复记录写入剔除表。

## 无效记录规则

以下记录剔除：

- `job_id` 为空。
- `job_name` 为空。
- `company_name` 为空。
- `job_url` 为空。

## 社会人士岗位过滤规则

ncss 本身是大学生就业服务平台，因此过滤规则采取保守策略，避免误删应届生可投岗位。

剔除：

- 明确要求 3 年及以上工作经验的岗位。
- 明确面向社会招聘，且文本中没有应届、毕业生、校招、校园招聘、实习、三方协议、高校等学生友好关键词的岗位。

暂时保留：

- `应届毕业生优先`
- `有经验者优先`
- `经验不限`
- `应届 + 往届均可`
- 没写经验要求的岗位
- 同时提到校园招聘和社会招聘，但岗位本身仍面向学生或应届生的岗位

## 薪资解析规则

第一版只做月薪范围解析：

| 原始薪资 | `salary_min` | `salary_max` |
| --- | ---: | ---: |
| `4K-6K/月` | 4000 | 6000 |
| `3.5K-6K/月` | 3500 | 6000 |
| `10K-15K/月` | 10000 | 15000 |
| `8K/月` | 8000 | 8000 |
| `20K以上/月` | 20000 | 空 |
| `3K以下/月` | 空 | 3000 |

无法解析、空值或非月薪格式的薪资，`salary_min` 和 `salary_max` 保持为空，并在清洗报告中统计。

## 输出目录

```text
data_processing/data/cleaned/ncss_jobs/date=YYYY-MM-DD/run=YYYYMMDD_HHMMSS/
├── cleaned_jobs_ncss_YYYY-MM-DD.jsonl
├── cleaned_jobs_ncss_YYYY-MM-DD.csv
├── excluded_jobs_ncss_YYYY-MM-DD.jsonl
├── excluded_jobs_ncss_YYYY-MM-DD.csv
├── cleaning_report.json
└── cleaning_report.md
```

## 后续待做

- `job_category` 后续通过岗位名称和描述自动分类。
- 技能提取后续单独输出 `job_skill` 表。
- 如果组长提供更严格的毕业生筛选规则，需要同步修改本文档和清洗脚本。
