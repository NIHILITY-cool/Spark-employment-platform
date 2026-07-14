package com.employment.dto;

import java.util.List;

public record CategoryFamilyMetric(String family, long jobCount, List<String> typicalJobs,
                                   String rule, List<CategoryShare> categories) {
}
