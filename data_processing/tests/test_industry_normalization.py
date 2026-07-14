from data_processing.industry_normalization import load_industry_rules, normalize_industry


def test_exact_alias_maps_to_standard_industry() -> None:
    result = normalize_industry("互联网/电子商务")
    assert result.industry == "信息技术"
    assert result.review_status == "auto"


def test_keyword_match_handles_new_source_text() -> None:
    result = normalize_industry("云计算与大数据平台服务")
    assert result.industry == "信息技术"
    assert result.review_status == "auto"


def test_uncertain_industry_requires_review() -> None:
    result = normalize_industry("神秘新兴交叉赛道")
    assert result.industry == "其他"
    assert result.review_status == "review"


def test_blank_industry_is_not_forced_into_other_business_category() -> None:
    result = normalize_industry("")
    assert result.industry == "未标注"
    assert result.review_status == "empty"


def test_preloaded_rules_support_spark_worker_execution() -> None:
    result = normalize_industry("证券与基金服务", load_industry_rules())
    assert result.industry == "金融财会"
