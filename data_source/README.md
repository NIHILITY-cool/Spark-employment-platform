# 数据来源模块

## 模块职责

负责公开招聘岗位数据的采集、解析、保存和质量检查。

## 环境安装

```bash
cd data_source
pip install -r requirements.txt
```

## 输入数据

- 公开招聘网站或公开数据集

## 输出数据

- 原始岗位数据（CSV / JSON）
- 采集日志
- 数据质量报告

## 已合并的数据源（2026-07-11）

- **国聘**：原始快照位于 `data/raw/guopin/date=2026-07-11/`；采集器为 `crawlers/guopin_job_crawler.py`。
- **猎聘**：原始快照位于 `data/raw/liepin/date=2026-07-11/`；采集器为 `crawlers/liepin_job_crawler.py`。
- **国家大学生就业服务平台（ncss）**：原始合并快照位于 `data/raw/ncss_jobs/date=2026-07-11/run=20260711_160114_merged/`；通用爬虫、解析器和校验脚本已分别归入 `crawlers/`、`parsers/`、`scripts/`。
- **智联招聘**：原始快照位于 `data/raw/zhilian/date=2026-07-11/jobs_zhilian_2026-07-11.csv`。该快照为无表头 CSV，由 Spark 使用固定 13 列模式读取；不导入旧采集脚本中的会话信息或凭据。

原始数据目录被 `.gitignore` 排除，便于本地与 HDFS 使用而不会误提交大文件。ncss 的采集台账与字段说明见 `../docs/data-source/ncss/`。

采集器不会携带会话信息。若公开接口在合法访问边界内要求本机会话，只能通过本地环境变量提供，且不得提交：`GUOPIN_API_AUTH`、`LIEPIN_COOKIE`、`LIEPIN_XSRF_TOKEN`。

智联快照以岗位链接生成稳定来源岗位 ID；仅解析月薪范围，日薪、时薪、次薪和面议薪资不折算为月薪。

## 运行命令

```bash
# 运行采集
python scripts/run_crawler.py

# 验证原始数据
python scripts/validate_raw_data.py

# 上传到 HDFS
bash scripts/upload_raw_to_hdfs.sh
```

## 测试方法

```bash
cd data_source
pytest tests/
```

## 当前负责人

待分配

## 当前进度

参见 `docs/10-progress-log.md`
