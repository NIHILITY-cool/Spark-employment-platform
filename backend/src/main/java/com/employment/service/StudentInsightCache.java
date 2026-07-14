package com.employment.service;

import com.employment.vo.UniversityStudentInsightResponse;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Component;
import org.springframework.transaction.support.TransactionSynchronization;
import org.springframework.transaction.support.TransactionSynchronizationManager;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Duration;
import java.util.HexFormat;
import java.util.function.Supplier;

@Component
public class StudentInsightCache {
    private static final Logger log = LoggerFactory.getLogger(StudentInsightCache.class);
    private static final String KEY_PREFIX = "employment:university:students:";
    private static final String VERSION_KEY = KEY_PREFIX + "version";
    private static final Duration TTL = Duration.ofMinutes(5);

    private final StringRedisTemplate redis;
    private final ObjectMapper objectMapper;

    public StudentInsightCache(StringRedisTemplate redis, ObjectMapper objectMapper) {
        this.redis = redis;
        this.objectMapper = objectMapper;
    }

    public UniversityStudentInsightResponse getOrLoad(int page, int size, String keyword, String status,
                                                       Supplier<UniversityStudentInsightResponse> loader) {
        String version = null;
        try {
            version = currentVersion();
            String cached = redis.opsForValue().get(key(version, page, size, keyword, status));
            if (cached != null) {
                log.debug("Student insight cache hit: page={}, size={}, status={}", page, size, status);
                return objectMapper.readValue(cached, UniversityStudentInsightResponse.class);
            }
            log.info("Student insight cache miss; loading from MySQL: page={}, size={}, status={}",
                    page, size, status);
        } catch (RuntimeException | JsonProcessingException exception) {
            log.debug("Student insight cache lookup unavailable; using MySQL fallback", exception);
        }

        UniversityStudentInsightResponse response = loader.get();
        if (version != null) {
            try {
                redis.opsForValue().set(key(version, page, size, keyword, status),
                        objectMapper.writeValueAsString(response), TTL);
            } catch (RuntimeException | JsonProcessingException exception) {
                log.debug("Student insight cache write unavailable", exception);
            }
        }
        return response;
    }

    public void invalidateAfterCommit() {
        if (TransactionSynchronizationManager.isSynchronizationActive()) {
            TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {
                @Override
                public void afterCommit() {
                    invalidate();
                }
            });
            return;
        }
        invalidate();
    }

    public void invalidate() {
        try {
            Long version = redis.opsForValue().increment(VERSION_KEY);
            log.info("Student insight cache invalidated: version={}", version);
        } catch (RuntimeException exception) {
            log.debug("Student insight cache invalidation unavailable; cached pages will expire by TTL", exception);
        }
    }

    private String currentVersion() {
        String version = redis.opsForValue().get(VERSION_KEY);
        return version == null ? "0" : version;
    }

    private static String key(String version, int page, int size, String keyword, String status) {
        return KEY_PREFIX + "v" + version + ":" + page + ":" + size + ":" + status + ":" + digest(keyword);
    }

    private static String digest(String value) {
        try {
            return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256")
                    .digest(value.getBytes(StandardCharsets.UTF_8)));
        } catch (NoSuchAlgorithmException exception) {
            throw new IllegalStateException("SHA-256 is unavailable", exception);
        }
    }
}
