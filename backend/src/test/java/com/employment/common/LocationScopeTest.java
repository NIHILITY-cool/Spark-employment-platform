package com.employment.common;

import org.junit.jupiter.api.Test;

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
}
