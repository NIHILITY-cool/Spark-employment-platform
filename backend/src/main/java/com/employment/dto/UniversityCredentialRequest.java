package com.employment.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record UniversityCredentialRequest(@NotBlank String username,
                                          @NotBlank @Size(min = 6, max = 72) String password) {
}
