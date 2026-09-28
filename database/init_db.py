# database/init_db.py
import os
import sys
import mysql.connector
from werkzeug.security import generate_password_hash

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from config import Config


def init_database():
    print(f"Connecting to MySQL at {Config.MYSQL_HOST}:{Config.MYSQL_PORT}...")
    # 1. Connect without selecting database to ensure database exists
    conn = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        port=Config.MYSQL_PORT,
    )
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.MYSQL_DATABASE};")
    conn.commit()
    cursor.close()
    conn.close()

    # 2. Reconnect to execute schema
    conn = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DATABASE,
        port=Config.MYSQL_PORT,
    )
    cursor = conn.cursor()

    # Disable foreign key checks for clean migration
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")

    current_dir = os.path.dirname(os.path.abspath(__file__))
    schema_path = os.path.join(current_dir, "schema.sql")

    if os.path.exists(schema_path):
        with open(schema_path, "r", encoding="utf-8") as f:
            lines = [line for line in f.readlines() if not line.strip().startswith("--")]
            full_sql = "".join(lines)
            for stmt in full_sql.split(";"):
                cleaned = stmt.strip()
                if cleaned:
                    cursor.execute(cleaned)
        conn.commit()

    # Ensure `role_id` is removed from `users` if an older schema created it
    cursor.execute("""
        SELECT COUNT(*) 
        FROM information_schema.COLUMNS 
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'users' AND COLUMN_NAME = 'role_id';
    """, (Config.MYSQL_DATABASE,))
    has_role_id = cursor.fetchone()[0] > 0
    if has_role_id:
        print("Migrating schema: Removing obsolete 'role_id' column from 'users' table...")
        cursor.execute("ALTER TABLE users DROP COLUMN role_id;")
        conn.commit()

    # Ensure `teacher_feedback` exists in `submissions`
    cursor.execute("""
        SELECT COUNT(*) 
        FROM information_schema.COLUMNS 
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'submissions' AND COLUMN_NAME = 'teacher_feedback';
    """, (Config.MYSQL_DATABASE,))
    has_teacher_feedback = cursor.fetchone()[0] > 0
    if not has_teacher_feedback:
        cursor.execute("ALTER TABLE submissions ADD COLUMN teacher_feedback TEXT NULL;")
        conn.commit()

    # Ensure `order_num` exists in `questions`
    cursor.execute("""
        SELECT COUNT(*) 
        FROM information_schema.COLUMNS 
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'questions' AND COLUMN_NAME = 'order_num';
    """, (Config.MYSQL_DATABASE,))
    has_order_num = cursor.fetchone()[0] > 0
    if not has_order_num:
        cursor.execute("ALTER TABLE questions ADD COLUMN order_num INT DEFAULT 0;")
        conn.commit()

    # Ensure `time_limit_minutes` exists in `quizzes`
    cursor.execute("""
        SELECT COUNT(*) 
        FROM information_schema.COLUMNS 
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'quizzes' AND COLUMN_NAME = 'time_limit_minutes';
    """, (Config.MYSQL_DATABASE,))
    has_time_limit = cursor.fetchone()[0] > 0
    if not has_time_limit:
        cursor.execute("ALTER TABLE quizzes ADD COLUMN time_limit_minutes INT DEFAULT 0;")
        conn.commit()

    # 3. Seed Roles, Permissions, and Bridges
    seed_path = os.path.join(current_dir, "seed.sql")
    if os.path.exists(seed_path):
        with open(seed_path, "r", encoding="utf-8") as f:
            lines = [line for line in f.readlines() if not line.strip().startswith("--")]
            full_sql = "".join(lines)
            for stmt in full_sql.split(";"):
                cleaned = stmt.strip()
                if cleaned:
                    cursor.execute(cleaned)
        conn.commit()

    # 4. Seed Verified Accounts (password: Password@123)
    password_hash = generate_password_hash("Password@123")

    demo_users = [
        ("admin", "admin@institute.edu", "Admin"),
        ("teacher_jane", "jane@institute.edu", "Teacher"),
        ("instructor_socheat", "socheat@institute.edu", "Teacher"),
        ("student_john", "john@student.edu", "Student"),
        ("student_alice", "alice@student.edu", "Student"),
    ]

    for username, email, role_name in demo_users:
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, is_active)
            VALUES (%s, %s, %s, TRUE)
            ON DUPLICATE KEY UPDATE 
                email = VALUES(email),
                password_hash = VALUES(password_hash),
                is_active = VALUES(is_active);
        """, (username, email, password_hash))
        
        # Get user id
        cursor.execute("SELECT id FROM users WHERE username = %s;", (username,))
        user_id = cursor.fetchone()[0]

        # Get role id
        cursor.execute("SELECT id FROM roles WHERE name = %s;", (role_name,))
        role_id = cursor.fetchone()[0]

        # Clear existing and assign proper role
        cursor.execute("DELETE FROM user_roles WHERE user_id = %s;", (user_id,))
        cursor.execute("INSERT INTO user_roles (user_id, role_id) VALUES (%s, %s);", (user_id, role_id))
    
    conn.commit()

    # 6. Seed Sample Quizzes, Questions, and Options
    cursor.execute("""
        INSERT INTO quizzes (id, title, description, pass_percentage, created_by)
        VALUES (1, 'Python OOP & Software Architecture', 
                'Comprehensive assessment covering classes, inheritance, encapsulation, polymorphism, and repository patterns.', 
                60.0, 2)
        ON DUPLICATE KEY UPDATE 
            title=VALUES(title), 
            description=VALUES(description), 
            pass_percentage=VALUES(pass_percentage);
    """)

    questions_data = [
        (1, 1, 'Which OOP principle focuses on bundling data attributes and methods that operate on that data into a single class unit?', 2, 1),
        (2, 1, 'In a layered architectural pattern, what is the primary responsibility of a Repository class?', 3, 2),
        (3, 1, 'What mechanism allows a subclass to provide a specific implementation of a method already defined in its parent class?', 2, 3),
        (4, 1, 'In Flask, how does session data persist between client HTTP requests?', 3, 4)
    ]

    cursor.executemany("""
        INSERT INTO questions (id, quiz_id, prompt, points, order_num)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE 
            prompt=VALUES(prompt), 
            points=VALUES(points),
            order_num=VALUES(order_num);
    """, questions_data)

    options_data = [
        # Question 1
        (1, 1, 'Encapsulation', True),
        (2, 1, 'Polymorphism', False),
        (3, 1, 'Multiple Inheritance', False),
        (4, 1, 'Recursion', False),
        # Question 2
        (5, 2, 'Isolate and encapsulate database query logic away from business domain services', True),
        (6, 2, 'Directly render HTML Jinja templates to the user browser', False),
        (7, 2, 'Route incoming HTTP requests to controller blueprints', False),
        (8, 2, 'Validate CSRF tokens in client forms', False),
        # Question 3
        (9, 3, 'Method Overriding', True),
        (10, 3, 'Type Casting', False),
        (11, 3, 'Garbage Collection', False),
        (12, 3, 'Data Hydration', False),
        # Question 4
        (13, 4, 'Cryptographically signed cookie stored on the client browser', True),
        (14, 4, 'Plain text file saved in Windows AppData', False),
        (15, 4, 'Global Python variable accessible by all web workers', False),
        (16, 4, 'Hardcoded URL query parameters in HTTP headers', False),
    ]

    cursor.executemany("""
        INSERT INTO question_options (id, question_id, option_text, is_correct)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE 
            option_text=VALUES(option_text), 
            is_correct=VALUES(is_correct);
    """, options_data)

    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
    conn.commit()

    cursor.close()
    conn.close()
    print("Database schema verified and seeded with 5-Table RBAC and demo quiz data successfully.")


if __name__ == "__main__":
    init_database()