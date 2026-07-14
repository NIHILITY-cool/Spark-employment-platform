package com.employment.vo;

import java.util.List;

public record UniversityStudentInsightResponse(UniversityStudentInsightSummary summary,
                                               List<UniversityStudentInsight> students,
                                               String dataBasis) {
}
