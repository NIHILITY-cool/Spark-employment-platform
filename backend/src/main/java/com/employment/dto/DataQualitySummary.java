package com.employment.dto;

import java.time.LocalDate;
import java.util.List;

public record DataQualitySummary(LocalDate statDate, String source, long rawRecordCount,
                                 long cleanedRecordCount, long excludedRecordCount,
                                 long duplicateJobIdCount, List<DataQualityItem> missingFields,
                                 List<DataQualityItem> exclusionReasons,
                                 List<DataQualityItem> salaryParseStatus, String note) {
}
