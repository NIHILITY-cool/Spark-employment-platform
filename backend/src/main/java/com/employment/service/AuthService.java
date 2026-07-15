package com.employment.service;

import com.employment.dto.LoginRequest;
import com.employment.dto.StudentRegistrationRequest;
import com.employment.security.AuthenticatedAccount;
import com.employment.vo.AccountView;
import com.employment.vo.AdminAccountView;
import com.employment.vo.AuthResponse;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.http.HttpStatus;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.support.GeneratedKeyHolder;
import org.springframework.jdbc.support.KeyHolder;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;
import org.springframework.web.server.ResponseStatusException;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.security.SecureRandom;
import java.sql.PreparedStatement;
import java.sql.Statement;
import java.time.LocalDateTime;
import java.time.Duration;
import java.time.Year;
import java.util.Base64;
import java.util.List;
import java.util.Locale;
import java.util.Optional;

@Service
public class AuthService {
    private static final int SESSION_DAYS = 7;
    private static final List<String> ROLES = List.of("STUDENT", "UNIVERSITY", "ADMIN");
    private final JdbcTemplate jdbc;
    private final PasswordEncoder passwordEncoder;
    private final RedisSessionStore sessionStore;
    private final StudentInsightCache studentInsightCache;
    private final SecureRandom secureRandom = new SecureRandom();

    public AuthService(JdbcTemplate jdbc, PasswordEncoder passwordEncoder, RedisSessionStore sessionStore,
                       StudentInsightCache studentInsightCache) {
        this.jdbc = jdbc;
        this.passwordEncoder = passwordEncoder;
        this.sessionStore = sessionStore;
        this.studentInsightCache = studentInsightCache;
    }

    @Transactional
    public AuthResponse registerStudent(StudentRegistrationRequest request) {
        String studentNo = request.studentNo().trim();
        String name = request.name().trim();
        if (studentNo.length() > 64 || name.length() > 64) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "学号或姓名长度超出限制");
        }
        try {
            KeyHolder studentKey = new GeneratedKeyHolder();
            jdbc.update(connection -> {
                PreparedStatement statement = connection.prepareStatement("""
                        INSERT INTO student(student_no, name, college, major, education, graduation_year, profile_completed)
                        VALUES (?, ?, '待完善', '待完善', '待完善', ?, 0)
                        """, Statement.RETURN_GENERATED_KEYS);
                statement.setString(1, studentNo);
                statement.setString(2, name);
                statement.setInt(3, Year.now().getValue() + 1);
                return statement;
            }, studentKey);
            Long studentId = requiredKey(studentKey);
            KeyHolder accountKey = new GeneratedKeyHolder();
            jdbc.update(connection -> {
                PreparedStatement statement = connection.prepareStatement("""
                        INSERT INTO platform_account(role, username, password_hash, display_name, student_id)
                        VALUES ('STUDENT', ?, ?, ?, ?)
                        """, Statement.RETURN_GENERATED_KEYS);
                statement.setString(1, studentNo);
                statement.setString(2, passwordEncoder.encode(request.password()));
                statement.setString(3, name);
                statement.setLong(4, studentId);
                return statement;
            }, accountKey);
            studentInsightCache.invalidateAfterCommit();
            return createSession(new AuthenticatedAccount(requiredKey(accountKey), "STUDENT", studentNo, name, studentId, true));
        } catch (DuplicateKeyException exception) {
            throw new ResponseStatusException(HttpStatus.CONFLICT, "该学号已注册");
        }
    }

    public AuthResponse login(LoginRequest request) {
        String role = request.role().trim().toUpperCase(Locale.ROOT);
        if (!ROLES.contains(role)) throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "登录角色无效");
        AccountRow row = jdbc.query("""
                        SELECT id, role, username, password_hash, display_name, student_id, enabled
                        FROM platform_account WHERE username = ? AND role = ?
                        """, rs -> rs.next() ? accountRow(rs) : null, request.username().trim(), role);
        if (row == null || !row.enabled() || !passwordEncoder.matches(request.password(), row.passwordHash())) {
            throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "账号或密码不正确");
        }
        return createSession(row.account());
    }

    public Optional<AuthenticatedAccount> authenticate(String token) {
        if (!StringUtils.hasText(token)) return Optional.empty();
        String tokenHash = hash(token);
        Optional<AuthenticatedAccount> cached = sessionStore.find(tokenHash);
        if (cached.isPresent()) return cached;
        SessionRow session = jdbc.query("""
                        SELECT a.id, a.role, a.username, a.display_name, a.student_id, a.enabled
                             , s.expires_at
                        FROM auth_session s JOIN platform_account a ON a.id = s.account_id
                        WHERE s.token_hash = ? AND s.expires_at > NOW() AND a.enabled = 1
                        """, rs -> rs.next() ? new SessionRow(account(rs), rs.getTimestamp("expires_at").toLocalDateTime()) : null,
                tokenHash);
        if (session == null) return Optional.empty();
        sessionStore.put(tokenHash, session.account(), Duration.between(LocalDateTime.now(), session.expiresAt()));
        return Optional.of(session.account());
    }

    public AccountView me() {
        return view(currentAccount());
    }

    public void logout(String token) {
        if (!StringUtils.hasText(token)) return;
        String tokenHash = hash(token);
        jdbc.update("DELETE FROM auth_session WHERE token_hash = ?", tokenHash);
        sessionStore.evict(tokenHash);
    }

    public List<AdminAccountView> accounts() {
        return jdbc.query("""
                SELECT id, role, username, display_name, student_id, enabled, updated_at
                FROM platform_account
                WHERE role IN ('UNIVERSITY', 'STUDENT')
                ORDER BY FIELD(role, 'UNIVERSITY', 'STUDENT'), updated_at DESC
                """, (rs, rowNum) -> new AdminAccountView(rs.getLong("id"), rs.getString("role"),
                rs.getString("username"), rs.getString("display_name"), nullableLong(rs, "student_id"),
                rs.getBoolean("enabled"), rs.getTimestamp("updated_at").toLocalDateTime()));
    }

    @Transactional
    public void resetPassword(Long accountId, String password) {
        requireStudentAccountTarget(accountId);
        jdbc.update("UPDATE platform_account SET password_hash = ? WHERE id = ? AND role = 'STUDENT'",
                passwordEncoder.encode(password), accountId);
        deleteAccountSessions(accountId);
    }

    @Transactional
    public void setEnabled(Long accountId, boolean enabled) {
        requireStudentAccountTarget(accountId);
        jdbc.update("UPDATE platform_account SET enabled = ? WHERE id = ? AND role = 'STUDENT'", enabled, accountId);
        if (!enabled) deleteAccountSessions(accountId);
        studentInsightCache.invalidateAfterCommit();
    }

    private void requireStudentAccountTarget(Long accountId) {
        String role = jdbc.query("SELECT role FROM platform_account WHERE id = ?",
                rs -> rs.next() ? rs.getString("role") : null, accountId);
        if (role == null) throw new ResponseStatusException(HttpStatus.NOT_FOUND, "账号不存在");
        if (!"STUDENT".equals(role)) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "该操作仅适用于学生账号");
        }
    }

    @Transactional
    public void updateUniversityCredential(String username, String password) {
        Long accountId = jdbc.query("SELECT id FROM platform_account WHERE role = 'UNIVERSITY' LIMIT 1",
                rs -> rs.next() ? rs.getLong(1) : null);
        if (accountId == null) throw new ResponseStatusException(HttpStatus.NOT_FOUND, "高校账号不存在");
        try {
            jdbc.update("UPDATE platform_account SET username = ?, password_hash = ?, display_name = '高校就业中心' WHERE id = ?",
                    username.trim(), passwordEncoder.encode(password), accountId);
        } catch (DuplicateKeyException exception) {
            throw new ResponseStatusException(HttpStatus.CONFLICT, "该账号名已被使用");
        }
        deleteAccountSessions(accountId);
    }

    @Transactional
    public void seedSystemAccounts() {
        seed("ADMIN", "admin", "1024", "系统管理员");
        seed("UNIVERSITY", "university", "1024", "高校就业中心");
    }

    public void requireStudentAccess(Long studentId) {
        AuthenticatedAccount account = currentAccount();
        if ("ADMIN".equals(account.role())) return;
        if (!"STUDENT".equals(account.role()) || account.studentId() == null || !account.studentId().equals(studentId)) {
            throw new ResponseStatusException(HttpStatus.FORBIDDEN, "无权访问其他学生数据");
        }
    }

    public void requireAdmin() {
        if (!"ADMIN".equals(currentAccount().role())) {
            throw new ResponseStatusException(HttpStatus.FORBIDDEN, "需要管理员权限");
        }
    }

    public AuthenticatedAccount currentAccount() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        if (authentication == null || !(authentication.getPrincipal() instanceof AuthenticatedAccount account)) {
            throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "请先登录");
        }
        return account;
    }

    private void seed(String role, String username, String password, String displayName) {
        Integer count = jdbc.queryForObject("SELECT COUNT(*) FROM platform_account WHERE role = ?", Integer.class, role);
        if (count != null && count > 0) return;
        jdbc.update("INSERT INTO platform_account(role, username, password_hash, display_name) VALUES (?, ?, ?, ?)",
                role, username, passwordEncoder.encode(password), displayName);
    }

    private AuthResponse createSession(AuthenticatedAccount account) {
        byte[] bytes = new byte[32];
        secureRandom.nextBytes(bytes);
        String token = Base64.getUrlEncoder().withoutPadding().encodeToString(bytes);
        LocalDateTime expiresAt = LocalDateTime.now().plusDays(SESSION_DAYS);
        deleteAccountSessions(account.id());
        jdbc.update("DELETE FROM auth_session WHERE expires_at <= NOW()");
        jdbc.update("INSERT INTO auth_session(account_id, token_hash, expires_at) VALUES (?, ?, ?)",
                account.id(), hash(token), expiresAt);
        return new AuthResponse(token, expiresAt, view(account));
    }

    private static String hash(String token) {
        try {
            byte[] digest = MessageDigest.getInstance("SHA-256").digest(token.getBytes(StandardCharsets.UTF_8));
            return java.util.HexFormat.of().formatHex(digest);
        } catch (NoSuchAlgorithmException exception) {
            throw new IllegalStateException(exception);
        }
    }

    private void deleteAccountSessions(Long accountId) {
        List<String> tokenHashes = jdbc.queryForList(
                "SELECT token_hash FROM auth_session WHERE account_id = ?", String.class, accountId);
        jdbc.update("DELETE FROM auth_session WHERE account_id = ?", accountId);
        sessionStore.evictAll(tokenHashes);
    }

    private static Long requiredKey(KeyHolder holder) {
        Number key = holder.getKey();
        if (key == null) throw new IllegalStateException("未生成数据主键");
        return key.longValue();
    }

    private static AuthenticatedAccount account(java.sql.ResultSet rs) throws java.sql.SQLException {
        return new AuthenticatedAccount(rs.getLong("id"), rs.getString("role"), rs.getString("username"),
                rs.getString("display_name"), nullableLong(rs, "student_id"), rs.getBoolean("enabled"));
    }

    private static AccountRow accountRow(java.sql.ResultSet rs) throws java.sql.SQLException {
        return new AccountRow(account(rs), rs.getString("password_hash"), rs.getBoolean("enabled"));
    }

    private static Long nullableLong(java.sql.ResultSet rs, String column) throws java.sql.SQLException {
        long value = rs.getLong(column);
        return rs.wasNull() ? null : value;
    }

    private static AccountView view(AuthenticatedAccount account) {
        return new AccountView(account.id(), account.role(), account.username(), account.displayName(),
                account.studentId(), account.enabled());
    }

    private record AccountRow(AuthenticatedAccount account, String passwordHash, boolean enabled) {
    }

    private record SessionRow(AuthenticatedAccount account, LocalDateTime expiresAt) {
    }
}
