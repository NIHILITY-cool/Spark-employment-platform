USE spark_employment;

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
    KEY idx_student_experience_student (student_id, experience_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学生项目、实习与获奖经历';
