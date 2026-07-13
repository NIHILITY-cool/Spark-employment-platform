from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from bs4 import BeautifulSoup


CONTACT_TEXT_RE = re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")


def scrub_contact_text(value: str) -> str:
    return CONTACT_TEXT_RE.sub("[PHONE_REDACTED]", value)


def timestamp_ms_to_text(value: Any) -> str:
    if value in (None, ""):
        return ""
    try:
        return datetime.fromtimestamp(int(value) / 1000).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(value)


def build_salary_text(low: Any, high: Any) -> str:
    try:
        low_num = float(low or 0)
        high_num = float(high or 0)
    except Exception:
        return ""
    if low_num == 0 and high_num == 0:
        return "面议"
    low_text = f"{low_num:g}K"
    high_text = f"{high_num:g}K"
    return f"{low_text}-{high_text}/月"


def build_yuan_salary_text(low: Any, high: Any) -> str:
    try:
        low_num = int(float(low or 0))
        high_num = int(float(high or 0))
    except Exception:
        return ""
    if low_num <= 0 and high_num <= 0:
        return "面议"
    if low_num > 0 and high_num > 0:
        return f"{low_num}-{high_num}元/月"
    if low_num > 0:
        return f"{low_num}元以上/月"
    return f"{high_num}元以下/月"


def text_or_empty(node) -> str:
    if not node:
        return ""
    return " ".join(node.get_text("\n", strip=True).split())


def block_text_or_empty(node) -> str:
    if not node:
        return ""
    lines = [line.strip() for line in node.get_text("\n", strip=True).replace("\r", "\n").split("\n")]
    return "\n".join(line for line in lines if line)


def compact_text(value: str) -> str:
    return " ".join(value.split())


RESPONSIBILITY_KEYWORDS = [
    "岗位职责",
    "职位职责",
    "工作职责",
    "核心岗位职责",
    "工作内容",
    "职位描述",
    "岗位描述",
    "职责描述",
]
REQUIREMENT_KEYWORDS = [
    "岗位要求",
    "职位要求",
    "任职要求",
    "任职资格",
    "招聘要求",
    "任职条件",
    "资格要求",
    "能力要求",
]


def strip_section_prefix(line: str) -> str:
    return re.sub(r"^[\s\-*•◦（(]*[一二三四五六七八九十\d]*[、.．）)]?\s*", "", line).strip()


def split_heading_content(line: str, keywords: list[str]) -> tuple[bool, str]:
    text = strip_section_prefix(line)
    for keyword in keywords:
        index = text.find(keyword)
        if index < 0:
            continue
        prefix = text[:index].strip("【[] 　")
        if prefix and len(text) > 40 and "：" not in text and ":" not in text:
            continue
        rest = text[index + len(keyword) :].strip()
        rest = rest.lstrip("】] ：:")
        return True, rest
    return False, ""


def split_job_detail_text(raw_text: str) -> dict[str, str]:
    normalized_text = raw_text.replace("\r", "\n")
    heading_matches: list[tuple[int, int, str]] = []
    for keyword in RESPONSIBILITY_KEYWORDS:
        for match in re.finditer(re.escape(keyword), normalized_text):
            heading_matches.append((match.start(), match.end(), "job_responsibility"))
    for keyword in REQUIREMENT_KEYWORDS:
        for match in re.finditer(re.escape(keyword), normalized_text):
            heading_matches.append((match.start(), match.end(), "job_requirement"))
    heading_matches.sort(key=lambda item: item[0])

    if heading_matches:
        sections: dict[str, list[str]] = {
            "job_responsibility": [],
            "job_requirement": [],
        }
        for index, (_, heading_end, section_name) in enumerate(heading_matches):
            next_start = heading_matches[index + 1][0] if index + 1 < len(heading_matches) else len(normalized_text)
            content = normalized_text[heading_end:next_start].strip()
            content = content.lstrip("】] ：:")
            if content:
                sections[section_name].append(content)
        return {
            "job_description": compact_text(raw_text),
            "job_responsibility": compact_text("\n".join(sections["job_responsibility"])),
            "job_requirement": compact_text("\n".join(sections["job_requirement"])),
        }

    lines = [line.strip() for line in normalized_text.split("\n") if line.strip()]
    sections: dict[str, list[str]] = {
        "job_responsibility": [],
        "job_requirement": [],
    }
    current: str | None = None

    for line in lines:
        is_requirement, requirement_rest = split_heading_content(line, REQUIREMENT_KEYWORDS)
        if is_requirement:
            current = "job_requirement"
            if requirement_rest:
                sections[current].append(requirement_rest)
            continue

        is_responsibility, responsibility_rest = split_heading_content(line, RESPONSIBILITY_KEYWORDS)
        if is_responsibility:
            current = "job_responsibility"
            if responsibility_rest:
                sections[current].append(responsibility_rest)
            continue

        if current:
            sections[current].append(line)

    return {
        "job_description": compact_text(raw_text),
        "job_responsibility": compact_text("\n".join(sections["job_responsibility"])),
        "job_requirement": compact_text("\n".join(sections["job_requirement"])),
    }


def parse_job_detail_html(html: str) -> dict[str, str]:
    soup = BeautifulSoup(html, "lxml")

    company_info: dict[str, str] = {}
    for item in soup.select("ul.details li"):
        key_node = item.select_one(".ico")
        value_node = item.select_one(".show")
        key = text_or_empty(key_node)
        value = text_or_empty(value_node)
        if key:
            company_info[key] = value

    address_node = soup.select_one("#companyNameMap")
    detail = {
        "detail_job_name": text_or_empty(soup.select_one("#jobName")),
        "detail_company_name": text_or_empty(soup.select_one("#realCorpName")),
        "corp_id": text_or_empty(soup.select_one("#corpId")),
        "job_description": block_text_or_empty(soup.select_one("pre.mainContent")),
        "industry": text_or_empty(soup.select_one("#mainindustries")),
        "industry_sector": text_or_empty(soup.select_one("#industrySectors")),
        "company_address": text_or_empty(address_node),
        "company_website": company_info.get("公司网址", ""),
    }
    return detail


EDUCATION_CODE_MAP = {
    "00": "不限",
    "10": "研究生",
    "11": "博士研究生",
    "14": "硕士研究生",
    "20": "大学本科",
    "21": "大学本科",
    "30": "大学专科",
    "31": "大学专科",
    "40": "中等专科",
    "41": "中等专科",
    "44": "职业高中",
    "47": "技工学校",
    "50": "技工学校",
    "60": "高中",
    "61": "普通高中",
    "70": "初中",
    "71": "初中",
    "80": "小学",
    "81": "小学",
    "90": "其他",
}


def normalize_mohrss_experience(value: Any) -> str:
    text = str(value or "").strip()
    if not text or text == "0":
        return "经验不限"
    if text.isdigit():
        return f"{text}年及以上"
    return text


def normalize_mohrss_job(
    item: dict[str, Any],
    source_name: str,
    source_url: str,
    crawl_time: str,
    sanitized_raw: dict[str, Any],
) -> dict[str, Any]:
    description = scrub_contact_text(str(item.get("acb22a") or ""))
    detail_sections = split_job_detail_text(description)
    education_code = str(item.get("aac011") or "").strip()
    city = item.get("area_") or item.get("aab302", "")
    district = item.get("aab302", "")

    return {
        "source_job_id": str(item.get("acb200", "")),
        "job_name": item.get("aca112", ""),
        "company_name": item.get("aab004", ""),
        "city": city,
        "district": district if district != city else "",
        "industry": item.get("aca111_", ""),
        "company_size": "",
        "company_type": "",
        "salary_text": build_yuan_salary_text(item.get("acb241"), item.get("acb242")),
        "education_text": EDUCATION_CODE_MAP.get(education_code, education_code),
        "experience_text": normalize_mohrss_experience(item.get("acb246")),
        "job_description": detail_sections["job_description"],
        "job_responsibility": detail_sections["job_responsibility"],
        "job_requirement": detail_sections["job_requirement"],
        "publish_time": item.get("s_aae395") or item.get("s_ctime") or "",
        "source_name": source_name,
        "source_url": source_url,
        "crawl_time": crawl_time,
        "raw": sanitized_raw,
    }


def normalize_ncss_job(
    item: dict[str, Any],
    detail: dict[str, str] | None,
    source_name: str,
    source_url: str,
    crawl_time: str,
) -> dict[str, Any]:
    detail = detail or {}
    detail_sections = split_job_detail_text(detail.get("job_description", ""))
    responsibility_source = "explicit_heading"
    if not detail_sections["job_responsibility"]:
        responsibility_source = "fallback_job_description" if detail_sections["job_description"] else "missing"
    responsibility = detail_sections["job_responsibility"] or detail_sections["job_description"]
    company_name = item.get("recName") or detail.get("detail_company_name", "")
    job_name = item.get("jobName") or detail.get("detail_job_name", "")

    return {
        "source_job_id": item.get("jobId", ""),
        "job_name": job_name,
        "company_name": company_name,
        "city": item.get("areaCodeName", ""),
        "district": "",
        "industry": detail.get("industry", ""),
        "company_size": item.get("recScale", ""),
        "company_type": item.get("recProperty", ""),
        "salary_text": build_salary_text(item.get("lowMonthPay"), item.get("highMonthPay")),
        "education_text": item.get("degreeName", ""),
        "experience_text": "",
        "job_description": detail_sections["job_description"],
        "job_responsibility": responsibility,
        "job_requirement": detail_sections["job_requirement"],
        "publish_time": timestamp_ms_to_text(item.get("publishDate")),
        "source_name": source_name,
        "source_url": source_url,
        "crawl_time": crawl_time,
        "raw": {
            "major": item.get("major", ""),
            "head_count": item.get("headCount", ""),
            "update_time": timestamp_ms_to_text(item.get("updateDate")),
            "recruit_type": item.get("recruitType", ""),
            "company_id": item.get("recId", "") or detail.get("corp_id", ""),
            "company_logo": item.get("recLogo", ""),
            "job_tags": item.get("recTags", ""),
            "member_level": item.get("memberLevel", ""),
            "key_units": item.get("keyUnits", ""),
            "sources_name": item.get("sourcesName", ""),
            "sources_name_ch": item.get("sourcesNameCh", ""),
            "sources_type": item.get("sourcesType", ""),
            "industry_sector": detail.get("industry_sector", ""),
            "company_address": detail.get("company_address", ""),
            "company_website": detail.get("company_website", ""),
            "job_responsibility_source": responsibility_source,
        },
    }
