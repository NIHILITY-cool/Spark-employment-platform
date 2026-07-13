package com.employment.service;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;

class RecommendationServiceTest {
    @Test
    void recognizesChineseAndEnglishEducationLevels() {
        assertEquals(10, RecommendationService.educationScore("Bachelor", "本科及以上"));
        assertEquals(0, RecommendationService.educationScore("本科", "硕士及以上"));
        assertEquals(10, RecommendationService.educationScore("本科", "不限"));
    }

    @Test
    void favorsGraduateFriendlyExperienceRequirements() {
        assertEquals(20, RecommendationService.experienceScore("经验不限"));
        assertEquals(16, RecommendationService.experienceScore("1年以内"));
        assertEquals(8, RecommendationService.experienceScore("1-3年"));
        assertEquals(0, RecommendationService.experienceScore("5-10年"));
    }
}
