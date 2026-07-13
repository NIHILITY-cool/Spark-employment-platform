from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from parsers.job_parser import normalize_ncss_job, parse_job_detail_html
from pipelines.save_json import save_csv, save_jsonl


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


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_seen_job_ids(paths_text: str) -> set[str]:
    seen: set[str] = set()
    for path_text in parse_csv_values(paths_text):
        path = resolve_path(path_text)
        with path.open("r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                source_job_id = record.get("source_job_id")
                if source_job_id:
                    seen.add(source_job_id)
    return seen


def iter_list_items(api_dir: Path):
    for path in sorted(api_dir.glob("*.json")):
        try:
            payload = load_json(path)
        except Exception:
            continue
        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, dict):
            continue
        items = data.get("list", [])
        if isinstance(items, list):
            for item in items:
                yield path.name, item


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Recover jsonl/csv from an incomplete ncss run directory.")
    parser.add_argument("--run-dir", required=True, help="Run directory under data/raw/ncss_jobs.")
    parser.add_argument("--seen-jsonl", default="", help="Comma separated existing jsonl files used for duplicate skipping.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_dir = resolve_path(args.run_dir)
    config = load_json(ROOT / "configs" / "ncss_jobs_config.json")
    api_dir = run_dir / "api_responses"
    detail_dir = run_dir / "detail_pages"
    if not api_dir.exists():
        raise FileNotFoundError(f"Missing api_responses directory: {api_dir}")

    seen_job_ids = load_seen_job_ids(args.seen_jsonl) if args.seen_jsonl else set()
    existing_seen_count = len(seen_job_ids)
    records: list[dict] = []
    skipped_existing_or_duplicate = 0
    missing_detail_pages = 0
    api_file_count = 0
    raw_item_count = 0

    for api_file_name, item in iter_list_items(api_dir):
        api_file_count += 1
        raw_item_count += 1
        job_id = item.get("jobId", "")
        if job_id and job_id in seen_job_ids:
            skipped_existing_or_duplicate += 1
            continue
        if job_id:
            seen_job_ids.add(job_id)

        detail_url = config["detail_url_template"].format(job_id=job_id)
        detail_path = detail_dir / f"{job_id}.html"
        detail = {}
        if detail_path.exists():
            detail = parse_job_detail_html(detail_path.read_text(encoding="utf-8"))
        else:
            missing_detail_pages += 1

        record = normalize_ncss_job(
            item=item,
            detail=detail,
            source_name=config["source_name"],
            source_url=detail_url,
            crawl_time=datetime.now().isoformat(timespec="seconds"),
        )
        record.setdefault("raw", {})["recovered_from_api_file"] = api_file_name
        records.append(record)

    date_text = run_dir.parent.name.replace("date=", "")
    jsonl_path = run_dir / f"jobs_ncss_{date_text}_batch001.jsonl"
    csv_path = run_dir / f"jobs_ncss_{date_text}_batch001.csv"
    manifest_path = run_dir / "crawl_manifest_recovered.json"
    save_jsonl(jsonl_path, records)
    save_csv(csv_path, records, RAW_FIELDS)
    manifest = {
        "source_name": config["source_name"],
        "recover_mode": "incomplete_run",
        "run_dir": str(run_dir.relative_to(ROOT)),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "existing_seen_job_id_count": existing_seen_count,
        "api_response_files_seen": len(list(api_dir.glob("*.json"))),
        "api_items_seen": raw_item_count,
        "record_count": len(records),
        "unique_source_job_id_count": len({record.get("source_job_id") for record in records}),
        "skipped_existing_or_duplicate_count": skipped_existing_or_duplicate,
        "missing_detail_pages": missing_detail_pages,
        "output_jsonl": str(jsonl_path.relative_to(ROOT)),
        "output_csv": str(csv_path.relative_to(ROOT)),
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
