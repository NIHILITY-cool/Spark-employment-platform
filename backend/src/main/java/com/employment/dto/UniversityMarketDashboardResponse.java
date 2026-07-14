package com.employment.dto;

import java.time.LocalDate;
import java.util.List;

public record UniversityMarketDashboardResponse(LocalDate statDate, UniversityDashboardFilter filter,
                                                UniversityMarketSummary summary,
                                                List<DemandMetric> cities,
                                                List<DemandMetric> industries,
                                                List<DemandMetric> education,
                                                List<DemandMetric> companyScales,
                                                List<DemandMetric> jobCategories,
                                                List<DemandMetric> hotJobs,
                                                List<DemandMetric> hotSkills,
                                                List<SalaryBucket> salaryBuckets,
                                                List<CategoryFamilyMetric> categoryFamilies,
                                                List<RegionalCategoryShare> regionalCategoryShares,
                                                List<HeatmapCell> cityIndustryHeatmap,
                                                List<String> suggestions,
                                                DataQualitySummary dataQuality,
                                                String dataBasis) {
}
