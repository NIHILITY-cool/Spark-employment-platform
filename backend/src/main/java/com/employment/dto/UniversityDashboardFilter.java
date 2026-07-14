package com.employment.dto;

public record UniversityDashboardFilter(String city, String industry, String education,
                                        String category, String companyScale, String keyword,
                                        Integer minSalary, Integer maxSalary) {
}
