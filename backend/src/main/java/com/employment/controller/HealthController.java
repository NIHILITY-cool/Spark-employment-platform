package com.employment.controller;

import com.employment.mapper.JobMapper;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import java.time.LocalDate;
import java.util.Map;

@RestController
@RequestMapping("/api")
public class HealthController {
    private final JobMapper jobMapper;

    public HealthController(JobMapper jobMapper) {
        this.jobMapper = jobMapper;
    }

    @GetMapping("/health")
    public Map<String, Object> health() {
        return Map.of(
                "status", "UP",
                "service", "spark-employment-platform",
                "time", LocalDate.now().toString(),
                "jobCount", jobMapper.selectCount(null));
    }
}
