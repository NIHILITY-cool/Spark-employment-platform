"""将 Spark DWD、技能和市场统计结果以全量快照方式刷新到 MySQL。"""

from __future__ import annotations

import argparse
import os
from typing import Iterable

from pyspark.sql import DataFrame, SparkSession, functions as F


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export employment Spark outputs to MySQL.")
    parser.add_argument("--date", default="2026-07-11")
    parser.add_argument("--hdfs-root", default="/employment-platform")
    parser.add_argument("--jdbc-url", default=os.environ.get("MYSQL_JDBC_URL"))
    parser.add_argument("--user", default=os.environ.get("MYSQL_USER"))
    parser.add_argument("--password", default=os.environ.get("MYSQL_PASSWORD"))
    parser.add_argument("--driver", default="com.mysql.cj.jdbc.Driver")
    return parser.parse_args()


def jdbc_options(args: argparse.Namespace, table: str) -> dict[str, str]:
    if not args.jdbc_url or not args.user or not args.password:
        raise ValueError("MYSQL_JDBC_URL, MYSQL_USER and MYSQL_PASSWORD must be configured.")
    return {
        "url": args.jdbc_url,
        "dbtable": table,
        "user": args.user,
        "password": args.password,
        "driver": args.driver,
        "rewriteBatchedStatements": "true",
    }


def replace_snapshot(frame: DataFrame, args: argparse.Namespace, table: str) -> None:
    # `truncate=true` preserves the schema and indexes created by database/schema.sql.
    frame.write.format("jdbc").options(**jdbc_options(args, table)).option("truncate", "true").mode("overwrite").save()


def statistic_frame(
    spark: SparkSession,
    path: str,
    date: str,
    stat_type: str,
    dimension: str,
    value: str,
    extra_columns: Iterable[str] = (),
) -> DataFrame:
    source = spark.read.parquet(path)
    extra = [column for column in extra_columns if column in source.columns]
    extra_json = F.to_json(F.struct(*[F.col(column) for column in extra])).alias("extra_json") if extra else F.lit(None).cast("string").alias("extra_json")
    return source.select(
        F.to_date(F.lit(date)).alias("stat_date"),
        F.lit(stat_type).alias("stat_type"),
        F.col(dimension).cast("string").alias("dimension_key"),
        F.col(value).cast("double").alias("metric_value"),
        extra_json,
    )


def main() -> None:
    args = parse_args()
    spark = SparkSession.builder.appName("employment-export-to-mysql").getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    profile_root = f"{args.hdfs_root}/warehouse/dwd/job_profiles/date={args.date}"
    skills_root = f"{args.hdfs_root}/cleaned/job_skills/date={args.date}"
    statistics_root = f"{args.hdfs_root}/output/job_statistics/date={args.date}"
    jobs = spark.read.parquet(profile_root).select(
        "job_key", F.col("source").alias("source_name"), F.col("job_id").alias("source_job_id"),
        "job_name", "job_category", "company_name", "industry", "company_scale", "city", "district",
        F.col("education").alias("education_requirement"), F.col("experience").alias("experience_requirement"),
        "salary_raw", "salary_min", "salary_max", "job_description", "job_url", "crawl_date",
        "job_status", "last_seen_date", "record_hash",
    )
    job_skills = spark.read.parquet(skills_root).select(
        "job_key", "skill_name", "skill_category", "skill_weight", "source_text", "match_alias", "crawl_date"
    )
    stats = [
        statistic_frame(spark, f"{statistics_root}/city_distribution", args.date, "city_distribution", "city", "job_count"),
        statistic_frame(spark, f"{statistics_root}/industry_distribution", args.date, "industry_distribution", "industry", "job_count"),
        statistic_frame(spark, f"{statistics_root}/education_distribution", args.date, "education_distribution", "education", "job_count"),
        statistic_frame(spark, f"{statistics_root}/experience_distribution", args.date, "experience_distribution", "experience", "job_count"),
        statistic_frame(spark, f"{statistics_root}/source_distribution", args.date, "source_distribution", "source", "job_count"),
        statistic_frame(spark, f"{statistics_root}/job_category_distribution", args.date, "job_category_distribution", "job_category", "count"),
        statistic_frame(spark, f"{statistics_root}/hot_skills", args.date, "hot_skills", "skill_name", "job_count", ("skill_category",)),
        statistic_frame(spark, f"{statistics_root}/hot_jobs", args.date, "hot_jobs", "job_name", "job_count", ("average_salary",)),
    ]
    market_statistics = stats[0]
    for frame in stats[1:]:
        market_statistics = market_statistics.unionByName(frame)

    replace_snapshot(jobs, args, "job")
    replace_snapshot(job_skills, args, "job_skill")
    replace_snapshot(market_statistics, args, "market_statistic")
    print(f"MySQL export complete: jobs={jobs.count()}, job_skills={job_skills.count()}, statistics={market_statistics.count()}")
    spark.stop()


if __name__ == "__main__":
    main()
