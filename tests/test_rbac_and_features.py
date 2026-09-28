# tests/test_rbac_and_features.py
import unittest
from unittest.mock import MagicMock, patch
from app.models.user import User
from app.models.quiz import Quiz
from app.models.question import Question, Option
from app.models.submission import Submission, SubmissionAnswer
from app.repositories.user_repository import UserRepository
from app.repositories.quiz_repository import QuizRepository
from app.services.quiz_service import QuizService
from app.services.auth_service import AuthService
from app.routes.security import require_permission, login_required
from flask import Flask, session, jsonify

class RBACTestSuite(unittest.TestCase):
    def setUp(self):
        # Admin user
        self.admin_user = User(
            id=1,
            username="admin",
            email="admin@test.edu",
            password_hash="hash",
            is_active=True,
            roles=["Admin"],
            permissions=["user:manage", "quiz:create", "quiz:view"]
        )

        # Teacher user
        self.teacher_user = User(
            id=2,
            username="teacher_jane",
            email="jane@test.edu",
            password_hash="hash",
            is_active=True,
            roles=["Teacher"],
            permissions=["quiz:create", "quiz:edit", "quiz:delete", "quiz:score", "quiz:view", "report:view_all"]
        )

        # Student user
        self.student_user = User(
            id=3,
            username="student_john",
            email="john@test.edu",
            password_hash="hash",
            is_active=True,
            roles=["Student"],
            permissions=["quiz:view", "quiz:submit", "report:view_own"]
        )

    # 1. Domain Model Authorization Tests
    def test_admin_bypasses_all_permissions(self):
        # Admin should return True even for unlisted permission
        self.assertTrue(self.admin_user.has_permission("quiz:delete"))
        self.assertTrue(self.admin_user.has_permission("non_existent:permission"))
        self.assertTrue(self.admin_user.is_admin)
        self.assertFalse(self.admin_user.is_student)

    def test_teacher_permissions(self):
        self.assertTrue(self.teacher_user.has_permission("quiz:create"))
        self.assertTrue(self.teacher_user.has_permission("quiz:score"))
        self.assertTrue(self.teacher_user.has_permission("report:view_all"))
        # Teacher does not have user:manage
        self.assertFalse(self.teacher_user.has_permission("user:manage"))
        self.assertTrue(self.teacher_user.is_teacher)
        self.assertFalse(self.teacher_user.is_admin)

    def test_student_permissions(self):
        self.assertTrue(self.student_user.has_permission("quiz:view"))
        self.assertTrue(self.student_user.has_permission("quiz:submit"))
        # Student cannot create, edit, delete, score or manage
        self.assertFalse(self.student_user.has_permission("quiz:create"))
        self.assertFalse(self.student_user.has_permission("quiz:delete"))
        self.assertFalse(self.student_user.has_permission("quiz:score"))
        self.assertFalse(self.student_user.has_permission("report:view_all"))
        self.assertFalse(self.student_user.has_permission("user:manage"))
        self.assertTrue(self.student_user.is_student)

    def test_has_role_case_insensitive(self):
        self.assertTrue(self.teacher_user.has_role("teacher"))
        self.assertTrue(self.teacher_user.has_role("Teacher"))
        self.assertFalse(self.teacher_user.has_role("Admin"))

    # 2. Google Form Payload Parsing in QuizService
    def test_quiz_service_parse_valid_google_form(self):
        mock_quiz_repo = MagicMock()
        mock_sub_repo = MagicMock()
        service = QuizService(mock_quiz_repo, mock_sub_repo)

        form_data = {
            "title": "Google Form Style Assessment",
            "description": "Form description",
            "pass_percentage": 75.0,
            "questions": [
                {
                    "prompt": "What is Python?",
                    "points": 3,
                    "options": [
                        {"text": "A programming language", "is_correct": True},
                        {"text": "A reptile only", "is_correct": False}
                    ]
                }
            ]
        }

        quiz = service.parse_quiz_form_data(form_data, creator_id=2)
        self.assertEqual(quiz.title, "Google Form Style Assessment")
        self.assertEqual(quiz.pass_percentage, 75.0)
        self.assertEqual(len(quiz.questions), 1)
        self.assertEqual(quiz.questions[0].points, 3)
        self.assertEqual(len(quiz.questions[0].options), 2)
        self.assertTrue(quiz.questions[0].options[0].is_correct)
        self.assertEqual(quiz.max_possible_score, 3)

    def test_quiz_service_parse_fails_no_correct_option(self):
        mock_quiz_repo = MagicMock()
        service = QuizService(mock_quiz_repo)

        invalid_data = {
            "title": "Invalid Form",
            "questions": [
                {
                    "prompt": "No answer key selected",
                    "points": 1,
                    "options": [
                        {"text": "Opt A", "is_correct": False},
                        {"text": "Opt B", "is_correct": False}
                    ]
                }
            ]
        }
        with self.assertRaises(ValueError):
            service.parse_quiz_form_data(invalid_data, creator_id=2)

    # 3. Web Security Decorator Tests
    def test_require_permission_allows_authorized_user(self):
        app = Flask(__name__)
        app.secret_key = "test-secret"

        @app.route("/api/test-create")
        @require_permission("quiz:create")
        def create_route():
            return jsonify({"status": "allowed"}), 200

        client = app.test_client()

        # Test as Teacher (has quiz:create)
        with client.session_transaction() as sess:
            sess["user_id"] = 2
            sess["username"] = "teacher_jane"
            sess["roles"] = ["Teacher"]
            sess["permissions"] = ["quiz:create", "quiz:view"]

        response = client.get("/api/test-create")
        self.assertEqual(response.status_code, 200)

    def test_require_permission_blocks_unauthorized_user_with_403(self):
        app = Flask(__name__)
        app.secret_key = "test-secret"

        @app.route("/api/test-create")
        @require_permission("quiz:create")
        def create_route():
            return jsonify({"status": "allowed"}), 200

        client = app.test_client()

        # Test as Student (lacks quiz:create)
        with client.session_transaction() as sess:
            sess["user_id"] = 3
            sess["username"] = "student_john"
            sess["roles"] = ["Student"]
            sess["permissions"] = ["quiz:view", "quiz:submit"]

        response = client.get("/api/test-create")
        self.assertEqual(response.status_code, 403)
        self.assertIn("Forbidden", response.get_json()["error"])

    def test_require_permission_admin_bypass(self):
        app = Flask(__name__)
        app.secret_key = "test-secret"

        @app.route("/api/test-secret-action")
        @require_permission("super:secret:action")
        def secret_route():
            return jsonify({"status": "admin_granted"}), 200

        client = app.test_client()

        # Test as Admin (bypasses check even though permission is not in list)
        with client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "admin"
            sess["roles"] = ["Admin"]
            sess["permissions"] = []

        response = client.get("/api/test-secret-action")
        self.assertEqual(response.status_code, 200)

    # 4. Atomic Transaction Rollback Tests
    @patch("app.repositories.quiz_repository.DatabaseConnection.get_connection")
    def test_quiz_repository_create_rollback_on_error(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Simulate exception during question insert
        mock_cursor.execute.side_effect = [None, Exception("DB Error inserting question")]

        repo = QuizRepository()
        opt = Option(id=None, question_id=None, option_text="A", is_correct=True)
        q = Question(id=None, quiz_id=None, prompt="Prompt?", points=1, options=[opt])
        quiz = Quiz(id=None, title="Test", description="", created_by=1, pass_percentage=50, questions=[q])

        with self.assertRaises(Exception):
            repo.create(quiz)

        # Verify rollback was called
        mock_conn.rollback.assert_called_once()
        mock_conn.commit.assert_not_called()

    # 5. Assessment Timer & CSV Export Tests
    def test_quiz_service_time_limit_parsing(self):
        mock_repo = MagicMock()
        service = QuizService(mock_repo)

        form_data = {
            "title": "Timed Assessment",
            "description": "Timed Exam",
            "pass_percentage": 75,
            "time_limit_minutes": 25,
            "questions": [
                {
                    "prompt": "What is OOP?",
                    "points": 2,
                    "options": [
                        {"text": "Object-Oriented Programming", "is_correct": True},
                        {"text": "Only One Process", "is_correct": False}
                    ]
                }
            ]
        }

        quiz = service.parse_quiz_form_data(form_data, creator_id=2)
        self.assertEqual(quiz.time_limit_minutes, 25)
        self.assertEqual(quiz.title, "Timed Assessment")
        self.assertEqual(quiz.pass_percentage, 75.0)

    def test_quiz_service_public_view_timer(self):
        mock_repo = MagicMock()
        mock_quiz = Quiz(
            id=10,
            title="Timed Midterm",
            description="Good luck!",
            created_by=2,
            pass_percentage=60.0,
            time_limit_minutes=45,
            questions=[
                Question(
                    id=1,
                    quiz_id=10,
                    prompt="Q1",
                    points=5,
                    options=[Option(id=1, question_id=1, option_text="Opt1", is_correct=True)]
                )
            ]
        )
        mock_repo.get_by_id.return_value = mock_quiz
        service = QuizService(mock_repo)

        public_view = service.get_public_quiz_view(10)
        self.assertIsNotNone(public_view)
        self.assertEqual(public_view["time_limit_minutes"], 45)
        self.assertNotIn("is_correct", public_view["questions"][0]["options"][0])

    @patch("app.routes.web_bp.quiz_service.get_responses_overview")
    def test_export_quiz_csv_authorized(self, mock_overview):
        from app import create_app
        test_app = create_app()
        test_app.config["TESTING"] = True

        mock_quiz = Quiz(id=5, title="Biology Final", description="", created_by=2)
        mock_sub = Submission(
            id=101,
            quiz_id=5,
            student_id=3,
            total_score=8.0,
            max_score=10.0,
            passed=True,
            teacher_feedback="Great work!",
            submitted_at="2026-09-22 20:00",
            student_username="student_john"
        )
        mock_overview.return_value = {
            "quiz": mock_quiz,
            "stats": {"total_responses": 1, "avg_score": 8.0, "pass_rate": 100.0},
            "submissions": [mock_sub]
        }

        client = test_app.test_client()
        with client.session_transaction() as sess:
            sess["user_id"] = 2
            sess["username"] = "teacher_jane"
            sess["roles"] = ["Teacher"]
            sess["permissions"] = ["report:view_all"]

        response = client.get("/teacher/quizzes/5/export-csv")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "text/csv")
        self.assertIn("attachment; filename=", response.headers.get("Content-Disposition", ""))

        csv_text = response.data.decode("utf-8")
        self.assertIn("Submission ID,Quiz ID,Quiz Title,Student Username", csv_text)
        self.assertIn("Biology Final", csv_text)
        self.assertIn("student_john", csv_text)
        self.assertIn("PASSED", csv_text)
        self.assertIn("Great work!", csv_text)

    def test_export_quiz_csv_forbidden_for_student(self):
        from app import create_app
        test_app = create_app()
        test_app.config["TESTING"] = True

        client = test_app.test_client()
        with client.session_transaction() as sess:
            sess["user_id"] = 3
            sess["username"] = "student_john"
            sess["roles"] = ["Student"]
            sess["permissions"] = ["quiz:view", "quiz:submit"]

        response = client.get("/teacher/quizzes/5/export-csv")
        # Student lacks report:view_all permission; should redirect with flash
        self.assertEqual(response.status_code, 302)

    def test_admin_dashboard_sequential_row_indexing_and_user_id_badge(self):
        from app import create_app
        test_app = create_app()
        test_app.config["TESTING"] = True

        client = test_app.test_client()
        with client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "admin"
            sess["roles"] = ["Admin"]
            sess["permissions"] = ["user:manage"]

        response = client.get("/admin/dashboard")
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")

        # Verify 'No.' table header
        self.assertIn('<th class="ps-4" style="width: 70px;">No.</th>', html)
        # Verify sequential numbering and User ID badges
        self.assertIn("User ID: #", html)

    @patch("app.repositories.user_repository.DatabaseConnection.get_connection")
    def test_user_repository_list_all_sql_ordering(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []

        repo = UserRepository()
        repo.list_all()

        # Check executed SQL statement contains ORDER BY id ASC
        called_sql = mock_cursor.execute.call_args[0][0]
        self.assertIn("ORDER BY id ASC", called_sql)

    @patch("app.repositories.quiz_repository.DatabaseConnection.get_connection")
    def test_quiz_repository_get_question_breakdown(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            {
                "question_id": 10,
                "prompt": "What is polymorphism?",
                "points": 5.0,
                "order_num": 1,
                "total_attempts": 4,
                "correct_count": 3
            },
            {
                "question_id": 11,
                "prompt": "What is encapsulation?",
                "points": 5.0,
                "order_num": 2,
                "total_attempts": 0,
                "correct_count": 0
            }
        ]

        repo = QuizRepository()
        breakdown = repo.get_question_breakdown(quiz_id=1)

        self.assertEqual(len(breakdown), 2)
        # Question 1: 3/4 = 75.0%
        self.assertEqual(breakdown[0]["question_id"], 10)
        self.assertEqual(breakdown[0]["total_attempts"], 4)
        self.assertEqual(breakdown[0]["correct_count"], 3)
        self.assertEqual(breakdown[0]["incorrect_count"], 1)
        self.assertEqual(breakdown[0]["accuracy_rate"], 75.0)

        # Question 2: 0 attempts = 0.0%
        self.assertEqual(breakdown[1]["question_id"], 11)
        self.assertEqual(breakdown[1]["total_attempts"], 0)
        self.assertEqual(breakdown[1]["accuracy_rate"], 0.0)

    def test_teacher_responses_view_renders_question_analytics(self):
        from app import create_app
        test_app = create_app()
        test_app.config["TESTING"] = True

        client = test_app.test_client()
        with client.session_transaction() as sess:
            sess["user_id"] = 2
            sess["username"] = "teacher_jane"
            sess["roles"] = ["Teacher"]
            sess["permissions"] = ["quiz:view", "report:view_all"]

        response = client.get("/teacher/quizzes/1/responses")
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")

        # Verify Question Performance section header and mastery components
        self.assertIn("Question Performance &amp; Item Analysis", html)
        self.assertIn("Accuracy rate and student answer distribution", html)
        self.assertIn("Mastery Progress Bar", html)

if __name__ == "__main__":
    unittest.main()
