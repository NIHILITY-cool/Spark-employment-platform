"""Industry normalization rules for market analysis.

The pipeline keeps the algorithm deliberately small:
1. exact alias lookup;
2. keyword containment score;
3. lightweight text similarity fallback;
4. uncertain values are marked for review instead of being forced.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from difflib import SequenceMatcher


DICTIONARY_PATH = Path(__file__).resolve().parent / "dictionaries" / "industries.csv"
HIGH_CONFIDENCE = 0.82
REVIEW_CONFIDENCE = 0.58


@dataclass(frozen=True)
class NormalizedIndustry:
    raw: str
    industry: str
    confidence: float
    review_status: str
    method: str


def _clean(value: object) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"\s+", "", text)
    return text.replace("（", "(").replace("）", ")")


def _split_terms(value: str) -> list[str]:
    return [item.strip() for item in re.split(r"[|,，、/；;]", value or "") if item.strip()]


@lru_cache(maxsize=1)
def _load_dictionary() -> tuple[dict[str, str], list[dict[str, object]]]:
    aliases: dict[str, str] = {}
    entries: list[dict[str, object]] = []
    with DICTIONARY_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            industry = row["industry"].strip()
            alias_terms = [industry, *_split_terms(row.get("aliases", ""))]
            keyword_terms = _split_terms(row.get("keywords", ""))
            for term in alias_terms:
                aliases[_clean(term)] = industry
            entries.append({
                "industry": industry,
                "aliases": [_clean(term) for term in alias_terms],
                "keywords": [_clean(term) for term in keyword_terms],
            })
    return aliases, entries


def normalize_industry(value: object) -> NormalizedIndustry:
    raw = str(value or "").strip()
    text = _clean(raw)
    if not text:
        return NormalizedIndustry(raw, "未标注", 1.0, "empty", "empty")

    aliases, entries = _load_dictionary()
    if text in aliases:
        return NormalizedIndustry(raw, aliases[text], 1.0, "auto", "alias")

    best_industry = "其他"
    best_score = 0.0
    best_method = "fallback"
    for entry in entries:
        industry = str(entry["industry"])
        keywords = list(entry["keywords"])
        aliases_for_entry = list(entry["aliases"])
        keyword_hits = sum(1 for keyword in keywords if keyword and (keyword in text or text in keyword))
        if keyword_hits:
            score = min(0.96, 0.68 + keyword_hits * 0.09)
            if score > best_score:
                best_industry, best_score, best_method = industry, score, "keyword"
        for alias in aliases_for_entry:
            if not alias:
                continue
            score = SequenceMatcher(None, text, alias).ratio()
            if score > best_score:
                best_industry, best_score, best_method = industry, score, "similarity"

    if best_score >= HIGH_CONFIDENCE:
        return NormalizedIndustry(raw, best_industry, round(best_score, 4), "auto", best_method)
    if best_score >= REVIEW_CONFIDENCE:
        return NormalizedIndustry(raw, best_industry, round(best_score, 4), "review", best_method)
    return NormalizedIndustry(raw, "其他", round(best_score, 4), "review", "fallback")
