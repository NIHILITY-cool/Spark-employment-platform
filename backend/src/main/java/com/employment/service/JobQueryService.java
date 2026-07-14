package com.employment.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.employment.common.LocationScope;
import com.employment.dto.JobFilterOptions;
import com.employment.entity.Job;
import com.employment.mapper.JobMapper;
import com.employment.vo.JobDetailResponse;
import com.employment.vo.PageResponse;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;
import org.springframework.web.server.ResponseStatusException;
import java.util.List;
import java.util.Map;

@Service
public class JobQueryService {
    private final JobMapper jobMapper;

    public JobQueryService(JobMapper jobMapper) {
        this.jobMapper = jobMapper;
    }

    public PageResponse<Job> list(long page, long size, String keyword, String city, String category,
                                  Integer minSalary, Integer maxSalary) {
        if (minSalary != null && maxSalary != null && minSalary > maxSalary) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "最低薪资不能高于最高薪资");
        }
        long safePage = Math.max(page, 1);
        long safeSize = Math.min(Math.max(size, 1), 100);
        QueryWrapper<Job> query = new QueryWrapper<Job>().eq("job_status", "active");
        if (StringUtils.hasText(keyword)) {
            String trimmed = keyword.trim();
            query.and(w -> w.like("job_name", trimmed).or().like("company_name", trimmed));
        }
        if (StringUtils.hasText(city)) query.eq("city", normalizeCity(city));
        if (StringUtils.hasText(category)) query.eq("job_category", category.trim());
        if (minSalary != null) query.ge("salary_max", minSalary);
        if (maxSalary != null) query.le("salary_min", maxSalary);
        query.orderByDesc("last_seen_date").orderByDesc("salary_max").orderByAsc("job_key");
        Page<Job> result = jobMapper.selectPage(new Page<>(safePage, safeSize), query);
        return new PageResponse<>(result.getCurrent(), result.getSize(), result.getTotal(), result.getRecords());
    }

    public JobDetailResponse detail(String jobKey) {
        Job job = jobMapper.selectById(jobKey);
        if (job == null || !"active".equals(job.jobStatus)) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "岗位不存在或已失效");
        }
        return new JobDetailResponse(job);
    }

    public JobFilterOptions filters() {
        List<String> cities = jobMapper.selectObjs(new QueryWrapper<Job>().select("DISTINCT city")
                        .eq("job_status", "active").ne("city", "").orderByAsc("city"))
                .stream().map(String::valueOf).filter(LocationScope::isCity).toList();
        List<String> categories = jobMapper.selectObjs(new QueryWrapper<Job>().select("DISTINCT job_category")
                        .eq("job_status", "active").ne("job_category", "").orderByAsc("job_category"))
                .stream().map(String::valueOf).toList();
        return new JobFilterOptions(cities, categories);
    }

    private String normalizeCity(String city) {
        String normalized = city.trim().replaceFirst("市+$", "");
        return "中国".equals(normalized) ? "全国" : normalized;
    }
}
