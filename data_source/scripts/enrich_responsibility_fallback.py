from __future__ import annotations

import argparse
import csv
import json
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


def find_latest_jsonl() -> Path:
    files = sorted((ROOT / "data" / "raw" / "ncss_jobs").glob("date=*/run=*/jobs_ncss_*.jsonl"))
    non_empty_files = [path for path in files if path.stat().st_size > 0]
    if not non_empty_files:
        raise FileNotFoundError("No non-empty raw job jsonl found under data/raw/ncss_jobs.")
    return non_empty_files[-1]


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


def enrich(records: list[dict]) -> dict:
    stats = {
        "record_count": len(records),
        "explicit_heading": 0,
        "fallback_job_description": 0,
        "missing": 0,
    }
    for record in records:
        raw = record.setdefault("raw", {})
        if record.get("job_responsibility"):
            source = raw.get("job_responsibility_source", "explicit_heading")
            raw["job_responsibility_source"] = source
            if source in stats:
                stats[source] += 1
            else:
                stats["explicit_heading"] += 1
        elif record.get("job_description"):
            record["job_responsibility"] = record["job_description"]
            raw["job_responsibility_source"] = "fallback_job_description"
            stats["fallback_job_description"] += 1
        else:
            raw["job_responsibility_source"] = "missing"
            stats["missing"] += 1
    return stats


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fill missing job_responsibility from job_description.")
    parser.add_argument("--input", default="", help="Raw jsonl file. Defaults to latest non-empty ncss job jsonl.")
    return parser.parse_args()


def resolve_input_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    if path.exists():
        return path.resolve()
    return (ROOT / path).resolve()


def main() -> None:
    args = parse_args()
    input_path = resolve_input_path(args.input) if args.input else find_latest_jsonl()
    records = load_jsonl(input_path)
    stats = enrich(records)
    save_jsonl(input_path, records)
    save_csv(input_path.with_suffix(".csv"), records)
    print(json.dumps({"input_file": str(input_path.relative_to(ROOT)), **stats}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
