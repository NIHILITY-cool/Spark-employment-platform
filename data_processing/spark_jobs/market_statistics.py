"""基于 DWD 岗位表生成前端可用的基础市场统计。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pyspark.sql import SparkSession, functions as F

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from location_normalization import CANONICAL_CITIES


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate market statistics from cleaned job data.")
    parser.add_argument("--date", default="2026-07-11")
    parser.add_argument("--hdfs-root", default="/employment-platform")
    parser.add_argument("--mode", choices=("errorifexists", "overwrite"), default="errorifexists")
    return parser.parse_args()


def write_stat(frame, output: str, mode: str) -> None:
    frame.write.mode(mode).parquet(output)


def main() -> None:
    args = parse_args()
    spark = SparkSession.builder.appName("employment-market-statistics").getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    jobs = spark.read.parquet(f"{args.hdfs_root}/warehouse/dwd/jobs/date={args.date}")
    output_root = f"{args.hdfs_root}/output/job_statistics/date={args.date}"
    city_jobs = jobs.filter(F.col("city").isin(*CANONICAL_CITIES))

    write_stat(city_jobs.groupBy("city").agg(F.count("*").alias("job_count")).orderBy(F.desc("job_count")), f"{output_root}/city_distribution", args.mode)
    write_stat(jobs.groupBy("industry").agg(F.count("*").alias("job_count")).orderBy(F.desc("job_count")), f"{output_root}/industry_distribution", args.mode)
    write_stat(jobs.groupBy("education").agg(F.count("*").alias("job_count")).orderBy(F.desc("job_count")), f"{output_root}/education_distribution", args.mode)
    write_stat(jobs.groupBy("experience").agg(F.count("*").alias("job_count")).orderBy(F.desc("job_count")), f"{output_root}/experience_distribution", args.mode)
    write_stat(
        jobs.groupBy("job_name").agg(F.count("*").alias("job_count"), F.round(F.avg((F.col("salary_min") + F.col("salary_max")) / 2), 2).alias("average_salary")).orderBy(F.desc("job_count")).limit(100),
        f"{output_root}/hot_jobs",
        args.mode,
    )
    write_stat(
        jobs.groupBy("source").agg(F.count("*").alias("job_count")).orderBy("source"),
        f"{output_root}/source_distribution",
        args.mode,
    )
    jobs.groupBy("source").count().orderBy("source").show(truncate=False)
    print(f"market statistics written to {output_root}")
    spark.stop()


if __name__ == "__main__":
    main()
