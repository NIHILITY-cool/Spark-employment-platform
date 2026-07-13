package com.employment.controller;

import com.employment.entity.Job;
import com.employment.dto.JobFilterOptions;
import com.employment.service.JobQueryService;
import com.employment.vo.JobDetailResponse;
import com.employment.vo.PageResponse;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/jobs")
public class JobController {
    private final JobQueryService jobQueryService;

    public JobController(JobQueryService jobQueryService) {
        this.jobQueryService = jobQueryService;
    }

    @GetMapping
    public PageResponse<Job> list(
            @RequestParam(defaultValue = "1") long page,
            @RequestParam(defaultValue = "20") long size,
            @RequestParam(required = false) String keyword,
            @RequestParam(required = false) String city,
            @RequestParam(required = false) String category,
            @RequestParam(required = false) Integer minSalary,
            @RequestParam(required = false) Integer maxSalary) {
        return jobQueryService.list(page, size, keyword, city, category, minSalary, maxSalary);
    }

    @GetMapping("/{jobKey}")
    public JobDetailResponse detail(@PathVariable String jobKey) {
        return jobQueryService.detail(jobKey);
    }

    @GetMapping("/filters")
    public JobFilterOptions filters() {
        return jobQueryService.filters();
    }
}
