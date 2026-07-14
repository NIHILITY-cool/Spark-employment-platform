package com.employment.service;

import com.employment.vo.JobRecommendation;
import com.employment.vo.UniversityStudentInsight;
import com.employment.vo.UniversityStudentInsightResponse;
import com.employment.vo.UniversityStudentInsightSummary;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

@Service
public class UniversityStudentInsightService {
    private final JdbcTemplate jdbc;
    private final RecommendationService recommendationService;

    public UniversityStudentInsightService(JdbcTemplate jdbc, RecommendationService recommendationService) {
        this.jdbc = jdbc;
        this.recommendationService = recommendationService;
    }

    public UniversityStudentInsightResponse overview() {
        List<StudentRow> rows = jdbc.query("""
                SELECT s.id, s.student_no, s.name, s.college, s.major, s.education, s.graduation_year,
                       s.profile_completed, s.updated_at,
                       (SELECT COUNT(*) FROM student_skill ss WHERE ss.student_id = s.id) AS skill_count,
                       (SELECT COUNT(*) FROM student_experience se WHERE se.student_id = s.id) AS experience_count,
                       EXISTS(SELECT 1 FROM job_preference jp WHERE jp.student_id = s.id
                              AND (jp.expected_job <> '' OR jp.expected_city <> '' OR jp.expected_industry <> '')) AS preference_saved
                FROM student s LEFT JOIN platform_account a ON a.student_id = s.id
                WHERE a.id IS NULL OR (a.role = 'STUDENT' AND a.enabled = 1)
                ORDER BY s.updated_at DESC, s.id DESC
                """, (rs, rowNum) -> row(rs));
        List<UniversityStudentInsight> students = rows.stream().map(this::analyze)
                .sorted(Comparator.comparing(UniversityStudentInsight::difficult).reversed()
                        .thenComparingInt(UniversityStudentInsight::topMatchScore)
                        .thenComparing(UniversityStudentInsight::lastSavedAt, Comparator.reverseOrder()))
                .toList();
        long completed = students.stream().filter(UniversityStudentInsight::profileCompleted).count();
        long difficult = students.stream().filter(UniversityStudentInsight::difficult).count();
        List<UniversityStudentInsight> scored = students.stream().filter(item -> item.topMatchScore() > 0).toList();
        int average = scored.isEmpty() ? 0 : (int) Math.round(scored.stream()
                .mapToInt(UniversityStudentInsight::topMatchScore).average().orElse(0));
        return new UniversityStudentInsightResponse(
                new UniversityStudentInsightSummary(students.size(), completed, difficult, average), students,
                "学生情况以学生最后一次保存的画像、技能、经历和就业期望为准；匹配分来自当前有效岗位，不作为就业结果预测。" );
    }

    private UniversityStudentInsight analyze(StudentRow row) {
        List<String> gaps = new ArrayList<>();
        List<String> evidence = new ArrayList<>();
        if (!row.profileCompleted()) gaps.add("基本画像尚未完善");
        if (row.skillCount() == 0) gaps.add("技能清单未保存");
        else evidence.add("已维护 " + row.skillCount() + " 项技能");
        if (row.experienceCount() == 0) gaps.add("缺少项目或实习经历");
        else evidence.add("已维护 " + row.experienceCount() + " 条实践经历");
        if (!row.preferenceSaved()) gaps.add("未保存就业期望");
        else evidence.add("已保存就业方向与地区偏好");

        List<JobRecommendation> recommendations = row.profileCompleted() && row.preferenceSaved()
                ? safeRecommendations(row.studentId()) : List.of();
        JobRecommendation best = recommendations.isEmpty() ? null : recommendations.get(0);
        int topScore = best == null ? 0 : best.totalScore();
        int averageScore = recommendations.isEmpty() ? 0 : (int) Math.round(recommendations.stream()
                .mapToInt(JobRecommendation::totalScore).average().orElse(0));
        if (best != null) {
            if (best.experienceScore() < 18) gaps.add("实践经历与目标岗位关联偏弱");
            if (best.directionScore() < 18) gaps.add("目标方向证据不足");
            if (topScore < 50) gaps.add("当前最佳岗位匹配偏低");
            evidence.add(best.recommendationReason());
        }
        boolean difficult = gaps.size() >= 3 || (topScore > 0 && topScore < 50);
        String status = difficult ? "需重点关注"
                : !row.profileCompleted() ? "待完善画像"
                : topScore >= 65 ? "匹配较好" : "准备中";
        return new UniversityStudentInsight(row.studentId(), row.studentNo(), row.name(), row.college(), row.major(),
                row.education(), row.graduationYear(), row.profileCompleted(), row.lastSavedAt(), row.skillCount(),
                row.experienceCount(), row.preferenceSaved(), topScore, averageScore,
                best == null ? "" : best.job().jobName, best == null ? "" : best.job().jobCategory,
                difficult, status, List.copyOf(gaps), List.copyOf(evidence));
    }

    private List<JobRecommendation> safeRecommendations(Long studentId) {
        try {
            return recommendationService.topForOverview(studentId, 5);
        } catch (RuntimeException exception) {
            return List.of();
        }
    }

    private static StudentRow row(ResultSet rs) throws SQLException {
        return new StudentRow(rs.getLong("id"), rs.getString("student_no"), rs.getString("name"),
                rs.getString("college"), rs.getString("major"), rs.getString("education"),
                rs.getInt("graduation_year"), rs.getBoolean("profile_completed"),
                rs.getTimestamp("updated_at").toLocalDateTime(), rs.getInt("skill_count"),
                rs.getInt("experience_count"), rs.getBoolean("preference_saved"));
    }

    private record StudentRow(Long studentId, String studentNo, String name, String college, String major,
                              String education, Integer graduationYear, boolean profileCompleted,
                              LocalDateTime lastSavedAt, int skillCount, int experienceCount,
                              boolean preferenceSaved) {
    }
}
