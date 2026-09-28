# app/repositories/quiz_repository.py
from typing import List, Optional, Dict
from app.models.quiz import Quiz
from app.models.question import Question, Option
from app.repositories.db_connection import DatabaseConnection

class QuizRepository:
    def get_by_id(self, quiz_id: int) -> Optional[Quiz]:
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            # Query Quiz with creator username
            sql = """
                SELECT q.id, q.title, q.description, q.pass_percentage, q.time_limit_minutes, q.created_by, 
                       DATE_FORMAT(q.created_at, '%Y-%m-%d %H:%i') as created_at,
                       u.username as creator_username
                FROM quizzes q
                LEFT JOIN users u ON q.created_by = u.id
                WHERE q.id = %s
            """
            cursor.execute(sql, (quiz_id,))
            quiz_row = cursor.fetchone()
            if not quiz_row:
                return None

            creator_username = quiz_row.pop("creator_username", None)
            created_at = quiz_row.pop("created_at", None)

            quiz = Quiz(**quiz_row)
            quiz.creator_username = creator_username
            quiz.created_at = created_at

            # Query Questions
            cursor.execute("SELECT id, quiz_id, prompt, points, order_num FROM questions WHERE quiz_id = %s ORDER BY order_num ASC, id ASC", (quiz_id,))
            question_rows = cursor.fetchall()

            for q_row in question_rows:
                question = Question(**q_row)
                cursor.execute(
                    "SELECT id, question_id, option_text, is_correct FROM question_options WHERE question_id = %s ORDER BY id ASC",
                    (question.id,)
                )
                option_rows = cursor.fetchall()
                question.options = [Option(
                    id=opt["id"],
                    question_id=opt["question_id"],
                    option_text=opt["option_text"],
                    is_correct=bool(opt["is_correct"])
                ) for opt in option_rows]
                quiz.questions.append(question)

            return quiz
        finally:
            cursor.close()
            conn.close()

    def list_all(self) -> List[Quiz]:
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            sql = """
                SELECT q.id, q.title, q.description, q.pass_percentage, q.time_limit_minutes, q.created_by,
                       DATE_FORMAT(q.created_at, '%Y-%m-%d %H:%i') as created_at,
                       u.username as creator_username,
                       COUNT(qu.id) as question_count
                FROM quizzes q
                LEFT JOIN users u ON q.created_by = u.id
                LEFT JOIN questions qu ON q.id = qu.quiz_id
                GROUP BY q.id, q.title, q.description, q.pass_percentage, q.time_limit_minutes, q.created_by, q.created_at, u.username
                ORDER BY q.id DESC
            """
            cursor.execute(sql)
            rows = cursor.fetchall()
            quizzes = []
            for row in rows:
                creator_username = row.pop("creator_username", None)
                created_at = row.pop("created_at", None)
                q_count = row.pop("question_count", 0)
                q = Quiz(**row)
                q.creator_username = creator_username
                q.created_at = created_at
                q.questions = [None] * q_count
                quizzes.append(q)

            return quizzes
        finally:
            cursor.close()
            conn.close()

    def list_by_creator(self, user_id: int) -> List[Quiz]:
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            sql = """
                SELECT q.id, q.title, q.description, q.pass_percentage, q.time_limit_minutes, q.created_by,
                       DATE_FORMAT(q.created_at, '%Y-%m-%d %H:%i') as created_at,
                       u.username as creator_username,
                       COUNT(qu.id) as question_count
                FROM quizzes q
                LEFT JOIN users u ON q.created_by = u.id
                LEFT JOIN questions qu ON q.id = qu.quiz_id
                WHERE q.created_by = %s
                GROUP BY q.id, q.title, q.description, q.pass_percentage, q.time_limit_minutes, q.created_by, q.created_at, u.username
                ORDER BY q.id DESC
            """
            cursor.execute(sql, (user_id,))
            rows = cursor.fetchall()
            quizzes = []
            for row in rows:
                creator_username = row.pop("creator_username", None)
                created_at = row.pop("created_at", None)
                q_count = row.pop("question_count", 0)
                q = Quiz(**row)
                q.creator_username = creator_username
                q.created_at = created_at
                q.questions = [None] * q_count
                quizzes.append(q)

            return quizzes
        finally:
            cursor.close()
            conn.close()

    def create(self, quiz: Quiz) -> int:
        """
        Atomically insert quiz, its questions, and question options.
        Rolls back all changes if an error occurs.
        """
        conn = DatabaseConnection.get_connection()
        conn.autocommit = False
        cursor = conn.cursor()
        try:
            # 1. Insert Quiz
            insert_quiz_sql = """
                INSERT INTO quizzes (title, description, pass_percentage, time_limit_minutes, created_by)
                VALUES (%s, %s, %s, %s, %s)
            """
            time_limit = getattr(quiz, 'time_limit_minutes', 0) or 0
            cursor.execute(insert_quiz_sql, (quiz.title, quiz.description, quiz.pass_percentage, time_limit, quiz.created_by))
            quiz_id = cursor.lastrowid

            # 2. Insert Questions & Options
            for idx, question in enumerate(quiz.questions):
                insert_q_sql = """
                    INSERT INTO questions (quiz_id, prompt, points, order_num)
                    VALUES (%s, %s, %s, %s)
                """
                order_num = getattr(question, 'order_num', idx + 1) or (idx + 1)
                cursor.execute(insert_q_sql, (quiz_id, question.prompt, question.points, order_num))
                question_id = cursor.lastrowid

                for option in question.options:
                    insert_opt_sql = """
                        INSERT INTO question_options (question_id, option_text, is_correct)
                        VALUES (%s, %s, %s)
                    """
                    cursor.execute(insert_opt_sql, (question_id, option.option_text, option.is_correct))

            conn.commit()
            return quiz_id
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()

    def update(self, quiz: Quiz) -> bool:
        """
        Atomically update quiz metadata, refresh its questions, and options.
        Rolls back all changes if an error occurs.
        """
        conn = DatabaseConnection.get_connection()
        conn.autocommit = False
        cursor = conn.cursor()
        try:
            # 1. Update Quiz metadata
            update_quiz_sql = """
                UPDATE quizzes
                SET title = %s, description = %s, pass_percentage = %s, time_limit_minutes = %s
                WHERE id = %s
            """
            time_limit = getattr(quiz, 'time_limit_minutes', 0) or 0
            cursor.execute(update_quiz_sql, (quiz.title, quiz.description, quiz.pass_percentage, time_limit, quiz.id))

            # 2. Delete existing questions (options cascade via foreign key)
            cursor.execute("DELETE FROM questions WHERE quiz_id = %s", (quiz.id,))

            # 3. Re-insert questions and options
            for idx, question in enumerate(quiz.questions):
                insert_q_sql = """
                    INSERT INTO questions (quiz_id, prompt, points, order_num)
                    VALUES (%s, %s, %s, %s)
                """
                order_num = getattr(question, 'order_num', idx + 1) or (idx + 1)
                cursor.execute(insert_q_sql, (quiz.id, question.prompt, question.points, order_num))
                question_id = cursor.lastrowid

                for option in question.options:
                    insert_opt_sql = """
                        INSERT INTO question_options (question_id, option_text, is_correct)
                        VALUES (%s, %s, %s)
                    """
                    cursor.execute(insert_opt_sql, (question_id, option.option_text, option.is_correct))

            conn.commit()
            return True
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()

    def delete(self, quiz_id: int) -> bool:
        """Cascade deletes the quiz and all associated questions/options/submissions."""
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM quizzes WHERE id = %s", (quiz_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            cursor.close()
            conn.close()

    def get_stats(self, quiz_id: int) -> Dict:
        """Returns response statistics for a quiz (for Google Form Responses tab)."""
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            sql = """
                SELECT 
                    COUNT(*) as total_responses,
                    COALESCE(AVG(total_score), 0) as avg_score,
                    COALESCE(MAX(total_score), 0) as max_score_achieved,
                    COALESCE(SUM(CASE WHEN passed = 1 THEN 1 ELSE 0 END), 0) as passed_count
                FROM submissions
                WHERE quiz_id = %s
            """
            cursor.execute(sql, (quiz_id,))
            row = cursor.fetchone() or {}
            total = int(row.get("total_responses", 0) or 0)
            passed = int(row.get("passed_count", 0) or 0)
            pass_rate = round((float(passed) / total * 100.0), 1) if total > 0 else 0.0

            return {
                "total_responses": total,
                "avg_score": round(float(row.get("avg_score", 0.0)), 2),
                "max_score_achieved": round(float(row.get("max_score_achieved", 0.0)), 2),
                "passed_count": passed,
                "pass_rate": pass_rate
            }
        finally:
            cursor.close()
            conn.close()

    def get_question_breakdown(self, quiz_id: int) -> List[Dict]:
        """Returns per-question accuracy and attempt metrics for a quiz."""
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            sql = """
                SELECT 
                    q.id as question_id,
                    q.prompt,
                    q.points,
                    q.order_num,
                    COUNT(sa.id) as total_attempts,
                    COALESCE(SUM(CASE WHEN sa.is_correct = 1 THEN 1 ELSE 0 END), 0) as correct_count
                FROM questions q
                LEFT JOIN submission_answers sa ON q.id = sa.question_id
                WHERE q.quiz_id = %s
                GROUP BY q.id, q.prompt, q.points, q.order_num
                ORDER BY q.order_num ASC, q.id ASC
            """
            cursor.execute(sql, (quiz_id,))
            rows = cursor.fetchall()
            breakdown = []
            for row in rows:
                total = int(row.get("total_attempts", 0) or 0)
                correct = int(row.get("correct_count", 0) or 0)
                incorrect = total - correct
                accuracy = round((float(correct) / total * 100.0), 1) if total > 0 else 0.0
                breakdown.append({
                    "question_id": int(row["question_id"]),
                    "prompt": row["prompt"],
                    "points": float(row["points"]),
                    "order_num": int(row["order_num"]),
                    "total_attempts": total,
                    "correct_count": correct,
                    "incorrect_count": incorrect,
                    "accuracy_rate": accuracy
                })
            return breakdown
        finally:
            cursor.close()
            conn.close()