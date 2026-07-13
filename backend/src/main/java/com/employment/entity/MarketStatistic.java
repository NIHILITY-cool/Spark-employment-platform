package com.employment.entity;

import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableName;
import java.math.BigDecimal;
import java.time.LocalDate;

@TableName("market_statistic")
public class MarketStatistic {
    @TableField("stat_date") public LocalDate statDate;
    @TableField("stat_type") public String statType;
    @TableField("dimension_key") public String dimensionKey;
    @TableField("metric_value") public BigDecimal metricValue;
    @TableField("extra_json") public String extraJson;
}
