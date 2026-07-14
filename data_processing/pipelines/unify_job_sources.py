"""
统一数据处理流水线
以 liepin 的处理方式为基准，处理 guopin 和 ncss 的数据：
  1. 去重（按关键字段）
  2. 去掉没有岗位描述的
  3. 工作经验没有的当"经验不限"
  4. 统一标准化字段输出

用法: python unified_process.py
"""

import os
import sys
import pandas as pd
from datetime import datetime
from pathlib import Path

TIMESTAMP = os.environ.get("JOB_DATA_DATE", "2026-07-11")
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
from data_processing.industry_normalization import normalize_industry

DATA_SOURCE_ROOT = PROJECT_ROOT / "data_source" / "data" / "raw"
DATA_PROCESSING_ROOT = PROJECT_ROOT / "data_processing"

# ============================================================
#  输出目录
# ============================================================
DIR_OUTPUT = DATA_PROCESSING_ROOT / "data" / "standardized" / f"date={TIMESTAMP}"
DIR_ANALYSIS = DATA_PROCESSING_ROOT / "output" / "market_analysis" / f"date={TIMESTAMP}"
DIR_OUTPUT.mkdir(parents=True, exist_ok=True)
DIR_ANALYSIS.mkdir(parents=True, exist_ok=True)

# ============================================================
#  标准字段
# ============================================================
STANDARD_FIELDS = [
    "job_id", "job_name", "job_category", "company_name", "industry",
    "company_scale", "city", "district", "education", "experience",
    "salary_raw", "salary_min", "salary_max", "job_description",
    "job_url", "crawl_date", "source",
]

# ============================================================
#  1. 处理 liepin（已标准化，作为基准）
# ============================================================
def process_liepin():
    """读取 liepin 已标准化的数据"""
    path = DIR_OUTPUT / f"job_standard_liepin_{TIMESTAMP}.csv"
    if not os.path.exists(path):
        print(f"⚠️  liepin 标准化文件不存在: {path}")
        return None

    df = pd.read_csv(path)
    df["source"] = "liepin"
    print(f"\n{'='*50}")
    print(f"  liepin 数据")
    print(f"{'='*50}")
    print(f"  读取: {len(df)} 行, {len(df.columns)} 列")

    # 确保 salary_min/salary_max 为数值
    df["salary_min"] = pd.to_numeric(df["salary_min"], errors="coerce")
    df["salary_max"] = pd.to_numeric(df["salary_max"], errors="coerce")

    # 去掉没有岗位描述的
    before = len(df)
    df = df[df["job_description"].notna() & (df["job_description"].str.strip() != "")]
    print(f"  去掉无描述: {before} → {len(df)} 行")

    # 经验不限填充
    df["experience"] = df["experience"].fillna("经验不限")
    df.loc[df["experience"].str.strip() == "", "experience"] = "经验不限"

    print(f"  最终: {len(df)} 行")
    return df


# ============================================================
#  2. 处理 guopin（原始CSV无表头，需要按liepin方式清洗）
# ============================================================
def process_guopin():
    """处理国聘数据"""
    path = DATA_SOURCE_ROOT / "guopin" / f"date={TIMESTAMP}" / f"jobs_guopin_{TIMESTAMP}.csv"
    if not os.path.exists(path):
        print(f"⚠️  guopin 文件不存在: {path}")
        return None

    # guopin CSV 无表头，列顺序固定
    COL_NAMES = [
        "job_id",           # 0: bigint job id
        "job_category",     # 1: category text
        "job_name",         # 2: job title
        "company_name",     # 3: company
        "_unused",          # 4: empty/company_short
        "location",         # 5: city-district
        "education",        # 6: education
        "experience",       # 7: work experience
        "salary_min",       # 8: salary min (already yuan)
        "salary_max",       # 9: salary max (already yuan)
        "job_description",  # 10: description (multiline)
        "job_url",          # 11: url
        "crawl_date",       # 12: crawl date
    ]

    df = pd.read_csv(path, names=COL_NAMES, header=None)
    # 兼容历史无表头快照和当前采集器写出的带表头 CSV。
    if not df.empty and str(df.iloc[0]["job_id"]).strip() == "job_id":
        df = df.iloc[1:].copy()

    print(f"\n{'='*50}")
    print(f"  guopin 数据")
    print(f"{'='*50}")
    print(f"  读取: {len(df)} 行")

    # --- 去空关键字段 ---
    key_cols = ["job_id", "job_name", "company_name", "education", "location"]
    for col in key_cols:
        before = len(df)
        df = df[df[col].notna() & (df[col].astype(str).str.strip() != "")]
        if len(df) < before:
            print(f"  去空({col}): {before} → {len(df)} 行")

    # --- 去掉没有岗位描述的（参考liepin方式）---
    before = len(df)
    df = df[df["job_description"].notna() & (df["job_description"].astype(str).str.strip() != "")]
    print(f"  去掉无描述: {before} → {len(df)} 行")

    # --- 工作经验没有就当"经验不限" ---
    df["experience"] = df["experience"].fillna("经验不限")
    df.loc[df["experience"].astype(str).str.strip() == "", "experience"] = "经验不限"
    null_exp_before = (df["experience"] == "经验不限").sum()
    print(f"  经验不限: {null_exp_before} 条")

    # --- 去重（参考liepin的dup_cols）---
    dup_cols = [
        "job_name", "location", "education", "experience",
        "company_name", "job_id",
    ]
    # 只用在df里存在的列
    dup_cols = [c for c in dup_cols if c in df.columns]
    before = len(df)
    df.drop_duplicates(subset=dup_cols, keep="first", inplace=True)
    print(f"  去重: {before} → {len(df)} 行")

    # --- 提取城市和区域 ---
    df["city"] = df["location"].astype(str).str.split("-").str[0].str.strip()
    df["district"] = df["location"].astype(str).str.split("-").str[1].str.strip()
    # 处理没有district的情况
    df["district"] = df["district"].fillna("")

    # --- 统一学历 ---
    if "requireEduLevel" in df.columns:
        df.loc[df["education"] == "统招本科", "education"] = "本科"

    # --- 薪资已在元单位，保持不变 ---
    df["salary_min"] = pd.to_numeric(df["salary_min"], errors="coerce")
    df["salary_max"] = pd.to_numeric(df["salary_max"], errors="coerce")

    # --- 构建 salary_raw ---
    def build_salary_raw(row):
        if pd.notna(row["salary_min"]) and pd.notna(row["salary_max"]):
            lo = int(row["salary_min"])
            hi = int(row["salary_max"])
            if lo >= 1000 and hi >= 1000:
                return f"{lo//1000}k-{hi//1000}k"
            return f"{lo}-{hi}"
        return ""

    df["salary_raw"] = df.apply(build_salary_raw, axis=1)

    # --- 标准化字段映射 ---
    result = pd.DataFrame()
    result["job_id"] = df["job_id"].astype(str).str.strip()
    result["job_name"] = df["job_name"].astype(str).str.strip()
    result["job_category"] = df["job_category"].astype(str).str.strip()
    result["company_name"] = df["company_name"].astype(str).str.strip()
    result["industry"] = ""                          # guopin 无行业字段
    result["company_scale"] = ""                     # guopin 无规模字段
    result["city"] = df["city"]
    result["district"] = df["district"]
    result["education"] = df["education"].astype(str).str.strip()
    result["experience"] = df["experience"].astype(str).str.strip()
    result["salary_raw"] = df["salary_raw"]
    result["salary_min"] = df["salary_min"]
    result["salary_max"] = df["salary_max"]
    result["job_description"] = df["job_description"].astype(str).str.strip()
    result["job_url"] = df["job_url"].astype(str).str.strip()
    result["crawl_date"] = df["crawl_date"].astype(str).str.strip()
    result["source"] = "guopin"

    # --- 清理 crawl_date 格式 ---
    result["crawl_date"] = result["crawl_date"].str.replace("-", "").str[:8]
    # 格式化为 YYYY-MM-DD
    def fmt_date(d):
        d = str(d).strip()
        if len(d) == 8 and d.isdigit():
            return f"{d[:4]}-{d[4:6]}-{d[6:8]}"
        return d
    result["crawl_date"] = result["crawl_date"].apply(fmt_date)

    print(f"  最终: {len(result)} 行, {len(result.columns)} 列")
    return result


# ============================================================
#  3. 处理 ncss（已清洗，但需要统一按liepin规则再处理）
# ============================================================
def process_ncss():
    """处理ncss数据"""
    path = DATA_PROCESSING_ROOT / "data" / "cleaned" / "ncss_jobs" / f"date={TIMESTAMP}" / "run=20260711_163237" / f"cleaned_jobs_ncss_{TIMESTAMP}.csv"
    if not os.path.exists(path):
        print(f"⚠️  ncss 文件不存在: {path}")
        return None

    df = pd.read_csv(path)

    print(f"\n{'='*50}")
    print(f"  ncss 数据")
    print(f"{'='*50}")
    print(f"  读取: {len(df)} 行")

    # --- 去掉没有岗位描述的（参考liepin方式）---
    before = len(df)
    df = df[df["job_description"].notna() & (df["job_description"].astype(str).str.strip() != "")]
    print(f"  去掉无描述: {before} → {len(df)} 行")

    # --- 工作经验没有就当"经验不限" ---
    df["experience"] = df["experience"].fillna("经验不限")
    df.loc[df["experience"].astype(str).str.strip() == "", "experience"] = "经验不限"
    null_exp = (df["experience"] == "经验不限").sum()
    print(f"  经验不限: {null_exp} 条")

    # --- 确保 salary 为数值 ---
    df["salary_min"] = pd.to_numeric(df["salary_min"], errors="coerce")
    df["salary_max"] = pd.to_numeric(df["salary_max"], errors="coerce")

    # --- 去重（参考liepin的dup_cols）---
    dup_cols = [
        "job_name", "city", "education", "experience",
        "company_name", "industry", "job_id",
    ]
    dup_cols = [c for c in dup_cols if c in df.columns]
    before = len(df)
    df.drop_duplicates(subset=dup_cols, keep="first", inplace=True)
    print(f"  去重: {before} → {len(df)} 行")

    # --- 统一字段 ---
    # 选择存在且需要的标准字段
    available_std = [c for c in STANDARD_FIELDS if c in df.columns and c != "source"]
    result = df[available_std].copy()
    result["source"] = "ncss"

    # 确保所有标准字段都存在
    for col in STANDARD_FIELDS:
        if col not in result.columns:
            result[col] = ""

    print(f"  最终: {len(result)} 行, {len(result.columns)} 列")
    return result


# ============================================================
#  4. 合并 & 分析
# ============================================================
def merge_and_analyze(dfs: list[pd.DataFrame]):
    """合并所有数据，跨源去重，输出分析"""
    print(f"\n{'#'*50}")
    print(f"  合并 & 分析")
    print(f"{'#'*50}")

    # 合并
    df_all = pd.concat(dfs, ignore_index=True)
    df_all["city"] = (
        df_all["city"].fillna("").astype(str).str.strip().str.replace(r"市+$", "", regex=True)
        .replace({"中国": "全国"})
    )
    df_all["industry"] = df_all["industry"].apply(lambda value: normalize_industry(value).industry)
    print(f"\n  合并后: {len(df_all)} 行")

    # 按source统计
    print(f"  各来源数量:")
    for s in df_all["source"].unique():
        print(f"    {s}: {len(df_all[df_all['source'] == s])}")

    # --- 跨源去重（同岗位名+同城市+同公司）---
    cross_dup_cols = ["job_name", "company_name", "city"]
    before = len(df_all)
    df_all.drop_duplicates(subset=cross_dup_cols, keep="first", inplace=True)
    print(f"  跨源去重(job_name+company_name+city): {before} → {len(df_all)} 行")

    # 确保标准列
    for col in STANDARD_FIELDS:
        if col not in df_all.columns:
            df_all[col] = ""

    df_out = df_all[STANDARD_FIELDS].copy()

    # 保存合并标准数据
    merged_path = DIR_OUTPUT / f"job_standard_all_{TIMESTAMP}.csv"
    df_out.to_csv(merged_path, index=False, encoding="utf-8-sig")
    print(f"\n  合并标准数据: {merged_path} ({len(df_out)} 条, {len(df_out.columns)} 列)")

    # 按来源分别保存
    for src in df_out["source"].unique():
        src_df = df_out[df_out["source"] == src].drop(columns=["source"])
        src_path = DIR_OUTPUT / f"job_standard_{src}_{TIMESTAMP}.csv"
        src_df.to_csv(src_path, index=False, encoding="utf-8-sig")
        print(f"  {src} 标准数据: {src_path} ({len(src_df)} 条)")

    # --- 分析 ---
    print(f"\n{'='*50}")
    print(f"  数据分析")
    print(f"{'='*50}")

    # 使用统一数据做分析
    df = df_out.copy()
    # 只取有薪资范围的数据
    df_sal = df[df["salary_min"].notna() & df["salary_max"].notna()]

    _agg = lambda c: df.groupby(c).agg(岗位数=("job_name", "count")).sort_values("岗位数", ascending=False)

    _sal = lambda c: (
        df_sal.groupby(c)
        .agg(
            平均最低薪=("salary_min", lambda x: round(x.mean(), 0)),
            平均最高薪=("salary_max", lambda x: round(x.mean(), 0)),
            岗位数=("job_name", "count"),
        )
        .sort_values("岗位数", ascending=False)
    )

    tables = {
        "city_jobs": _agg("city"),
        "industry_jobs": _agg("industry"),
        "city_salary": _sal("city"),
        "industry_salary": _sal("industry").query("岗位数 >= 3"),
        "edu_dist": _agg("education"),
        "exp_dist": _agg("experience"),
        "source_dist": _agg("source"),
        "salary_stats": pd.DataFrame({
            "平均最低薪": [round(df_sal["salary_min"].mean(), 0)],
            "平均最高薪": [round(df_sal["salary_max"].mean(), 0)],
            "平均中位数薪资": [round(((df_sal["salary_min"] + df_sal["salary_max"]) / 2).mean(), 0)],
        }),
    }

    import sqlite3
    conn = sqlite3.connect(DIR_ANALYSIS / "jobs_analysis.db")
    for name, t in tables.items():
        csv_p = DIR_ANALYSIS / f"{name}.csv"
        t.to_csv(csv_p, index=False, encoding="utf-8-sig")
        t.to_sql(name, conn, if_exists="replace", index=False)
        print(f"  {name}: {len(t)} 条")
    conn.close()

    print(f"\n  分析结果保存到: {DIR_ANALYSIS}/")
    return df_out


# ============================================================
#  主流程
# ============================================================
if __name__ == "__main__":
    print(f"\n{'#'*50}")
    print(f"  统一数据处理流水线")
    print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*50}")

    # 1. 处理各数据源
    df_liepin = process_liepin()
    df_guopin = process_guopin()
    df_ncss = process_ncss()

    # 2. 收集有效数据
    dfs = []
    for label, df in [("liepin", df_liepin), ("guopin", df_guopin), ("ncss", df_ncss)]:
        if df is not None and len(df) > 0:
            dfs.append(df)
        else:
            print(f"  ⚠️  {label} 无数据，跳过")

    if not dfs:
        print("❌ 无有效数据，退出")
        exit(1)

    # 3. 合并分析
    final_df = merge_and_analyze(dfs)

    # 4. 打印摘要
    print(f"\n{'#'*50}")
    print(f"  流水线完成!")
    print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*50}")
    print(f"  最终: {len(final_df)} 条标准岗位数据")
    print(f"  输出: {DIR_OUTPUT}/")
    for path in sorted(DIR_OUTPUT.iterdir()):
        print(f"    {path.name}")
