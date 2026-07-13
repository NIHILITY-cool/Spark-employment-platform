# 数据处理与分析模块

## 模块职责

使用 Pandas 和 Spark 完成岗位数据清洗、标准化、技能提取、岗位画像构建和市场需求统计分析。

## 环境安装

```bash
cd data_processing
pip install -r requirements.txt
```

## 输入数据

- 当前本地主输入：`../data_source/data/raw/ncss_jobs/date=2026-07-11/run=20260711_160114_merged/jobs_ncss_2026-07-11_merged.jsonl`
- HDFS 原始岗位数据
- 标准字典文件（dictionaries/）

## 输出数据

- 当前本地清洗结果：`data/cleaned/ncss_jobs/date=2026-07-11/run=20260711_163237/`
- HDFS 清洗后岗位数据
- 岗位技能数据
- 岗位画像
- 市场统计结果
- Hive 分析表

## 目录说明

| 目录 | 用途 |
|------|------|
| `pandas_jobs/` | Pandas 快速探索和规则试验 |
| `spark_jobs/` | Spark 批量清洗和统计分析 |
| `dictionaries/` | 标准字典（技能、专业、城市等） |
| `sql/` | Spark SQL 查询脚本 |
| `notebooks/` | Jupyter 探索笔记 |

## 运行命令

```bash
# ncss 岗位清洗：字段统一、去重、薪资解析、明显社会人士岗位过滤
python pandas_jobs/clean_ncss_jobs.py

# 查看清洗规则
type CLEANING_RULES.md

# Spark 清洗
spark-submit spark_jobs/job_cleaning.py

# 导出结果
spark-submit spark_jobs/export_results.py
```

## 测试方法

```bash
cd data_processing
pytest tests/
```

## 当前负责人

待分配

## 当前进度

参见 `../docs/10-progress-log.md`

## 当前清洗结果

2026-07-11 已按组长统一字段标准完成 ncss 岗位第一版清洗：

- 输入记录数：10834
- 清洗后记录数：10809
- 剔除记录数：25
- 唯一岗位 ID 数：10809
- 薪资解析：10834 条全部成功解析为月薪范围
- `job_category` 暂时为空，后续自动分类
- `experience` 当前为空，原因是 ncss 合并原始表该字段为空
- `district` 当前为空，原因是 ncss 当前地点主要为省/直辖市级

输出位置：

```text
data/cleaned/ncss_jobs/date=2026-07-11/run=20260711_163237/
├── cleaned_jobs_ncss_2026-07-11.jsonl
├── cleaned_jobs_ncss_2026-07-11.csv
├── excluded_jobs_ncss_2026-07-11.jsonl
├── excluded_jobs_ncss_2026-07-11.csv
├── cleaning_report.json
└── cleaning_report.md
```
