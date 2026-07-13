package com.employment.vo;

import java.util.List;

public record SkillGapResponse(Long studentId, List<String> masteredSkills, List<String> missingSkills,
                               String suggestion) {
}
