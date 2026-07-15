package com.employment.service;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;

class UniversityAnalysisServiceTest {
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
