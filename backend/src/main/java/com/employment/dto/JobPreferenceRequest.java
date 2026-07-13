package com.employment.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;

public record JobPreferenceRequest(String expectedJob, String expectedCity, String expectedIndustry,
                                   @Min(0) Integer salaryMin, @Min(0) Integer salaryMax,
                                   Boolean acceptRemoteCity) {
}
