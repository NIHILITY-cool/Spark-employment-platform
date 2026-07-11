from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_FIELDS = [
    "source_job_id",
    "job_name",
    "company_name",
    "city",
    "district",
    "industry",
    "company_size",
    "company_type",
    "salary_text",
    "education_text",
    "experience_text",
    "job_description",
    "job_responsibility",
    "job_requirement",
    "publish_time",
    "source_name",
    "source_url",
    "crawl_time",
]


def parse_csv_values(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def resolve_path(value: str) -> Path:
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


def save_jsonl(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")


def save_csv(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=RAW_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)


def merge_records(input_paths: list[Path]) -> tuple[list[dict], dict]:
    seen_ids: set[str] = set()
    merged: list[dict] = []
    input_stats: list[dict] = []
    duplicate_count = 0
    missing_id_count = 0

    for path in input_paths:
        records = load_jsonl(path)
        added = 0
        skipped_duplicate = 0
        skipped_missing_id = 0
        for record in records:
            source_job_id = record.get("source_job_id")
            if not source_job_id:
                skipped_missing_id += 1
                missing_id_count += 1
                continue
            if source_job_id in seen_ids:
                skipped_duplicate += 1
                duplicate_count += 1
                continue
            seen_ids.add(source_job_id)
            merged.append(record)
            added += 1
        input_stats.append(
            {
                "input_file": display_path(path),
                "record_count": len(records),
                "added_count": added,
                "skipped_duplicate_count": skipped_duplicate,
                "skipped_missing_source_job_id_count": skipped_missing_id,
            }
        )

    stats = {
        "input_file_count": len(input_paths),
        "input_record_count": sum(item["record_count"] for item in input_stats),
        "record_count": len(merged),
        "unique_source_job_id_count": len(seen_ids),
        "skipped_duplicate_count": duplicate_count,
        "skipped_missing_source_job_id_count": missing_id_count,
        "input_files": input_stats,
    }
    return merged, stats


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge raw job jsonl files by source_job_id.")
    parser.add_argument("--inputs", required=True, help="Comma separated raw jsonl files.")
    parser.add_argument(
        "--output-root",
        default=str(ROOT / "data" / "raw" / "ncss_jobs"),
        help="Output root. Defaults to data/raw/ncss_jobs.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_paths = [resolve_path(value) for value in parse_csv_values(args.inputs)]
    if not input_paths:
        raise ValueError("--inputs cannot be empty.")
    for path in input_paths:
        if not path.exists():
            raise FileNotFoundError(path)

    now = datetime.now()
    date_dir = now.strftime("%Y-%m-%d")
    run_id = now.strftime("%Y%m%d_%H%M%S")
    output_root = resolve_path(args.output_root)
    output_dir = output_root / f"date={date_dir}" / f"run={run_id}_merged"
    output_dir.mkdir(parents=True, exist_ok=True)

    records, stats = merge_records(input_paths)
    output_jsonl = output_dir / f"jobs_ncss_{date_dir}_merged.jsonl"
    output_csv = output_dir / f"jobs_ncss_{date_dir}_merged.csv"
    save_jsonl(output_jsonl, records)
    save_csv(output_csv, records)

    manifest = {
        "source_name": "国家大学生就业服务平台",
        "merge_mode": "dedupe_by_source_job_id",
        "generated_at": now.isoformat(timespec="seconds"),
        **stats,
        "output_jsonl": display_path(output_jsonl),
        "output_csv": display_path(output_csv),
    }
    manifest_path = output_dir / "merge_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
