package com.employment.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

public record StudentProfileRequest(String studentNo, @NotBlank String name, @NotBlank String college,
                                    @NotBlank String major, @NotBlank String education,
                                    @NotNull @Max(2100) Integer graduationYear) {
}
