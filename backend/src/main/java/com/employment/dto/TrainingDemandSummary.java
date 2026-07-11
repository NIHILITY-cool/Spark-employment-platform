package com.employment.dto;

public record TrainingDemandSummary(long jobCount, long entryFriendlyCount, Double averageSalaryMin,
                                    Double averageSalaryMax, int extractedSkillCount) {
}
