package com.employment.vo;

import com.employment.entity.JobPreference;
import com.employment.entity.Student;
import com.employment.entity.StudentExperience;
import com.employment.entity.StudentSkill;
import java.util.List;

public record StudentProfileResponse(Student profile, List<StudentSkill> skills,
                                     List<StudentExperience> experiences, JobPreference preference) {
}
