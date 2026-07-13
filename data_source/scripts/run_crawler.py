from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from crawlers.ncss_job_crawler import NcssJobCrawler
from pipelines.save_json import save_csv, save_jsonl


DEFAULT_CONFIG = ROOT / "configs" / "ncss_jobs_config.json"
DEFAULT_HEADERS = ROOT / "configs" / "headers.example.json"
ALL_AREA_CODES = [
    "11",
    "12",
    "13",
    "14",
    "15",
    "21",
    "22",
    "23",
    "31",
    "32",
    "33",
    "34",
    "35",
    "36",
    "37",
    "41",
    "42",
    "43",
    "44",
    "45",
    "46",
    "50",
    "51",
    "52",
    "53",
    "54",
    "61",
    "62",
    "63",
    "64",
    "65",
    "71",
    "81",
    "82",
]
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


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def setup_logger(log_path: Path) -> logging.Logger:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("ncss_crawler")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run ncss public job crawler.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--headers", default=str(DEFAULT_HEADERS))
    parser.add_argument("--start-page", type=int, default=None)
    parser.add_argument("--max-pages", type=int, default=None)
    parser.add_argument("--page-size", type=int, default=None)
    parser.add_argument("--all-area-codes", action="store_true", help="Use all province-level ncss area codes.")
    parser.add_argument("--area-codes", default="", help="Comma separated ncss area codes, for example: 11,31,44.")
    parser.add_argument("--degree-codes", default="", help="Comma separated degree codes, for example: 51,41,31,11,01.")
    parser.add_argument("--category-codes", default="", help="Comma separated category codes, for example: 01,02,03.")
    parser.add_argument("--month-pays", default="", help="Comma separated salary filters, for example: 2,2-5,5-10.")
    parser.add_argument("--job-types", default="", help="Comma separated job type codes: 01 full-time, 02 part-time, 03 intern.")
    parser.add_argument("--seen-jsonl", default="", help="Comma separated existing jsonl files used only for duplicate skipping.")
    parser.add_argument("--delay-seconds", type=float, default=None)
    parser.add_argument("--no-details", action="store_true")
    return parser.parse_args()


def parse_csv_values(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def resolve_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    if path.exists():
        return path.resolve()
    return (ROOT / path).resolve()


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


def build_query_jobs(args: argparse.Namespace) -> list[tuple[str, dict[str, str]]]:
    area_codes = ALL_AREA_CODES if args.all_area_codes else parse_csv_values(args.area_codes)
    dimensions = [
        ("areaCode", area_codes),
        ("degreeCode", parse_csv_values(args.degree_codes)),
        ("categoryCode", parse_csv_values(args.category_codes)),
        ("monthPay", parse_csv_values(args.month_pays)),
        ("jobType", parse_csv_values(args.job_types)),
    ]
    active_dimensions = [(name, values) for name, values in dimensions if values]
    if not active_dimensions:
        return []

    query_jobs: list[tuple[str, dict[str, str]]] = []
    names = [name for name, _ in active_dimensions]
    value_lists = [values for _, values in active_dimensions]
    for values in product(*value_lists):
        overrides = {name: value for name, value in zip(names, values)}
        label = "_".join(f"{name}={value}" for name, value in overrides.items())
        query_jobs.append((label, overrides))
    return query_jobs


def dedupe_records(records: list[dict]) -> list[dict]:
    seen: set[str] = set()
    deduped: list[dict] = []
    for record in records:
        source_job_id = record.get("source_job_id")
        if not source_job_id or source_job_id in seen:
            continue
        seen.add(source_job_id)
        deduped.append(record)
    return deduped


def main() -> None:
    args = parse_args()
    config = load_json(Path(args.config))
    headers = load_json(Path(args.headers))
    if args.no_details:
        config["fetch_details"] = False
    if args.delay_seconds is not None:
        config["delay_seconds"] = args.delay_seconds

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    date_dir = datetime.now().strftime("%Y-%m-%d")
    output_dir = ROOT / "data" / "raw" / "ncss_jobs" / f"date={date_dir}" / f"run={run_id}"
    log_path = ROOT / "logs" / f"ncss_jobs_{run_id}.log"
    logger = setup_logger(log_path)

    logger.info("start ncss job crawler output=%s", output_dir)
    crawler = NcssJobCrawler(config=config, headers=headers, output_dir=output_dir, logger=logger)
    seen_job_ids = load_seen_job_ids(args.seen_jsonl) if args.seen_jsonl else set()
    existing_seen_count = len(seen_job_ids)
    query_jobs = build_query_jobs(args)
    if query_jobs:
        records_before_dedupe: list[dict] = []
        sub_manifests: list[dict] = []
        for query_label, query_overrides in query_jobs:
            logger.info("start query batch label=%s overrides=%s", query_label, query_overrides)
            query_records, query_manifest = crawler.crawl(
                start_page=args.start_page,
                max_pages=args.max_pages,
                page_size=args.page_size,
                query_overrides=query_overrides,
                query_label=query_label,
                seen_job_ids=seen_job_ids,
            )
            records_before_dedupe.extend(query_records)
            sub_manifests.append(query_manifest)
        records = dedupe_records(records_before_dedupe)
        manifest = {
            "source_name": config["source_name"],
            "list_endpoint": config["list_endpoint"],
            "crawl_mode": "query_combinations",
            "query_count": len(query_jobs),
            "query_jobs": [{"label": label, "overrides": overrides} for label, overrides in query_jobs],
            "existing_seen_job_id_count": existing_seen_count,
            "started_at": sub_manifests[0]["started_at"] if sub_manifests else datetime.now().isoformat(timespec="seconds"),
            "ended_at": datetime.now().isoformat(timespec="seconds"),
            "record_count_before_dedupe": len(records_before_dedupe),
            "record_count": len(records),
            "unique_source_job_id_count": len({record.get("source_job_id") for record in records}),
            "duplicate_source_job_id_count": len(records_before_dedupe) - len(records),
            "skipped_existing_or_duplicate_count": sum(item.get("skipped_duplicate_count", 0) for item in sub_manifests),
            "sub_manifests": sub_manifests,
        }
    else:
        records, manifest = crawler.crawl(
            start_page=args.start_page,
            max_pages=args.max_pages,
            page_size=args.page_size,
        )

    jsonl_path = output_dir / f"jobs_ncss_{date_dir}_batch001.jsonl"
    csv_path = output_dir / f"jobs_ncss_{date_dir}_batch001.csv"
    manifest_path = output_dir / "crawl_manifest.json"
    save_jsonl(jsonl_path, records)
    save_csv(csv_path, records, RAW_FIELDS)
    manifest["output_jsonl"] = str(jsonl_path.relative_to(ROOT))
    manifest["output_csv"] = str(csv_path.relative_to(ROOT))
    manifest["log_file"] = str(log_path.relative_to(ROOT))
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    logger.info("saved jsonl=%s", jsonl_path)
    logger.info("saved csv=%s", csv_path)
    logger.info("saved manifest=%s", manifest_path)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
