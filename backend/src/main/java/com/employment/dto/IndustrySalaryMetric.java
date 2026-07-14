package com.employment.dto;

public record IndustrySalaryMetric(String industry, long jobCount, long salarySampleCount,
                                   Double averageSalary, long below5k, long from5kTo8k,
                                   long from8kTo12k, long from12kTo20k, long above20k) {
}
