package com.employment.vo;

public record AccountView(Long id, String role, String username, String displayName,
                          Long studentId, boolean enabled) {
}
