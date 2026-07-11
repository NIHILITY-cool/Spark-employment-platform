package com.employment.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;

@TableName("student_skill")
public class StudentSkill {
    @TableId(value = "id", type = IdType.AUTO) public Long id;
    @TableField("student_id") public Long studentId;
    @TableField("skill_name") public String skillName;
    @TableField("skill_level") public Integer skillLevel;
}
