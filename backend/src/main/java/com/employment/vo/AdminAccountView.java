package com.employment.vo;

import java.time.LocalDateTime;

public record AdminAccountView(Long id, String role, String username, String displayName,
                               Long studentId, boolean enabled, LocalDateTime updatedAt) {
}
