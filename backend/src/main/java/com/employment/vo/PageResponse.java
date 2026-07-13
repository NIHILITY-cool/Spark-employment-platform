package com.employment.vo;

import java.util.List;

public record PageResponse<T>(long page, long size, long total, List<T> records) {
}
