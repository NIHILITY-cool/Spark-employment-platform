package com.employment.common;

import java.util.Set;

public final class LocationScope {
    private static final Set<String> PROVINCE_LEVEL_LOCATIONS = Set.of(
            "安徽", "福建", "甘肃", "广东", "广西", "贵州", "海南", "河北", "黑龙江", "河南", "湖北",
            "湖南", "吉林", "江苏", "江西", "辽宁", "内蒙古", "宁夏", "青海", "山东", "山西", "陕西",
            "四川", "西藏", "新疆", "云南", "浙江", "香港", "澳门", "台湾", "全国");

    private LocationScope() { }

    public static boolean isCity(String value) {
        return value != null && !value.isBlank() && !PROVINCE_LEVEL_LOCATIONS.contains(value.trim());
    }

    public static Set<String> provinceLevelLocations() {
        return PROVINCE_LEVEL_LOCATIONS;
    }
}
