# 数据来源模块

## 模块职责

负责公开招聘岗位数据的采集、解析、保存和质量检查。

当前主线数据源：
- 国家大学生就业服务平台：`https://www.ncss.cn/`

已归档、不作为当前主数据的数据源/派生集：
- 中国公共招聘网 MOHRSS：岗位不全是毕业生岗位，暂不进入当前主分析。
- BOSS 直聘实验：采集失败，暂不进入当前主分析。
- `graduate_jobs` 派生集合：由其他对话二次整理生成，容易与 ncss 主数据重复或混淆，暂不进入当前主分析。

归档位置：

```text
data_source/_archive_unused/20260711_cleanup/
```

当前采集对象：
- 公开职位列表接口：`/student/jobs/jobslist/ajax/`
- 公开职位详情页：`/student/jobs/{jobId}/detail.html`

## 环境安装

```bash
cd data_source
pip install -r requirements.txt
```

## 输出字段

岗位原始数据字段已对齐小组 `plan.md`，并补充岗位职责字段：

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
job_responsibility
job_requirement
publish_time
source_name
source_url
crawl_time
```

字段说明：
- `job_description`：岗位详情原文。
- `job_responsibility`：优先从“岗位职责 / 工作内容 / 职位描述 / 岗位描述”等段落抽取；如果没有显式标题，则回退为岗位详情原文。
- `job_requirement`：从“任职要求 / 岗位要求 / 职位要求”等段落抽取。
- `raw.job_responsibility_source`：记录 `job_responsibility` 的来源，可能是 `explicit_heading`、`fallback_job_description` 或 `missing`。

## 输出目录

```text
data_source/data/raw/ncss_jobs/date=YYYY-MM-DD/run=YYYYMMDD_HHMMSS/
├── api_responses/
├── detail_pages/
├── jobs_ncss_YYYY-MM-DD_batch001.jsonl
├── jobs_ncss_YYYY-MM-DD_batch001.csv
├── crawl_manifest.json
├── raw_data_quality_report.json
└── raw_data_quality_report.md
```

说明：`data_source/data/` 属于本地原始数据目录，已被 `.gitignore` 排除，不建议直接提交到 GitHub。

补充说明：MOHRSS、BOSS 和 `graduate_jobs` 的历史数据、脚本、配置和日志已归档到 `_archive_unused/20260711_cleanup/`，保留追溯但不参与当前主线。

## 运行命令

```bash
# 默认采集
python scripts/run_crawler.py

# 指定页数和每页数量
python scripts/run_crawler.py --max-pages 5 --page-size 20

# 从指定页开始采集，适合补抓
python scripts/run_crawler.py --start-page 6 --max-pages 5 --page-size 20

# 按多个地区批量采集，并按 source_job_id 去重
python scripts/run_crawler.py --area-codes 11,31,44,32,33,51,42,61,12,13,37,50 --max-pages 5 --page-size 20 --delay-seconds 0.5

# 按公开筛选条件分片扩量。注意含 01 这类前导 0 的参数必须加引号。
python scripts/run_crawler.py --all-area-codes --category-codes "01,02,03" --max-pages 5 --page-size 20 --delay-seconds 0.3 --seen-jsonl "已有jsonl1,已有jsonl2"
python scripts/run_crawler.py --all-area-codes --degree-codes "51,41,31,11,01" --max-pages 5 --page-size 20 --delay-seconds 0.3 --seen-jsonl "已有jsonl1,已有jsonl2"
python scripts/run_crawler.py --all-area-codes --month-pays "2,2-5,5-10,10-15,15-25,25-50,50,0" --max-pages 5 --page-size 20 --delay-seconds 0.3 --seen-jsonl "已有jsonl1,已有jsonl2"
python scripts/run_crawler.py --all-area-codes --job-types "01,02,03" --max-pages 5 --page-size 20 --delay-seconds 0.3 --seen-jsonl "已有jsonl1,已有jsonl2"

# 只采列表，不抓详情页
python scripts/run_crawler.py --max-pages 5 --page-size 20 --no-details

# 用岗位详情原文补全缺失的 job_responsibility
python scripts/enrich_responsibility_fallback.py

# 验证最新非空原始数据
python scripts/validate_raw_data.py

# 验证指定文件
python scripts/validate_raw_data.py --input data/raw/ncss_jobs/date=YYYY-MM-DD/run=YYYYMMDD_HHMMSS/jobs_ncss_YYYY-MM-DD_batch001.jsonl

# 合并多个 ncss 原始岗位批次，按 source_job_id 去重
python scripts/merge_raw_jobs.py --inputs "jsonl1,jsonl2,jsonl3"

# 上传到 HDFS
bash scripts/upload_raw_to_hdfs.sh
```

## 当前正式采集结果

### 国家大学生就业服务平台 ncss

2026-07-10 至 2026-07-11 已完成 ncss 公开岗位数据多轮分片扩量，并合并为当前推荐总表。

推荐使用的合并总表：

```text
data_source/data/raw/ncss_jobs/date=2026-07-11/run=20260711_160114_merged/jobs_ncss_2026-07-11_merged.jsonl
data_source/data/raw/ncss_jobs/date=2026-07-11/run=20260711_160114_merged/jobs_ncss_2026-07-11_merged.csv
```

合并与质量结果：
- 输入正式/保留批次：12 个。
- 合并后岗位记录：10834 条。
- 唯一岗位 ID：10834 个。
- 重复岗位 ID：0 个。
- `source_job_id`、`job_name`、`company_name`、`city`、`salary_text`、`education_text`、`source_name`、`source_url`、`crawl_time` 均无缺失。
- `job_description` 缺失 39 条，缺失率 0.36%。
- `job_responsibility` 缺失 39 条，缺失率 0.36%。
- `job_responsibility` 来源：5117 条来自显式标题抽取，5678 条来自岗位详情原文回退，39 条确实缺失。
- 合并 manifest：`data_source/data/raw/ncss_jobs/date=2026-07-11/run=20260711_160114_merged/merge_manifest.json`。
- 总表质量报告：`data_source/data/raw/ncss_jobs/date=2026-07-11/run=20260711_160114_merged/raw_data_quality_report.md`。
- `data_source/data/raw/ncss_jobs/` 当前原始文件总数约 15590 个，总大小约 1065.08 MB。

正式/保留批次清单：

| 批次 | 分片方式 | 新增记录 |
| --- | --- | ---: |
| `run=20260710_202419` | 12 个重点地区 | 1200 |
| `run=20260710_205055` | 全部省级地区 | 1576 |
| `run=20260710_210645` | 职业类别分片试跑，参数未保留前导 0，仅保留有效记录 | 182 |
| `run=20260710_211137` | 职业类别 `01-10` | 3388 |
| `run=20260710_214233` | 职业类别 `11-20`，网络中断后从已保存响应恢复 | 1149 |
| `run=20260711_150424` | 职业类别 `11-12` 补采 | 461 |
| `run=20260711_151058` | 职业类别 `13-16` | 455 |
| `run=20260711_151710` | 职业类别 `17-20` | 173 |
| `run=20260711_152036` | 职业类别 `21-29` | 2162 |
| `run=20260711_154411` | 学历分片 | 56 |
| `run=20260711_154948` | 薪资分片 | 28 |
| `run=20260711_155717` | 职位类型分片 | 4 |

说明：
- 当前采集没有使用登录态，没有绕过权限。
- 未筛选列表第 6 页公开接口返回 `请登录后查看`，因此通过地区、职业类别、学历、薪资、职位类型等公开筛选参数进行分片扩量。
- 学历、薪资、职位类型三轮分片新增分别只有 56、28、4 条，说明在当前公开访问边界内，继续用同类参数扩量的边际收益很低。
- 早期 `run=20260710_200638` 是 100 条样本批次，`run=20260710_202337` 是小规模测试批次，均不作为当前推荐主数据。

总表质量报告：

```text
data_source/data/raw/ncss_jobs/date=2026-07-11/run=20260711_160114_merged/raw_data_quality_report.md
```

### 历史归档：MOHRSS

2026-07-10 曾完成中国公共招聘网公开岗位小批量采集：
- 采集范围：2 页，每页 20 条。
- 原始岗位记录：40 条。
- 唯一岗位 ID：40 个。
- 重复岗位 ID：0 个。
- `source_job_id`、`job_name`、`company_name`、`city`、`salary_text`、`education_text`、`job_description`、`source_name`、`source_url`、`crawl_time` 均无缺失。
- `job_responsibility` 缺失 38 条，缺失率 95%，原因是该源大量岗位描述没有“岗位职责/工作内容”等显式标题；后续清洗可优先使用 `job_description`。
- 联系方式过滤检查：输出目录中未发现 `aae004`、`aae005`、`aae006`、联系人、联系电话、手机等字段或文本。

历史输出位置已归档为：

```text
data_source/_archive_unused/20260711_cleanup/data/raw/mohrss_jobs/date=2026-07-10/run=20260710_204514/
```

2026-07-10 曾继续完成中国公共招聘网公开岗位扩量采集与合并：
- 采集范围：第 1-103 页，每页 20 条。
- 合并后岗位记录：2060 条。
- 唯一岗位 ID：2060 个。
- 重复岗位 ID：0 个。
- `source_job_id`、`job_name`、`company_name`、`city`、`salary_text`、`education_text`、`job_description`、`source_name`、`source_url`、`crawl_time` 均无缺失。
- 手机号形态文本已统一替换为 `[PHONE_REDACTED]`，复扫结果为 0 个手机号形态文本命中。
- 学历代码 `21`、`47`、`81` 已映射为 `大学本科`、`技工学校`、`小学`。

该数据源岗位不全是毕业生岗位，当前不推荐作为主数据。历史合并批次已归档为：

```text
data_source/_archive_unused/20260711_cleanup/data/raw/mohrss_jobs/date=2026-07-10/run=20260710_210426_merged/
```

## 公开访问边界记录

2026-07-10 已尝试从第 6 页继续采集未筛选的 ncss 岗位列表：

```bash
python scripts/run_crawler.py --start-page 6 --max-pages 5 --page-size 20
```

平台公开接口返回 `请登录后查看`。因此当前不采集登录后内容，不绕过权限。

边界记录批次：

```text
data_source/data/raw/ncss_jobs/date=2026-07-10/run=20260710_201505/
```

说明：`run=20260710_201338` 是修复空响应处理前产生的中间失败目录，不作为正式数据批次。`run=20260710_202337` 是地区批量逻辑的小规模测试批次，不作为正式数据批次。

## 当前进度

参见 `docs/10-progress-log.md`。
