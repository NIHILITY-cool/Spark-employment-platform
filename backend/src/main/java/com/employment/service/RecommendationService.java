package com.employment.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.employment.entity.Job;
import com.employment.entity.JobPreference;
import com.employment.entity.Student;
import com.employment.entity.StudentExperience;
import com.employment.entity.StudentSkill;
import com.employment.mapper.JobMapper;
import com.employment.mapper.JobPreferenceMapper;
import com.employment.mapper.StudentSkillMapper;
import com.employment.mapper.StudentExperienceMapper;
import com.employment.vo.JobRecommendation;
import com.employment.vo.SkillGapResponse;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;
import org.springframework.web.server.ResponseStatusException;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.time.LocalDate;
import java.time.temporal.ChronoUnit;
import java.util.regex.Pattern;

@Service
public class RecommendationService {
    private static final List<String> MATCH_TERMS = List.of(
            "数据", "分析", "开发", "后端", "前端", "java", "python", "sql", "spark", "hadoop",
            "vue", "react", "算法", "模型", "机器学习", "人工智能", "ai", "测试", "运维", "云计算",
            "数据库", "可视化", "产品", "运营", "营销", "销售", "用户", "市场", "电商", "供应链",
            "采购", "客户", "增长", "策划", "需求", "项目管理", "金融", "财务", "会计", "审计",
            "银行", "证券", "投资", "风控", "机械", "制造", "生产", "设备", "自动化", "电气",
            "质量", "工艺", "医药", "医疗", "生物", "临床", "建筑", "施工", "教育", "教学",
            "物流", "服务", "设计", "视频", "内容", "新媒体");
    private static final Map<String, List<String>> DIRECTION_TERMS = Map.of(
            "大数据开发", List.of("大数据", "数据工程", "数仓", "数据仓库", "etl", "spark", "hadoop", "离线计算", "实时计算"),
            "后端开发", List.of("后端", "java开发", "服务端", "微服务", "spring", "接口开发"),
            "前端开发", List.of("前端", "web开发", "vue", "react", "javascript", "typescript"),
            "数据分析", List.of("数据分析", "商业分析", "经营分析", "bi", "报表", "指标体系"),
            "人工智能", List.of("人工智能", "机器学习", "算法工程", "大模型", "深度学习", "自然语言", "计算机视觉"));
    private static final Pattern QUANTIFIED_RESULT = Pattern.compile("\\d+|%|提升|降低|优化|上线|落地|排名|获奖|一等奖|二等奖|三等奖");
    private static final Pattern STRUCTURED_YEARS = Pattern.compile("(\\d+)\\s*(?:-\\s*\\d+|至\\s*\\d+)?\\s*年");
    private static final Pattern REQUIRED_YEARS = Pattern.compile("(\\d+)\\s*(?:-\\s*\\d+|至\\s*\\d+)?\\s*年(?:以上)?(?:相关)?(?:工作)?经验");
    private final StudentProfileService studentProfileService;
    private final StudentSkillMapper studentSkillMapper;
    private final StudentExperienceMapper studentExperienceMapper;
    private final JobPreferenceMapper jobPreferenceMapper;
    private final JobMapper jobMapper;

    public RecommendationService(StudentProfileService studentProfileService, StudentSkillMapper studentSkillMapper,
                                 StudentExperienceMapper studentExperienceMapper,
                                 JobPreferenceMapper jobPreferenceMapper, JobMapper jobMapper) {
        this.studentProfileService = studentProfileService;
        this.studentSkillMapper = studentSkillMapper;
        this.studentExperienceMapper = studentExperienceMapper;
        this.jobPreferenceMapper = jobPreferenceMapper;
        this.jobMapper = jobMapper;
    }

    public List<JobRecommendation> top(Long studentId, int limit) {
        Context context = context(studentId);
        int safeLimit = Math.min(Math.max(limit, 1), 20);
        List<JobRecommendation> ranked = score(jobMapper.selectList(candidateQuery(context.preference)).stream()
                .filter(job -> educationEligible(context.student.education, job.educationRequirement)).toList(), context).stream()
                .sorted(Comparator.comparingInt(JobRecommendation::totalScore).reversed()
                        .thenComparing(item -> item.job().jobKey))
                .toList();
        if (context.preference != null && StringUtils.hasText(context.preference.expectedJob)) {
            List<JobRecommendation> aligned = ranked.stream().filter(item -> item.directionScore() >= 18).toList();
            ranked = aligned;
        }
        return ranked.stream().limit(safeLimit).toList();
    }

    public JobRecommendation match(Long studentId, String jobKey) {
        Context context = context(studentId);
        Job job = jobMapper.selectById(jobKey);
        if (job == null || !"active".equals(job.jobStatus)) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "岗位不存在或已失效");
        }
        return score(List.of(job), context).get(0);
    }

    public SkillGapResponse skillGap(Long studentId) {
        Context context = context(studentId);
        return new SkillGapResponse(studentId, context.masteredNames, List.of(),
                "技能仅作为学生画像记录，推荐排序以方向、经历和硬门槛为准。");
    }

    private List<JobRecommendation> score(List<Job> jobs, Context context) {
        if (jobs.isEmpty()) return List.of();
        return jobs.stream().map(job -> scoreOne(job, context)).toList();
    }

    private JobRecommendation scoreOne(Job job, Context context) {
        String jobText = searchableJobText(job);
        int skillScore = 0;
        int directionScore = directionScore(context.student, context.preference, job, jobText);
        int cityScore = 0;
        int salaryScore = 0;
        int industryScore = industryScore(context.preference, job, jobText);
        int freshnessScore = freshnessScore(job.lastSeenDate);
        List<String> reasons = new ArrayList<>();
        JobPreference preference = context.preference;
        if (directionScore >= 14) reasons.add("岗位方向符合期望");
        if (preference != null && StringUtils.hasText(preference.expectedCity)
                && normalizeCity(preference.expectedCity).equals(normalizeCity(job.city))) {
            cityScore = 10;
            reasons.add("工作城市符合期望");
        } else if (preference != null && Boolean.TRUE.equals(preference.acceptRemoteCity)) {
            cityScore = 4;
        }
        if (preference != null) {
            salaryScore = salaryScore(preference.salaryMin, job);
            if (salaryScore >= 7) reasons.add("薪资达到期望");
        }
        int educationScore = 0;
        List<String> experienceTerms = matchedExperienceTerms(context.experiences, jobText);
        int requiredYears = requiredExperienceYears(job.experienceRequirement, job.jobDescription);
        int experienceScore = experienceScore(requiredYears, context.experiences, jobText);
        if (!experienceTerms.isEmpty()) reasons.add("经历命中 " + String.join("、", experienceTerms.stream().limit(4).toList()));
        if (requiredYears >= 3) reasons.add("岗位要求 " + requiredYears + " 年以上经验，经历分已限制");
        if (industryScore > 0) reasons.add("行业偏好相符");
        String reason = reasons.isEmpty() ? "根据岗位方向、经历证据与岗位门槛进行基础匹配" : String.join("；", reasons);
        int totalScore = experienceScore + directionScore + cityScore
                + industryScore + salaryScore + freshnessScore;
        return new JobRecommendation(job, totalScore, skillScore, experienceScore, directionScore,
                educationScore, cityScore, industryScore, salaryScore, freshnessScore,
                List.of(), List.of(), experienceTerms, reason);
    }

    private Context context(Long studentId) {
        Student student = studentProfileService.requiredStudent(studentId);
        List<StudentSkill> skills = studentSkillMapper.selectList(new QueryWrapper<StudentSkill>().eq("student_id", studentId));
        List<String> names = skills.stream().map(skill -> skill.skillName).filter(StringUtils::hasText).sorted().toList();
        List<StudentExperience> experiences = studentExperienceMapper.selectList(new QueryWrapper<StudentExperience>()
                .eq("student_id", studentId));
        return new Context(student, names, experiences, jobPreferenceMapper.selectById(studentId));
    }

    private QueryWrapper<Job> candidateQuery(JobPreference preference) {
        QueryWrapper<Job> query = new QueryWrapper<Job>().eq("job_status", "active");
        if (preference != null && StringUtils.hasText(preference.expectedCity) && !Boolean.TRUE.equals(preference.acceptRemoteCity)) {
            query.eq("city", normalizeCity(preference.expectedCity));
        }
        return query.last("ORDER BY last_seen_date DESC, MOD(CRC32(job_key), 1009) LIMIT 5000");
    }

    static int salaryScore(Integer expectedMinimum, Job job) {
        if (expectedMinimum == null || expectedMinimum <= 0 || job.salaryMax == null) return 0;
        if (job.salaryMin != null && job.salaryMin >= expectedMinimum) return 10;
        if (job.salaryMax >= expectedMinimum) return 7;
        return job.salaryMax >= expectedMinimum * 0.8 ? 3 : 0;
    }

    static int educationScore(String studentEducation, String requirement) {
        int requiredRank = educationRank(requirement);
        if (requiredRank == 0) return 10;
        return educationRank(studentEducation) >= requiredRank ? 10 : 0;
    }

    static boolean educationEligible(String studentEducation, String requirement) {
        int requiredRank = educationRank(requirement);
        return requiredRank == 0 || educationRank(studentEducation) >= requiredRank;
    }

    static int experienceRequirementScore(String requirement, boolean hasProject, boolean hasInternship) {
        String normalized = normalizeStatic(requirement);
        if (normalized.isEmpty() || normalized.contains("不限") || normalized.contains("应届")
                || normalized.contains("在校")) return 8;
        if (normalized.contains("1年以内") || normalized.contains("一年以内")) {
            if (hasInternship) return 8;
            return hasProject ? 6 : 2;
        }
        if (normalized.contains("1-3年") || normalized.contains("1至3年")) {
            if (hasInternship) return 6;
            return hasProject ? 4 : 0;
        }
        if (hasInternship) return 2;
        return 0;
    }

    private int experienceScore(int requiredYears, List<StudentExperience> experiences, String jobText) {
        boolean hasProject = experiences.stream().anyMatch(item -> "project".equals(item.experienceType));
        boolean hasInternship = experiences.stream().anyMatch(item -> "internship".equals(item.experienceType));
        int requirementScore = experienceRequirementScore(requiredYears, hasProject, hasInternship);
        int relevanceScore = 0;
        for (StudentExperience experience : experiences) {
            long termCount = MATCH_TERMS.stream().filter(term -> containsTerm(jobText, term)
                    && containsTerm(searchableExperienceText(experience), term)).count();
            int perTerm = "internship".equals(experience.experienceType) ? 5
                    : "project".equals(experience.experienceType) ? 4 : 1;
            int perExperienceCap = "internship".equals(experience.experienceType) ? 18
                    : "project".equals(experience.experienceType) ? 16 : 4;
            relevanceScore += Math.min(perExperienceCap, (int) termCount * perTerm);
        }
        int relevanceCap = requiredYears >= 5 ? 8 : requiredYears >= 3 ? 15 : requiredYears >= 2 ? 22 : 28;
        relevanceScore = Math.min(relevanceCap, relevanceScore);
        int achievementScore = achievementScore(experiences);
        return Math.min(40, requirementScore + relevanceScore + achievementScore);
    }

    static int requiredExperienceYears(String requirement, String description) {
        int structured = yearsFromText(normalizeStatic(requirement), STRUCTURED_YEARS);
        int described = yearsFromText(normalizeStatic(description), REQUIRED_YEARS);
        return Math.max(structured, described);
    }

    private static int yearsFromText(String text, Pattern pattern) {
        var matcher = pattern.matcher(text);
        int years = 0;
        while (matcher.find()) years = Math.max(years, Integer.parseInt(matcher.group(1)));
        return years;
    }

    private static int experienceRequirementScore(int requiredYears, boolean hasProject, boolean hasInternship) {
        if (requiredYears == 0) return 8;
        if (requiredYears <= 1) {
            if (hasInternship) return 8;
            return hasProject ? 6 : 2;
        }
        if (requiredYears <= 3) {
            if (hasInternship) return 6;
            return hasProject ? 4 : 0;
        }
        return hasInternship ? 2 : 0;
    }

    static int achievementScore(List<StudentExperience> experiences) {
        int score = 0;
        for (StudentExperience experience : experiences) {
            String text = searchableExperienceText(experience);
            if ("award".equals(experience.experienceType)) {
                if (text.contains("国家") || text.contains("全国") || text.contains("国际")) score = Math.max(score, 4);
                else if (text.contains("省") || text.contains("市级")) score = Math.max(score, 3);
                else score = Math.max(score, 2);
            } else if (QUANTIFIED_RESULT.matcher(text).find()) {
                score = Math.min(4, score + 1);
            }
        }
        return Math.min(4, score);
    }

    private static List<String> matchedExperienceTerms(List<StudentExperience> experiences, String jobText) {
        String experienceText = experiences.stream().map(RecommendationService::searchableExperienceText)
                .reduce("", (left, right) -> left + " " + right);
        return MATCH_TERMS.stream().filter(term -> containsTerm(jobText, term)
                && containsTerm(experienceText, term)).distinct().limit(8).toList();
    }

    private static int directionScore(Student student, JobPreference preference, Job job, String jobText) {
        if (preference != null && StringUtils.hasText(preference.expectedJob)) {
            String expected = normalizeStatic(preference.expectedJob);
            String jobName = normalizeStatic(job.jobName);
            String category = normalizeStatic(job.jobCategory);
            if (jobName.contains(expected)) return 30;
            List<String> directionTerms = DIRECTION_TERMS.entrySet().stream()
                    .filter(entry -> expected.contains(entry.getKey()) || entry.getKey().contains(expected))
                    .map(Map.Entry::getValue).findFirst().orElse(List.of(expected));
            long titleMatches = directionTerms.stream().filter(term -> containsTerm(jobName, term)).count();
            if (titleMatches > 0) return 30;
            long textMatches = directionTerms.stream().filter(term -> containsTerm(jobText, term)).count();
            if (textMatches >= 2 && category.equals(expected)) return 24;
            if (textMatches >= 2) return 18;
            if (textMatches == 1 && category.equals(expected)) return 15;
            if (category.equals(expected)) return 9;
            return Math.min(12, sharedTerms(expected, jobText) * 6);
        }
        return Math.min(12, sharedTerms(normalizeStatic(student.major), jobText) * 4);
    }

    private static int industryScore(JobPreference preference, Job job, String jobText) {
        if (preference == null || !StringUtils.hasText(preference.expectedIndustry)) return 0;
        String expected = normalizeStatic(preference.expectedIndustry);
        String industry = normalizeStatic(job.industry);
        if (industry.contains(expected) || (StringUtils.hasText(industry) && expected.contains(industry))
                || jobText.contains(expected)) return 5;
        return sharedTerms(expected, industry + " " + jobText) > 0 ? 3 : 0;
    }

    static int freshnessScore(LocalDate lastSeenDate) {
        if (lastSeenDate == null) return 0;
        long days = Math.max(0, ChronoUnit.DAYS.between(lastSeenDate, LocalDate.now()));
        if (days <= 7) return 5;
        if (days <= 30) return 3;
        if (days <= 90) return 1;
        return 0;
    }

    private static int sharedTerms(String left, String right) {
        return (int) MATCH_TERMS.stream().filter(term -> containsTerm(left, term) && containsTerm(right, term)).count();
    }

    private static String searchableJobText(Job job) {
        return normalizeStatic((job.jobName == null ? "" : job.jobName) + " "
                + (job.jobCategory == null ? "" : job.jobCategory) + " "
                + (job.industry == null ? "" : job.industry) + " "
                + (job.jobDescription == null ? "" : job.jobDescription));
    }

    private static String searchableExperienceText(StudentExperience experience) {
        return normalizeStatic((experience.title == null ? "" : experience.title) + " "
                + (experience.organization == null ? "" : experience.organization) + " "
                + (experience.role == null ? "" : experience.role) + " "
                + (experience.description == null ? "" : experience.description));
    }

    private static boolean containsTerm(String text, String term) {
        if (!StringUtils.hasText(text) || !StringUtils.hasText(term)) return false;
        if (term.chars().allMatch(character -> character < 128)) {
            return Pattern.compile("(^|[^a-z0-9])" + Pattern.quote(term) + "([^a-z0-9]|$)").matcher(text).find();
        }
        return text.contains(term);
    }

    private static int educationRank(String value) {
        String normalized = normalizeStatic(value);
        if (normalized.contains("博士") || normalized.contains("doctor")) return 4;
        if (normalized.contains("硕士") || normalized.contains("master")) return 3;
        if (normalized.contains("本科") || normalized.contains("bachelor")) return 2;
        if (normalized.contains("专科") || normalized.contains("大专") || normalized.contains("college")) return 1;
        return 0;
    }

    private static String normalizeStatic(String value) {
        return value == null ? "" : value.trim().toLowerCase(Locale.ROOT).replace("—", "-").replace("–", "-");
    }

    private String normalizeCity(String value) {
        String normalized = value == null ? "" : value.trim().replaceFirst("市+$", "");
        return "中国".equals(normalized) ? "全国" : normalized;
    }

    private record Context(Student student, List<String> masteredNames,
                           List<StudentExperience> experiences,
                           JobPreference preference) { }
}
