package com.employment.service;

import com.employment.common.LocationScope;
import com.employment.dto.CategoryFamilyMetric;
import com.employment.dto.CategoryShare;
import com.employment.dto.DataQualityItem;
import com.employment.dto.DataQualitySummary;
import com.employment.dto.DemandMetric;
import com.employment.dto.HeatmapCell;
import com.employment.dto.IndustrySalaryMetric;
import com.employment.dto.IndustrySalaryResponse;
import com.employment.dto.RegionalCategoryShare;
import com.employment.dto.SalaryBucket;
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
import java.util.regex.Pattern;

@Service
public class UniversityAnalysisService {
    private static final Map<String, CategoryFamilyDefinition> CATEGORY_FAMILIES = categoryFamilies();
    private static final Map<String, String> INDUSTRY_RULES = industryRules();
    private static final LocalDate DEMO_BATCH_DATE = LocalDate.of(2026, 7, 11);
    private static final long DEMO_EXCLUDED_COUNT = 25;
    private final NamedParameterJdbcTemplate jdbc;

    public UniversityAnalysisService(NamedParameterJdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    public UniversityMarketDashboardResponse marketDashboard(String requestedCity, String requestedIndustry,
                                                             String requestedEducation, String requestedCategory,
                                                             String requestedCompanyScale, String requestedKeyword,
                                                             Integer minSalary, Integer maxSalary) {
        return marketDashboardFromDatabase(requestedCity, requestedIndustry, requestedEducation, requestedCategory,
                requestedCompanyScale, requestedKeyword, minSalary, maxSalary);
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
        boolean provinceFilter = LocationScope.isProvince(city);
        MapSqlParameterSource parameters = new MapSqlParameterSource()
                .addValue("city", city).addValue("industry", industry).addValue("education", education)
                .addValue("category", category).addValue("companyScale", companyScale)
                .addValue("keyword", keyword).addValue("keywordLike", "%" + keyword + "%")
                .addValue("minSalary", minSalary).addValue("maxSalary", maxSalary)
                .addValue("provinceCities", LocationScope.citiesForProvince(city))
                .addValue("provinceLevelLocations", LocationScope.provinceLevelLocations());
        String filter = dashboardFilter(city, industry, education, category, companyScale, keyword,
                minSalary, maxSalary, provinceFilter);

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
        List<DemandMetric> provinceDemand = provinceDemand(filter, parameters);
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
        LocalDate batchDate = currentBatchDate();
        DataQualitySummary dataQuality = dataQuality(batchDate, parameters);

        return new UniversityMarketDashboardResponse(batchDate,
                new UniversityDashboardFilter(city, industry, education, category, companyScale,
                        keyword, minSalary, maxSalary),
                summary, provinceDemand, cities, industries, educationItems, companyScales, jobCategories, hotJobs, hotSkills,
                salaryBuckets, categoryFamilies, regionalCategoryShares, cityIndustryHeatmap,
                dashboardSuggestions(summary, categoryFamilies, cities, hotSkills), dataQuality,
                "基于 Spark 清洗后写入 MySQL 的 " + batchDate
                        + " 公开岗位批次；高校端只展示市场需求信号，不生成学生就业率或培养质量结论。");
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

        List<String> orderedCategories = new ArrayList<>(INDUSTRY_RULES.keySet());
        String categories = orderedCategories.stream()
                .map(category -> "SELECT '" + category + "' AS industry_category, "
                        + (orderedCategories.indexOf(category) + 1) + " AS sort_order")
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

        return new IndustrySalaryResponse(currentBatchDate(), city, industries,
                "按岗位名称与岗位描述关键词依次匹配；薪资采用月薪上下限中位值，未命中规则的岗位归入其他。");
    }

    private String dashboardFilter(String city, String industry, String education, String category,
                                   String companyScale, String keyword, Integer minSalary, Integer maxSalary,
                                   boolean provinceFilter) {
        StringBuilder filter = new StringBuilder(" WHERE j.job_status = 'active' ");
        if (StringUtils.hasText(city)) {
            filter.append(provinceFilter ? " AND j.city IN (:provinceCities) " : " AND j.city = :city ");
        }
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

    private List<DemandMetric> provinceDemand(String filter, MapSqlParameterSource parameters) {
        List<DemandMetric> cities = metrics("""
                SELECT j.city AS dimension_key, COUNT(*) AS job_count,
                       ROUND(AVG(j.salary_min), 0) AS average_salary_min,
                       ROUND(AVG(j.salary_max), 0) AS average_salary_max
                FROM job j
                """ + filter + """
                  AND j.city <> ''
                GROUP BY j.city
                """, parameters);
        Map<String, ProvinceAccumulator> grouped = new LinkedHashMap<>();
        for (DemandMetric city : cities) {
            String province = LocationScope.provinceOf(city.key());
            if (!StringUtils.hasText(province)) continue;
            grouped.computeIfAbsent(province, ignored -> new ProvinceAccumulator()).add(city);
        }
        return grouped.entrySet().stream()
                .map(entry -> entry.getValue().metric(entry.getKey()))
                .sorted((left, right) -> Long.compare(right.jobCount(), left.jobCount()))
                .toList();
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
                  AND j.city <> ''
                GROUP BY j.city, category, j.job_name
                """, parameters, (rs, rowNum) -> new RegionalRawRow(rs.getString("city"),
                rs.getString("category"), rs.getString("job_name"), rs.getLong("job_count")));
        Map<String, Map<String, Long>> grouped = new LinkedHashMap<>();
        Map<String, Long> totals = new LinkedHashMap<>();
        for (RegionalRawRow row : rows) {
            String province = LocationScope.provinceOf(row.city());
            if (!StringUtils.hasText(province)) continue;
            String family = categoryFamily(row.category(), row.jobName());
            Map<String, Long> familyCounts = grouped.computeIfAbsent(province, ignored -> new LinkedHashMap<>());
            familyCounts.put(family, familyCounts.getOrDefault(family, 0L) + row.jobCount());
            totals.put(province, totals.getOrDefault(province, 0L) + row.jobCount());
        }
        List<RegionalCategoryShare> result = new ArrayList<>();
        List<String> provinces = totals.entrySet().stream()
                .sorted((left, right) -> Long.compare(right.getValue(), left.getValue()))
                .map(Map.Entry::getKey).toList();
        for (String province : provinces) {
            Map<String, Long> familyCounts = grouped.getOrDefault(province, Map.of());
            result.add(new RegionalCategoryShare(province, totals.getOrDefault(province, 0L),
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
                  AND j.city <> ''
                GROUP BY j.city, industry
                """, parameters, (rs, rowNum) -> new HeatmapCell(rs.getString("city"),
                rs.getString("industry"), rs.getLong("job_count")));
        Map<String, Long> grouped = new LinkedHashMap<>();
        Map<String, Long> industryTotals = new LinkedHashMap<>();
        for (HeatmapCell row : rows) {
            String province = LocationScope.provinceOf(row.x());
            if (!StringUtils.hasText(province)) continue;
            String key = province + "::" + row.y();
            grouped.put(key, grouped.getOrDefault(key, 0L) + row.jobCount());
            industryTotals.put(row.y(), industryTotals.getOrDefault(row.y(), 0L) + row.jobCount());
        }
        List<String> topIndustries = topKeys(industryTotals, 12);
        return grouped.entrySet().stream()
                .map(entry -> {
                    String[] parts = entry.getKey().split("::", 2);
                    return new HeatmapCell(parts[0], parts[1], entry.getValue());
                })
                .filter(row -> topIndustries.contains(row.y()))
                .sorted((left, right) -> {
                    int provinceCompare = left.x().compareTo(right.x());
                    return provinceCompare != 0 ? provinceCompare : left.y().compareTo(right.y());
                })
                .toList();
    }

    private DataQualitySummary dataQuality(LocalDate batchDate, MapSqlParameterSource parameters) {
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
        return new DataQualitySummary(batchDate, "NCSS、国聘、猎聘、智联公开岗位",
                activeTotal, activeTotal, 0, 0, missingFields, List.of(), salaryParseStatus,
                "字段缺失按当前 MySQL 有效岗位批次统计；原始记录数与清洗剔除原因需结合对应批次清洗报告查看。");
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
        List<DemandMetric> provinceDemand = demoMetrics(rows, DemoJobRow::province, 34);
        List<DemandMetric> cities = demoMetrics(rows, DemoJobRow::city, 20);
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
        return new UniversityMarketDashboardResponse(DEMO_BATCH_DATE,
                new UniversityDashboardFilter(city, industry, education, category, companyScale,
                        keyword, minSalary, maxSalary),
                summary, provinceDemand, cities, industries, educationItems, companyScales, jobCategories, hotJobs, hotSkills,
                demoSalaryBuckets(rows), categoryFamilies, demoRegionalShares(rows), demoHeatmap(rows),
                dashboardSuggestions(summary, categoryFamilies, cities, hotSkills), demoQuality(jobCount),
                "后端演示聚合数据：数据库或 SQL 暂不可用时由 Spring Boot 返回，接口仍保持 200；连接 MySQL 后会自动切换为真实岗位聚合。");
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
        return new DataQualitySummary(DEMO_BATCH_DATE, "后端演示聚合岗位样本",
                total + DEMO_EXCLUDED_COUNT, total, DEMO_EXCLUDED_COUNT, 0,
                missingFields,
                List.of(new DataQualityItem("hard_experience_requirement", 22, 0.18),
                        new DataQualityItem("social_recruitment_without_student_hint", 3, 0.02)),
                List.of(new DataQualityItem("已解析", total, 100.0),
                        new DataQualityItem("未解析", 0, 0.0)),
                "数据质量用于说明岗位样本可解释性，不是高校业务效果评分。");
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

    private LocalDate currentBatchDate() {
        LocalDate batchDate = jdbc.queryForObject(
                "SELECT MAX(j.crawl_date) FROM job j WHERE j.job_status = 'active'",
                new MapSqlParameterSource(), LocalDate.class);
        return batchDate == null ? DEMO_BATCH_DATE : batchDate;
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

    private static final class ProvinceAccumulator {
        private long jobCount;
        private long salaryMinWeight;
        private long salaryMaxWeight;
        private double salaryMinTotal;
        private double salaryMaxTotal;

        private void add(DemandMetric city) {
            jobCount += city.jobCount();
            if (city.averageSalaryMin() != null) {
                salaryMinTotal += city.averageSalaryMin() * city.jobCount();
                salaryMinWeight += city.jobCount();
            }
            if (city.averageSalaryMax() != null) {
                salaryMaxTotal += city.averageSalaryMax() * city.jobCount();
                salaryMaxWeight += city.jobCount();
            }
        }

        private DemandMetric metric(String province) {
            Double averageMin = salaryMinWeight == 0 ? null : Math.round(salaryMinTotal / salaryMinWeight * 100.0) / 100.0;
            Double averageMax = salaryMaxWeight == 0 ? null : Math.round(salaryMaxTotal / salaryMaxWeight * 100.0) / 100.0;
            return new DemandMetric(province, jobCount, averageMin, averageMax);
        }
    }

    private static final class DemoMetricAccumulator {
        private long count;
        private double salaryMinTotal;
        private double salaryMaxTotal;
    }
}
