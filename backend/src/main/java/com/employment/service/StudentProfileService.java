package com.employment.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.employment.dto.JobPreferenceRequest;
import com.employment.dto.StudentProfileRequest;
import com.employment.dto.StudentSkillRequest;
import com.employment.entity.JobPreference;
import com.employment.entity.Student;
import com.employment.entity.StudentSkill;
import com.employment.mapper.JobPreferenceMapper;
import com.employment.mapper.StudentMapper;
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
    private final JobPreferenceMapper jobPreferenceMapper;

    public StudentProfileService(StudentMapper studentMapper, StudentSkillMapper studentSkillMapper,
                                 JobPreferenceMapper jobPreferenceMapper) {
        this.studentMapper = studentMapper;
        this.studentSkillMapper = studentSkillMapper;
        this.jobPreferenceMapper = jobPreferenceMapper;
    }

    @Transactional
    public Student create(StudentProfileRequest request) {
        Student student = from(request);
        student.profileCompleted = true;
        studentMapper.insert(student);
        return student;
    }

    public StudentProfileResponse profile(Long studentId) {
        Student student = requiredStudent(studentId);
        List<StudentSkill> skills = studentSkillMapper.selectList(new QueryWrapper<StudentSkill>()
                .eq("student_id", studentId).orderByDesc("skill_level").orderByAsc("skill_name"));
        return new StudentProfileResponse(student, skills, jobPreferenceMapper.selectById(studentId));
    }

    @Transactional
    public Student update(Long studentId, StudentProfileRequest request) {
        Student current = requiredStudent(studentId);
        Student next = from(request);
        next.id = current.id;
        next.profileCompleted = true;
        studentMapper.updateById(next);
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
            return existing;
        }
        studentSkillMapper.insert(skill);
        return skill;
    }

    @Transactional
    public void deleteSkill(Long studentId, Long skillId) {
        requiredStudent(studentId);
        if (studentSkillMapper.delete(new QueryWrapper<StudentSkill>().eq("id", skillId).eq("student_id", studentId)) == 0) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "技能不存在");
        }
    }

    @Transactional
    public JobPreference savePreference(Long studentId, JobPreferenceRequest request) {
        requiredStudent(studentId);
        if (request.salaryMin() != null && request.salaryMax() != null && request.salaryMin() > request.salaryMax()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "期望最低薪资不能高于最高薪资");
        }
        JobPreference preference = jobPreferenceMapper.selectById(studentId);
        if (preference == null) preference = new JobPreference();
        preference.studentId = studentId;
        preference.expectedJob = trim(request.expectedJob());
        preference.expectedCity = normalizeCity(request.expectedCity());
        preference.expectedIndustry = trim(request.expectedIndustry());
        preference.salaryMin = request.salaryMin();
        preference.salaryMax = request.salaryMax();
        preference.acceptRemoteCity = Boolean.TRUE.equals(request.acceptRemoteCity());
        if (jobPreferenceMapper.selectById(studentId) == null) jobPreferenceMapper.insert(preference);
        else jobPreferenceMapper.updateById(preference);
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

    private String trim(String value) { return value == null ? "" : value.trim(); }
    private String normalizeCity(String value) {
        String normalized = trim(value).replaceFirst("市+$", "");
        return "中国".equals(normalized) ? "全国" : normalized;
    }
    private String emptyToNull(String value) {
        String trimmed = trim(value);
        return trimmed.isEmpty() ? null : trimmed;
    }
}
