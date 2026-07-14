package com.employment.service;

import com.employment.entity.StudentExperience;
import com.employment.entity.Job;
import org.junit.jupiter.api.Test;

import java.time.LocalDate;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;

class RecommendationServiceTest {
    @Test
    void recognizesChineseAndEnglishEducationLevels() {
        assertEquals(10, RecommendationService.educationScore("Bachelor", "本科及以上"));
        assertEquals(0, RecommendationService.educationScore("本科", "硕士及以上"));
        assertEquals(10, RecommendationService.educationScore("本科", "不限"));
        assertEquals(false, RecommendationService.educationEligible("本科", "硕士及以上"));
        assertEquals(true, RecommendationService.educationEligible("本科", "本科及以上"));
    }

    @Test
    void combinesExperienceEvidenceWithJobThresholds() {
        assertEquals(8, RecommendationService.experienceRequirementScore("经验不限", false, false));
        assertEquals(6, RecommendationService.experienceRequirementScore("1年以内", true, false));
        assertEquals(6, RecommendationService.experienceRequirementScore("1-3年", false, true));
        assertEquals(0, RecommendationService.experienceRequirementScore("5-10年", true, false));
    }

    @Test
    void recoversExperienceYearsFromDescriptionWhenStructuredFieldIsWrong() {
        assertEquals(5, RecommendationService.requiredExperienceYears("经验不限", "要求5-10年相关工作经验"));
        assertEquals(3, RecommendationService.requiredExperienceYears("3年以上", "负责项目交付"));
        assertEquals(0, RecommendationService.requiredExperienceYears("应届生", "欢迎在校学生"));
    }

    @Test
    void rewardsConcreteResultsAndMeaningfulAwardsWithoutDominatingTheScore() {
        StudentExperience project = experience("project", "数据分析平台", "负责 SQL 分析，上线后效率提升 30%");
        StudentExperience award = experience("award", "全国大学生数据竞赛一等奖", "全国一等奖");
        assertEquals(4, RecommendationService.achievementScore(List.of(project, award)));
    }

    @Test
    void recentJobsReceiveFreshnessEvidence() {
        assertEquals(5, RecommendationService.freshnessScore(LocalDate.now().minusDays(2)));
        assertEquals(3, RecommendationService.freshnessScore(LocalDate.now().minusDays(20)));
        assertEquals(0, RecommendationService.freshnessScore(LocalDate.now().minusDays(120)));
    }

    @Test
    void salaryUsesOnlyTheMinimumExpectationAndNeverPenalizesHigherPay() {
        Job highPay = new Job();
        highPay.salaryMin = 18000;
        highPay.salaryMax = 25000;
        Job overlapping = new Job();
        overlapping.salaryMin = 6000;
        overlapping.salaryMax = 12000;
        assertEquals(10, RecommendationService.salaryScore(8000, highPay));
        assertEquals(7, RecommendationService.salaryScore(8000, overlapping));
    }

    private StudentExperience experience(String type, String title, String description) {
        StudentExperience experience = new StudentExperience();
        experience.experienceType = type;
        experience.title = title;
        experience.description = description;
        return experience;
    }
}
