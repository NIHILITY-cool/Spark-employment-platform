from __future__ import annotations

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from crawlers.base_crawler import BaseCrawler
from parsers.job_parser import normalize_ncss_job, parse_job_detail_html


class NcssJobCrawler(BaseCrawler):
    def __init__(
        self,
        config: dict[str, Any],
        headers: dict[str, str],
        output_dir: Path,
        logger: logging.Logger,
    ) -> None:
        super().__init__(
            headers=headers,
            delay_seconds=float(config.get("delay_seconds", 1.0)),
            timeout_seconds=int(config.get("timeout_seconds", 20)),
            logger=logger,
        )
        self.config = config
        self.output_dir = output_dir
        self.api_dir = output_dir / "api_responses"
        self.detail_dir = output_dir / "detail_pages"
        self.source_name = config["source_name"]
        self.list_endpoint = config["list_endpoint"]
        self.detail_url_template = config["detail_url_template"]
        self.fetch_details = bool(config.get("fetch_details", True))

    def crawl(
        self,
        max_pages: int | None = None,
        page_size: int | None = None,
        start_page: int | None = None,
        query_overrides: dict[str, str] | None = None,
        query_label: str = "all",
        seen_job_ids: set[str] | None = None,
    ) -> tuple[list[dict], dict]:
        max_pages = max_pages or int(self.config.get("max_pages", 5))
        page_size = page_size or int(self.config.get("page_size", 20))
        start_page = start_page or int(self.config.get("start_page", 1))
        end_page = start_page + max_pages - 1
        query_overrides = query_overrides or {}
        safe_query_label = re.sub(r"[^A-Za-z0-9_.=-]+", "_", query_label)
        records: list[dict] = []
        manifest: dict[str, Any] = {
            "source_name": self.source_name,
            "list_endpoint": self.list_endpoint,
            "query_label": query_label,
            "query_overrides": query_overrides,
            "start_page": start_page,
            "max_pages": max_pages,
            "page_size": page_size,
            "started_at": datetime.now().isoformat(timespec="seconds"),
            "pages": [],
            "detail_errors": [],
            "skipped_duplicate_count": 0,
        }
        self.detail_errors = manifest["detail_errors"]

        for offset in range(start_page, end_page + 1):
            params = dict(self.config.get("default_query", {}))
            params.update(query_overrides)
            params["offset"] = str(offset)
            params["limit"] = str(page_size)
            self.logger.info("fetch list offset=%s limit=%s", offset, page_size)
            data = self.get_json(self.list_endpoint, params=params)
            self.save_json(self.api_dir / f"{safe_query_label}_jobslist_offset_{offset}_limit_{page_size}.json", data)
            payload = data.get("data") if isinstance(data, dict) else None
            if not isinstance(payload, dict):
                manifest["pages"].append(
                    {
                        "offset": offset,
                        "limit": page_size,
                        "record_count": 0,
                        "response_flag": data.get("flag") if isinstance(data, dict) else None,
                        "response_global": data.get("global", []) if isinstance(data, dict) else [],
                        "response_errors": data.get("errors", []) if isinstance(data, dict) else [],
                    }
                )
                self.logger.info("list returned no public data offset=%s, stop", offset)
                break

            items = payload.get("list", [])
            page_info = payload.get("pagenation", {})
            page_skipped = 0
            page_new = 0
            manifest["pages"].append(
                {
                    "offset": offset,
                    "limit": page_size,
                    "record_count": len(items),
                    "new_record_count": page_new,
                    "skipped_duplicate_count": page_skipped,
                    "pagenation": page_info,
                }
            )
            if not items:
                self.logger.info("empty list offset=%s, stop", offset)
                break

            page_entry = manifest["pages"][-1]
            for item in items:
                job_id = item.get("jobId", "")
                if seen_job_ids is not None and job_id and job_id in seen_job_ids:
                    page_skipped += 1
                    continue
                if seen_job_ids is not None and job_id:
                    seen_job_ids.add(job_id)
                records.append(self._build_record(item))
                page_new += 1
            page_entry["new_record_count"] = page_new
            page_entry["skipped_duplicate_count"] = page_skipped
            manifest["skipped_duplicate_count"] += page_skipped

        manifest["ended_at"] = datetime.now().isoformat(timespec="seconds")
        manifest["record_count"] = len(records)
        manifest["unique_source_job_id_count"] = len({record.get("source_job_id") for record in records})
        return records, manifest

    def _build_record(self, item: dict[str, Any]) -> dict[str, Any]:
        job_id = item.get("jobId", "")
        detail_url = self.detail_url_template.format(job_id=job_id)
        detail: dict[str, str] = {}
        if self.fetch_details and job_id:
            try:
                html = self.get_text(detail_url)
                self.save_text(self.detail_dir / f"{job_id}.html", html)
                detail = parse_job_detail_html(html)
            except Exception as exc:
                self.logger.warning("detail failed job_id=%s error=%s", job_id, exc)
                if hasattr(self, "detail_errors"):
                    self.detail_errors.append({"job_id": job_id, "url": detail_url, "error": str(exc)})
        return normalize_ncss_job(
            item=item,
            detail=detail,
            source_name=self.source_name,
            source_url=detail_url,
            crawl_time=datetime.now().isoformat(timespec="seconds"),
        )
