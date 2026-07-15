-- ============================================================
-- Mock Students Removal Script
-- Removes ALL students with student_no LIKE 'SIM2026%'
-- and their associated data via CASCADE or explicit deletion
-- ============================================================

USE spark_employment;

START TRANSACTION;

-- Check how many SIM2026 students exist before deletion
SELECT COUNT(*) AS before_student_count FROM student WHERE student_no LIKE 'SIM2026%';
SELECT COUNT(*) AS before_account_count FROM platform_account WHERE username LIKE 'SIM2026%';

-- Delete auth sessions for SIM2026 accounts
DELETE FROM auth_session WHERE account_id IN (
  SELECT id FROM platform_account WHERE username LIKE 'SIM2026%'
);

-- Delete platform accounts for SIM2026 students
DELETE FROM platform_account WHERE username LIKE 'SIM2026%';

-- Delete student_skill (cascade should handle this, but explicit is safer)
DELETE FROM student_skill WHERE student_id IN (
  SELECT id FROM student WHERE student_no LIKE 'SIM2026%'
);

-- Delete student_experience
DELETE FROM student_experience WHERE student_id IN (
  SELECT id FROM student WHERE student_no LIKE 'SIM2026%'
);

-- Delete job_preference
DELETE FROM job_preference WHERE student_id IN (
  SELECT id FROM student WHERE student_no LIKE 'SIM2026%'
);

-- Delete students
DELETE FROM student WHERE student_no LIKE 'SIM2026%';

-- Verify removal
SELECT COUNT(*) AS after_student_count FROM student WHERE student_no LIKE 'SIM2026%';
SELECT COUNT(*) AS after_account_count FROM platform_account WHERE username LIKE 'SIM2026%';

COMMIT;

-- End of removal script