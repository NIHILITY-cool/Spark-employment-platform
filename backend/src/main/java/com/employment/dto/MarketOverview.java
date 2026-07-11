package com.employment.dto;

import com.employment.entity.MarketStatistic;
import java.time.LocalDate;
import java.util.List;

public record MarketOverview(LocalDate statDate, List<MarketStatistic> cities, List<MarketStatistic> industries,
                             List<MarketStatistic> education, List<MarketStatistic> experience,
                             List<MarketStatistic> hotJobs, List<MarketStatistic> hotSkills) {
}
