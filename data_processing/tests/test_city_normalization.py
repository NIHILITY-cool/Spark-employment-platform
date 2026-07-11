from data_processing.pandas_jobs.clean_ncss_jobs import split_location


def test_city_suffix_is_removed() -> None:
    assert split_location("成都市", "") == ("成都", "")
    assert split_location("珠海市", "香洲区") == ("珠海", "香洲区")


def test_non_suffix_city_text_is_preserved() -> None:
    assert split_location("山东省莱芜市", "") == ("山东省莱芜", "")
    assert split_location("北京", "海淀区") == ("北京", "海淀区")


def test_country_wide_location_is_not_treated_as_a_city() -> None:
    assert split_location("中国", "") == ("全国", "")
