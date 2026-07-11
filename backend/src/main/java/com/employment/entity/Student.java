package com.employment.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;

@TableName("student")
public class Student {
    @TableId(value = "id", type = IdType.AUTO) public Long id;
    @TableField("student_no") public String studentNo;
    public String name;
    public String college;
    public String major;
    public String education;
    @TableField("graduation_year") public Integer graduationYear;
    @TableField("profile_completed") public Boolean profileCompleted;
}
