package com.employment.controller;

import com.employment.service.RecommendationService;
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

    public RecommendationController(RecommendationService recommendationService) { this.recommendationService = recommendationService; }

    @GetMapping("/top10")
    public List<JobRecommendation> top10(@RequestParam Long studentId, @RequestParam(defaultValue = "10") int limit) {
        return recommendationService.top(studentId, limit);
    }

    @GetMapping("/{jobKey}/match")
    public JobRecommendation match(@PathVariable String jobKey, @RequestParam Long studentId) {
        return recommendationService.match(studentId, jobKey);
    }

    @GetMapping("/skill-gap")
    public SkillGapResponse skillGap(@RequestParam Long studentId) { return recommendationService.skillGap(studentId); }
}
