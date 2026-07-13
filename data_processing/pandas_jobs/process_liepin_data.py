"""
数据清洗 + 分析（与 data/data_process.ipynb 逻辑一致）
对爬取的岗位详情数据做清洗，并生成各维度分析图表
"""

import os
import pandas as pd
import sqlite3
from datetime import datetime
from pathlib import Path

TIMESTAMP = os.environ.get("JOB_DATA_DATE", "2026-07-11")
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_PATH = PROJECT_ROOT / "data_source" / "data" / "raw" / "liepin" / f"date={TIMESTAMP}" / f"job_detail_{TIMESTAMP}.csv"
CLEANED_DIR = PROJECT_ROOT / "data_processing" / "data" / "cleaned" / "liepin" / f"date={TIMESTAMP}"
ANALYSIS_DIR = PROJECT_ROOT / "data_processing" / "output" / "source_analysis" / "liepin" / f"date={TIMESTAMP}"
CLEANED_DIR.mkdir(parents=True, exist_ok=True)
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

# ===== 1. 读取 =====
file_path = RAW_PATH
df = pd.read_csv(file_path)
print(f"读取文件: {file_path}")
print(f"原始: {df.shape[0]} 行, {df.shape[1]} 列")

# ===== 2. 去空 =====
key_cols = [
    "title", "dq", "salary", "requireEduLevel", "company",
    "industry", "compScale", "jobId", "companyId",
]
df.dropna(subset=key_cols, inplace=True)
print(f"去空: {df.shape[0]} 行")

# ===== 3. 去重 =====
dup_cols = [
    "title", "dq", "salary", "requireEduLevel", "requireWorkYears",
    "company", "industry", "compScale", "jobId", "companyId",
]
df.drop_duplicates(subset=dup_cols, keep="first", inplace=True)
print(f"去重: {df.shape[0]} 行")

# ===== 4. 提取城市 =====
df["city"] = df["dq"].str.split("-").str[0].str.strip().str.replace(r"市+$", "", regex=True)
df["city"] = df["city"].replace({"中国": "全国"})

# ===== 5. 统一学历 =====
df.loc[df["requireEduLevel"] == "统招本科", "requireEduLevel"] = "本科"

# ===== 6. 过滤薪资 =====
df = df[df["salary"] != "薪资面议"]
df = df[~df["salary"].str.contains("元/天|元/日", na=False)]
print(f"过滤薪资后: {df.shape[0]} 行")

# ===== 7. 填充经验 =====
df.loc[df["requireWorkYears"].isnull(), "requireWorkYears"] = "经验不限"

# ===== 8. 解析薪资 =====
# 去·15薪等后缀，去k，拆分
salary_clean = df["salary"].str.replace(r"·.*$", "", regex=True).str.replace("k", "", regex=False)
parts = salary_clean.str.split("-", expand=True)

# 过滤掉无法解析的薪资
valid = parts[1].notna() & salary_clean.str.match(r"^\d+\.?\d*-\d+\.?\d*$")
df = df[valid]
parts = parts[valid]

df["salary_min"] = parts[0].astype(float) * 1000
df["salary_max"] = parts[1].astype(float) * 1000
print(f"解析薪资后: {df.shape[0]} 行")

# ===== 9. 保存清洗后数据 =====
cleaned_path = CLEANED_DIR / f"data_cleaned_{TIMESTAMP}.csv"
df.to_csv(cleaned_path, index=False, encoding="utf-8-sig")
print(f"\n保存清洗结果: {cleaned_path}")
print(f"最终: {df.shape[0]} 行, {df.shape[1]} 列")

# ===== 10. 分析 =====
print(f"\n{'=' * 50}")
print("  数据分析")
print(f"{'=' * 50}")

_agg = lambda c: df.groupby(c).agg(岗位数=("title", "count")).sort_values("岗位数", ascending=False)

_sal = lambda c: (
    df.groupby(c)
    .agg(
        平均最低薪=("salary_min", lambda x: round(x.mean(), 0)),
        平均最高薪=("salary_max", lambda x: round(x.mean(), 0)),
        岗位数=("title", "count"),
    )
    .sort_values("岗位数", ascending=False)
)

tables = {
    # 各城市岗位数量
    "city_jobs": _agg("city"),
    # 各行业岗位数量
    "industry_jobs": _agg("industry"),
    # 各城市平均薪资
    "city_salary": _sal("city"),
    # 各行业平均薪资（≥3个岗位的行业）
    "industry_salary": _sal("industry").query("岗位数 >= 3"),
    # 学历分布
    "edu_dist": _agg("requireEduLevel"),
    # 经验分布
    "exp_dist": _agg("requireWorkYears"),
    # 公司规模分布
    "scale_dist": _agg("compScale"),
    # 招聘最多的公司 Top10
    "top_companies": _agg("company").head(10),
    # 整体薪资统计
    "salary_stats": pd.DataFrame(
        {
            "平均最低薪": [round(df["salary_min"].mean(), 0)],
            "平均最高薪": [round(df["salary_max"].mean(), 0)],
            "平均中位数薪资": [round(((df["salary_min"] + df["salary_max"]) / 2).mean(), 0)],
        }
    ),
}

# 打印摘要
for name, t in tables.items():
    print(f"\n--- {name} ---")
    print(t.head(5).to_string())

# ===== 11. 保存分析结果 =====
conn = sqlite3.connect(ANALYSIS_DIR / "jobs_analysis.db")
for name, t in tables.items():
    csv_p = ANALYSIS_DIR / f"{name}.csv"
    t.to_csv(csv_p, index=False, encoding="utf-8-sig")
    t.to_sql(name, conn, if_exists="replace", index=False)
conn.close()

print(f"\n{'=' * 50}")
print(f"  分析结果保存到: {ANALYSIS_DIR}/")
print(f"  共 {len(tables)} 张表")
print(f"{'=' * 50}")
