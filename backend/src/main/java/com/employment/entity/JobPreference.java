package com.employment.entity;

import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;

@TableName("job_preference")
public class JobPreference {
    @TableId("student_id") public Long studentId;
    @TableField("expected_job") public String expectedJob;
    @TableField("expected_city") public String expectedCity;
    @TableField("expected_industry") public String expectedIndustry;
    @TableField("salary_min") public Integer salaryMin;
    @TableField("salary_max") public Integer salaryMax;
    @TableField("accept_remote_city") public Boolean acceptRemoteCity;
}
