# 数据处理与分析模块

## 模块职责

使用 Pandas 和 Spark 完成岗位数据清洗、标准化、技能提取、岗位画像构建和市场需求统计分析。

行业字段通过 `dictionaries/industries.csv` 的标准行业、别名和关键词统一归类。Pandas 合并任务与 Spark 主清洗任务共用 `industry_normalization.py` 规则；低置信度值归入“其他”，空值保留为“未标注”。

## 环境安装

```bash
cd data_processing
pip install -r requirements.txt
```

## 输入数据

- HDFS 原始岗位数据
- 标准字典文件（dictionaries/）

## 输出数据

- HDFS 清洗后岗位数据
- 岗位技能数据
- 岗位画像
- 市场统计结果
- Hive 分析表

## 已合并的本地处理结果（2026-07-11）

- `data/cleaned/`：猎聘与 ncss 清洗结果，ncss 同时保留被剔除岗位。
- `data/standardized/`：国聘、猎聘、ncss 的统一标准岗位表，以及三站合并表。
- `output/market_analysis/`：三站合并后的城市、行业、学历、经验、薪资和来源分布统计。
- `output/source_analysis/liepin/`：猎聘单源分析结果。
- `reports/ncss/`：ncss 合并、质量和清洗报告。

原始快照和 CSV 结果均按项目 `.gitignore` 策略保留在本地，不会被误提交。可复现脚本包括 `pandas_jobs/clean_ncss_jobs.py`、`pandas_jobs/process_liepin_data.py`、`pandas_jobs/standardize_liepin_jobs.py` 和 `pipelines/unify_job_sources.py`。

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
# Pandas 探索
python pandas_jobs/inspect_raw_data.py

# Spark 清洗
spark-submit spark_jobs/job_cleaning.py

# 导出结果
spark-submit spark_jobs/export_results.py
```

### 虚拟机 Spark 批处理

HDFS Raw 数据按 `source=guopin|liepin|ncss/date=YYYY-MM-DD` 分区存放。首次处理已在 2026-07-11 数据上验证，输出分别写入 HDFS 的 Cleaned、DWD 与 Output 层。

智联招聘快照作为第四个来源，使用 `source=zhilian/date=2026-07-11` 分区。首次接入或重算该日期前，先上传本地快照：

```bash
hdfs dfs -mkdir -p /employment-platform/raw/jobs/source=zhilian/date=2026-07-11
hdfs dfs -put -f ../data_source/data/raw/zhilian/date=2026-07-11/jobs_zhilian_2026-07-11.csv \
  /employment-platform/raw/jobs/source=zhilian/date=2026-07-11/
```

```bash
export HADOOP_CONF_DIR="$HOME/opt/hadoop-3.5.0/etc/hadoop"
export HADOOP_HOME="$HOME/opt/hadoop-3.5.0"
export SPARK_HOME="$HOME/opt/spark-4.1.2"

# 将 Raw CSV 清洗为统一岗位表（首次运行保持默认 errorifexists）
$SPARK_HOME/bin/spark-submit \
  --master spark://192.168.64.2:7077 \
  --conf spark.hadoop.fs.defaultFS=hdfs://hwadee01:9000 \
  --conf spark.sql.shuffle.partitions=8 \
  spark_jobs/job_cleaning.py --date 2026-07-11

# 基于 DWD 岗位表生成市场统计
$SPARK_HOME/bin/spark-submit \
  --master spark://192.168.64.2:7077 \
  --conf spark.hadoop.fs.defaultFS=hdfs://hwadee01:9000 \
  --conf spark.sql.shuffle.partitions=8 \
  spark_jobs/market_statistics.py --date 2026-07-11

# 使用字典完成岗位分类与技能提取
$SPARK_HOME/bin/spark-submit \
  --master spark://192.168.64.2:7077 \
  --conf spark.hadoop.fs.defaultFS=hdfs://hwadee01:9000 \
  --conf spark.sql.shuffle.partitions=8 \
  spark_jobs/skill_extraction.py --date 2026-07-11
```

若某一日期分区需要整体重算，显式追加 `--mode overwrite`；不要直接删除 HDFS 原始数据。城市口径变更或新增数据源时，依次重跑清洗、市场统计、技能提取和 MySQL 导出，确保前端与数据库使用同一快照。

## 测试方法

```bash
cd data_processing
pytest tests/
```

## 当前负责人

待分配

## 当前进度

参见 `docs/10-progress-log.md`
