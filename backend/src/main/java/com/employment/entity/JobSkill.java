package com.employment.entity;

import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableName;
import java.math.BigDecimal;
import java.time.LocalDate;

@TableName("job_skill")
public class JobSkill {
    @TableField("job_key") public String jobKey;
    @TableField("skill_name") public String skillName;
    @TableField("skill_category") public String skillCategory;
    @TableField("skill_weight") public BigDecimal skillWeight;
    @TableField("source_text") public String sourceText;
    @TableField("match_alias") public String matchAlias;
    @TableField("crawl_date") public LocalDate crawlDate;
}
