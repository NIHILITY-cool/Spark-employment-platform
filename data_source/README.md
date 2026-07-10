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
