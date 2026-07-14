package com.employment.controller;

import com.employment.dto.TrainingAlignmentResponse;
import com.employment.dto.UniversityMarketDashboardResponse;
import com.employment.service.UniversityAnalysisService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/university")
public class UniversityController {
    private final UniversityAnalysisService universityAnalysisService;

    public UniversityController(UniversityAnalysisService universityAnalysisService) {
        this.universityAnalysisService = universityAnalysisService;
    }

    @GetMapping("/market-dashboard")
    public UniversityMarketDashboardResponse marketDashboard(
            @RequestParam(required = false) String city,
            @RequestParam(required = false) String industry,
            @RequestParam(required = false) String education,
            @RequestParam(required = false) String category,
            @RequestParam(required = false) String companyScale,
            @RequestParam(required = false) String keyword,
            @RequestParam(required = false) Integer minSalary,
            @RequestParam(required = false) Integer maxSalary) {
        return universityAnalysisService.marketDashboard(city, industry, education, category,
                companyScale, keyword, minSalary, maxSalary);
    }

    @GetMapping("/training-alignment")
    public TrainingAlignmentResponse trainingAlignment(
            @RequestParam(defaultValue = "数据科学与大数据技术") String major,
            @RequestParam(required = false) String city) {
        return universityAnalysisService.trainingAlignment(major, city);
    }
}
