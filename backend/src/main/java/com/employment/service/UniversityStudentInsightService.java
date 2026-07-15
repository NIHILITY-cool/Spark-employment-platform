package com.employment.service;

import com.employment.vo.JobRecommendation;
import com.employment.vo.UniversityStudentInsight;
import com.employment.vo.UniversityStudentInsightResponse;
import com.employment.vo.UniversityStudentInsightSummary;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;
import java.util.Map;

@Service
public class UniversityStudentInsightService {
    private static final int MAX_PAGE_SIZE = 30;
    private static final String ACTIVE_STUDENT = """
            FROM student s LEFT JOIN platform_account a ON a.student_id = s.id
            WHERE (a.id IS NULL OR (a.role = 'STUDENT' AND a.enabled = 1))
            """;
    private static final String BASIC_GAP_COUNT = """
            ((CASE WHEN s.profile_completed = 0 THEN 1 ELSE 0 END)
             + (CASE WHEN NOT EXISTS(SELECT 1 FROM student_skill ss WHERE ss.student_id = s.id) THEN 1 ELSE 0 END)
             + (CASE WHEN NOT EXISTS(SELECT 1 FROM student_experience se WHERE se.student_id = s.id) THEN 1 ELSE 0 END)
             + (CASE WHEN NOT EXISTS(SELECT 1 FROM job_preference jp WHERE jp.student_id = s.id
                         AND (jp.expected_job <> '' OR jp.expected_city <> '' OR jp.expected_industry <> ''))
                     THEN 1 ELSE 0 END))
            """;

    private final JdbcTemplate jdbc;
    private final RecommendationService recommendationService;
    private final StudentInsightCache cache;

    public UniversityStudentInsightService(JdbcTemplate jdbc, RecommendationService recommendationService,
                                           StudentInsightCache cache) {
        this.jdbc = jdbc;
        this.recommendationService = recommendationService;
        this.cache = cache;
    }

    public UniversityStudentInsightResponse overview(int requestedPage, int requestedSize,
                                                      String requestedKeyword, String requestedStatus) {
        int size = Math.min(Math.max(requestedSize, 1), MAX_PAGE_SIZE);
        String keyword = StringUtils.hasText(requestedKeyword) ? requestedKeyword.trim() : "";
        String status = normalizeStatus(requestedStatus);
        int page = Math.max(requestedPage, 1);
        return cache.getOrLoad(page, size, keyword, status,
                () -> loadOverview(page, size, keyword, status));
    }

    private UniversityStudentInsightResponse loadOverview(int requestedPage, int size,
                                                           String keyword, String status) {
        List<Object> filterArguments = new ArrayList<>();
        String filter = pageFilter(keyword, status, filterArguments);

        Long filteredTotal = jdbc.queryForObject("SELECT COUNT(*) " + ACTIVE_STUDENT + filter,
                Long.class, filterArguments.toArray());
        long total = filteredTotal == null ? 0 : filteredTotal;
        int totalPages = Math.max(1, (int) Math.ceil(total / (double) size));
        int page = Math.min(requestedPage, totalPages);

        List<Object> pageArguments = new ArrayList<>(filterArguments);
        pageArguments.add(size);
        pageArguments.add((page - 1) * size);
        List<StudentRow> rows = jdbc.query("""
                SELECT s.id, s.student_no, s.name, s.college, s.major, s.education, s.graduation_year,
                       s.profile_completed, s.updated_at,
                       (SELECT COUNT(*) FROM student_skill ss WHERE ss.student_id = s.id) AS skill_count,
                       (SELECT COUNT(*) FROM student_experience se WHERE se.student_id = s.id) AS experience_count,
                       EXISTS(SELECT 1 FROM job_preference jp WHERE jp.student_id = s.id
                              AND (jp.expected_job <> '' OR jp.expected_city <> '' OR jp.expected_industry <> '')) AS preference_saved
                """ + ACTIVE_STUDENT + filter + " ORDER BY (" + BASIC_GAP_COUNT + ") DESC, s.updated_at DESC, s.id DESC LIMIT ? OFFSET ?",
                (rs, rowNum) -> row(rs), pageArguments.toArray());

        List<UniversityStudentInsight> students = rows.stream().map(this::analyze)
                .sorted(Comparator.comparing(UniversityStudentInsight::difficult).reversed()
                        .thenComparingInt(UniversityStudentInsight::topMatchScore)
                        .thenComparing(UniversityStudentInsight::lastSavedAt, Comparator.reverseOrder()))
                .toList();

        Map<String, Object> summaryRow = jdbc.queryForMap("""
                SELECT COUNT(*) AS student_count,
                       COALESCE(SUM(CASE WHEN s.profile_completed = 1 THEN 1 ELSE 0 END), 0) AS completed_count,
                       COALESCE(SUM(CASE WHEN """ + BASIC_GAP_COUNT + " >= 3 THEN 1 ELSE 0 END), 0) AS difficult_count " + ACTIVE_STUDENT);
        List<UniversityStudentInsight> scored = students.stream().filter(item -> item.bestJobName() != null
                && !item.bestJobName().isBlank()).toList();
        int pageAverage = scored.isEmpty() ? 0 : (int) Math.round(scored.stream()
                .mapToInt(UniversityStudentInsight::topMatchScore).average().orElse(0));
        UniversityStudentInsightSummary summary = new UniversityStudentInsightSummary(
                number(summaryRow, "student_count"), number(summaryRow, "completed_count"),
                number(summaryRow, "difficult_count"), pageAverage);

        return new UniversityStudentInsightResponse(summary, students,
                "学生情况来自最后一次保存的画像、技能、经历和就业期望；匹配分按当前页实时计算，不作为就业结果预测。",
                page, size, total, totalPages);
    }

    private String pageFilter(String keyword, String status, List<Object> arguments) {
        StringBuilder sql = new StringBuilder();
        if (StringUtils.hasText(keyword)) {
            String like = "%" + keyword + "%";
            sql.append(" AND (s.name LIKE ? OR s.student_no LIKE ? OR s.college LIKE ? OR s.major LIKE ?)");
            arguments.add(like);
            arguments.add(like);
            arguments.add(like);
            arguments.add(like);
        }
        if ("support".equals(status)) sql.append(" AND (").append(BASIC_GAP_COUNT).append(") >= 3");
        if ("incomplete".equals(status)) sql.append(" AND (").append(BASIC_GAP_COUNT).append(") BETWEEN 1 AND 2");
        if ("complete".equals(status)) sql.append(" AND (").append(BASIC_GAP_COUNT).append(") = 0");
        return sql.toString();
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
        int profileGapCount = gaps.size();

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
        } else if (row.profileCompleted() && row.preferenceSaved()) {
            gaps.add("当前岗位批次暂无满足学历门槛的候选岗位");
        }
        boolean difficult = profileGapCount >= 3;
        String state = difficult ? "重点支持"
                : profileGapCount > 0 ? "待完善资料"
                : best == null ? "暂无匹配"
                : topScore >= 65 ? "匹配较好" : "常规跟进";
        return new UniversityStudentInsight(row.studentId(), row.studentNo(), row.name(), row.college(), row.major(),
                row.education(), row.graduationYear(), row.profileCompleted(), row.lastSavedAt(), row.skillCount(),
                row.experienceCount(), row.preferenceSaved(), topScore, averageScore,
                best == null ? "" : best.job().jobName, best == null ? "" : best.job().jobCategory,
                difficult, state, List.copyOf(gaps), List.copyOf(evidence));
    }

    private List<JobRecommendation> safeRecommendations(Long studentId) {
        try {
            return recommendationService.topForOverview(studentId, 5);
        } catch (RuntimeException exception) {
            return List.of();
        }
    }

    private static String normalizeStatus(String value) {
        String normalized = value == null ? "all" : value.trim().toLowerCase(Locale.ROOT);
        if ("difficult".equals(normalized)) return "support";
        if ("normal".equals(normalized)) return "complete";
        return List.of("all", "support", "incomplete", "complete").contains(normalized) ? normalized : "all";
    }

    private static long number(Map<String, Object> row, String key) {
        Object value = row.get(key);
        return value instanceof Number number ? number.longValue() : 0;
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
