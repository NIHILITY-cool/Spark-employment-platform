"""Shared location and salary rules for the employment data pipelines."""

from __future__ import annotations

import re


PROVINCE_LEVEL_LOCATIONS = frozenset({
    "安徽", "福建", "甘肃", "广东", "广西", "贵州", "海南", "河北", "黑龙江", "河南", "湖北",
    "湖南", "吉林", "江苏", "江西", "辽宁", "内蒙古", "宁夏", "青海", "山东", "山西", "陕西",
    "四川", "西藏", "新疆", "云南", "浙江", "香港", "澳门", "台湾", "全国",
})
DIRECT_CONTROLLED_CITIES = frozenset({"北京", "天津", "上海", "重庆"})
PROVINCE_PREFIXES = tuple(sorted((
    "内蒙古自治区", "广西壮族自治区", "宁夏回族自治区", "新疆维吾尔自治区", "西藏自治区",
    "香港特别行政区", "澳门特别行政区", "黑龙江省", "广东省", "山东省", "四川省", "河北省", "河南省",
    "云南省", "辽宁省", "湖南省", "安徽省", "湖北省", "浙江省", "江苏省", "福建省", "江西省",
    "陕西省", "山西省", "贵州省", "甘肃省", "青海省", "吉林省", "海南省", "台湾省",
), key=len, reverse=True))
PROVINCE_ALIASES = {
    "内蒙古自治区": "内蒙古", "广西壮族自治区": "广西", "宁夏回族自治区": "宁夏", "新疆维吾尔自治区": "新疆",
    "西藏自治区": "西藏", "香港特别行政区": "香港", "澳门特别行政区": "澳门",
}
LOCATION_LABEL_RE = re.compile(r"(?:工作地点|工作地址|办公地点|上班地点|岗位地点|工作地区)\s*(?:为|在|是)?\s*[:：]?\s*([^\n\r。；;]{1,80})")
CITY_IN_LOCATION_RE = re.compile(r"(?:^|[省区、，,;；\s])([\u4e00-\u9fff]{2,8})市")
ZHILIAN_SALARY_RE = re.compile(r"(?P<lower>\d+(?:\.\d+)?)\s*-\s*(?P<upper>\d+(?:\.\d+)?)\s*(?P<unit>万|元|[Kk])")


def clean_text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "").replace("\u3000", " ")).strip()


def normalize_city_name(value: object) -> str:
    text = clean_text(value)
    if text == "中国":
        return "全国"
    text = text.removesuffix("市")
    if text in PROVINCE_ALIASES:
        return PROVINCE_ALIASES[text]
    if text.endswith("省"):
        if len(text) > 2:
            text = text.removesuffix("省")
        else:
            return text
    for prefix in PROVINCE_PREFIXES:
        if text.startswith(prefix) and len(text) > len(prefix):
            text = text[len(prefix):]
            break
    return text


def is_province_level(value: object) -> bool:
    return normalize_city_name(value) in PROVINCE_LEVEL_LOCATIONS


def city_from_location_text(value: object) -> str:
    candidates: set[str] = set()
    for segment in LOCATION_LABEL_RE.findall(clean_text(value)):
        for match in CITY_IN_LOCATION_RE.finditer(segment):
            city = normalize_city_name(match.group(1))
            if city and not is_province_level(city):
                candidates.add(city)
        for municipality in DIRECT_CONTROLLED_CITIES:
            if municipality in segment:
                candidates.add(municipality)
    return candidates.pop() if len(candidates) == 1 else ""


def resolve_city(city_value: object, district_value: object = "", description: object = "") -> tuple[str, str]:
    """Return a normalized location and whether it is a verifiable city or province-level location."""
    city = normalize_city_name(city_value)
    if city and not is_province_level(city):
        return city, "city"
    district = clean_text(district_value)
    if district.endswith("市"):
        district_city = normalize_city_name(district)
        if district_city and not is_province_level(district_city):
            return district_city, "city"
    extracted = city_from_location_text(description)
    if extracted:
        return extracted, "city"
    return city, "province" if city else "unknown"


def parse_zhilian_monthly_salary(value: object) -> tuple[int | None, int | None]:
    """Parse only monthly Zhilian ranges; daily, hourly and per-task pay stay unparsed."""
    text = clean_text(value).replace(" ", "")
    if not text or any(marker in text for marker in ("/天", "/时", "/次")):
        return None, None
    match = ZHILIAN_SALARY_RE.search(text)
    if not match:
        return None, None
    factor = {"万": 10_000, "元": 1, "K": 1_000, "k": 1_000}[match.group("unit")]
    lower = round(float(match.group("lower")) * factor)
    upper = round(float(match.group("upper")) * factor)
    return (lower, upper) if 0 <= lower <= upper else (None, None)
