package com.employment.vo;

import java.time.LocalDateTime;
import java.util.List;

public record UniversityStudentInsight(Long studentId, String studentNo, String name, String college,
                                       String major, String education, Integer graduationYear,
                                       boolean profileCompleted, LocalDateTime lastSavedAt,
                                       int skillCount, int experienceCount, boolean preferenceSaved,
                                       int topMatchScore, int averageMatchScore, String bestJobName,
                                       String bestJobCategory, boolean difficult, String status,
                                       List<String> gaps, List<String> evidence) {
}
