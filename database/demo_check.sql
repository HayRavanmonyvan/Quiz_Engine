-- Active: 1788409622977@@127.0.0.1@3306@quiz_engine_db
-- 1. Check Latest Registered Users & Assigned RBAC Roles
SELECT 
    u.id AS user_id, 
    u.username, 
    u.email, 
    r.name AS role_name
FROM users u
JOIN user_roles ur ON u.id = ur.user_id
JOIN roles r ON ur.role_id = r.id
ORDER BY u.id DESC 
LIMIT 3;

-- 2. Check Quizzes, Total Questions, and Options
SELECT 
    q.id AS quiz_id, 
    q.title, 
    COUNT(DISTINCT qu.id) AS total_questions, 
    COUNT(qo.id) AS total_options
FROM quizzes q
LEFT JOIN questions qu ON q.id = qu.quiz_id
LEFT JOIN question_options qo ON qu.id = qo.question_id
GROUP BY q.id, q.title
ORDER BY q.id DESC 
LIMIT 3;

-- 3. Check Child Question Count for Cascade Delete Testing
SELECT COUNT(*) AS active_questions 
FROM questions 
WHERE quiz_id = 1;