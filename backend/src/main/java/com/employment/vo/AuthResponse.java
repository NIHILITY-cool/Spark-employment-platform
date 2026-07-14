package com.employment.vo;

import java.time.LocalDateTime;

public record AuthResponse(String token, LocalDateTime expiresAt, AccountView account) {
}
