package com.employment.vo;

import com.employment.entity.Job;
import java.util.List;

public record JobRecommendation(Job job, int totalScore, int skillScore, List<String> matchedSkills,
                                List<String> missingSkills, String recommendationReason) {
}
