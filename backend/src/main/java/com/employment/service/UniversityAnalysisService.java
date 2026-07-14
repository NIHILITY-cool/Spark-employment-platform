package com.employment.service;

import com.employment.common.LocationScope;
import com.employment.dto.DemandMetric;
import com.employment.dto.IndustrySalaryMetric;
import com.employment.dto.IndustrySalaryResponse;
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
import java.util.regex.Pattern;

@Service
public class UniversityAnalysisService {
    private static final Map<String, String> MAJOR_CATEGORIES = majorCategories();
    private static final Map<String, String> INDUSTRY_RULES = industryRules();
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
                .addValue("category", category).addValue("city", city)
                .addValue("provinceLevelLocations", LocationScope.provinceLevelLocations());
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
                  AND j.city NOT IN (:provinceLevelLocations)
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
                      AND city NOT IN (:provinceLevelLocations)
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

    public IndustrySalaryResponse industrySalaryDistribution(String requestedCity) {
        String city = normalizeCity(requestedCity);
        MapSqlParameterSource parameters = new MapSqlParameterSource().addValue("city", city);
        StringBuilder classifier = new StringBuilder("CASE");
        int ruleIndex = 0;
        for (Map.Entry<String, String> rule : INDUSTRY_RULES.entrySet()) {
            String parameterName = "industryPattern" + ruleIndex++;
            classifier.append(" WHEN searchable_text REGEXP :").append(parameterName)
                    .append(" THEN '").append(rule.getKey()).append("'");
            parameters.addValue(parameterName, rule.getValue());
        }
        classifier.append(" ELSE '其他' END");

        String categories = INDUSTRY_RULES.keySet().stream()
                .map(category -> "SELECT '" + category + "' AS industry_category, "
                        + (new ArrayList<>(INDUSTRY_RULES.keySet()).indexOf(category) + 1) + " AS sort_order")
                .reduce((left, right) -> left + " UNION ALL " + right).orElse("")
                + " UNION ALL SELECT '其他', " + (INDUSTRY_RULES.size() + 1);

        String salarySql = """
                WITH source_jobs AS (
                    SELECT LOWER(CONCAT_WS(' ', j.job_name, COALESCE(j.job_description, ''))) AS searchable_text,
                           CASE WHEN j.salary_min > 0 AND j.salary_max >= j.salary_min
                                THEN (j.salary_min + j.salary_max) / 2.0 END AS monthly_salary
                    FROM job j
                    WHERE j.job_status = 'active'
                    %s
                ), classified AS (
                    SELECT %s AS industry_category, monthly_salary FROM source_jobs
                ), category_order AS (
                    %s
                ), aggregated AS (
                    SELECT industry_category, COUNT(*) AS job_count,
                           COUNT(monthly_salary) AS salary_sample_count,
                           ROUND(AVG(monthly_salary), 0) AS average_salary,
                           SUM(CASE WHEN monthly_salary < 5000 THEN 1 ELSE 0 END) AS below_5k,
                           SUM(CASE WHEN monthly_salary >= 5000 AND monthly_salary < 8000 THEN 1 ELSE 0 END) AS from_5k_to_8k,
                           SUM(CASE WHEN monthly_salary >= 8000 AND monthly_salary < 12000 THEN 1 ELSE 0 END) AS from_8k_to_12k,
                           SUM(CASE WHEN monthly_salary >= 12000 AND monthly_salary < 20000 THEN 1 ELSE 0 END) AS from_12k_to_20k,
                           SUM(CASE WHEN monthly_salary >= 20000 THEN 1 ELSE 0 END) AS above_20k
                    FROM classified GROUP BY industry_category
                )
                SELECT c.industry_category, COALESCE(a.job_count, 0) AS job_count,
                       COALESCE(a.salary_sample_count, 0) AS salary_sample_count, a.average_salary,
                       COALESCE(a.below_5k, 0) AS below_5k, COALESCE(a.from_5k_to_8k, 0) AS from_5k_to_8k,
                       COALESCE(a.from_8k_to_12k, 0) AS from_8k_to_12k,
                       COALESCE(a.from_12k_to_20k, 0) AS from_12k_to_20k, COALESCE(a.above_20k, 0) AS above_20k
                FROM category_order c LEFT JOIN aggregated a ON a.industry_category = c.industry_category
                ORDER BY c.sort_order
                """.formatted(StringUtils.hasText(city) ? "AND j.city = :city" : "", classifier, categories);

        List<IndustrySalaryMetric> industries = jdbc.query(salarySql, parameters, (rs, rowNum) -> new IndustrySalaryMetric(
                rs.getString("industry_category"), rs.getLong("job_count"), rs.getLong("salary_sample_count"),
                nullableDouble(rs.getObject("average_salary")), rs.getLong("below_5k"),
                rs.getLong("from_5k_to_8k"), rs.getLong("from_8k_to_12k"),
                rs.getLong("from_12k_to_20k"), rs.getLong("above_20k")));

        return new IndustrySalaryResponse(LocalDate.of(2026, 7, 11), city, industries,
                "按岗位名称与岗位描述关键词依次匹配；薪资采用月薪上下限中位值，未命中规则的岗位归入其他。");
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

    static Map<String, String> industryRules() {
        LinkedHashMap<String, String> rules = new LinkedHashMap<>();
        rules.put("金融", "金融|银行|证券|保险|基金|信贷|投资|理财|风控|会计|审计|财务|税务");
        rules.put("商贸与消费", "电商|电子商务|零售|商贸|贸易|销售|营销|品牌|采购|供应链|消费品|服装|美妆|珠宝");
        rules.put("医药生物", "医药|医疗|生物|制药|药品|临床|护理|医生|医院|医疗器械");
        rules.put("科技", "互联网|软件|数据|算法|人工智能|(^|[^a-z])ai([^a-z]|$)|开发工程师|程序员|运维|测试工程师|信息技术|网络安全|云计算|芯片|半导体|电子|通信");
        rules.put("制造业", "制造|机械|机电|自动化|汽车|新能源|工业|工厂|生产|材料|化工|设备|电气");
        rules.put("农业与食品", "农业|农学|种植|养殖|畜牧|水产|食品|粮食|饮料|餐饮");
        rules.put("服务业", "服务|酒店|旅游|物流|运输|客服|行政|人力资源|物业|家政|美容|法律");
        rules.put("建筑与房地产", "建筑|房地产|地产|土木|工程造价|施工|装饰|装修|园林|测绘");
        rules.put("教育", "教育|教师|老师|教研|培训|课程|学校|高校|讲师");
        return Collections.unmodifiableMap(rules);
    }

    static String classifyIndustry(String jobName, String jobDescription) {
        String text = ((jobName == null ? "" : jobName) + " "
                + (jobDescription == null ? "" : jobDescription)).toLowerCase();
        return INDUSTRY_RULES.entrySet().stream()
                .filter(rule -> Pattern.compile(rule.getValue()).matcher(text).find())
                .map(Map.Entry::getKey).findFirst().orElse("其他");
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
