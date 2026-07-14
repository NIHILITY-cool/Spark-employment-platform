package com.employment.vo;

import java.util.List;

public record UniversityStudentInsightResponse(UniversityStudentInsightSummary summary,
                                               List<UniversityStudentInsight> students,
                                               String dataBasis,
                                               int page,
                                               int size,
                                               long total,
                                               int totalPages) {
}
