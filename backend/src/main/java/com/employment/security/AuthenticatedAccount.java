package com.employment.security;

public record AuthenticatedAccount(Long id, String role, String username, String displayName,
                                   Long studentId, boolean enabled) {
}
