package com.employment.dto;

import java.util.List;

public record JobFilterOptions(List<String> cities, List<String> categories) {
}
