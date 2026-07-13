"""将国聘、猎聘和 ncss 原始岗位 CSV 清洗为统一的 Spark DWD 岗位表。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pyspark.sql import DataFrame, SparkSession, functions as F
from pyspark.sql.types import StringType, StructField, StructType

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from location_normalization import parse_zhilian_monthly_salary, resolve_city


HDFS_ROOT = "/employment-platform"
GUOPIN_COLUMNS = [
    "job_id", "job_category", "job_name", "company_name", "company_short_name",
    "location", "education", "experience", "salary_min", "salary_max",
    "job_description", "job_url", "crawl_date",
]
ZHILIAN_COLUMNS = [
    "job_name", "company_name", "industry", "company_scale", "location_detail", "city", "district",
    "education", "experience", "salary_raw", "job_description", "job_url", "company_url",
]
STANDARD_COLUMNS = [
    "job_key", "job_id", "job_name", "job_category", "company_name", "industry",
    "company_scale", "city", "district", "education", "experience", "salary_raw",
    "salary_min", "salary_max", "job_description", "job_url", "crawl_date", "source",
    "job_status", "last_seen_date", "record_hash",
]
LOCATION_RESULT_SCHEMA = StructType([
    StructField("city", StringType(), False),
    StructField("granularity", StringType(), False),
])
SALARY_RESULT_SCHEMA = StructType([
    StructField("salary_min", StringType(), True),
    StructField("salary_max", StringType(), True),
])
resolve_location_udf = F.udf(resolve_city, LOCATION_RESULT_SCHEMA)
parse_zhilian_salary_udf = F.udf(
    lambda value: tuple(str(item) if item is not None else None for item in parse_zhilian_monthly_salary(value)),
    SALARY_RESULT_SCHEMA,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clean raw job CSV files into the DWD job table.")
    parser.add_argument("--date", default="2026-07-11", help="Raw data partition date (YYYY-MM-DD).")
    parser.add_argument("--hdfs-root", default=HDFS_ROOT)
    parser.add_argument("--mode", choices=("errorifexists", "overwrite"), default="errorifexists")
    return parser.parse_args()


def read_csv(spark: SparkSession, path: str, header: bool, schema: StructType | None = None) -> DataFrame:
    reader = (
        spark.read.option("header", header).option("multiLine", True).option("quote", '"')
        .option("escape", '"').option("encoding", "UTF-8")
    )
    return reader.schema(schema).csv(path) if schema else reader.csv(path)


def cleaned_text(column: str) -> F.Column:
    return F.trim(F.regexp_replace(F.coalesce(F.col(column).cast("string"), F.lit("")), "[\\u200B\\uFEFF]", ""))


def normalize_common(frame: DataFrame, source: str, date: str) -> DataFrame:
    text_columns = [
        "job_id", "job_name", "job_category", "company_name", "industry", "company_scale",
        "city", "district", "education", "experience", "salary_raw", "job_description", "job_url",
    ]
    for column in text_columns:
        frame = frame.withColumn(column, cleaned_text(column))

    frame = (
        frame.withColumn("_location", resolve_location_udf(F.col("city"), F.col("district"), F.col("job_description")))
        .withColumn("city", F.col("_location.city"))
        .drop("_location")
        .withColumn("education", F.when(F.col("education") == "统招本科", F.lit("本科")).otherwise(F.col("education")))
        .withColumn("experience", F.when(F.col("experience") == "", F.lit("经验不限")).otherwise(F.col("experience")))
        .withColumn("salary_min", F.expr("try_cast(salary_min AS DOUBLE)").cast("long"))
        .withColumn("salary_max", F.expr("try_cast(salary_max AS DOUBLE)").cast("long"))
        .filter(F.col("job_id") != "")
        .filter(F.col("job_name") != "")
        .filter(F.col("company_name") != "")
        .filter(F.col("city") != "")
        .filter(F.col("salary_min").isNotNull() & F.col("salary_max").isNotNull())
        .filter((F.col("salary_min") >= 0) & (F.col("salary_max") >= F.col("salary_min")))
        .filter(F.col("salary_max") <= 1_000_000)
        .withColumn("source", F.lit(source))
        .withColumn("crawl_date", F.to_date(F.lit(date)))
        .withColumn("job_status", F.lit("active"))
        .withColumn("last_seen_date", F.to_date(F.lit(date)))
    )
    return frame


def read_guopin(spark: SparkSession, root: str, date: str) -> DataFrame:
    schema = StructType([StructField(name, StringType(), True) for name in GUOPIN_COLUMNS])
    raw = read_csv(spark, f"{root}/raw/jobs/source=guopin/date={date}", header=False, schema=schema)
    location_parts = F.split(cleaned_text("location"), "[-—–－]")
    frame = raw.select(
        "job_id", "job_name", "job_category", "company_name",
        F.lit("").alias("industry"), F.lit("").alias("company_scale"),
        F.element_at(location_parts, 1).alias("city"),
        F.coalesce(F.get(location_parts, 1), F.lit("")).alias("district"),
        "education", "experience",
        F.concat_ws("-", F.col("salary_min"), F.col("salary_max")).alias("salary_raw"),
        "salary_min", "salary_max", "job_description", "job_url",
    )
    return normalize_common(frame, "guopin", date)


def read_liepin(spark: SparkSession, root: str, date: str) -> DataFrame:
    raw = read_csv(spark, f"{root}/raw/jobs/source=liepin/date={date}", header=True)
    location_parts = F.split(cleaned_text("dq"), "[-—–－]")
    salary_text = cleaned_text("salary")
    salary_match = F.regexp_extract(salary_text, r"^(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)", 0)
    lower = F.regexp_extract(salary_text, r"^(\d+(?:\.\d+)?)\s*-", 1)
    upper = F.regexp_extract(salary_text, r"-\s*(\d+(?:\.\d+)?)", 1)
    frame = raw.select(
        F.col("jobId").cast("string").alias("job_id"), F.col("title").alias("job_name"),
        F.lit("").alias("job_category"), F.col("company").alias("company_name"),
        F.col("industry").alias("industry"), F.col("compScale").alias("company_scale"),
        F.element_at(location_parts, 1).alias("city"),
        F.coalesce(F.get(location_parts, 1), F.lit("")).alias("district"),
        F.col("requireEduLevel").alias("education"), F.col("requireWorkYears").alias("experience"),
        F.col("salary").alias("salary_raw"),
        (lower.try_cast("double") * 1000).alias("salary_min"), (upper.try_cast("double") * 1000).alias("salary_max"),
        F.col("job_description").alias("job_description"), F.col("jobLink").alias("job_url"),
    ).filter(salary_match != "")
    return normalize_common(frame, "liepin", date)


def read_ncss(spark: SparkSession, root: str, date: str) -> DataFrame:
    raw = read_csv(spark, f"{root}/raw/jobs/source=ncss/date={date}", header=True)
    salary_text = cleaned_text("salary_text")
    lower = F.regexp_extract(salary_text, r"(\d+(?:\.\d+)?)K\s*-", 1)
    upper = F.regexp_extract(salary_text, r"-\s*(\d+(?:\.\d+)?)K", 1)
    # NCSS 的职责和要求字段来源及分段格式不稳定，且职责字段可能是完整描述的兜底副本。
    # 仅保留采集后清洗的岗位描述，避免重复拼接并保留原始文本语义。
    description = cleaned_text("job_description")
    student_hint = r"应届|毕业生|校园招聘|校招|实习|学生|在校"
    hard_experience = r"(?:[3-9]|[1-9][0-9])\s*年\s*(?:以上|及以上).{0,8}(?:经验|经历)"
    frame = raw.select(
        F.col("source_job_id").alias("job_id"), F.col("job_name"), F.lit("").alias("job_category"),
        F.col("company_name"), F.col("industry"), F.col("company_size").alias("company_scale"),
        F.col("city"), F.col("district"), F.col("education_text").alias("education"),
        F.col("experience_text").alias("experience"), F.col("salary_text").alias("salary_raw"),
        (lower.try_cast("double") * 1000).alias("salary_min"), (upper.try_cast("double") * 1000).alias("salary_max"),
        description.alias("job_description"), F.col("source_url").alias("job_url"),
    )
    frame = frame.filter(~F.col("job_description").rlike(hard_experience))
    frame = frame.filter(~(F.col("job_description").contains("面向社会") & ~F.col("job_description").rlike(student_hint)))
    return normalize_common(frame, "ncss", date)


def read_zhilian(spark: SparkSession, root: str, date: str) -> DataFrame:
    schema = StructType([StructField(name, StringType(), True) for name in ZHILIAN_COLUMNS])
    raw = read_csv(spark, f"{root}/raw/jobs/source=zhilian/date={date}", header=False, schema=schema)
    frame = raw.select(
        F.sha2(cleaned_text("job_url"), 256).alias("job_id"), "job_name", F.lit("").alias("job_category"),
        "company_name", "industry", "company_scale", "city", "district", "education", "experience",
        "salary_raw", F.lit(None).cast("long").alias("salary_min"), F.lit(None).cast("long").alias("salary_max"),
        "job_description", "job_url",
    ).withColumn("_salary", parse_zhilian_salary_udf(F.col("salary_raw")))
    frame = frame.withColumn("salary_min", F.col("_salary.salary_min").cast("long")) \
        .withColumn("salary_max", F.col("_salary.salary_max").cast("long")).drop("_salary")
    return normalize_common(frame, "zhilian", date)


def main() -> None:
    args = parse_args()
    spark = SparkSession.builder.appName("employment-job-cleaning").getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    spark.sparkContext.addPyFile(str(Path(__file__).resolve().parents[1] / "location_normalization.py"))

    jobs = read_guopin(spark, args.hdfs_root, args.date) \
        .unionByName(read_liepin(spark, args.hdfs_root, args.date)) \
        .unionByName(read_ncss(spark, args.hdfs_root, args.date)) \
        .unionByName(read_zhilian(spark, args.hdfs_root, args.date))
    jobs = jobs.dropDuplicates(["source", "job_id"]).dropDuplicates(["source", "job_name", "company_name", "city", "salary_min", "salary_max"])
    jobs = jobs.withColumn("job_key", F.concat_ws(":", F.col("source"), F.col("job_id")))
    jobs = jobs.withColumn("record_hash", F.sha2(F.concat_ws("||", *[F.col(column).cast("string") for column in STANDARD_COLUMNS[:-1]]), 256))
    jobs = jobs.select(*STANDARD_COLUMNS)

    cleaned_path = f"{args.hdfs_root}/cleaned/jobs/date={args.date}"
    dwd_path = f"{args.hdfs_root}/warehouse/dwd/jobs/date={args.date}"
    jobs.write.mode(args.mode).partitionBy("source").parquet(cleaned_path)
    jobs.write.mode(args.mode).partitionBy("source").parquet(dwd_path)

    jobs.groupBy("source").count().orderBy("source").show(truncate=False)
    print(f"cleaned jobs written to {cleaned_path}")
    print(f"DWD jobs written to {dwd_path}")
    spark.stop()


if __name__ == "__main__":
    main()
