package com.employment.vo;

import com.employment.entity.Job;
import java.util.List;

public record JobRecommendation(Job job, int totalScore, int skillScore, int experienceScore,
                                int directionScore, int educationScore, int cityScore, int industryScore,
                                int salaryScore, int freshnessScore,
                                List<String> matchedSkills, List<String> missingSkills,
                                List<String> matchedExperienceTerms,
                                String recommendationReason) {
}
