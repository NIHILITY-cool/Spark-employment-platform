-- ============================================================
-- Clean up student data that existed before the SIM2026 dataset
-- Safe to run again after importing: SIM2026 students are preserved
-- ============================================================

USE spark_employment;

START TRANSACTION;

-- Show existing students before cleanup
SELECT 'Before cleanup:' AS stage;
SELECT id, student_no, name, college, major FROM student;

-- Delete sessions for old student accounts only
DELETE FROM auth_session WHERE account_id IN (
    SELECT a.id FROM platform_account a
    LEFT JOIN student s ON s.id = a.student_id
    WHERE a.role = 'STUDENT'
      AND (s.student_no IS NULL OR s.student_no NOT LIKE 'SIM2026%')
);

-- Delete old student accounts, preserving the generated SIM2026 accounts
DELETE a FROM platform_account a
LEFT JOIN student s ON s.id = a.student_id
WHERE a.role = 'STUDENT'
  AND (s.student_no IS NULL OR s.student_no NOT LIKE 'SIM2026%');

-- Delete data linked to old students
DELETE ss FROM student_skill ss JOIN student s ON s.id = ss.student_id
WHERE s.student_no IS NULL OR s.student_no NOT LIKE 'SIM2026%';
DELETE se FROM student_experience se JOIN student s ON s.id = se.student_id
WHERE s.student_no IS NULL OR s.student_no NOT LIKE 'SIM2026%';
DELETE jp FROM job_preference jp JOIN student s ON s.id = jp.student_id
WHERE s.student_no IS NULL OR s.student_no NOT LIKE 'SIM2026%';

-- Delete old students, including demo001, and preserve SIM2026 students
DELETE FROM student WHERE student_no IS NULL OR student_no NOT LIKE 'SIM2026%';

-- Verify
SELECT 'After cleanup:' AS stage;
SELECT COUNT(*) AS remaining_students FROM student;
SELECT COUNT(*) AS remaining_sim_students FROM student WHERE student_no LIKE 'SIM2026%';
SELECT COUNT(*) AS remaining_student_accounts FROM platform_account WHERE role = 'STUDENT';

COMMIT;

-- ============================================================
-- This deletes all pre-existing non-SIM2026 student data.
-- It never affects admin/university accounts or the generated SIM2026 dataset.
-- ============================================================
