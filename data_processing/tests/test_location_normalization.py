from data_processing.location_normalization import (
    city_from_location_text,
    is_province_level,
    parse_zhilian_monthly_salary,
    resolve_city,
)


def test_province_is_not_treated_as_a_city() -> None:
    assert is_province_level("广东省")
    assert not is_province_level("广州市")


def test_resolve_city_prefers_city_level_district() -> None:
    assert resolve_city("四川省", "成都市") == ("成都", "city")


def test_resolve_city_canonicalizes_embedded_city_names() -> None:
    assert resolve_city("新疆乌鲁木齐") == ("乌鲁木齐", "city")
    assert resolve_city("宁波余姚市三七") == ("宁波", "city")


def test_resolve_city_preserves_province_scope_and_rejects_free_text() -> None:
    assert resolve_city("广东省") == ("广东", "province")
    assert resolve_city("拓展海外") == ("地点待定", "unknown")


def test_resolve_city_extracts_city_from_job_location_text() -> None:
    description = "岗位职责略。工作地点：广东省广州市天河区珠江新城。"
    assert city_from_location_text(description) == "广州"
    assert resolve_city("广东省", "", description) == ("广州", "city")


def test_ambiguous_location_text_is_not_used_to_invent_a_city() -> None:
    assert resolve_city("广东省", "", "工作地点：北京、上海、成都均有岗位") == ("广东", "province")


def test_zhilian_monthly_salary_parser_rejects_non_monthly_pay() -> None:
    assert parse_zhilian_monthly_salary("1-1.5万·13薪") == (10_000, 15_000)
    assert parse_zhilian_monthly_salary("8000-15000元") == (8_000, 15_000)
    assert parse_zhilian_monthly_salary("120-160元/天") == (None, None)
