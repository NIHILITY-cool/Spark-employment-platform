package com.employment.controller;

import com.employment.dto.IndustrySalaryResponse;
import com.employment.dto.TrainingAlignmentResponse;
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

    @GetMapping("/training-alignment")
    public TrainingAlignmentResponse trainingAlignment(
            @RequestParam(defaultValue = "数据科学与大数据技术") String major,
            @RequestParam(required = false) String city) {
        return universityAnalysisService.trainingAlignment(major, city);
    }

    @GetMapping("/industry-salary-distribution")
    public IndustrySalaryResponse industrySalaryDistribution(@RequestParam(required = false) String city) {
        return universityAnalysisService.industrySalaryDistribution(city);
    }
}
