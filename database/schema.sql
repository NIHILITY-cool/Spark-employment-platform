CREATE DATABASE IF NOT EXISTS spark_employment
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_0900_ai_ci;

USE spark_employment;

CREATE TABLE IF NOT EXISTS job (
    job_key VARCHAR(180) NOT NULL COMMENT '来源与来源岗位 ID 组成的稳定唯一键',
    source_name VARCHAR(32) NOT NULL,
    source_job_id VARCHAR(128) NOT NULL,
    job_name VARCHAR(255) NOT NULL,
    job_category VARCHAR(64) NOT NULL DEFAULT '其他',
    company_name VARCHAR(255) NOT NULL,
    industry VARCHAR(128) NOT NULL DEFAULT '',
    company_scale VARCHAR(64) NOT NULL DEFAULT '',
    city VARCHAR(64) NOT NULL,
    district VARCHAR(64) NOT NULL DEFAULT '',
    education_requirement VARCHAR(64) NOT NULL DEFAULT '',
    experience_requirement VARCHAR(64) NOT NULL DEFAULT '',
    salary_raw VARCHAR(128) NOT NULL DEFAULT '',
    salary_min INT NULL,
    salary_max INT NULL,
    job_description MEDIUMTEXT NULL,
    job_url VARCHAR(1024) NOT NULL DEFAULT '',
    crawl_date DATE NOT NULL,
    job_status VARCHAR(16) NOT NULL DEFAULT 'active',
    last_seen_date DATE NOT NULL,
    record_hash CHAR(64) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (job_key),
    KEY idx_job_city (city),
    KEY idx_job_category (job_category),
    KEY idx_job_source_date (source_name, crawl_date),
    KEY idx_job_salary (salary_min, salary_max)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Spark 清洗后的标准岗位表';

CREATE TABLE IF NOT EXISTS job_skill (
    job_key VARCHAR(180) NOT NULL,
    skill_name VARCHAR(128) NOT NULL,
    skill_category VARCHAR(64) NOT NULL,
    skill_weight DECIMAL(5,2) NOT NULL DEFAULT 1.00,
    source_text VARCHAR(32) NOT NULL DEFAULT 'job_description',
    match_alias VARCHAR(128) NOT NULL DEFAULT '',
    crawl_date DATE NOT NULL,
    PRIMARY KEY (job_key, skill_name),
    KEY idx_job_skill_name (skill_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='岗位技能提取结果';

CREATE TABLE IF NOT EXISTS market_statistic (
    stat_date DATE NOT NULL,
    stat_type VARCHAR(64) NOT NULL,
    dimension_key VARCHAR(255) NOT NULL,
    metric_value DECIMAL(16,2) NOT NULL,
    extra_json JSON NULL,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (stat_date, stat_type, dimension_key),
    KEY idx_market_stat_type (stat_type, stat_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Spark 输出的市场统计结果';

CREATE TABLE IF NOT EXISTS student (
    id BIGINT NOT NULL AUTO_INCREMENT,
    student_no VARCHAR(64) NULL,
    name VARCHAR(64) NOT NULL,
    college VARCHAR(128) NOT NULL,
    major VARCHAR(128) NOT NULL,
    education VARCHAR(32) NOT NULL,
    graduation_year SMALLINT NOT NULL,
    profile_completed TINYINT(1) NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_student_no (student_no),
    KEY idx_student_major (major),
    KEY idx_student_graduation_year (graduation_year)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学生当前画像';

CREATE TABLE IF NOT EXISTS student_skill (
    id BIGINT NOT NULL AUTO_INCREMENT,
    student_id BIGINT NOT NULL,
    skill_name VARCHAR(128) NOT NULL,
    skill_level TINYINT NOT NULL DEFAULT 3,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_student_skill (student_id, skill_name),
    KEY idx_student_skill_name (skill_name),
    CONSTRAINT fk_student_skill_student FOREIGN KEY (student_id) REFERENCES student(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学生技能';

CREATE TABLE IF NOT EXISTS student_experience (
    id BIGINT NOT NULL AUTO_INCREMENT,
    student_id BIGINT NOT NULL,
    experience_type VARCHAR(16) NOT NULL COMMENT 'project/internship/award',
    title VARCHAR(180) NOT NULL,
    organization VARCHAR(180) NOT NULL DEFAULT '',
    role VARCHAR(120) NOT NULL DEFAULT '',
    description TEXT NOT NULL,
    start_date DATE NULL,
    end_date DATE NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_student_experience_student (student_id, experience_type),
    CONSTRAINT fk_student_experience_student FOREIGN KEY (student_id) REFERENCES student(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学生项目、实习与获奖经历';

CREATE TABLE IF NOT EXISTS job_preference (
    student_id BIGINT NOT NULL,
    expected_job VARCHAR(128) NOT NULL DEFAULT '',
    expected_city VARCHAR(64) NOT NULL DEFAULT '',
    expected_industry VARCHAR(128) NOT NULL DEFAULT '',
    salary_min INT NULL,
    salary_max INT NULL,
    accept_remote_city TINYINT(1) NOT NULL DEFAULT 0,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (student_id),
    CONSTRAINT fk_job_preference_student FOREIGN KEY (student_id) REFERENCES student(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学生就业期望';
