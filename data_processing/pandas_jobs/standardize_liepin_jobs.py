"""
字段标准化映射
将清洗后的数据转换为统一标准字段格式
"""

import pandas as pd
import os
from pathlib import Path

TIMESTAMP = os.environ.get("JOB_DATA_DATE", "2026-07-11")
PROJECT_ROOT = Path(__file__).resolve().parents[2]
INPUT_PATH = PROJECT_ROOT / "data_processing" / "data" / "cleaned" / "liepin" / f"date={TIMESTAMP}" / f"data_cleaned_{TIMESTAMP}.csv"
OUTPUT_DIR = PROJECT_ROOT / "data_processing" / "data" / "standardized" / f"date={TIMESTAMP}"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ===== 1. 读取清洗后数据 =====
df = pd.read_csv(INPUT_PATH)
print(f"读入: {df.shape[0]} 行, {df.shape[1]} 列")

# ===== 2. 字段映射 =====
result = pd.DataFrame()

# 直接映射
result["job_id"] = df["jobId"].astype(int)
result["job_name"] = df["title"]
result["job_category"] = ""                                                    # 后续自动分类，暂为空
result["company_name"] = df["company"]
result["industry"] = df["industry"]
result["company_scale"] = df["compScale"]
result["city"] = df["dq"].str.split("-").str[0].str.strip().str.replace(r"市+$", "", regex=True)
result["city"] = result["city"].replace({"中国": "全国"})
result["district"] = df["dq"].str.split("-").str[1].str.strip()                # 北京-建外大街 → 建外大街
result["education"] = df["requireEduLevel"]
result["experience"] = df["requireWorkYears"]
result["salary_raw"] = df["salary"]
result["salary_min"] = df["salary_min"].astype(int)
result["salary_max"] = df["salary_max"].astype(int)
result["job_description"] = df["job_description"]
result["job_url"] = df["jobLink"]
result["crawl_date"] = TIMESTAMP

print(f"字段数: {len(result.columns)}")
print(f"列名: {list(result.columns)}")

# ===== 3. 保存 =====
output_path = OUTPUT_DIR / f"job_standard_liepin_{TIMESTAMP}.csv"
result.to_csv(output_path, index=False, encoding="utf-8-sig")
print(f"\n保存: {output_path}")
print(f"共 {len(result)} 条")

# ===== 4. 预览 =====
print(f"\n--- 前5条 ---")
print(result.head(5).to_string())
print(f"\n--- 数据类型 ---")
print(result.dtypes)
