package com.employment.controller;

import com.employment.dto.JobPreferenceRequest;
import com.employment.dto.StudentProfileRequest;
import com.employment.dto.StudentExperienceRequest;
import com.employment.dto.StudentSkillRequest;
import com.employment.entity.JobPreference;
import com.employment.entity.Student;
import com.employment.entity.StudentExperience;
import com.employment.entity.StudentSkill;
import com.employment.service.StudentProfileService;
import com.employment.service.AuthService;
import com.employment.vo.StudentProfileResponse;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/students")
public class StudentController {
    private final StudentProfileService studentProfileService;
    private final AuthService authService;

    public StudentController(StudentProfileService studentProfileService, AuthService authService) {
        this.studentProfileService = studentProfileService;
        this.authService = authService;
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public Student create(@Valid @RequestBody StudentProfileRequest request) {
        authService.requireAdmin();
        return studentProfileService.create(request);
    }

    @GetMapping("/{studentId}/profile")
    public StudentProfileResponse profile(@PathVariable Long studentId) {
        authService.requireStudentAccess(studentId);
        return studentProfileService.profile(studentId);
    }

    @PutMapping("/{studentId}/profile")
    public Student update(@PathVariable Long studentId, @Valid @RequestBody StudentProfileRequest request) {
        authService.requireStudentAccess(studentId);
        return studentProfileService.update(studentId, request);
    }

    @PostMapping("/{studentId}/skills")
    @ResponseStatus(HttpStatus.CREATED)
    public StudentSkill addSkill(@PathVariable Long studentId, @Valid @RequestBody StudentSkillRequest request) {
        authService.requireStudentAccess(studentId);
        return studentProfileService.addSkill(studentId, request);
    }

    @DeleteMapping("/{studentId}/skills/{skillId}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void deleteSkill(@PathVariable Long studentId, @PathVariable Long skillId) {
        authService.requireStudentAccess(studentId);
        studentProfileService.deleteSkill(studentId, skillId);
    }

    @PostMapping("/{studentId}/experiences")
    @ResponseStatus(HttpStatus.CREATED)
    public StudentExperience addExperience(@PathVariable Long studentId,
                                           @Valid @RequestBody StudentExperienceRequest request) {
        authService.requireStudentAccess(studentId);
        return studentProfileService.addExperience(studentId, request);
    }

    @PutMapping("/{studentId}/experiences/{experienceId}")
    public StudentExperience updateExperience(@PathVariable Long studentId, @PathVariable Long experienceId,
                                              @Valid @RequestBody StudentExperienceRequest request) {
        authService.requireStudentAccess(studentId);
        return studentProfileService.updateExperience(studentId, experienceId, request);
    }

    @DeleteMapping("/{studentId}/experiences/{experienceId}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void deleteExperience(@PathVariable Long studentId, @PathVariable Long experienceId) {
        authService.requireStudentAccess(studentId);
        studentProfileService.deleteExperience(studentId, experienceId);
    }

    @PutMapping("/{studentId}/preference")
    public JobPreference savePreference(@PathVariable Long studentId, @Valid @RequestBody JobPreferenceRequest request) {
        authService.requireStudentAccess(studentId);
        return studentProfileService.savePreference(studentId, request);
    }
}
