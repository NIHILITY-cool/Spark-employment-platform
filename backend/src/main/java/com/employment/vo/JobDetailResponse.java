package com.employment.vo;

import com.employment.entity.Job;
import com.employment.entity.JobSkill;
import java.util.List;

public record JobDetailResponse(Job job, List<JobSkill> skills) {
}
