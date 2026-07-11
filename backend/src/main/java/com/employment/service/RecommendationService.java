package com.employment.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.employment.entity.Job;
import com.employment.entity.JobPreference;
import com.employment.entity.JobSkill;
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
        for (JobSkill skill : jobSkills) {
            if (context.mastered.contains(normalize(skill.skillName))) matched.add(skill.skillName);
            else missing.add(skill.skillName);
        }
        int skillScore = jobSkills.isEmpty() ? 0 : (int) Math.round(60.0 * matched.size() / jobSkills.size());
        int preferenceScore = 0;
        List<String> reasons = new ArrayList<>();
        JobPreference preference = context.preference;
        if (preference != null && StringUtils.hasText(preference.expectedJob)
                && job.jobCategory != null && job.jobCategory.contains(preference.expectedJob)) {
            preferenceScore += 15; reasons.add("岗位方向符合期望");
        }
        if (preference != null && StringUtils.hasText(preference.expectedCity)
                && normalizeCity(preference.expectedCity).equals(normalizeCity(job.city))) {
            preferenceScore += 10; reasons.add("工作城市符合期望");
        } else if (preference != null && Boolean.TRUE.equals(preference.acceptRemoteCity)) {
            preferenceScore += 4;
        }
        if (preference != null && salaryOverlaps(preference, job)) {
            preferenceScore += 10; reasons.add("薪资区间有重合");
        }
        preferenceScore += 5;
        if (!matched.isEmpty()) reasons.add("已掌握 " + String.join("、", matched.stream().limit(3).toList()));
        String reason = reasons.isEmpty() ? "根据岗位活跃度与学生技能进行基础匹配" : String.join("；", reasons);
        return new JobRecommendation(job, Math.min(100, skillScore + preferenceScore), skillScore, matched, missing, reason);
    }

    private Context context(Long studentId) {
        studentProfileService.requiredStudent(studentId);
        List<StudentSkill> skills = studentSkillMapper.selectList(new QueryWrapper<StudentSkill>().eq("student_id", studentId));
        List<String> names = skills.stream().map(skill -> skill.skillName).filter(StringUtils::hasText).sorted().toList();
        Set<String> normalized = new LinkedHashSet<>();
        names.forEach(name -> normalized.add(normalize(name)));
        return new Context(normalized, names, jobPreferenceMapper.selectById(studentId));
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

    private String normalize(String value) { return value == null ? "" : value.trim().toLowerCase(Locale.ROOT); }
    private String normalizeCity(String value) {
        String normalized = value == null ? "" : value.trim().replaceFirst("市+$", "");
        return "中国".equals(normalized) ? "全国" : normalized;
    }

    private record Context(Set<String> mastered, List<String> masteredNames, JobPreference preference) { }
}
