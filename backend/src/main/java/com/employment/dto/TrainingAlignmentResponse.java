package com.employment.dto;

import java.time.LocalDate;
import java.util.List;
import java.util.Map;

public record TrainingAlignmentResponse(LocalDate statDate, String major, String targetCategory, String city,
                                        Map<String, String> availableMajors, TrainingDemandSummary summary,
                                        List<DemandMetric> cities, List<DemandMetric> industries,
                                        List<DemandMetric> education, List<DemandMetric> skills,
                                        List<RegionalDemandCell> regionalMatrix, List<String> suggestions,
                                        String dataBasis) {
}
