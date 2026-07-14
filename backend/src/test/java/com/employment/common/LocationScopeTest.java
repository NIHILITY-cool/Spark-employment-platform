package com.employment.common;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

class LocationScopeTest {
    @Test
    void keepsMunicipalitiesAndFiltersProvinceLevelLocations() {
        assertTrue(LocationScope.isCity("北京"));
        assertTrue(LocationScope.isCity("成都"));
        assertFalse(LocationScope.isCity("广东"));
        assertFalse(LocationScope.isCity("全国"));
        assertFalse(LocationScope.isCity("技术与"));
        assertFalse(LocationScope.isCity("地点待定"));
    }

    @Test
    void mapsCanonicalCitiesToTheirProvince() {
        assertEquals("广东", LocationScope.provinceOf("深圳"));
        assertEquals("江苏", LocationScope.provinceOf("张家港"));
        assertEquals("黑龙江", LocationScope.provinceOf("五大连池"));
        assertEquals("北京", LocationScope.provinceOf("北京市"));
        assertTrue(LocationScope.citiesForProvince("四川").contains("成都"));
        assertTrue(LocationScope.citiesForProvince("四川").contains("西昌"));
        assertEquals("", LocationScope.provinceOf("地点待定"));
    }
}
