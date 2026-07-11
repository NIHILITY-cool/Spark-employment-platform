from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


DATA_PROCESSING_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = DATA_PROCESSING_ROOT.parent
DEFAULT_INPUT = (
    PROJECT_ROOT
    / "data_source"
    / "data"
    / "raw"
    / "ncss_jobs"
    / "date=2026-07-11"
    / "run=20260711_160114_merged"
    / "jobs_ncss_2026-07-11_merged.csv"
)

CLEANED_FIELDS = [
    "job_id",
    "job_name",
    "job_category",
    "company_name",
    "industry",
    "company_scale",
    "city",
    "district",
    "education",
    "experience",
    "salary_raw",
    "salary_min",
    "salary_max",
    "job_description",
    "job_url",
    "crawl_date",
]

EXCLUDED_FIELDS = CLEANED_FIELDS + ["exclude_reason", "source_job_id"]

STUDENT_HINTS = [
    "应届",
    "毕业生",
    "校园招聘",
    "校园 招聘",
    "校招",
    "实习",
    "三方协议",
    "高校",
    "学生",
    "在校",
]

SOCIAL_ONLY_PATTERNS = [
    re.compile(pattern)
    for pattern in [
        r"面向社会(?:公开)?招聘",
        r"面向社会招募",
        r"社会招聘人员",
        r"社会人员",
        r"社会人士",
        r"仅限社会",
        r"不接受应届",
    ]
]

HARD_EXPERIENCE_PATTERNS = [
    re.compile(r"(?<![\d])([3-9]|1[0-9])\s*年\s*(?:以上|及以上).{0,8}(?:经验|经历)"),
    re.compile(r"(?:经验|经历).{0,8}(?<![\d])([3-9]|1[0-9])\s*年\s*(?:以上|及以上)"),
    re.compile(r"[三四五六七八九十]\s*年\s*(?:以上|及以上).{0,8}(?:经验|经历)"),
    re.compile(r"(?:经验|经历).{0,8}[三四五六七八九十]\s*年\s*(?:以上|及以上)"),
]

LOCATION_SPLIT_RE = re.compile(r"[-—–－]")
SALARY_RANGE_RE = re.compile(
    r"(?P<min>\d+(?:\.\d+)?)\s*[Kk千]\s*[-~—–至到]\s*(?P<max>\d+(?:\.\d+)?)\s*[Kk千]?"
)
SALARY_SINGLE_RE = re.compile(r"(?P<value>\d+(?:\.\d+)?)\s*[Kk千]")


def resolve_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    if path.exists():
        return path.resolve()
    return (PROJECT_ROOT / path).resolve()


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).replace("\u3000", " ")
    return re.sub(r"\s+", " ", text).strip()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def load_records(path: Path) -> list[dict[str, Any]]:
    """Load either crawler JSONL output or the delivered merged CSV snapshot."""
    if path.suffix.lower() != ".csv":
        return load_jsonl(path)
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def save_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")


def save_csv(path: Path, records: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)


def normalize_city(value: str) -> str:
    city = re.sub(r"市+$", "", clean_text(value))
    return "全国" if city == "中国" else city


def split_location(city_value: str, district_value: str) -> tuple[str, str]:
    city = clean_text(city_value)
    district = clean_text(district_value)
    if district or not LOCATION_SPLIT_RE.search(city):
        return normalize_city(city), district
    parts = [part.strip() for part in LOCATION_SPLIT_RE.split(city, maxsplit=1)]
    if len(parts) == 2:
        return normalize_city(parts[0]), parts[1]
    return normalize_city(city), district


def to_yuan(value: str) -> int:
    return int(round(float(value) * 1000))


def parse_salary(salary_raw: str) -> tuple[int | None, int | None, str]:
    salary = clean_text(salary_raw).replace(" ", "")
    if not salary or salary in {"面议", "薪资面议", "--", "不限"}:
        return None, None, "empty_or_negotiable"
    range_match = SALARY_RANGE_RE.search(salary)
    if range_match:
        salary_min = to_yuan(range_match.group("min"))
        salary_max = to_yuan(range_match.group("max"))
        if salary_min > salary_max:
            salary_min, salary_max = salary_max, salary_min
        return salary_min, salary_max, "range"
    single_match = SALARY_SINGLE_RE.search(salary)
    if single_match:
        value = to_yuan(single_match.group("value"))
        if "以上" in salary or "起" in salary:
            return value, None, "lower_bound"
        if "以下" in salary or "以内" in salary:
            return None, value, "upper_bound"
        return value, value, "single"
    return None, None, "unparsed"


def build_filter_text(record: dict[str, Any]) -> str:
    parts = [
        record.get("job_name", ""),
        record.get("job_description", ""),
        record.get("job_responsibility", ""),
        record.get("job_requirement", ""),
    ]
    return clean_text(" ".join(clean_text(part) for part in parts))


def has_student_hint(text: str) -> bool:
    return any(hint in text for hint in STUDENT_HINTS)


def social_filter_reason(record: dict[str, Any]) -> str:
    text = build_filter_text(record)
    for pattern in HARD_EXPERIENCE_PATTERNS:
        if pattern.search(text):
            return "hard_experience_requirement"
    if not has_student_hint(text):
        for pattern in SOCIAL_ONLY_PATTERNS:
            if pattern.search(text):
                return "social_recruitment_without_student_hint"
    return ""


def map_record(record: dict[str, Any]) -> dict[str, Any]:
    city, district = split_location(record.get("city", ""), record.get("district", ""))
    salary_raw = clean_text(record.get("salary_text", ""))
    salary_min, salary_max, _ = parse_salary(salary_raw)
    crawl_time = clean_text(record.get("crawl_time", ""))
    return {
        "job_id": clean_text(record.get("source_job_id", "")),
        "job_name": clean_text(record.get("job_name", "")),
        "job_category": "",
        "company_name": clean_text(record.get("company_name", "")),
        "industry": clean_text(record.get("industry", "")),
        "company_scale": clean_text(record.get("company_size", "")),
        "city": city,
        "district": district,
        "education": clean_text(record.get("education_text", "")),
        "experience": clean_text(record.get("experience_text", "")),
        "salary_raw": salary_raw,
        "salary_min": salary_min if salary_min is not None else "",
        "salary_max": salary_max if salary_max is not None else "",
        "job_description": clean_text(record.get("job_description", "")),
        "job_url": clean_text(record.get("source_url", "")),
        "crawl_date": crawl_time[:10] if crawl_time else "",
    }


def required_missing_reason(cleaned: dict[str, Any]) -> str:
    for field in ["job_id", "job_name", "company_name", "job_url"]:
        if not cleaned.get(field):
            return f"missing_{field}"
    return ""


def clean_records(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    seen_job_ids: set[str] = set()
    cleaned_records: list[dict[str, Any]] = []
    excluded_records: list[dict[str, Any]] = []
    exclusion_counter: Counter[str] = Counter()
    salary_parse_counter: Counter[str] = Counter()

    for record in records:
        mapped = map_record(record)
        _, _, salary_status = parse_salary(mapped["salary_raw"])
        salary_parse_counter[salary_status] += 1

        source_job_id = clean_text(record.get("source_job_id", ""))
        reason = required_missing_reason(mapped)
        if not reason and mapped["job_id"] in seen_job_ids:
            reason = "duplicate_job_id"
        if not reason:
            reason = social_filter_reason(record)

        if reason:
            excluded = {**mapped, "exclude_reason": reason, "source_job_id": source_job_id}
            excluded_records.append(excluded)
            exclusion_counter[reason] += 1
            continue

        seen_job_ids.add(mapped["job_id"])
        cleaned_records.append(mapped)

    report = {
        "input_record_count": len(records),
        "cleaned_record_count": len(cleaned_records),
        "excluded_record_count": len(excluded_records),
        "unique_job_id_count": len({record["job_id"] for record in cleaned_records if record.get("job_id")}),
        "exclusion_reasons": dict(exclusion_counter),
        "salary_parse_status": dict(salary_parse_counter),
        "missing_fields_after_cleaning": {
            field: sum(1 for record in cleaned_records if record.get(field) in ("", None))
            for field in CLEANED_FIELDS
        },
        "top_cities": Counter(record.get("city", "") for record in cleaned_records).most_common(20),
        "top_industries": Counter(record.get("industry", "") for record in cleaned_records).most_common(20),
        "top_education": Counter(record.get("education", "") for record in cleaned_records).most_common(20),
    }
    return cleaned_records, excluded_records, report


def write_markdown_report(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# ncss 岗位清洗报告",
        "",
        f"- 输入文件：`{report['input_file']}`",
        f"- 输出文件：`{report['output_jsonl']}`",
        f"- 生成时间：{report['generated_at']}",
        f"- 输入记录数：{report['input_record_count']}",
        f"- 清洗后记录数：{report['cleaned_record_count']}",
        f"- 剔除记录数：{report['excluded_record_count']}",
        f"- 唯一岗位 ID 数：{report['unique_job_id_count']}",
        "",
        "## 剔除原因",
        "",
        "| 原因 | 数量 |",
        "| --- | ---: |",
    ]
    for reason, count in report["exclusion_reasons"].items():
        lines.append(f"| `{reason}` | {count} |")
    if not report["exclusion_reasons"]:
        lines.append("| 无 | 0 |")

    lines.extend(["", "## 薪资解析状态", "", "| 状态 | 数量 |", "| --- | ---: |"])
    for status, count in report["salary_parse_status"].items():
        lines.append(f"| `{status}` | {count} |")

    lines.extend(["", "## 清洗后字段缺失", "", "| 字段 | 缺失数 |", "| --- | ---: |"])
    for field, count in report["missing_fields_after_cleaning"].items():
        lines.append(f"| `{field}` | {count} |")

    lines.extend(["", "## 城市 Top 20", ""])
    for value, count in report["top_cities"]:
        lines.append(f"- {value or '空值'}：{count}")

    lines.extend(["", "## 行业 Top 20", ""])
    for value, count in report["top_industries"]:
        lines.append(f"- {value or '空值'}：{count}")

    lines.extend(["", "## 学历 Top 20", ""])
    for value, count in report["top_education"]:
        lines.append(f"- {value or '空值'}：{count}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clean merged ncss jobs into the team standard schema.")
    parser.add_argument("--input", default=str(DEFAULT_INPUT), help="Merged ncss JSONL or CSV file.")
    parser.add_argument(
        "--output-root",
        default=str(DATA_PROCESSING_ROOT / "data" / "cleaned" / "ncss_jobs"),
        help="Cleaned output root.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = resolve_path(args.input)
    output_root = resolve_path(args.output_root)
    now = datetime.now()
    date_dir = now.strftime("%Y-%m-%d")
    run_id = now.strftime("%Y%m%d_%H%M%S")
    output_dir = output_root / f"date={date_dir}" / f"run={run_id}"
    output_dir.mkdir(parents=True, exist_ok=True)

    records = load_records(input_path)
    cleaned_records, excluded_records, report = clean_records(records)

    output_jsonl = output_dir / f"cleaned_jobs_ncss_{date_dir}.jsonl"
    output_csv = output_dir / f"cleaned_jobs_ncss_{date_dir}.csv"
    excluded_jsonl = output_dir / f"excluded_jobs_ncss_{date_dir}.jsonl"
    excluded_csv = output_dir / f"excluded_jobs_ncss_{date_dir}.csv"
    report_json = output_dir / "cleaning_report.json"
    report_md = output_dir / "cleaning_report.md"

    save_jsonl(output_jsonl, cleaned_records)
    save_csv(output_csv, cleaned_records, CLEANED_FIELDS)
    save_jsonl(excluded_jsonl, excluded_records)
    save_csv(excluded_csv, excluded_records, EXCLUDED_FIELDS)

    report = {
        "input_file": display_path(input_path),
        "generated_at": now.isoformat(timespec="seconds"),
        **report,
        "output_jsonl": display_path(output_jsonl),
        "output_csv": display_path(output_csv),
        "excluded_jsonl": display_path(excluded_jsonl),
        "excluded_csv": display_path(excluded_csv),
    }
    report_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown_report(report, report_md)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
