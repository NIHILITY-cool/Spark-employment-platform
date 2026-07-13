package com.employment.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.employment.common.LocationScope;
import com.employment.dto.MarketOverview;
import com.employment.entity.MarketStatistic;
import com.employment.mapper.MarketStatisticMapper;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;
import java.time.LocalDate;
import java.util.List;
import java.util.Set;

@Service
public class MarketQueryService {
    private static final Set<String> TYPES = Set.of("city_distribution", "industry_distribution",
            "education_distribution", "experience_distribution", "hot_jobs", "hot_skills", "source_distribution");
    private final MarketStatisticMapper marketStatisticMapper;

    public MarketQueryService(MarketStatisticMapper marketStatisticMapper) {
        this.marketStatisticMapper = marketStatisticMapper;
    }

    public List<MarketStatistic> statistics(String type, LocalDate date) {
        if (!TYPES.contains(type)) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "不支持的统计类型: " + type);
        }
        return query(type, date);
    }

    public MarketOverview overview(LocalDate date) {
        return new MarketOverview(date, query("city_distribution", date), query("industry_distribution", date),
                query("education_distribution", date), query("experience_distribution", date),
                query("hot_jobs", date), query("hot_skills", date));
    }

    private List<MarketStatistic> query(String type, LocalDate date) {
        List<MarketStatistic> statistics = marketStatisticMapper.selectList(new QueryWrapper<MarketStatistic>()
                .eq("stat_type", type).eq("stat_date", date)
                .orderByDesc("metric_value").orderByAsc("dimension_key"));
        return "city_distribution".equals(type)
                ? statistics.stream().filter(item -> LocationScope.isCity(item.dimensionKey)).toList()
                : statistics;
    }
}
