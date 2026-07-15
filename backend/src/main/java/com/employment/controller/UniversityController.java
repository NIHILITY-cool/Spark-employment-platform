package com.employment.controller;

import com.employment.dto.IndustrySalaryResponse;
import com.employment.dto.UniversityMarketDashboardResponse;
import com.employment.service.UniversityAnalysisService;
import com.employment.service.UniversityStudentInsightService;
import com.employment.vo.UniversityStudentInsightResponse;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/university")
public class UniversityController {
    private final UniversityAnalysisService universityAnalysisService;
    private final UniversityStudentInsightService studentInsightService;

    public UniversityController(UniversityAnalysisService universityAnalysisService,
                                UniversityStudentInsightService studentInsightService) {
        this.universityAnalysisService = universityAnalysisService;
        this.studentInsightService = studentInsightService;
    }

    @GetMapping("/students")
    public UniversityStudentInsightResponse students(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size,
            @RequestParam(required = false) String keyword,
            @RequestParam(defaultValue = "all") String status) {
        return studentInsightService.overview(page, size, keyword, status);
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

    @GetMapping("/industry-salary-distribution")
    public IndustrySalaryResponse industrySalaryDistribution(@RequestParam(required = false) String city) {
        return universityAnalysisService.industrySalaryDistribution(city);
    }
}
