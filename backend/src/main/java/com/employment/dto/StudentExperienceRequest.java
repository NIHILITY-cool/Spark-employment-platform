package com.employment.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import java.time.LocalDate;

public record StudentExperienceRequest(
        @NotBlank @Pattern(regexp = "project|internship|award", message = "经历类型必须是 project、internship 或 award")
        String experienceType,
        @NotBlank @Size(max = 180) String title,
        @Size(max = 180) String organization,
        @Size(max = 120) String role,
        @NotBlank @Size(max = 4000) String description,
        LocalDate startDate,
        LocalDate endDate) {
}
