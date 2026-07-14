package com.employment.dto;

public record UniversityMarketSummary(long jobCount, long companyCount, long cityCount,
                                      long industryCount, Double averageSalary,
                                      Double medianSalary, Double maxSalary,
                                      long entryFriendlyCount, long skillJobCount) {
}
