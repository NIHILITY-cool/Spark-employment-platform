package com.employment.controller;

import com.employment.dto.MarketOverview;
import com.employment.entity.MarketStatistic;
import com.employment.service.MarketQueryService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import java.time.LocalDate;
import java.util.List;

@RestController
@RequestMapping("/api/market")
public class MarketStatisticController {
    private final MarketQueryService marketQueryService;
    public MarketStatisticController(MarketQueryService marketQueryService) { this.marketQueryService = marketQueryService; }

    @GetMapping("/statistics/{type}")
    public List<MarketStatistic> statistics(@PathVariable String type, @RequestParam(defaultValue = "2026-07-11") LocalDate date) {
        return marketQueryService.statistics(type, date);
    }

    @GetMapping("/overview")
    public MarketOverview overview(@RequestParam(defaultValue = "2026-07-11") LocalDate date) {
        return marketQueryService.overview(date);
    }
}
