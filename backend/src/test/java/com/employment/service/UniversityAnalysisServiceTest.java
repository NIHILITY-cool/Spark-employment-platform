package com.employment.service;

import com.employment.dto.DemandMetric;
import com.employment.dto.TrainingDemandSummary;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class UniversityAnalysisServiceTest {
    @Test
    void exposesTheFiveSupportedMajorDirections() {
        assertEquals("大数据开发", UniversityAnalysisService.majorCategories().get("数据科学与大数据技术"));
        assertEquals(5, UniversityAnalysisService.majorCategories().size());
    }

    @Test
    void suggestionsUseMarketEvidenceAndAvoidQualityClaims() {
        TrainingDemandSummary summary = new TrainingDemandSummary(100, 20, 8000.0, 12000.0, 3);
        List<String> suggestions = UniversityAnalysisService.suggestions(summary,
                List.of(new DemandMetric("SQL", 50, null, null)),
                List.of(new DemandMetric("成都", 30, null, null)), "");
        assertTrue(suggestions.stream().anyMatch(item -> item.contains("SQL")));
        assertTrue(suggestions.stream().anyMatch(item -> item.contains("低经验门槛")));
        assertTrue(suggestions.stream().noneMatch(item -> item.contains("培养质量")));
    }

    @Test
    void classifiesIndustriesFromJobNamesAndDescriptionsInRuleOrder() {
        assertEquals("金融", UniversityAnalysisService.classifyIndustry("银行风控专员", "负责信贷模型"));
        assertEquals("商贸与消费", UniversityAnalysisService.classifyIndustry("品牌运营", "负责电商销售"));
        assertEquals("医药生物", UniversityAnalysisService.classifyIndustry("临床研究员", "生物制药方向"));
        assertEquals("科技", UniversityAnalysisService.classifyIndustry("后端开发工程师", "Java 软件开发"));
        assertEquals("制造业", UniversityAnalysisService.classifyIndustry("机械工程师", "汽车生产设备"));
        assertEquals("农业与食品", UniversityAnalysisService.classifyIndustry("食品研发", "农产品加工"));
        assertEquals("服务业", UniversityAnalysisService.classifyIndustry("酒店前台", "旅游服务"));
        assertEquals("建筑与房地产", UniversityAnalysisService.classifyIndustry("造价工程师", "建筑施工"));
        assertEquals("教育", UniversityAnalysisService.classifyIndustry("课程教研", "高校教师"));
        assertEquals("其他", UniversityAnalysisService.classifyIndustry("档案管理员", "负责资料归档"));
        assertEquals(9, UniversityAnalysisService.industryRules().size());
    }
}
