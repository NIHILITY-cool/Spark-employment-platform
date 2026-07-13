package com.employment.entity;

import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDate;

@TableName("job")
public class Job {
    @TableId("job_key") public String jobKey;
    @TableField("source_name") public String sourceName;
    @TableField("source_job_id") public String sourceJobId;
    @TableField("job_name") public String jobName;
    @TableField("job_category") public String jobCategory;
    @TableField("company_name") public String companyName;
    public String industry;
    @TableField("company_scale") public String companyScale;
    public String city;
    public String district;
    @TableField("education_requirement") public String educationRequirement;
    @TableField("experience_requirement") public String experienceRequirement;
    @TableField("salary_raw") public String salaryRaw;
    @TableField("salary_min") public Integer salaryMin;
    @TableField("salary_max") public Integer salaryMax;
    @TableField("job_description") public String jobDescription;
    @TableField("job_url") public String jobUrl;
    @TableField("crawl_date") public LocalDate crawlDate;
    @TableField("job_status") public String jobStatus;
    @TableField("last_seen_date") public LocalDate lastSeenDate;
}
