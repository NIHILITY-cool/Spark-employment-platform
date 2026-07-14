package com.employment.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDate;

@TableName("student_experience")
public class StudentExperience {
    @TableId(value = "id", type = IdType.AUTO) public Long id;
    @TableField("student_id") public Long studentId;
    @TableField("experience_type") public String experienceType;
    public String title;
    public String organization;
    public String role;
    public String description;
    @TableField("start_date") public LocalDate startDate;
    @TableField("end_date") public LocalDate endDate;
}
