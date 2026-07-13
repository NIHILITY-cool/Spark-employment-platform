package com.employment.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

public record StudentSkillRequest(@NotBlank String skillName, @NotNull @Min(1) @Max(5) Integer skillLevel) {
}
