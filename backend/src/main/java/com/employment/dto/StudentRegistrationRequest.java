package com.employment.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record StudentRegistrationRequest(@NotBlank String studentNo, @NotBlank String name,
                                         @NotBlank @Size(min = 6, max = 72) String password) {
}
