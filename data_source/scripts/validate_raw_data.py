from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FIELDS = [
    "source_job_id",
    "job_name",
    "company_name",
    "city",
    "salary_text",
    "education_text",
    "job_description",
    "job_responsibility",
    "source_name",
    "source_url",
    "crawl_time",
]


def find_latest_jsonl() -> Path:
    files = sorted((ROOT / "data" / "raw" / "ncss_jobs").glob("date=*/run=*/jobs_ncss_*.jsonl"))
    if not files:
        raise FileNotFoundError("No raw job jsonl found under data/raw/ncss_jobs.")
    non_empty_files = [path for path in files if path.stat().st_size > 0]
    return non_empty_files[-1] if non_empty_files else files[-1]


def resolve_input_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    if path.exists():
        return path.resolve()
    return (ROOT / path).resolve()


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def load_jsonl(path: Path) -> list[dict]:
    records: list[dict] = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def missing_count(records: list[dict], field: str) -> int:
    return sum(1 for record in records if record.get(field) in (None, "", []))


def build_report(records: list[dict], input_path: Path) -> dict:
    ids = [record.get("source_job_id") for record in records if record.get("source_job_id")]
    duplicate_ids = [job_id for job_id, count in Counter(ids).items() if count > 1]
    missing = {
        field: {
            "count": missing_count(records, field),
            "rate": round(missing_count(records, field) / len(records), 4) if records else 0,
        }
        for field in REQUIRED_FIELDS
    }
    return {
        "input_file": display_path(input_path),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "record_count": len(records),
        "unique_source_job_id_count": len(set(ids)),
        "duplicate_source_job_id_count": len(duplicate_ids),
        "duplicate_source_job_ids": duplicate_ids[:50],
        "missing_required_fields": missing,
        "top_cities": Counter(record.get("city", "") for record in records).most_common(20),
        "top_companies": Counter(record.get("company_name", "") for record in records).most_common(20),
        "top_education": Counter(record.get("education_text", "") for record in records).most_common(20),
    }


def write_markdown(report: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# 原始岗位数据质量报告",
        "",
        f"- 输入文件：`{report['input_file']}`",
        f"- 生成时间：{report['generated_at']}",
        f"- 记录数：{report['record_count']}",
        f"- 唯一岗位 ID 数：{report['unique_source_job_id_count']}",
        f"- 重复岗位 ID 数：{report['duplicate_source_job_id_count']}",
        "",
        "## 必填字段缺失率",
        "",
        "| 字段 | 缺失数 | 缺失率 |",
        "| --- | ---: | ---: |",
    ]
    for field, stats in report["missing_required_fields"].items():
        lines.append(f"| `{field}` | {stats['count']} | {stats['rate']:.2%} |")
    lines.extend(["", "## 城市 Top 20", ""])
    for value, count in report["top_cities"]:
        lines.append(f"- {value or '空值'}：{count}")
    lines.extend(["", "## 企业 Top 20", ""])
    for value, count in report["top_companies"]:
        lines.append(f"- {value or '空值'}：{count}")
    lines.extend(["", "## 学历要求 Top 20", ""])
    for value, count in report["top_education"]:
        lines.append(f"- {value or '空值'}：{count}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate raw job data.")
    parser.add_argument("--input", default="", help="Raw jsonl file. Defaults to latest non-empty ncss job jsonl.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = resolve_input_path(args.input) if args.input else find_latest_jsonl()
    records = load_jsonl(input_path)
    report = build_report(records, input_path)
    run_dir = input_path.parent
    report_json = run_dir / "raw_data_quality_report.json"
    report_md = run_dir / "raw_data_quality_report.md"
    report_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(report, report_md)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
