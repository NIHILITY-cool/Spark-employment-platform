"""使用岗位类别和技能字典构建岗位画像、岗位技能明细及相关市场统计。"""

from __future__ import annotations

import argparse
from functools import reduce

from pyspark.sql import DataFrame, SparkSession, functions as F


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Classify jobs and extract required skills from the DWD job table.")
    parser.add_argument("--date", default="2026-07-11")
    parser.add_argument("--hdfs-root", default="/employment-platform")
    parser.add_argument("--mode", choices=("errorifexists", "overwrite"), default="errorifexists")
    return parser.parse_args()


def categorize_jobs(jobs: DataFrame, category_rows: list) -> DataFrame:
    search_text = F.lower(F.concat_ws(" ", F.col("job_name"), F.col("job_description")))
    category = F.lit("其他")
    # Later rows have lower priority; reverse iteration preserves CSV declaration order.
    for row in reversed(category_rows):
        category = F.when(search_text.rlike(row.keywords.lower()), F.lit(row.job_category)).otherwise(category)
    return jobs.withColumn("job_category", category)


def build_skill_rows(profiles: DataFrame, alias_rows: list) -> DataFrame:
    search_text = F.lower(F.concat_ws(" ", F.col("job_name"), F.col("job_description")))
    candidates: list[DataFrame] = []
    for row in alias_rows:
        candidates.append(
            profiles.withColumn("search_text", search_text)
            .filter(F.col("search_text").contains(row.alias))
            .select(
                "job_key", "job_id", "source", "job_category", "crawl_date",
                F.lit(row.skill_name).alias("skill_name"),
                F.lit(row.skill_category).alias("skill_category"),
                F.lit(float(row.default_weight)).alias("skill_weight"),
                F.lit(row.alias).alias("match_alias"),
                F.when(F.lower(F.col("job_name")).contains(row.alias), F.lit("job_name")).otherwise(F.lit("job_description")).alias("source_text"),
            )
        )
    if not candidates:
        raise RuntimeError("No skill aliases are available; check skill_aliases.csv.")
    return reduce(lambda left, right: left.unionByName(right), candidates).dropDuplicates(["job_key", "skill_name"])


def main() -> None:
    args = parse_args()
    spark = SparkSession.builder.appName("employment-skill-extraction").getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    dictionary_root = f"{args.hdfs_root}/raw/dictionaries"
    jobs = spark.read.parquet(f"{args.hdfs_root}/warehouse/dwd/jobs/date={args.date}")
    categories = spark.read.option("header", True).csv(f"{dictionary_root}/job_categories.csv").collect()
    skills = spark.read.option("header", True).csv(f"{dictionary_root}/skills.csv")
    aliases = (
        spark.read.option("header", True).csv(f"{dictionary_root}/skill_aliases.csv")
        .withColumn("alias", F.lower(F.trim(F.col("alias"))))
        .filter(F.col("alias") != "")
        .join(skills, "skill_name", "inner")
        .select("alias", "skill_name", "skill_category", "default_weight")
        .collect()
    )

    profiles = categorize_jobs(jobs, categories)
    job_skills = build_skill_rows(profiles, aliases)
    profile_path = f"{args.hdfs_root}/warehouse/dwd/job_profiles/date={args.date}"
    skill_path = f"{args.hdfs_root}/cleaned/job_skills/date={args.date}"
    output_root = f"{args.hdfs_root}/output/job_statistics/date={args.date}"

    profiles.write.mode(args.mode).partitionBy("source").parquet(profile_path)
    job_skills.write.mode(args.mode).partitionBy("source").parquet(skill_path)
    profiles.groupBy("job_category").count().orderBy(F.desc("count")).write.mode(args.mode).parquet(f"{output_root}/job_category_distribution")
    job_skills.groupBy("skill_name", "skill_category").agg(F.countDistinct("job_key").alias("job_count")).orderBy(F.desc("job_count")).write.mode(args.mode).parquet(f"{output_root}/hot_skills")

    profiles.groupBy("job_category").count().orderBy(F.desc("count")).show(20, truncate=False)
    job_skills.groupBy("skill_name").count().orderBy(F.desc("count")).show(20, truncate=False)
    print(f"job profiles written to {profile_path}")
    print(f"job skills written to {skill_path}")
    spark.stop()


if __name__ == "__main__":
    main()
