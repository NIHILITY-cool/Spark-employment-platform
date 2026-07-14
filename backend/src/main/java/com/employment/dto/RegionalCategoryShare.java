package com.employment.dto;

import java.util.List;

public record RegionalCategoryShare(String city, long jobCount, List<CategoryShare> categories) {
}
