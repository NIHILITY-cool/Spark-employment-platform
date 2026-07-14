package com.employment.controller;

import com.employment.service.RecommendationService;
import com.employment.service.AuthService;
import com.employment.vo.JobRecommendation;
import com.employment.vo.SkillGapResponse;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import java.util.List;

@RestController
@RequestMapping("/api/recommendations")
public class RecommendationController {
    private final RecommendationService recommendationService;
    private final AuthService authService;

    public RecommendationController(RecommendationService recommendationService, AuthService authService) {
        this.recommendationService = recommendationService;
        this.authService = authService;
    }

    @GetMapping("/top10")
    public List<JobRecommendation> top10(@RequestParam Long studentId, @RequestParam(defaultValue = "10") int limit) {
        authService.requireStudentAccess(studentId);
        return recommendationService.top(studentId, limit);
    }

    @GetMapping("/{jobKey}/match")
    public JobRecommendation match(@PathVariable String jobKey, @RequestParam Long studentId) {
        authService.requireStudentAccess(studentId);
        return recommendationService.match(studentId, jobKey);
    }

    @GetMapping("/skill-gap")
    public SkillGapResponse skillGap(@RequestParam Long studentId) {
        authService.requireStudentAccess(studentId);
        return recommendationService.skillGap(studentId);
    }
}
