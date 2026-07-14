package com.employment.service;

import com.employment.security.AuthenticatedAccount;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Component;

import java.time.Duration;
import java.util.Collection;
import java.util.Optional;

@Component
public class RedisSessionStore {
    private static final Logger log = LoggerFactory.getLogger(RedisSessionStore.class);
    private static final String KEY_PREFIX = "employment:session:";
    private final StringRedisTemplate redis;
    private final ObjectMapper objectMapper;

    public RedisSessionStore(StringRedisTemplate redis, ObjectMapper objectMapper) {
        this.redis = redis;
        this.objectMapper = objectMapper;
    }

    public Optional<AuthenticatedAccount> find(String tokenHash) {
        try {
            String value = redis.opsForValue().get(key(tokenHash));
            if (value == null) return Optional.empty();
            return Optional.of(objectMapper.readValue(value, AuthenticatedAccount.class));
        } catch (RuntimeException | JsonProcessingException exception) {
            log.debug("Redis session lookup unavailable; using MySQL fallback", exception);
            return Optional.empty();
        }
    }

    public void put(String tokenHash, AuthenticatedAccount account, Duration ttl) {
        if (ttl.isZero() || ttl.isNegative()) return;
        try {
            redis.opsForValue().set(key(tokenHash), objectMapper.writeValueAsString(account), ttl);
        } catch (RuntimeException | JsonProcessingException exception) {
            log.debug("Redis session write unavailable", exception);
        }
    }

    public void evict(String tokenHash) {
        try {
            redis.delete(key(tokenHash));
        } catch (RuntimeException exception) {
            log.debug("Redis session eviction unavailable", exception);
        }
    }

    public void evictAll(Collection<String> tokenHashes) {
        if (tokenHashes.isEmpty()) return;
        try {
            redis.delete(tokenHashes.stream().map(RedisSessionStore::key).toList());
        } catch (RuntimeException exception) {
            log.debug("Redis session eviction unavailable", exception);
        }
    }

    private static String key(String tokenHash) {
        return KEY_PREFIX + tokenHash;
    }
}
