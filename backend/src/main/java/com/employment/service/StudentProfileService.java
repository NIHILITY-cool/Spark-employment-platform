package com.employment.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.UpdateWrapper;
import com.employment.dto.JobPreferenceRequest;
import com.employment.dto.StudentProfileRequest;
import com.employment.dto.StudentExperienceRequest;
import com.employment.dto.StudentSkillRequest;
import com.employment.entity.JobPreference;
import com.employment.entity.Student;
import com.employment.entity.StudentExperience;
import com.employment.entity.StudentSkill;
import com.employment.mapper.JobPreferenceMapper;
import com.employment.mapper.StudentMapper;
import com.employment.mapper.StudentExperienceMapper;
import com.employment.mapper.StudentSkillMapper;
import com.employment.vo.StudentProfileResponse;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;
import java.util.List;

@Service
public class StudentProfileService {
    private final StudentMapper studentMapper;
    private final StudentSkillMapper studentSkillMapper;
    private final StudentExperienceMapper studentExperienceMapper;
    private final JobPreferenceMapper jobPreferenceMapper;
    private final StudentInsightCache studentInsightCache;

    public StudentProfileService(StudentMapper studentMapper, StudentSkillMapper studentSkillMapper,
                                 StudentExperienceMapper studentExperienceMapper,
                                 JobPreferenceMapper jobPreferenceMapper,
                                 StudentInsightCache studentInsightCache) {
        this.studentMapper = studentMapper;
        this.studentSkillMapper = studentSkillMapper;
        this.studentExperienceMapper = studentExperienceMapper;
        this.jobPreferenceMapper = jobPreferenceMapper;
        this.studentInsightCache = studentInsightCache;
    }

    @Transactional
    public Student create(StudentProfileRequest request) {
        Student student = from(request);
        student.profileCompleted = true;
        studentMapper.insert(student);
        studentInsightCache.invalidateAfterCommit();
        return student;
    }

    public StudentProfileResponse profile(Long studentId) {
        Student student = requiredStudent(studentId);
        List<StudentSkill> skills = studentSkillMapper.selectList(new QueryWrapper<StudentSkill>()
                .eq("student_id", studentId).orderByDesc("skill_level").orderByAsc("skill_name"));
        List<StudentExperience> experiences = studentExperienceMapper.selectList(new QueryWrapper<StudentExperience>()
                .eq("student_id", studentId).orderByDesc("end_date").orderByDesc("start_date").orderByDesc("id"));
        return new StudentProfileResponse(student, skills, experiences, jobPreferenceMapper.selectById(studentId));
    }

    @Transactional
    public Student update(Long studentId, StudentProfileRequest request) {
        Student current = requiredStudent(studentId);
        Student next = from(request);
        next.id = current.id;
        next.profileCompleted = true;
        studentMapper.updateById(next);
        studentInsightCache.invalidateAfterCommit();
        return next;
    }

    @Transactional
    public StudentSkill addSkill(Long studentId, StudentSkillRequest request) {
        requiredStudent(studentId);
        StudentSkill skill = new StudentSkill();
        skill.studentId = studentId;
        skill.skillName = request.skillName().trim();
        skill.skillLevel = request.skillLevel();
        StudentSkill existing = studentSkillMapper.selectOne(new QueryWrapper<StudentSkill>()
                .eq("student_id", studentId).eq("skill_name", skill.skillName));
        if (existing != null) {
            existing.skillLevel = skill.skillLevel;
            studentSkillMapper.updateById(existing);
            touch(studentId);
            studentInsightCache.invalidateAfterCommit();
            return existing;
        }
        studentSkillMapper.insert(skill);
        touch(studentId);
        studentInsightCache.invalidateAfterCommit();
        return skill;
    }

    @Transactional
    public void deleteSkill(Long studentId, Long skillId) {
        requiredStudent(studentId);
        if (studentSkillMapper.delete(new QueryWrapper<StudentSkill>().eq("id", skillId).eq("student_id", studentId)) == 0) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "技能不存在");
        }
        touch(studentId);
        studentInsightCache.invalidateAfterCommit();
    }

    @Transactional
    public StudentExperience addExperience(Long studentId, StudentExperienceRequest request) {
        requiredStudent(studentId);
        StudentExperience experience = experienceFrom(studentId, request);
        studentExperienceMapper.insert(experience);
        touch(studentId);
        studentInsightCache.invalidateAfterCommit();
        return experience;
    }

    @Transactional
    public StudentExperience updateExperience(Long studentId, Long experienceId, StudentExperienceRequest request) {
        requiredStudent(studentId);
        StudentExperience current = studentExperienceMapper.selectOne(new QueryWrapper<StudentExperience>()
                .eq("id", experienceId).eq("student_id", studentId));
        if (current == null) throw new ResponseStatusException(HttpStatus.NOT_FOUND, "经历不存在");
        StudentExperience experience = experienceFrom(studentId, request);
        experience.id = current.id;
        studentExperienceMapper.updateById(experience);
        touch(studentId);
        studentInsightCache.invalidateAfterCommit();
        return experience;
    }

    @Transactional
    public void deleteExperience(Long studentId, Long experienceId) {
        requiredStudent(studentId);
        if (studentExperienceMapper.delete(new QueryWrapper<StudentExperience>()
                .eq("id", experienceId).eq("student_id", studentId)) == 0) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "经历不存在");
        }
        touch(studentId);
        studentInsightCache.invalidateAfterCommit();
    }

    @Transactional
    public JobPreference savePreference(Long studentId, JobPreferenceRequest request) {
        requiredStudent(studentId);
        JobPreference preference = jobPreferenceMapper.selectById(studentId);
        if (preference == null) preference = new JobPreference();
        preference.studentId = studentId;
        preference.expectedJob = trim(request.expectedJob());
        preference.expectedCity = normalizeCity(request.expectedCity());
        preference.expectedIndustry = trim(request.expectedIndustry());
        preference.salaryMin = request.salaryMin();
        preference.salaryMax = null;
        preference.acceptRemoteCity = Boolean.TRUE.equals(request.acceptRemoteCity());
        if (jobPreferenceMapper.selectById(studentId) == null) jobPreferenceMapper.insert(preference);
        else jobPreferenceMapper.updateById(preference);
        touch(studentId);
        studentInsightCache.invalidateAfterCommit();
        return preference;
    }

    public Student requiredStudent(Long studentId) {
        Student student = studentMapper.selectById(studentId);
        if (student == null) throw new ResponseStatusException(HttpStatus.NOT_FOUND, "学生不存在");
        return student;
    }

    private Student from(StudentProfileRequest request) {
        Student student = new Student();
        student.studentNo = emptyToNull(request.studentNo());
        student.name = request.name().trim();
        student.college = request.college().trim();
        student.major = request.major().trim();
        student.education = request.education().trim();
        student.graduationYear = request.graduationYear();
        return student;
    }

    private StudentExperience experienceFrom(Long studentId, StudentExperienceRequest request) {
        if (request.startDate() != null && request.endDate() != null
                && request.endDate().isBefore(request.startDate())) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "结束时间不能早于开始时间");
        }
        StudentExperience experience = new StudentExperience();
        experience.studentId = studentId;
        experience.experienceType = request.experienceType();
        experience.title = request.title().trim();
        experience.organization = trim(request.organization());
        experience.role = trim(request.role());
        experience.description = request.description().trim();
        experience.startDate = request.startDate();
        experience.endDate = request.endDate();
        return experience;
    }

    private String trim(String value) { return value == null ? "" : value.trim(); }
    private String normalizeCity(String value) {
        String normalized = trim(value).replaceFirst("市+$", "");
        return "中国".equals(normalized) ? "全国" : normalized;
    }
    private String emptyToNull(String value) {
        String trimmed = trim(value);
        return trimmed.isEmpty() ? null : trimmed;
    }

    private void touch(Long studentId) {
        studentMapper.update(null, new UpdateWrapper<Student>().eq("id", studentId)
                .setSql("updated_at = CURRENT_TIMESTAMP"));
    }
}
