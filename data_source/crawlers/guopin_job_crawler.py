"""国聘公开岗位列表采集器。

接口认证值通过 ``GUOPIN_API_AUTH`` 环境变量提供，不能写入代码或提交仓库。
运行前请确认站点条款与访问频率要求。
"""

from __future__ import annotations

import argparse
import csv
import os
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import requests


API_URL = "https://gp-api.iguopin.com/api/jobs/v1/recom-job"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
FIELDS = [
    "job_id", "job_category", "job_name", "company_name", "company_short_name",
    "location", "education", "experience", "salary_min", "salary_max",
    "job_description", "job_url", "crawl_date",
]


def build_headers() -> dict[str, str]:
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Origin": "https://www.iguopin.com",
        "Referer": "https://www.iguopin.com/",
        "User-Agent": "Mozilla/5.0",
    }
    if api_auth := os.environ.get("GUOPIN_API_AUTH"):
        headers["apiauth"] = api_auth
    return headers


def parse_job(item: dict[str, Any], crawl_date: str) -> dict[str, Any]:
    districts = item.get("district_list") or []
    district = districts[0] if districts and isinstance(districts[0], dict) else {}
    job_id = str(item.get("job_id") or "")
    return {
        "job_id": job_id,
        "job_category": str(item.get("category_cn") or ""),
        "job_name": str(item.get("job_name") or ""),
        "company_name": str(item.get("company_name") or ""),
        "company_short_name": str(item.get("company_short_name") or ""),
        "location": str(district.get("area_cn") or ""),
        "education": str(item.get("education_cn") or ""),
        "experience": str(item.get("experience_cn") or ""),
        "salary_min": item.get("min_wage") or "",
        "salary_max": item.get("max_wage") or "",
        "job_description": str(item.get("contents") or ""),
        "job_url": f"https://www.iguopin.com/job/detail?id={job_id}",
        "crawl_date": crawl_date,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Crawl public Guopin recommendation jobs.")
    parser.add_argument("--pages", type=int, default=20)
    parser.add_argument("--page-size", type=int, default=20)
    parser.add_argument("--delay-min", type=float, default=2.0)
    parser.add_argument("--delay-max", type=float, default=5.0)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    crawl_date = datetime.now().strftime("%Y-%m-%d")
    output = args.output or (
        PROJECT_ROOT / "data_source" / "data" / "raw" / "guopin" / f"date={crawl_date}" / f"jobs_guopin_{crawl_date}.csv"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    jobs: list[dict[str, Any]] = []

    for page in range(1, args.pages + 1):
        payload = {
            "search": {"page": page, "page_size": args.page_size},
            "recom": {"update_time": True, "company_nature": True, "hot_job": True},
        }
        response = requests.post(API_URL, headers=build_headers(), json=payload, timeout=20)
        response.raise_for_status()
        records = response.json().get("data", {}).get("list", [])
        if not records:
            break
        jobs.extend(parse_job(item, crawl_date) for item in records if isinstance(item, dict))
        time.sleep(random.uniform(args.delay_min, args.delay_max))

    with output.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(jobs)
    print(f"saved {len(jobs)} jobs to {output}")


if __name__ == "__main__":
    main()
