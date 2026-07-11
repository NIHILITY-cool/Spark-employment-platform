package com.employment.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.employment.entity.Job;
import com.employment.entity.JobPreference;
import com.employment.entity.JobSkill;
import com.employment.entity.Student;
import com.employment.entity.StudentSkill;
import com.employment.mapper.JobMapper;
import com.employment.mapper.JobPreferenceMapper;
import com.employment.mapper.JobSkillMapper;
import com.employment.mapper.StudentSkillMapper;
import com.employment.vo.JobRecommendation;
import com.employment.vo.SkillGapResponse;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;
import org.springframework.web.server.ResponseStatusException;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.math.BigDecimal;

@Service
public class RecommendationService {
    private final StudentProfileService studentProfileService;
    private final StudentSkillMapper studentSkillMapper;
    private final JobPreferenceMapper jobPreferenceMapper;
    private final JobMapper jobMapper;
    private final JobSkillMapper jobSkillMapper;

    public RecommendationService(StudentProfileService studentProfileService, StudentSkillMapper studentSkillMapper,
                                 JobPreferenceMapper jobPreferenceMapper, JobMapper jobMapper, JobSkillMapper jobSkillMapper) {
        this.studentProfileService = studentProfileService;
        this.studentSkillMapper = studentSkillMapper;
        this.jobPreferenceMapper = jobPreferenceMapper;
        this.jobMapper = jobMapper;
        this.jobSkillMapper = jobSkillMapper;
    }

    public List<JobRecommendation> top(Long studentId, int limit) {
        Context context = context(studentId);
        List<Job> candidates = jobMapper.selectList(candidateQuery(context.preference));
        return score(candidates, context).stream()
                .sorted(Comparator.comparingInt(JobRecommendation::totalScore).reversed()
                        .thenComparing(item -> item.job().jobKey))
                .limit(Math.min(Math.max(limit, 1), 20))
                .toList();
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
        LinkedHashMap<String, Integer> missingFrequency = new LinkedHashMap<>();
        for (JobRecommendation item : top(studentId, 10)) {
            item.missingSkills().forEach(skill -> missingFrequency.merge(skill, 1, Integer::sum));
        }
        List<String> missing = missingFrequency.entrySet().stream()
                .sorted(Map.Entry.<String, Integer>comparingByValue().reversed().thenComparing(Map.Entry.comparingByKey()))
                .map(Map.Entry::getKey).limit(10).toList();
        String suggestion = missing.isEmpty() ? "你的技能已覆盖当前推荐岗位的主要要求，可继续补充项目与实习经历。"
                : "优先补齐 " + String.join("、", missing.stream().limit(3).toList()) + "，并通过项目实践验证能力。";
        return new SkillGapResponse(studentId, context.masteredNames, missing, suggestion);
    }

    private List<JobRecommendation> score(List<Job> jobs, Context context) {
        if (jobs.isEmpty()) return List.of();
        List<String> jobKeys = jobs.stream().map(job -> job.jobKey).toList();
        Map<String, List<JobSkill>> skillsByJob = new LinkedHashMap<>();
        for (JobSkill skill : jobSkillMapper.selectList(new QueryWrapper<JobSkill>().in("job_key", jobKeys))) {
            skillsByJob.computeIfAbsent(skill.jobKey, ignored -> new ArrayList<>()).add(skill);
        }
        return jobs.stream().map(job -> scoreOne(job, skillsByJob.getOrDefault(job.jobKey, List.of()), context)).toList();
    }

    private JobRecommendation scoreOne(Job job, List<JobSkill> jobSkills, Context context) {
        List<String> matched = new ArrayList<>();
        List<String> missing = new ArrayList<>();
        double totalSkillWeight = 0;
        double matchedSkillWeight = 0;
        List<JobSkill> orderedSkills = jobSkills.stream()
                .sorted(Comparator.comparingDouble(this::skillWeight).reversed()
                        .thenComparing(skill -> skill.skillName))
                .toList();
        for (JobSkill skill : orderedSkills) {
            double weight = skillWeight(skill);
            totalSkillWeight += weight;
            if (context.mastered.contains(normalize(skill.skillName))) {
                matched.add(skill.skillName);
                matchedSkillWeight += weight;
            } else {
                missing.add(skill.skillName);
            }
        }

        double evidenceConfidence = Math.min(1.0, totalSkillWeight / 3.0);
        int skillScore = totalSkillWeight == 0 ? 0
                : (int) Math.round(40.0 * matchedSkillWeight / totalSkillWeight * evidenceConfidence);
        int directionScore = 0;
        int cityScore = 0;
        int salaryScore = 0;
        List<String> reasons = new ArrayList<>();
        JobPreference preference = context.preference;
        if (preference != null && StringUtils.hasText(preference.expectedJob)
                && job.jobCategory != null && job.jobCategory.contains(preference.expectedJob)) {
            directionScore = 15;
            reasons.add("岗位方向符合期望");
        }
        if (preference != null && StringUtils.hasText(preference.expectedCity)
                && normalizeCity(preference.expectedCity).equals(normalizeCity(job.city))) {
            cityScore = 10;
            reasons.add("工作城市符合期望");
        } else if (preference != null && Boolean.TRUE.equals(preference.acceptRemoteCity)) {
            cityScore = 4;
        }
        if (preference != null && salaryOverlaps(preference, job)) {
            salaryScore = 5;
            reasons.add("薪资区间有重合");
        }
        int educationScore = educationScore(context.student.education, job.educationRequirement);
        int experienceScore = experienceScore(job.experienceRequirement);
        if (!matched.isEmpty()) reasons.add("已掌握 " + String.join("、", matched.stream().limit(3).toList()));
        if (!jobSkills.isEmpty() && totalSkillWeight < 3) reasons.add("岗位技能证据较少，技能分已折减");
        String reason = reasons.isEmpty() ? "根据岗位活跃度与学生技能进行基础匹配" : String.join("；", reasons);
        int totalScore = skillScore + experienceScore + directionScore + educationScore + cityScore + salaryScore;
        return new JobRecommendation(job, totalScore, skillScore, experienceScore, directionScore,
                educationScore, cityScore, salaryScore, matched, missing, reason);
    }

    private Context context(Long studentId) {
        Student student = studentProfileService.requiredStudent(studentId);
        List<StudentSkill> skills = studentSkillMapper.selectList(new QueryWrapper<StudentSkill>().eq("student_id", studentId));
        List<String> names = skills.stream().map(skill -> skill.skillName).filter(StringUtils::hasText).sorted().toList();
        Set<String> normalized = new LinkedHashSet<>();
        names.forEach(name -> normalized.add(normalize(name)));
        return new Context(student, normalized, names, jobPreferenceMapper.selectById(studentId));
    }

    private QueryWrapper<Job> candidateQuery(JobPreference preference) {
        QueryWrapper<Job> query = new QueryWrapper<Job>().eq("job_status", "active");
        if (preference != null && StringUtils.hasText(preference.expectedJob)) query.like("job_category", preference.expectedJob);
        if (preference != null && StringUtils.hasText(preference.expectedCity) && !Boolean.TRUE.equals(preference.acceptRemoteCity)) {
            query.eq("city", normalizeCity(preference.expectedCity));
        }
        return query.orderByDesc("last_seen_date").orderByDesc("salary_max").last("LIMIT 300");
    }

    private boolean salaryOverlaps(JobPreference preference, Job job) {
        if (preference.salaryMin == null || preference.salaryMax == null || job.salaryMin == null || job.salaryMax == null) return false;
        return preference.salaryMin <= job.salaryMax && job.salaryMin <= preference.salaryMax;
    }

    private double skillWeight(JobSkill skill) {
        BigDecimal weight = skill.skillWeight;
        return weight == null || weight.signum() <= 0 ? 1.0 : weight.doubleValue();
    }

    static int educationScore(String studentEducation, String requirement) {
        int requiredRank = educationRank(requirement);
        if (requiredRank == 0) return 10;
        return educationRank(studentEducation) >= requiredRank ? 10 : 0;
    }

    static int experienceScore(String requirement) {
        String normalized = normalizeStatic(requirement);
        if (normalized.isEmpty() || normalized.contains("不限") || normalized.contains("应届")
                || normalized.contains("在校")) return 20;
        if (normalized.contains("1年以内") || normalized.contains("一年以内")) return 16;
        if (normalized.contains("1-3年") || normalized.contains("1至3年")) return 8;
        return 0;
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

    private String normalize(String value) { return value == null ? "" : value.trim().toLowerCase(Locale.ROOT); }
    private String normalizeCity(String value) {
        String normalized = value == null ? "" : value.trim().replaceFirst("市+$", "");
        return "中国".equals(normalized) ? "全国" : normalized;
    }

    private record Context(Student student, Set<String> mastered, List<String> masteredNames,
                           JobPreference preference) { }
}
