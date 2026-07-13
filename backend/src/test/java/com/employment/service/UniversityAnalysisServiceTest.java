package com.employment.service;

import com.employment.dto.DemandMetric;
import com.employment.dto.TrainingDemandSummary;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class UniversityAnalysisServiceTest {
    @Test
    void exposesTheFiveSupportedMajorDirections() {
        assertEquals("大数据开发", UniversityAnalysisService.majorCategories().get("数据科学与大数据技术"));
        assertEquals(5, UniversityAnalysisService.majorCategories().size());
    }

    @Test
    void suggestionsUseMarketEvidenceAndAvoidQualityClaims() {
        TrainingDemandSummary summary = new TrainingDemandSummary(100, 20, 8000.0, 12000.0, 3);
        List<String> suggestions = UniversityAnalysisService.suggestions(summary,
                List.of(new DemandMetric("SQL", 50, null, null)),
                List.of(new DemandMetric("成都", 30, null, null)), "");
        assertTrue(suggestions.stream().anyMatch(item -> item.contains("SQL")));
        assertTrue(suggestions.stream().anyMatch(item -> item.contains("低经验门槛")));
        assertTrue(suggestions.stream().noneMatch(item -> item.contains("培养质量")));
    }
}
