package com.employment.controller;

import com.employment.dto.AccountStatusRequest;
import com.employment.dto.PasswordResetRequest;
import com.employment.dto.UniversityCredentialRequest;
import com.employment.service.AuthService;
import com.employment.vo.AdminAccountView;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/admin")
public class AdminController {
    private final AuthService authService;

    public AdminController(AuthService authService) {
        this.authService = authService;
    }

    @GetMapping("/accounts")
    public List<AdminAccountView> accounts() {
        return authService.accounts();
    }

    @PutMapping("/accounts/{accountId}/password")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void resetPassword(@PathVariable Long accountId, @Valid @RequestBody PasswordResetRequest request) {
        authService.resetPassword(accountId, request.password());
    }

    @PutMapping("/accounts/{accountId}/status")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void status(@PathVariable Long accountId, @Valid @RequestBody AccountStatusRequest request) {
        authService.setEnabled(accountId, request.enabled());
    }

    @PutMapping("/university-credential")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void universityCredential(@Valid @RequestBody UniversityCredentialRequest request) {
        authService.updateUniversityCredential(request.username(), request.password());
    }
}
