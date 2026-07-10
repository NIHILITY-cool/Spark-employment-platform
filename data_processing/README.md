# 数据处理与分析模块

## 模块职责

使用 Pandas 和 Spark 完成岗位数据清洗、标准化、技能提取、岗位画像构建和市场需求统计分析。

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

## 测试方法

```bash
cd data_processing
pytest tests/
```

## 当前负责人

待分配

## 当前进度

参见 `docs/10-progress-log.md`
