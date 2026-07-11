package com.employment.service;

import com.employment.dto.DemandMetric;
import com.employment.dto.RegionalDemandCell;
import com.employment.dto.TrainingAlignmentResponse;
import com.employment.dto.TrainingDemandSummary;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Service
public class UniversityAnalysisService {
    private static final Map<String, String> MAJOR_CATEGORIES = majorCategories();
    private final NamedParameterJdbcTemplate jdbc;

    public UniversityAnalysisService(NamedParameterJdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    public TrainingAlignmentResponse trainingAlignment(String requestedMajor, String requestedCity) {
        String major = MAJOR_CATEGORIES.containsKey(requestedMajor)
                ? requestedMajor : MAJOR_CATEGORIES.keySet().iterator().next();
        String category = MAJOR_CATEGORIES.get(major);
        String city = normalizeCity(requestedCity);
        MapSqlParameterSource parameters = new MapSqlParameterSource()
                .addValue("category", category).addValue("city", city);
        String filter = " WHERE j.job_status = 'active' AND j.job_category = :category "
                + (StringUtils.hasText(city) ? " AND j.city = :city " : "");

        Map<String, Object> summaryRow = jdbc.queryForMap("""
                SELECT COUNT(*) AS job_count,
                       SUM(CASE WHEN j.experience_requirement = ''
                                  OR j.experience_requirement LIKE '%不限%'
                                  OR j.experience_requirement LIKE '%应届%'
                                  OR j.experience_requirement LIKE '%1年以内%' THEN 1 ELSE 0 END) AS entry_friendly_count,
                       ROUND(AVG(j.salary_min), 0) AS average_salary_min,
                       ROUND(AVG(j.salary_max), 0) AS average_salary_max
                FROM job j
                """ + filter, parameters);

        List<DemandMetric> skills = metrics("""
                SELECT js.skill_name AS dimension_key, COUNT(DISTINCT j.job_key) AS job_count,
                       NULL AS average_salary_min, NULL AS average_salary_max
                FROM job j JOIN job_skill js ON js.job_key = j.job_key
                """ + filter + " GROUP BY js.skill_name ORDER BY job_count DESC, dimension_key LIMIT 12", parameters);
        TrainingDemandSummary summary = new TrainingDemandSummary(number(summaryRow, "job_count"),
                number(summaryRow, "entry_friendly_count"), decimal(summaryRow, "average_salary_min"),
                decimal(summaryRow, "average_salary_max"), skills.size());

        List<DemandMetric> cities = metrics("""
                SELECT j.city AS dimension_key, COUNT(*) AS job_count,
                       ROUND(AVG(j.salary_min), 0) AS average_salary_min,
                       ROUND(AVG(j.salary_max), 0) AS average_salary_max
                FROM job j WHERE j.job_status = 'active' AND j.job_category = :category
                GROUP BY j.city ORDER BY job_count DESC, dimension_key LIMIT 10
                """, parameters);
        List<DemandMetric> industries = metrics("""
                SELECT COALESCE(NULLIF(j.industry, ''), '未标注') AS dimension_key, COUNT(*) AS job_count,
                       ROUND(AVG(j.salary_min), 0) AS average_salary_min,
                       ROUND(AVG(j.salary_max), 0) AS average_salary_max
                FROM job j
                """ + filter + " GROUP BY dimension_key ORDER BY job_count DESC, dimension_key LIMIT 10", parameters);
        List<DemandMetric> education = metrics("""
                SELECT COALESCE(NULLIF(j.education_requirement, ''), '不限') AS dimension_key, COUNT(*) AS job_count,
                       NULL AS average_salary_min, NULL AS average_salary_max
                FROM job j
                """ + filter + " GROUP BY dimension_key ORDER BY job_count DESC, dimension_key", parameters);

        List<RegionalDemandCell> matrix = jdbc.query("""
                WITH top_cities AS (
                    SELECT city FROM job WHERE job_status = 'active' AND city <> ''
                    GROUP BY city ORDER BY COUNT(*) DESC LIMIT 6
                ), top_categories AS (
                    SELECT job_category FROM job
                    WHERE job_status = 'active' AND job_category NOT IN ('', '其他')
                    GROUP BY job_category ORDER BY COUNT(*) DESC LIMIT 6
                )
                SELECT j.city, j.job_category, COUNT(*) AS job_count
                FROM job j JOIN top_cities c ON c.city = j.city
                JOIN top_categories g ON g.job_category = j.job_category
                WHERE j.job_status = 'active'
                GROUP BY j.city, j.job_category ORDER BY j.city, j.job_category
                """, parameters, (rs, rowNum) -> new RegionalDemandCell(rs.getString("city"),
                rs.getString("job_category"), rs.getLong("job_count")));

        return new TrainingAlignmentResponse(LocalDate.of(2026, 7, 11), major, category, city,
                MAJOR_CATEGORIES, summary, cities, industries, education, skills, matrix,
                suggestions(summary, skills, cities, city),
                "基于 Spark 清洗后写入 MySQL 的 2026-07-11 公开岗位批次；仅反映近期市场需求，不代表培养质量或长期预测。" );
    }

    static Map<String, String> majorCategories() {
        LinkedHashMap<String, String> mapping = new LinkedHashMap<>();
        mapping.put("数据科学与大数据技术", "大数据开发");
        mapping.put("计算机科学与技术", "后端开发");
        mapping.put("软件工程", "前端开发");
        mapping.put("统计学", "数据分析");
        mapping.put("人工智能", "人工智能");
        return Collections.unmodifiableMap(mapping);
    }

    static List<String> suggestions(TrainingDemandSummary summary, List<DemandMetric> skills,
                                    List<DemandMetric> cities, String city) {
        List<String> result = new ArrayList<>();
        if (!skills.isEmpty()) {
            result.add("优先评估 " + String.join("、", skills.stream().limit(3).map(DemandMetric::key).toList())
                    + " 是否已覆盖在课程或项目训练中。");
        }
        double friendlyRate = summary.jobCount() == 0 ? 0
                : 100.0 * summary.entryFriendlyCount() / summary.jobCount();
        if (friendlyRate < 35) result.add("低经验门槛岗位占比较低，建议增加企业项目和实践经历训练。" );
        if (!StringUtils.hasText(city) && !cities.isEmpty()) {
            result.add("该方向岗位主要集中在 " + String.join("、", cities.stream().limit(3).map(DemandMetric::key).toList())
                    + "，可作为校企合作区域参考。" );
        }
        if (summary.jobCount() == 0) result.add("当前筛选范围没有岗位样本，请扩大地区或调整专业方向。" );
        return result;
    }

    private List<DemandMetric> metrics(String sql, MapSqlParameterSource parameters) {
        return jdbc.query(sql, parameters, (rs, rowNum) -> new DemandMetric(rs.getString("dimension_key"),
                rs.getLong("job_count"), nullableDouble(rs.getObject("average_salary_min")),
                nullableDouble(rs.getObject("average_salary_max"))));
    }

    private static long number(Map<String, Object> row, String key) {
        Object value = row.get(key);
        return value instanceof Number number ? number.longValue() : 0;
    }

    private static Double decimal(Map<String, Object> row, String key) {
        return nullableDouble(row.get(key));
    }

    private static Double nullableDouble(Object value) {
        return value instanceof Number number ? number.doubleValue() : null;
    }

    private static String normalizeCity(String value) {
        if (!StringUtils.hasText(value)) return "";
        String normalized = value.trim().replaceFirst("市+$", "");
        return "中国".equals(normalized) ? "全国" : normalized;
    }
}
