package com.employment.dto;

import java.time.LocalDate;
import java.util.List;

public record IndustrySalaryResponse(LocalDate statDate, String city, List<IndustrySalaryMetric> industries,
                                     String classificationBasis) {
}
