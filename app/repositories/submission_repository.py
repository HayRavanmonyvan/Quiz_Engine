# app/repositories/submission_repository.py
from typing import List, Optional
from app.models.submission import Submission, SubmissionAnswer
from app.repositories.db_connection import DatabaseConnection

class SubmissionRepository:
    def save(self, submission: Submission) -> int:
        conn = DatabaseConnection.get_connection()
        conn.autocommit = False
        cursor = conn.cursor()
        try:
            query = """
                INSERT INTO submissions (quiz_id, student_id, total_score, max_score, passed, teacher_feedback)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                submission.quiz_id,
                submission.student_id,
                submission.total_score,
                submission.max_score,
                submission.passed,
                submission.teacher_feedback
            ))
            submission_id = cursor.lastrowid

            for ans in submission.answers:
                ans_query = """
                    INSERT INTO submission_answers (submission_id, question_id, selected_option_id, is_correct)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(ans_query, (submission_id, ans.question_id, ans.selected_option_id, ans.is_correct))

            conn.commit()
            return submission_id
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()

    def get_by_id(self, submission_id: int) -> Optional[Submission]:
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            sql = """
                SELECT s.id, s.quiz_id, s.student_id, s.total_score, s.max_score, s.passed, 
                       s.teacher_feedback,
                       DATE_FORMAT(s.submitted_at, '%Y-%m-%d %H:%i') as submitted_at,
                       u.username as student_username,
                       q.title as quiz_title
                FROM submissions s
                JOIN users u ON s.student_id = u.id
                JOIN quizzes q ON s.quiz_id = q.id
                WHERE s.id = %s
            """
            cursor.execute(sql, (submission_id,))
            row = cursor.fetchone()
            if not row:
                return None

            student_username = row.pop("student_username", None)
            quiz_title = row.pop("quiz_title", None)
            submitted_at = row.pop("submitted_at", None)

            sub = Submission(
                id=row["id"],
                quiz_id=row["quiz_id"],
                student_id=row["student_id"],
                total_score=float(row["total_score"]),
                max_score=float(row["max_score"]),
                passed=bool(row["passed"]),
                teacher_feedback=row.get("teacher_feedback"),
                student_username=student_username,
                quiz_title=quiz_title,
                submitted_at=submitted_at
            )

            # Query Answers with question and option labels
            ans_sql = """
                SELECT sa.question_id, sa.selected_option_id, sa.is_correct,
                       q.prompt as question_prompt, q.points as question_points,
                       so.option_text as selected_option_text,
                       co.option_text as correct_option_text
                FROM submission_answers sa
                JOIN questions q ON sa.question_id = q.id
                LEFT JOIN question_options so ON sa.selected_option_id = so.id
                LEFT JOIN question_options co ON q.id = co.question_id AND co.is_correct = TRUE
                WHERE sa.submission_id = %s
                ORDER BY q.id ASC
            """
            cursor.execute(ans_sql, (submission_id,))
            ans_rows = cursor.fetchall()

            for a in ans_rows:
                pts = float(a["question_points"]) if a["is_correct"] else 0.0
                sub.answers.append(
                    SubmissionAnswer(
                        question_id=a["question_id"],
                        selected_option_id=a["selected_option_id"],
                        is_correct=bool(a["is_correct"]),
                        question_prompt=a["question_prompt"],
                        selected_option_text=a["selected_option_text"],
                        correct_option_text=a["correct_option_text"],
                        points_awarded=pts
                    )
                )

            return sub
        finally:
            cursor.close()
            conn.close()

    def list_by_student(self, student_id: int) -> List[Submission]:
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            sql = """
                SELECT s.id, s.quiz_id, s.student_id, s.total_score, s.max_score, s.passed,
                       s.teacher_feedback,
                       DATE_FORMAT(s.submitted_at, '%Y-%m-%d %H:%i') as submitted_at,
                       q.title as quiz_title
                FROM submissions s
                JOIN quizzes q ON s.quiz_id = q.id
                WHERE s.student_id = %s
                ORDER BY s.id DESC
            """
            cursor.execute(sql, (student_id,))
            rows = cursor.fetchall()
            submissions = []
            for r in rows:
                submissions.append(
                    Submission(
                        id=r["id"],
                        quiz_id=r["quiz_id"],
                        student_id=r["student_id"],
                        total_score=float(r["total_score"]),
                        max_score=float(r["max_score"]),
                        passed=bool(r["passed"]),
                        teacher_feedback=r.get("teacher_feedback"),
                        quiz_title=r["quiz_title"],
                        submitted_at=r["submitted_at"]
                    )
                )
            return submissions
        finally:
            cursor.close()
            conn.close()

    def list_by_quiz(self, quiz_id: int) -> List[Submission]:
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            sql = """
                SELECT s.id, s.quiz_id, s.student_id, s.total_score, s.max_score, s.passed,
                       s.teacher_feedback,
                       DATE_FORMAT(s.submitted_at, '%Y-%m-%d %H:%i') as submitted_at,
                       u.username as student_username
                FROM submissions s
                JOIN users u ON s.student_id = u.id
                WHERE s.quiz_id = %s
                ORDER BY s.id DESC
            """
            cursor.execute(sql, (quiz_id,))
            rows = cursor.fetchall()
            submissions = []
            for r in rows:
                submissions.append(
                    Submission(
                        id=r["id"],
                        quiz_id=r["quiz_id"],
                        student_id=r["student_id"],
                        total_score=float(r["total_score"]),
                        max_score=float(r["max_score"]),
                        passed=bool(r["passed"]),
                        teacher_feedback=r.get("teacher_feedback"),
                        student_username=r["student_username"],
                        submitted_at=r["submitted_at"]
                    )
                )
            return submissions
        finally:
            cursor.close()
            conn.close()

    def list_all(self) -> List[Submission]:
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            sql = """
                SELECT s.id, s.quiz_id, s.student_id, s.total_score, s.max_score, s.passed,
                       s.teacher_feedback,
                       DATE_FORMAT(s.submitted_at, '%Y-%m-%d %H:%i') as submitted_at,
                       u.username as student_username,
                       q.title as quiz_title
                FROM submissions s
                JOIN users u ON s.student_id = u.id
                JOIN quizzes q ON s.quiz_id = q.id
                ORDER BY s.id DESC
            """
            cursor.execute(sql)
            rows = cursor.fetchall()
            submissions = []
            for r in rows:
                submissions.append(
                    Submission(
                        id=r["id"],
                        quiz_id=r["quiz_id"],
                        student_id=r["student_id"],
                        total_score=float(r["total_score"]),
                        max_score=float(r["max_score"]),
                        passed=bool(r["passed"]),
                        teacher_feedback=r.get("teacher_feedback"),
                        student_username=r["student_username"],
                        quiz_title=r["quiz_title"],
                        submitted_at=r["submitted_at"]
                    )
                )
            return submissions
        finally:
            cursor.close()
            conn.close()

    def update_score_and_feedback(self, submission_id: int, new_score: float, feedback: str) -> bool:
        """Allows Teacher/Admin to adjust score and leave feedback."""
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT s.max_score, q.pass_percentage
                FROM submissions s
                JOIN quizzes q ON s.quiz_id = q.id
                WHERE s.id = %s
            """, (submission_id,))
            row = cursor.fetchone()
            if not row:
                return False

            max_score = float(row["max_score"])
            pass_percentage = float(row["pass_percentage"])
            pct = (new_score / max_score * 100.0) if max_score > 0 else 0.0
            passed = pct >= pass_percentage

            update_sql = """
                UPDATE submissions 
                SET total_score = %s, passed = %s, teacher_feedback = %s
                WHERE id = %s
            """
            cursor.execute(update_sql, (new_score, passed, feedback, submission_id))
            conn.commit()
            return True
        finally:
            cursor.close()
            conn.close()