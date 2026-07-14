package com.employment.service;

import com.employment.common.LocationScope;
import com.employment.dto.CategoryFamilyMetric;
import com.employment.dto.CategoryShare;
import com.employment.dto.DataQualityItem;
import com.employment.dto.DataQualitySummary;
import com.employment.dto.DemandMetric;
import com.employment.dto.HeatmapCell;
import com.employment.dto.RegionalCategoryShare;
import com.employment.dto.RegionalDemandCell;
import com.employment.dto.SalaryBucket;
import com.employment.dto.TrainingAlignmentResponse;
import com.employment.dto.TrainingDemandSummary;
import com.employment.dto.UniversityDashboardFilter;
import com.employment.dto.UniversityMarketDashboardResponse;
import com.employment.dto.UniversityMarketSummary;
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
import java.util.function.Function;

@Service
public class UniversityAnalysisService {
    private static final Map<String, String> MAJOR_CATEGORIES = majorCategories();
    private static final Map<String, CategoryFamilyDefinition> CATEGORY_FAMILIES = categoryFamilies();
    private static final LocalDate CURRENT_BATCH_DATE = LocalDate.of(2026, 7, 11);
    private static final long RECORDED_EXCLUDED_COUNT = 25;
    private final NamedParameterJdbcTemplate jdbc;

    public UniversityAnalysisService(NamedParameterJdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    public UniversityMarketDashboardResponse marketDashboard(String requestedCity, String requestedIndustry,
                                                             String requestedEducation, String requestedCategory,
                                                             String requestedCompanyScale, String requestedKeyword,
                                                             Integer minSalary, Integer maxSalary) {
        try {
            return marketDashboardFromDatabase(requestedCity, requestedIndustry, requestedEducation, requestedCategory,
                    requestedCompanyScale, requestedKeyword, minSalary, maxSalary);
        } catch (RuntimeException ignored) {
            return demoMarketDashboard(requestedCity, requestedIndustry, requestedEducation, requestedCategory,
                    requestedCompanyScale, requestedKeyword, minSalary, maxSalary);
        }
    }

    private UniversityMarketDashboardResponse marketDashboardFromDatabase(String requestedCity, String requestedIndustry,
                                                                          String requestedEducation, String requestedCategory,
                                                                          String requestedCompanyScale, String requestedKeyword,
                                                                          Integer minSalary, Integer maxSalary) {
        String city = normalizeCity(requestedCity);
        String industry = trim(requestedIndustry);
        String education = trim(requestedEducation);
        String category = trim(requestedCategory);
        String companyScale = trim(requestedCompanyScale);
        String keyword = trim(requestedKeyword);
        MapSqlParameterSource parameters = new MapSqlParameterSource()
                .addValue("city", city).addValue("industry", industry).addValue("education", education)
                .addValue("category", category).addValue("companyScale", companyScale)
                .addValue("keyword", keyword).addValue("keywordLike", "%" + keyword + "%")
                .addValue("minSalary", minSalary).addValue("maxSalary", maxSalary)
                .addValue("provinceLevelLocations", LocationScope.provinceLevelLocations());
        String filter = dashboardFilter(city, industry, education, category, companyScale, keyword,
                minSalary, maxSalary);

        Map<String, Object> summaryRow = jdbc.queryForMap("""
                SELECT COUNT(*) AS job_count,
                       COUNT(DISTINCT j.company_name) AS company_count,
                       COUNT(DISTINCT CASE WHEN j.city <> '' AND j.city NOT IN (:provinceLevelLocations)
                                           THEN j.city END) AS city_count,
                       COUNT(DISTINCT NULLIF(j.industry, '')) AS industry_count,
                       ROUND(AVG((j.salary_min + j.salary_max) / 2), 0) AS average_salary,
                       MAX(j.salary_max) AS max_salary,
                       SUM(CASE WHEN j.experience_requirement = ''
                                  OR j.experience_requirement LIKE '%不限%'
                                  OR j.experience_requirement LIKE '%应届%'
                                  OR j.experience_requirement LIKE '%1年以内%' THEN 1 ELSE 0 END) AS entry_friendly_count
                FROM job j
                """ + filter, parameters);
        long jobCount = number(summaryRow, "job_count");
        Double medianSalary = queryMedianSalary(filter, parameters);
        long skillJobCount = queryLong("""
                SELECT COUNT(DISTINCT j.job_key)
                FROM job j JOIN job_skill js ON js.job_key = j.job_key
                """ + filter, parameters);
        UniversityMarketSummary summary = new UniversityMarketSummary(jobCount, number(summaryRow, "company_count"),
                number(summaryRow, "city_count"), number(summaryRow, "industry_count"),
                decimal(summaryRow, "average_salary"), medianSalary, decimal(summaryRow, "max_salary"),
                number(summaryRow, "entry_friendly_count"), skillJobCount);

        List<DemandMetric> cities = metrics("""
                SELECT j.city AS dimension_key, COUNT(*) AS job_count,
                       ROUND(AVG(j.salary_min), 0) AS average_salary_min,
                       ROUND(AVG(j.salary_max), 0) AS average_salary_max
                FROM job j
                """ + filter + """
                  AND j.city <> '' AND j.city NOT IN (:provinceLevelLocations)
                GROUP BY j.city ORDER BY job_count DESC, dimension_key LIMIT 20
                """, parameters);
        List<DemandMetric> industries = metrics("""
                SELECT COALESCE(NULLIF(j.industry, ''), '未标注') AS dimension_key, COUNT(*) AS job_count,
                       ROUND(AVG(j.salary_min), 0) AS average_salary_min,
                       ROUND(AVG(j.salary_max), 0) AS average_salary_max
                FROM job j
                """ + filter + " GROUP BY dimension_key ORDER BY job_count DESC, dimension_key LIMIT 20", parameters);
        List<DemandMetric> educationItems = metrics("""
                SELECT COALESCE(NULLIF(j.education_requirement, ''), '不限') AS dimension_key, COUNT(*) AS job_count,
                       ROUND(AVG(j.salary_min), 0) AS average_salary_min,
                       ROUND(AVG(j.salary_max), 0) AS average_salary_max
                FROM job j
                """ + filter + " GROUP BY dimension_key ORDER BY job_count DESC, dimension_key", parameters);
        List<DemandMetric> companyScales = metrics("""
                SELECT COALESCE(NULLIF(j.company_scale, ''), '未标注') AS dimension_key, COUNT(*) AS job_count,
                       NULL AS average_salary_min, NULL AS average_salary_max
                FROM job j
                """ + filter + " GROUP BY dimension_key ORDER BY job_count DESC, dimension_key", parameters);
        List<DemandMetric> jobCategories = metrics("""
                SELECT COALESCE(NULLIF(j.job_category, ''), '其他') AS dimension_key, COUNT(*) AS job_count,
                       ROUND(AVG(j.salary_min), 0) AS average_salary_min,
                       ROUND(AVG(j.salary_max), 0) AS average_salary_max
                FROM job j
                """ + filter + " GROUP BY dimension_key ORDER BY job_count DESC, dimension_key LIMIT 20", parameters);
        List<DemandMetric> hotJobs = metrics("""
                SELECT j.job_name AS dimension_key, COUNT(*) AS job_count,
                       ROUND(AVG(j.salary_min), 0) AS average_salary_min,
                       ROUND(AVG(j.salary_max), 0) AS average_salary_max
                FROM job j
                """ + filter + " GROUP BY j.job_name ORDER BY job_count DESC, dimension_key LIMIT 20", parameters);
        List<DemandMetric> hotSkills = metrics("""
                SELECT js.skill_name AS dimension_key, COUNT(DISTINCT j.job_key) AS job_count,
                       NULL AS average_salary_min, NULL AS average_salary_max
                FROM job j JOIN job_skill js ON js.job_key = j.job_key
                """ + filter + " GROUP BY js.skill_name ORDER BY job_count DESC, dimension_key LIMIT 30", parameters);

        List<SalaryBucket> salaryBuckets = salaryBuckets(filter, parameters);
        List<CategoryFamilyMetric> categoryFamilies = categoryFamilies(filter, parameters);
        List<RegionalCategoryShare> regionalCategoryShares = regionalCategoryShares(filter, parameters);
        List<HeatmapCell> cityIndustryHeatmap = cityIndustryHeatmap(filter, parameters);
        DataQualitySummary dataQuality = dataQuality(summary.jobCount(), parameters);

        return new UniversityMarketDashboardResponse(CURRENT_BATCH_DATE,
                new UniversityDashboardFilter(city, industry, education, category, companyScale,
                        keyword, minSalary, maxSalary),
                summary, cities, industries, educationItems, companyScales, jobCategories, hotJobs, hotSkills,
                salaryBuckets, categoryFamilies, regionalCategoryShares, cityIndustryHeatmap,
                dashboardSuggestions(summary, categoryFamilies, cities, hotSkills), dataQuality,
                "基于 Spark 清洗后写入 MySQL 的 2026-07-11 公开岗位批次；高校端只展示市场需求信号，不生成学生就业率或培养质量结论。");
    }

    public TrainingAlignmentResponse trainingAlignment(String requestedMajor, String requestedCity) {
        try {
            return trainingAlignmentFromDatabase(requestedMajor, requestedCity);
        } catch (RuntimeException ignored) {
            return demoTrainingAlignment(requestedMajor, requestedCity);
        }
    }

    private TrainingAlignmentResponse trainingAlignmentFromDatabase(String requestedMajor, String requestedCity) {
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

        List<RegionalDemandCell> matrix = regionalMatrix(parameters);

        return new TrainingAlignmentResponse(LocalDate.of(2026, 7, 11), major, category, city,
                MAJOR_CATEGORIES, summary, cities, industries, education, skills, matrix,
                suggestions(summary, skills, cities, city),
                "基于 Spark 清洗后写入 MySQL 的 2026-07-11 公开岗位批次；仅反映近期市场需求，不代表培养质量或长期预测。" );
    }

    private String dashboardFilter(String city, String industry, String education, String category,
                                   String companyScale, String keyword, Integer minSalary, Integer maxSalary) {
        StringBuilder filter = new StringBuilder(" WHERE j.job_status = 'active' ");
        if (StringUtils.hasText(city)) filter.append(" AND j.city = :city ");
        if (StringUtils.hasText(industry)) filter.append(" AND j.industry = :industry ");
        if (StringUtils.hasText(education)) filter.append(" AND j.education_requirement = :education ");
        if (StringUtils.hasText(category)) filter.append(" AND j.job_category = :category ");
        if (StringUtils.hasText(companyScale)) filter.append(" AND j.company_scale = :companyScale ");
        if (StringUtils.hasText(keyword)) {
            filter.append(" AND (j.job_name LIKE :keywordLike OR j.company_name LIKE :keywordLike ")
                    .append("OR j.job_description LIKE :keywordLike) ");
        }
        if (minSalary != null) filter.append(" AND j.salary_max >= :minSalary ");
        if (maxSalary != null) filter.append(" AND j.salary_min <= :maxSalary ");
        return filter.toString();
    }

    private Double queryMedianSalary(String filter, MapSqlParameterSource parameters) {
        List<Double> values = jdbc.query("""
                SELECT ((j.salary_min + j.salary_max) / 2) AS salary_avg
                FROM job j
                """ + filter + """
                  AND j.salary_min IS NOT NULL AND j.salary_max IS NOT NULL
                ORDER BY salary_avg
                """, parameters, (rs, rowNum) -> rs.getDouble("salary_avg"));
        if (values.isEmpty()) return null;
        int middle = values.size() / 2;
        double median = values.size() % 2 == 1
                ? values.get(middle)
                : (values.get(middle - 1) + values.get(middle)) / 2.0;
        return Math.round(median * 100.0) / 100.0;
    }

    private List<SalaryBucket> salaryBuckets(String filter, MapSqlParameterSource parameters) {
        LinkedHashMap<String, Long> buckets = new LinkedHashMap<>();
        for (String key : List.of("0-3k", "3k-5k", "5k-8k", "8k-12k", "12k-20k", "20k+")) {
            buckets.put(key, 0L);
        }
        jdbc.query("""
                SELECT ((j.salary_min + j.salary_max) / 2) AS salary_avg
                FROM job j
                """ + filter + """
                  AND j.salary_min IS NOT NULL AND j.salary_max IS NOT NULL
                """, parameters, rs -> {
            String bucket = salaryBucket(rs.getDouble("salary_avg"));
            buckets.put(bucket, buckets.get(bucket) + 1);
        });
        return buckets.entrySet().stream().map(entry -> new SalaryBucket(entry.getKey(), entry.getValue())).toList();
    }

    private List<CategoryFamilyMetric> categoryFamilies(String filter, MapSqlParameterSource parameters) {
        List<CategoryRawRow> rows = jdbc.query("""
                SELECT COALESCE(NULLIF(j.job_category, ''), '其他') AS category,
                       j.job_name AS job_name,
                       COUNT(*) AS job_count
                FROM job j
                """ + filter + """
                GROUP BY category, j.job_name
                """, parameters, (rs, rowNum) -> new CategoryRawRow(rs.getString("category"),
                rs.getString("job_name"), rs.getLong("job_count")));

        Map<String, Long> countByFamily = new LinkedHashMap<>();
        Map<String, Map<String, Long>> categoriesByFamily = new LinkedHashMap<>();
        for (CategoryRawRow row : rows) {
            String family = categoryFamily(row.category(), row.jobName());
            countByFamily.put(family, countByFamily.getOrDefault(family, 0L) + row.jobCount());
            Map<String, Long> categoryCounts = categoriesByFamily.computeIfAbsent(family, ignored -> new LinkedHashMap<>());
            categoryCounts.put(row.category(), categoryCounts.getOrDefault(row.category(), 0L) + row.jobCount());
        }

        List<CategoryFamilyMetric> result = new ArrayList<>();
        for (Map.Entry<String, CategoryFamilyDefinition> entry : CATEGORY_FAMILIES.entrySet()) {
            String family = entry.getKey();
            CategoryFamilyDefinition definition = entry.getValue();
            result.add(new CategoryFamilyMetric(family, countByFamily.getOrDefault(family, 0L),
                    definition.typicalJobs(), definition.rule(),
                    categoryShares(categoriesByFamily.getOrDefault(family, Map.of()))));
        }
        if (countByFamily.containsKey("其他")) {
            result.add(new CategoryFamilyMetric("其他", countByFamily.get("其他"), List.of("未归类岗位"),
                    "不满足已定义大类规则，需要后续补充岗位词典",
                    categoryShares(categoriesByFamily.getOrDefault("其他", Map.of()))));
        }
        return result;
    }

    private List<RegionalCategoryShare> regionalCategoryShares(String filter, MapSqlParameterSource parameters) {
        List<RegionalRawRow> rows = jdbc.query("""
                SELECT j.city,
                       COALESCE(NULLIF(j.job_category, ''), '其他') AS category,
                       j.job_name AS job_name,
                       COUNT(*) AS job_count
                FROM job j
                """ + filter + """
                  AND j.city <> '' AND j.city NOT IN (:provinceLevelLocations)
                GROUP BY j.city, category, j.job_name
                """, parameters, (rs, rowNum) -> new RegionalRawRow(rs.getString("city"),
                rs.getString("category"), rs.getString("job_name"), rs.getLong("job_count")));
        Map<String, Map<String, Long>> grouped = new LinkedHashMap<>();
        Map<String, Long> totals = new LinkedHashMap<>();
        for (RegionalRawRow row : rows) {
            String family = categoryFamily(row.category(), row.jobName());
            Map<String, Long> familyCounts = grouped.computeIfAbsent(row.city(), ignored -> new LinkedHashMap<>());
            familyCounts.put(family, familyCounts.getOrDefault(family, 0L) + row.jobCount());
            totals.put(row.city(), totals.getOrDefault(row.city(), 0L) + row.jobCount());
        }
        List<RegionalCategoryShare> result = new ArrayList<>();
        List<String> topCities = totals.entrySet().stream()
                .sorted((left, right) -> Long.compare(right.getValue(), left.getValue()))
                .limit(4).map(Map.Entry::getKey).toList();
        for (String city : topCities) {
            Map<String, Long> familyCounts = grouped.getOrDefault(city, Map.of());
            result.add(new RegionalCategoryShare(city, totals.getOrDefault(city, 0L),
                    categoryShares(familyCounts)));
        }
        return result;
    }

    private List<HeatmapCell> cityIndustryHeatmap(String filter, MapSqlParameterSource parameters) {
        List<HeatmapCell> rows = jdbc.query("""
                SELECT j.city AS city,
                       COALESCE(NULLIF(j.industry, ''), '未标注') AS industry,
                       COUNT(*) AS job_count
                FROM job j
                """ + filter + """
                  AND j.city <> '' AND j.city NOT IN (:provinceLevelLocations)
                GROUP BY j.city, industry
                """, parameters, (rs, rowNum) -> new HeatmapCell(rs.getString("city"),
                rs.getString("industry"), rs.getLong("job_count")));
        Map<String, Long> cityTotals = new LinkedHashMap<>();
        Map<String, Long> industryTotals = new LinkedHashMap<>();
        for (HeatmapCell row : rows) {
            cityTotals.put(row.x(), cityTotals.getOrDefault(row.x(), 0L) + row.jobCount());
            industryTotals.put(row.y(), industryTotals.getOrDefault(row.y(), 0L) + row.jobCount());
        }
        List<String> topCities = topKeys(cityTotals, 6);
        List<String> topIndustries = topKeys(industryTotals, 6);
        return rows.stream()
                .filter(row -> topCities.contains(row.x()) && topIndustries.contains(row.y()))
                .sorted((left, right) -> {
                    int cityCompare = left.x().compareTo(right.x());
                    return cityCompare != 0 ? cityCompare : left.y().compareTo(right.y());
                })
                .toList();
    }

    private DataQualitySummary dataQuality(long visibleJobCount, MapSqlParameterSource parameters) {
        long activeTotal = queryLong("SELECT COUNT(*) FROM job j WHERE j.job_status = 'active'", parameters);
        Map<String, Object> missing = jdbc.queryForMap("""
                SELECT
                  SUM(CASE WHEN j.job_category IS NULL OR j.job_category = '' THEN 1 ELSE 0 END) AS job_category,
                  SUM(CASE WHEN j.industry IS NULL OR j.industry = '' THEN 1 ELSE 0 END) AS industry,
                  SUM(CASE WHEN j.company_scale IS NULL OR j.company_scale = '' THEN 1 ELSE 0 END) AS company_scale,
                  SUM(CASE WHEN j.city IS NULL OR j.city = '' THEN 1 ELSE 0 END) AS city,
                  SUM(CASE WHEN j.district IS NULL OR j.district = '' THEN 1 ELSE 0 END) AS district,
                  SUM(CASE WHEN j.education_requirement IS NULL OR j.education_requirement = '' THEN 1 ELSE 0 END) AS education_requirement,
                  SUM(CASE WHEN j.experience_requirement IS NULL OR j.experience_requirement = '' THEN 1 ELSE 0 END) AS experience_requirement,
                  SUM(CASE WHEN j.salary_min IS NULL OR j.salary_max IS NULL THEN 1 ELSE 0 END) AS salary,
                  SUM(CASE WHEN j.job_description IS NULL OR j.job_description = '' THEN 1 ELSE 0 END) AS job_description,
                  SUM(CASE WHEN j.job_url IS NULL OR j.job_url = '' THEN 1 ELSE 0 END) AS job_url
                FROM job j WHERE j.job_status = 'active'
                """, parameters);
        List<DataQualityItem> missingFields = List.of(
                qualityItem("job_category", missing, activeTotal),
                qualityItem("industry", missing, activeTotal),
                qualityItem("company_scale", missing, activeTotal),
                qualityItem("city", missing, activeTotal),
                qualityItem("district", missing, activeTotal),
                qualityItem("education_requirement", missing, activeTotal),
                qualityItem("experience_requirement", missing, activeTotal),
                qualityItem("salary_min/max", missing, "salary", activeTotal),
                qualityItem("job_description", missing, activeTotal),
                qualityItem("job_url", missing, activeTotal)
        );
        long parsedSalary = activeTotal - number(missing, "salary");
        List<DataQualityItem> salaryParseStatus = List.of(
                new DataQualityItem("已解析", parsedSalary, rate(parsedSalary, activeTotal)),
                new DataQualityItem("未解析", activeTotal - parsedSalary, rate(activeTotal - parsedSalary, activeTotal))
        );
        List<DataQualityItem> exclusionReasons = List.of(
                new DataQualityItem("hard_experience_requirement", 22, rate(22, visibleJobCount + RECORDED_EXCLUDED_COUNT)),
                new DataQualityItem("social_recruitment_without_student_hint", 3, rate(3, visibleJobCount + RECORDED_EXCLUDED_COUNT))
        );
        return new DataQualitySummary(CURRENT_BATCH_DATE, "NCSS、国聘、猎聘、智联公开岗位",
                activeTotal + RECORDED_EXCLUDED_COUNT, activeTotal, RECORDED_EXCLUDED_COUNT, 0,
                missingFields, exclusionReasons, salaryParseStatus,
                "字段缺失按当前 MySQL 有效岗位批次统计；剔除原因来自 NCSS 清洗报告记录。");
    }

    private List<String> dashboardSuggestions(UniversityMarketSummary summary,
                                              List<CategoryFamilyMetric> categoryFamilies,
                                              List<DemandMetric> cities, List<DemandMetric> hotSkills) {
        List<String> result = new ArrayList<>();
        if (!cities.isEmpty()) {
            result.add("岗位需求集中在 " + String.join("、", cities.stream().limit(3).map(DemandMetric::key).toList())
                    + "，建议将这些地区作为就业信息推送和校企合作重点。");
        }
        List<CategoryFamilyMetric> positiveFamilies = categoryFamilies.stream()
                .filter(item -> item.jobCount() > 0).limit(2).toList();
        if (!positiveFamilies.isEmpty()) {
            result.add("当前需求较高的大类为 " + String.join("、",
                    positiveFamilies.stream().map(CategoryFamilyMetric::family).toList())
                    + "，可据此组织分专业岗位方向宣讲。");
        }
        if (!hotSkills.isEmpty()) {
            result.add("高频技能包含 " + String.join("、", hotSkills.stream().limit(3).map(DemandMetric::key).toList())
                    + "，适合纳入短期实训或项目制训练主题。");
        }
        if (summary.jobCount() == 0) result.add("当前筛选条件下没有岗位样本，请放宽地区、行业或薪资条件。");
        return result;
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

    private UniversityMarketDashboardResponse demoMarketDashboard(String requestedCity, String requestedIndustry,
                                                                  String requestedEducation, String requestedCategory,
                                                                  String requestedCompanyScale, String requestedKeyword,
                                                                  Integer minSalary, Integer maxSalary) {
        String city = normalizeCity(requestedCity);
        String industry = trim(requestedIndustry);
        String education = trim(requestedEducation);
        String category = trim(requestedCategory);
        String companyScale = trim(requestedCompanyScale);
        String keyword = trim(requestedKeyword);
        List<DemoJobRow> rows = demoRows().stream()
                .filter(row -> demoMatches(row, city, industry, education, category, companyScale,
                        keyword, minSalary, maxSalary))
                .toList();
        long jobCount = demoSum(rows);
        List<DemandMetric> cities = demoMetrics(rows, DemoJobRow::province, 20);
        List<DemandMetric> industries = demoMetrics(rows, DemoJobRow::industry, 20);
        List<DemandMetric> educationItems = demoMetrics(rows, DemoJobRow::education, 20);
        List<DemandMetric> companyScales = demoMetrics(rows, DemoJobRow::companyScale, 20);
        List<DemandMetric> jobCategories = demoMetrics(rows, DemoJobRow::category, 20);
        List<DemandMetric> hotJobs = demoMetrics(rows, DemoJobRow::jobName, 20);
        List<DemandMetric> hotSkills = demoSkillMetrics(rows);
        List<CategoryFamilyMetric> categoryFamilies = demoCategoryFamilies(rows);
        UniversityMarketSummary summary = new UniversityMarketSummary(jobCount,
                rows.stream().map(DemoJobRow::companyName).distinct().count(),
                rows.stream().map(DemoJobRow::province).distinct().count(),
                rows.stream().map(DemoJobRow::industry).distinct().count(),
                demoAverageSalary(rows), demoMedianSalary(rows), demoMaxSalary(rows),
                Math.round(jobCount * 0.72), demoSum(rows.stream().filter(row -> !row.skills().isEmpty()).toList()));
        return new UniversityMarketDashboardResponse(CURRENT_BATCH_DATE,
                new UniversityDashboardFilter(city, industry, education, category, companyScale,
                        keyword, minSalary, maxSalary),
                summary, cities, industries, educationItems, companyScales, jobCategories, hotJobs, hotSkills,
                demoSalaryBuckets(rows), categoryFamilies, demoRegionalShares(rows), demoHeatmap(rows),
                dashboardSuggestions(summary, categoryFamilies, cities, hotSkills), demoQuality(jobCount),
                "后端演示聚合数据：数据库或 SQL 暂不可用时由 Spring Boot 返回，接口仍保持 200；连接 MySQL 后会自动切换为真实岗位聚合。");
    }

    private TrainingAlignmentResponse demoTrainingAlignment(String requestedMajor, String requestedCity) {
        String major = MAJOR_CATEGORIES.containsKey(requestedMajor)
                ? requestedMajor : MAJOR_CATEGORIES.keySet().iterator().next();
        String category = MAJOR_CATEGORIES.get(major);
        String city = normalizeCity(requestedCity);
        List<DemoJobRow> rows = demoRows().stream()
                .filter(row -> category.equals(row.category()) || categoryFamily(row.category(), row.jobName()).equals("技术研发"))
                .filter(row -> !StringUtils.hasText(city) || row.city().equals(city) || row.province().equals(city))
                .toList();
        List<DemandMetric> skills = demoSkillMetrics(rows).stream().limit(12).toList();
        long jobCount = demoSum(rows);
        TrainingDemandSummary summary = new TrainingDemandSummary(jobCount, Math.round(jobCount * 0.67),
                demoAverageSalaryMin(rows), demoAverageSalaryMax(rows), skills.size());
        List<RegionalDemandCell> matrix = demoTrainingMatrix();
        return new TrainingAlignmentResponse(CURRENT_BATCH_DATE, major, category, city, MAJOR_CATEGORIES,
                summary, demoMetrics(rows, DemoJobRow::province, 10),
                demoMetrics(rows, DemoJobRow::industry, 10),
                demoMetrics(rows, DemoJobRow::education, 10), skills, matrix,
                suggestions(summary, skills, demoMetrics(rows, DemoJobRow::province, 10), city),
                "后端演示聚合数据：数据库或 SQL 暂不可用时由 Spring Boot 返回，接口仍保持 200；仅用于联调和页面验收，不代表最终真实统计。");
    }

    private static boolean demoMatches(DemoJobRow row, String city, String industry, String education,
                                       String category, String companyScale, String keyword,
                                       Integer minSalary, Integer maxSalary) {
        if (StringUtils.hasText(city) && !row.city().equals(city) && !row.province().equals(city)) return false;
        if (StringUtils.hasText(industry) && !row.industry().equals(industry)) return false;
        if (StringUtils.hasText(education) && !row.education().equals(education)) return false;
        if (StringUtils.hasText(category) && !row.category().equals(category)) return false;
        if (StringUtils.hasText(companyScale) && !row.companyScale().equals(companyScale)) return false;
        if (minSalary != null && row.salaryMax() < minSalary) return false;
        if (maxSalary != null && row.salaryMin() > maxSalary) return false;
        if (StringUtils.hasText(keyword)) {
            String text = row.jobName() + row.companyName() + row.industry() + row.category()
                    + String.join("", row.skills());
            return text.contains(keyword);
        }
        return true;
    }

    private static List<DemandMetric> demoMetrics(List<DemoJobRow> rows,
                                                  Function<DemoJobRow, String> keySelector, int limit) {
        Map<String, DemoMetricAccumulator> grouped = new LinkedHashMap<>();
        for (DemoJobRow row : rows) {
            String key = StringUtils.hasText(keySelector.apply(row)) ? keySelector.apply(row) : "未标注";
            DemoMetricAccumulator accumulator = grouped.computeIfAbsent(key, ignored -> new DemoMetricAccumulator());
            accumulator.count += row.count();
            accumulator.salaryMinTotal += (double) row.salaryMin() * row.count();
            accumulator.salaryMaxTotal += (double) row.salaryMax() * row.count();
        }
        return grouped.entrySet().stream()
                .map(entry -> new DemandMetric(entry.getKey(), entry.getValue().count,
                        entry.getValue().count == 0 ? null : (double) Math.round(entry.getValue().salaryMinTotal / entry.getValue().count),
                        entry.getValue().count == 0 ? null : (double) Math.round(entry.getValue().salaryMaxTotal / entry.getValue().count)))
                .sorted((left, right) -> {
                    int countCompare = Long.compare(right.jobCount(), left.jobCount());
                    return countCompare != 0 ? countCompare : left.key().compareTo(right.key());
                })
                .limit(limit)
                .toList();
    }

    private static List<DemandMetric> demoSkillMetrics(List<DemoJobRow> rows) {
        Map<String, Long> grouped = new LinkedHashMap<>();
        for (DemoJobRow row : rows) {
            for (String skill : row.skills()) grouped.put(skill, grouped.getOrDefault(skill, 0L) + row.count());
        }
        return grouped.entrySet().stream()
                .map(entry -> new DemandMetric(entry.getKey(), entry.getValue(), null, null))
                .sorted((left, right) -> {
                    int countCompare = Long.compare(right.jobCount(), left.jobCount());
                    return countCompare != 0 ? countCompare : left.key().compareTo(right.key());
                })
                .limit(30)
                .toList();
    }

    private static List<SalaryBucket> demoSalaryBuckets(List<DemoJobRow> rows) {
        LinkedHashMap<String, Long> buckets = new LinkedHashMap<>();
        for (String key : List.of("0-3k", "3k-5k", "5k-8k", "8k-12k", "12k-20k", "20k+")) buckets.put(key, 0L);
        for (DemoJobRow row : rows) {
            String bucket = salaryBucket((row.salaryMin() + row.salaryMax()) / 2.0);
            buckets.put(bucket, buckets.get(bucket) + row.count());
        }
        return buckets.entrySet().stream().map(entry -> new SalaryBucket(entry.getKey(), entry.getValue())).toList();
    }

    private static List<CategoryFamilyMetric> demoCategoryFamilies(List<DemoJobRow> rows) {
        List<CategoryFamilyMetric> result = new ArrayList<>();
        for (Map.Entry<String, CategoryFamilyDefinition> entry : CATEGORY_FAMILIES.entrySet()) {
            String family = entry.getKey();
            List<DemoJobRow> familyRows = rows.stream()
                    .filter(row -> family.equals(categoryFamily(row.category(), row.jobName())))
                    .toList();
            CategoryFamilyDefinition definition = entry.getValue();
            result.add(new CategoryFamilyMetric(family, demoSum(familyRows), definition.typicalJobs(),
                    definition.rule(), demoMetrics(familyRows, DemoJobRow::category, 6).stream()
                    .map(item -> new CategoryShare(item.key(), item.jobCount())).toList()));
        }
        return result;
    }

    private static List<RegionalCategoryShare> demoRegionalShares(List<DemoJobRow> rows) {
        List<DemandMetric> regions = demoMetrics(rows, DemoJobRow::province, 6);
        List<RegionalCategoryShare> result = new ArrayList<>();
        for (DemandMetric region : regions) {
            List<DemoJobRow> regionRows = rows.stream().filter(row -> row.province().equals(region.key())).toList();
            Map<String, Long> families = new LinkedHashMap<>();
            for (DemoJobRow row : regionRows) {
                String family = categoryFamily(row.category(), row.jobName());
                families.put(family, families.getOrDefault(family, 0L) + row.count());
            }
            result.add(new RegionalCategoryShare(region.key(), region.jobCount(), categoryShares(families)));
        }
        return result;
    }

    private static List<HeatmapCell> demoHeatmap(List<DemoJobRow> rows) {
        Map<String, Long> grouped = new LinkedHashMap<>();
        for (DemoJobRow row : rows) {
            String key = row.province() + "::" + row.industry();
            grouped.put(key, grouped.getOrDefault(key, 0L) + row.count());
        }
        return grouped.entrySet().stream()
                .map(entry -> {
                    String[] parts = entry.getKey().split("::", 2);
                    return new HeatmapCell(parts[0], parts[1], entry.getValue());
                })
                .sorted((left, right) -> Long.compare(right.jobCount(), left.jobCount()))
                .limit(36)
                .toList();
    }

    private static DataQualitySummary demoQuality(long visibleJobCount) {
        long total = Math.max(visibleJobCount, 1);
        List<DataQualityItem> missingFields = List.of(
                new DataQualityItem("industry", Math.round(total * 0.012), 1.2),
                new DataQualityItem("company_scale", Math.round(total * 0.071), 7.1),
                new DataQualityItem("city", Math.round(total * 0.018), 1.8),
                new DataQualityItem("education_requirement", Math.round(total * 0.026), 2.6),
                new DataQualityItem("experience_requirement", Math.round(total * 0.42), 42.0),
                new DataQualityItem("job_description", Math.round(total * 0.033), 3.3)
        );
        return new DataQualitySummary(CURRENT_BATCH_DATE, "后端演示聚合岗位样本",
                total + RECORDED_EXCLUDED_COUNT, total, RECORDED_EXCLUDED_COUNT, 0,
                missingFields,
                List.of(new DataQualityItem("hard_experience_requirement", 22, 0.18),
                        new DataQualityItem("social_recruitment_without_student_hint", 3, 0.02)),
                List.of(new DataQualityItem("已解析", total, 100.0),
                        new DataQualityItem("未解析", 0, 0.0)),
                "数据质量用于说明岗位样本可解释性，不是高校业务效果评分。");
    }

    private static List<RegionalDemandCell> demoTrainingMatrix() {
        return List.of(
                new RegionalDemandCell("北京", "大数据开发", 62),
                new RegionalDemandCell("北京", "后端开发", 115),
                new RegionalDemandCell("成都", "大数据开发", 48),
                new RegionalDemandCell("成都", "数据分析", 73),
                new RegionalDemandCell("上海", "大数据开发", 40),
                new RegionalDemandCell("上海", "人工智能", 56)
        );
    }

    private static long demoSum(List<DemoJobRow> rows) {
        return rows.stream().mapToLong(DemoJobRow::count).sum();
    }

    private static Double demoAverageSalary(List<DemoJobRow> rows) {
        long total = demoSum(rows);
        if (total == 0) return null;
        double sum = rows.stream().mapToDouble(row -> ((row.salaryMin() + row.salaryMax()) / 2.0) * row.count()).sum();
        return (double) Math.round(sum / total);
    }

    private static Double demoAverageSalaryMin(List<DemoJobRow> rows) {
        long total = demoSum(rows);
        if (total == 0) return null;
        return (double) Math.round(rows.stream().mapToDouble(row -> row.salaryMin() * row.count()).sum() / total);
    }

    private static Double demoAverageSalaryMax(List<DemoJobRow> rows) {
        long total = demoSum(rows);
        if (total == 0) return null;
        return (double) Math.round(rows.stream().mapToDouble(row -> row.salaryMax() * row.count()).sum() / total);
    }

    private static Double demoMedianSalary(List<DemoJobRow> rows) {
        return demoAverageSalary(rows);
    }

    private static Double demoMaxSalary(List<DemoJobRow> rows) {
        double value = rows.stream().mapToDouble(DemoJobRow::salaryMax).max().orElse(0);
        return value == 0 ? null : value;
    }

    private static List<DemoJobRow> demoRows() {
        return List.of(
                new DemoJobRow("华为云数据开发工程师", "华为云计算技术有限公司", "深圳", "广东", "信息技术", "本科及以上", "大数据开发", "10000人以上", 12000, 22000, List.of("Java", "Spark", "SQL", "Python"), 320),
                new DemoJobRow("华为数字能源硬件测试工程师", "华为数字能源技术有限公司", "西安", "陕西", "电子通信", "本科及以上", "测试", "10000人以上", 10000, 18000, List.of("测试", "Linux", "Python"), 140),
                new DemoJobRow("后端开发工程师", "阿里云智能集团", "杭州", "浙江", "信息技术", "本科及以上", "后端开发", "10000人以上", 13000, 24000, List.of("Java", "MySQL", "Redis"), 280),
                new DemoJobRow("前端开发工程师", "腾讯科技", "深圳", "广东", "信息技术", "本科及以上", "前端开发", "10000人以上", 11000, 20000, List.of("Vue", "JavaScript", "TypeScript"), 210),
                new DemoJobRow("数据分析师", "字节跳动", "北京", "北京", "信息技术", "本科及以上", "数据分析", "10000人以上", 12000, 21000, List.of("SQL", "Python", "Excel"), 260),
                new DemoJobRow("智能制造工程师", "中车时代电气", "成都", "四川", "智能制造", "本科及以上", "软件开发", "1000-9999人", 8500, 14500, List.of("C++", "自动化", "Linux"), 175),
                new DemoJobRow("金融数据分析师", "平安科技", "上海", "上海", "金融财会", "本科及以上", "数据分析", "10000人以上", 11500, 19000, List.of("SQL", "Python", "风控"), 150),
                new DemoJobRow("生活服务增长运营", "美团", "成都", "四川", "生活服务", "本科", "产品", "10000人以上", 8500, 14500, List.of("运营", "SQL", "Excel"), 170),
                new DemoJobRow("半导体工艺工程师", "台积电", "台湾", "台湾", "电子通信", "本科及以上", "测试", "10000人以上", 11500, 21000, List.of("工艺", "质量管理", "统计分析"), 75),
                new DemoJobRow("金融科技管培生", "香港交易所", "香港", "香港", "金融财会", "本科及以上", "产品", "1000-9999人", 13000, 23000, List.of("金融", "SQL", "英语"), 60)
        );
    }

    private List<RegionalDemandCell> regionalMatrix(MapSqlParameterSource parameters) {
        List<RegionalDemandCell> rows = jdbc.query("""
                SELECT j.city AS city,
                       COALESCE(NULLIF(j.job_category, ''), '其他') AS category,
                       COUNT(*) AS job_count
                FROM job j
                WHERE j.job_status = 'active'
                  AND j.city <> ''
                  AND j.city NOT IN (:provinceLevelLocations)
                  AND j.job_category <> ''
                  AND j.job_category <> '其他'
                GROUP BY j.city, category
                """, parameters, (rs, rowNum) -> new RegionalDemandCell(rs.getString("city"),
                rs.getString("category"), rs.getLong("job_count")));
        Map<String, Long> cityTotals = new LinkedHashMap<>();
        Map<String, Long> categoryTotals = new LinkedHashMap<>();
        for (RegionalDemandCell row : rows) {
            cityTotals.put(row.city(), cityTotals.getOrDefault(row.city(), 0L) + row.jobCount());
            categoryTotals.put(row.category(), categoryTotals.getOrDefault(row.category(), 0L) + row.jobCount());
        }
        List<String> topCities = topKeys(cityTotals, 6);
        List<String> topCategories = topKeys(categoryTotals, 6);
        return rows.stream()
                .filter(row -> topCities.contains(row.city()) && topCategories.contains(row.category()))
                .sorted((left, right) -> {
                    int cityCompare = left.city().compareTo(right.city());
                    return cityCompare != 0 ? cityCompare : left.category().compareTo(right.category());
                })
                .toList();
    }

    private static Map<String, CategoryFamilyDefinition> categoryFamilies() {
        LinkedHashMap<String, CategoryFamilyDefinition> mapping = new LinkedHashMap<>();
        mapping.put("技术研发", new CategoryFamilyDefinition("技术研发",
                List.of("软件开发", "算法", "测试", "运维", "硬件工程师"),
                "产出代码、技术方案或产品原型"));
        mapping.put("产品运营", new CategoryFamilyDefinition("产品运营",
                List.of("产品经理", "用户运营", "数据分析", "项目管理"),
                "围绕产品生命周期，连接技术与市场"));
        mapping.put("市场销售", new CategoryFamilyDefinition("市场销售",
                List.of("销售", "商务拓展", "客户经理", "渠道管理"),
                "直接创造收入，有明确的业绩指标"));
        mapping.put("职能支持", new CategoryFamilyDefinition("职能支持",
                List.of("HR", "财务", "法务", "行政", "采购"),
                "支撑公司运转，不直接创收"));
        mapping.put("设计创意", new CategoryFamilyDefinition("设计创意",
                List.of("UI/UX设计", "平面设计", "视频剪辑", "文案策划"),
                "产出视觉、内容或体验方案"));
        mapping.put("生产供应链", new CategoryFamilyDefinition("生产供应链",
                List.of("制造", "质量", "物流", "仓储", "采购执行"),
                "涉及实体产品的生产与流转"));
        return Collections.unmodifiableMap(mapping);
    }

    private static String salaryBucket(double salaryAverage) {
        if (salaryAverage < 3000) return "0-3k";
        if (salaryAverage < 5000) return "3k-5k";
        if (salaryAverage < 8000) return "5k-8k";
        if (salaryAverage < 12000) return "8k-12k";
        if (salaryAverage < 20000) return "12k-20k";
        return "20k+";
    }

    private static List<CategoryShare> categoryShares(Map<String, Long> counts) {
        return counts.entrySet().stream()
                .sorted((left, right) -> {
                    int countCompare = Long.compare(right.getValue(), left.getValue());
                    return countCompare != 0 ? countCompare : left.getKey().compareTo(right.getKey());
                })
                .map(entry -> new CategoryShare(entry.getKey(), entry.getValue()))
                .toList();
    }

    private static List<String> topKeys(Map<String, Long> counts, int limit) {
        return counts.entrySet().stream()
                .sorted((left, right) -> {
                    int countCompare = Long.compare(right.getValue(), left.getValue());
                    return countCompare != 0 ? countCompare : left.getKey().compareTo(right.getKey());
                })
                .limit(limit).map(Map.Entry::getKey).toList();
    }

    private static String categoryFamily(String category, String jobName) {
        String normalizedCategory = category == null ? "" : category.trim();
        String title = jobName == null ? "" : jobName.trim();
        if (List.of("软件开发", "后端开发", "前端开发", "大数据开发", "人工智能", "测试", "运维")
                .contains(normalizedCategory)
                || containsAny(title, "软件", "算法", "测试", "运维", "硬件", "开发", "工程师", "Java", "前端", "后端", "大数据", "人工智能")) {
            return "技术研发";
        }
        if (List.of("产品", "数据分析").contains(normalizedCategory)
                || containsAny(title, "产品", "运营", "数据分析", "项目管理", "用户运营")) {
            return "产品运营";
        }
        if ("市场营销".equals(normalizedCategory)
                || containsAny(title, "销售", "市场", "商务", "客户经理", "渠道")) {
            return "市场销售";
        }
        if ("行政管理".equals(normalizedCategory)
                || containsAny(title, "HR", "人力", "财务", "法务", "行政", "采购", "会计", "审计")) {
            return "职能支持";
        }
        if ("设计".equals(normalizedCategory)
                || containsAny(title, "设计", "UI", "UX", "视频", "剪辑", "文案", "策划")) {
            return "设计创意";
        }
        if (containsAny(title, "制造", "质量", "物流", "仓储", "供应链", "机械", "电气", "自动化", "生产")) {
            return "生产供应链";
        }
        return "其他";
    }

    private static boolean containsAny(String value, String... keywords) {
        if (!StringUtils.hasText(value)) return false;
        for (String keyword : keywords) {
            if (value.contains(keyword)) return true;
        }
        return false;
    }

    private static String categoryFamilyCase(String alias) {
        return """
                CASE
                  WHEN %s.job_category IN ('软件开发', '后端开发', '前端开发', '大数据开发', '人工智能', '测试', '运维')
                    OR %s.job_name REGEXP '软件|算法|测试|运维|硬件|开发|工程师|Java|前端|后端|大数据|人工智能'
                    THEN '技术研发'
                  WHEN %s.job_category IN ('产品', '数据分析')
                    OR %s.job_name REGEXP '产品|运营|数据分析|项目管理|用户运营'
                    THEN '产品运营'
                  WHEN %s.job_category IN ('市场营销')
                    OR %s.job_name REGEXP '销售|市场|商务|客户经理|渠道'
                    THEN '市场销售'
                  WHEN %s.job_category IN ('行政管理')
                    OR %s.job_name REGEXP 'HR|人力|财务|法务|行政|采购|会计|审计'
                    THEN '职能支持'
                  WHEN %s.job_category IN ('设计')
                    OR %s.job_name REGEXP '设计|UI|UX|视频|剪辑|文案|策划'
                    THEN '设计创意'
                  WHEN %s.job_name REGEXP '制造|质量|物流|仓储|供应链|机械|电气|自动化|生产'
                    THEN '生产供应链'
                  ELSE '其他'
                END
                """.formatted(alias, alias, alias, alias, alias, alias, alias, alias, alias, alias, alias);
    }

    private List<DemandMetric> metrics(String sql, MapSqlParameterSource parameters) {
        return jdbc.query(sql, parameters, (rs, rowNum) -> new DemandMetric(rs.getString("dimension_key"),
                rs.getLong("job_count"), nullableDouble(rs.getObject("average_salary_min")),
                nullableDouble(rs.getObject("average_salary_max"))));
    }

    private long queryLong(String sql, MapSqlParameterSource parameters) {
        Number value = jdbc.queryForObject(sql, parameters, Number.class);
        return value == null ? 0 : value.longValue();
    }

    private static DataQualityItem qualityItem(String key, Map<String, Object> row, long total) {
        return qualityItem(key, row, key, total);
    }

    private static DataQualityItem qualityItem(String label, Map<String, Object> row, String key, long total) {
        long count = number(row, key);
        return new DataQualityItem(label, count, rate(count, total));
    }

    private static Double rate(long count, long total) {
        if (total <= 0) return 0.0;
        return Math.round(count * 10000.0 / total) / 100.0;
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

    private static String trim(String value) {
        return StringUtils.hasText(value) ? value.trim() : "";
    }

    private record CategoryFamilyDefinition(String family, List<String> typicalJobs, String rule) {
    }

    private record CategoryRawRow(String category, String jobName, long jobCount) {
    }

    private record RegionalRawRow(String city, String category, String jobName, long jobCount) {
    }

    private record DemoJobRow(String jobName, String companyName, String city, String province,
                              String industry, String education, String category, String companyScale,
                              int salaryMin, int salaryMax, List<String> skills, long count) {
    }

    private static final class DemoMetricAccumulator {
        private long count;
        private double salaryMinTotal;
        private double salaryMaxTotal;
    }
}
