-- database/seed.sql
-- Seed Roles, Permissions, User-Roles, Role-Permissions, and Demo Quiz

-- 1. Roles
INSERT INTO roles (id, name, description) VALUES
(1, 'Admin', 'Full administrative privileges: manage users, edit all quizzes, and system reports'),
(2, 'Teacher', 'Can create, edit, delete, score quizzes, and view student responses'),
(3, 'Student', 'Can view available quizzes, submit attempts, and view personal results')
ON DUPLICATE KEY UPDATE name=VALUES(name), description=VALUES(description);

-- 2. Granular Permissions
INSERT INTO permissions (id, name, description) VALUES
(1, 'user:manage', 'Manage users, assign roles, toggle activation'),
(2, 'quiz:create', 'Create new quizzes, questions, and options'),
(3, 'quiz:edit', 'Update existing quizzes, questions, and options'),
(4, 'quiz:delete', 'Delete quizzes and associated records'),
(5, 'quiz:score', 'Grade submissions and provide instructor feedback'),
(6, 'quiz:view', 'View published quiz content and details'),
(7, 'quiz:submit', 'Attempt and submit answers to quizzes'),
(8, 'report:view_all', 'View all student submissions and class analytics'),
(9, 'report:view_own', 'View personal submission results and history')
ON DUPLICATE KEY UPDATE name=VALUES(name), description=VALUES(description);

-- 3. Role-Permission Mappings
-- Admin: All permissions (1 through 9)
INSERT IGNORE INTO role_permissions (role_id, permission_id) VALUES
(1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8), (1, 9);

-- Teacher: quiz management, scoring, viewing, and class analytics
INSERT IGNORE INTO role_permissions (role_id, permission_id) VALUES
(2, 2), (2, 3), (2, 4), (2, 5), (2, 6), (2, 8), (2, 9);

-- Student: viewing quizzes, submitting attempts, and viewing personal reports
INSERT IGNORE INTO role_permissions (role_id, permission_id) VALUES
(3, 6), (3, 7), (3, 9);

-- 4. Emergency Break-Glass Account (Password: BreakGlass@911)
INSERT INTO users (id, username, email, password_hash, is_active) VALUES
(99, 'emergency_admin', 'emergency@institute.edu', 'scrypt:32768:8:1$u7Fw83xH6sVj$c20d75f2c730e2f1839e0839e99a2245b796eb0cbebf1e5bdfdbff8c9fef4c09d5718df8645ce1e67c870cb1ca8c96ae2508107ef4ce61439774a3832dffc9fe', TRUE)
ON DUPLICATE KEY UPDATE username=VALUES(username);

INSERT IGNORE INTO user_roles (user_id, role_id) VALUES (99, 1);