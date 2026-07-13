"""猎聘公开岗位采集器：列表页和详情页职位描述。

会话信息只允许由本机环境变量提供，不能写入代码、日志或版本库。请仅在
站点公开访问边界与其服务条款允许的范围内运行。
"""

from __future__ import annotations

import argparse
import os
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from bs4 import BeautifulSoup


BASE_URL = "https://m.liepin.com/"
SEARCH_API = "https://api-c.liepin.com/api/com.liepin.searchfront4c.h5-search-job"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
FEATURES = [
    "title", "dq", "requireEduLevel", "requireWorkYears", "salary", "company",
    "industry", "compScale", "jobLabels", "jobId", "companyId",
]


def build_headers() -> dict[str, str]:
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Content-Type": "application/json;charset=UTF-8",
        "Origin": BASE_URL.rstrip("/"),
        "Referer": BASE_URL,
        "User-Agent": "Mozilla/5.0",
        "X-Client-Type": "web",
        "X-Requested-With": "XMLHttpRequest",
    }
    if cookie := os.environ.get("LIEPIN_COOKIE"):
        headers["Cookie"] = cookie
    if xsrf_token := os.environ.get("LIEPIN_XSRF_TOKEN"):
        headers["X-XSRF-Token"] = xsrf_token
    return headers


def fetch_detail_description(job_id: int, headers: dict[str, str]) -> str:
    """Extract the public job-introduction text, returning an empty value on failure."""
    try:
        response = requests.get(f"{BASE_URL}job/19{job_id}.shtml", headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        for heading in soup.find_all("dt"):
            if heading.get_text(strip=True) == "职位介绍":
                description = heading.find_next("dd")
                if description:
                    return description.get_text("\n", strip=True)
        fallback = soup.find("p", class_="ellipsis-10")
        return fallback.get_text("\n", strip=True) if fallback else ""
    except requests.RequestException as exc:
        print(f"detail request failed for {job_id}: {exc}")
        return ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Crawl publicly accessible Liepin job records.")
    parser.add_argument("--pages", type=int, default=20)
    parser.add_argument("--page-size", type=int, default=20)
    parser.add_argument("--city-code", default="410")
    parser.add_argument("--delay-min", type=float, default=1.0)
    parser.add_argument("--delay-max", type=float, default=3.0)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def search_payload(city_code: str, page_size: int, page: int) -> dict[str, Any]:
    return {
        "data": {
            "condition": {
                "dqCode": city_code, "industryCodes": [], "keyword": "", "sortflag": "0",
                "compKindCodes": ["000"], "compScaleCodes": ["000"], "compStageCodes": [""],
                "salarylow": "0", "salaryhigh": "999", "eduCodes": [""], "refreshTime": "000",
                "workYearCodes": ["0"], "jobkindCode": "", "openShieldComp": True,
                "pageSize": page_size, "curPage": page,
            }
        }
    }


def main() -> None:
    args = parse_args()
    headers = build_headers()
    records: list[dict[str, Any]] = []
    seen_job_ids: set[str] = set()

    for page in range(args.pages):
        response = requests.post(
            SEARCH_API,
            headers=headers,
            json=search_payload(args.city_code, args.page_size, page),
            timeout=20,
        )
        response.raise_for_status()
        jobs = response.json().get("data", {}).get("soJobForms", [])
        if not jobs:
            break
        for job in jobs:
            job_id = str(job.get("jobId") or "")
            if not job_id or job_id in seen_job_ids:
                continue
            seen_job_ids.add(job_id)
            record = {field: job.get(field, "") for field in FEATURES}
            record["jobLink"] = f"{BASE_URL}job/19{job_id}.shtml"
            record["companyLink"] = f"{BASE_URL}company/{job.get('companyId')}" if job.get("companyId") else ""
            record["job_description"] = fetch_detail_description(int(job_id), headers)
            records.append(record)
            time.sleep(random.uniform(args.delay_min, args.delay_max))
        print(f"page {page + 1}: {len(records)} unique jobs")
        time.sleep(random.uniform(args.delay_min, args.delay_max))

    crawl_date = datetime.now().strftime("%Y-%m-%d")
    output = args.output or (
        PROJECT_ROOT / "data_source" / "data" / "raw" / "liepin" / f"date={crawl_date}" / f"job_detail_{crawl_date}.csv"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(records).to_csv(output, index=False, encoding="utf-8-sig")
    print(f"saved {len(records)} jobs to {output}")


if __name__ == "__main__":
    main()
