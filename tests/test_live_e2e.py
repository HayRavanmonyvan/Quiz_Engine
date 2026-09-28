# tests/test_live_e2e.py
import unittest
from app import create_app
from app.repositories.user_repository import UserRepository

class LiveE2ETestSuite(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.user_repo = UserRepository()

    def test_live_database_users_and_5_table_rbac_hydration(self):
        # 1. Admin
        admin = self.user_repo.get_by_username("admin")
        self.assertIsNotNone(admin)
        self.assertIn("Admin", admin.roles)
        self.assertTrue(admin.is_admin)
        self.assertTrue(admin.has_permission("user:manage"))
        self.assertTrue(admin.has_permission("quiz:delete"))
        self.assertTrue(admin.has_permission("arbitrary:wildcard"))

        # 2. Teacher
        teacher = self.user_repo.get_by_username("teacher_jane")
        self.assertIsNotNone(teacher)
        self.assertIn("Teacher", teacher.roles)
        self.assertTrue(teacher.is_teacher)
        self.assertTrue(teacher.has_permission("quiz:create"))
        self.assertTrue(teacher.has_permission("report:view_all"))
        self.assertFalse(teacher.has_permission("user:manage"))

        # 3. Student
        student = self.user_repo.get_by_username("student_john")
        self.assertIsNotNone(student)
        self.assertIn("Student", student.roles)
        self.assertTrue(student.is_student)
        self.assertTrue(student.has_permission("quiz:view"))
        self.assertTrue(student.has_permission("quiz:submit"))
        self.assertFalse(student.has_permission("quiz:create"))
        self.assertFalse(student.has_permission("user:manage"))

    def test_role_navigation_and_access_controls(self):
        # 1. Anonymous user redirected to login
        res = self.client.get("/teacher/dashboard", follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertIn("/login", res.headers["Location"])

        # 2. Student signs in via demo-login
        res = self.client.get("/demo-login/student", follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"student_john", res.data)

        # Student accesses quiz list -> 200 OK
        res = self.client.get("/quizzes")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Available Assessments", res.data)

        # Student attempts to access Admin console -> redirected with error
        res = self.client.get("/admin/dashboard", follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Access Denied", res.data)

        # Student attempts to access Teacher quiz builder -> redirected with error
        res = self.client.get("/teacher/quizzes/new", follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Access Denied", res.data)

        # 3. Teacher signs in via demo-login
        res = self.client.get("/demo-login/teacher", follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"teacher_jane", res.data)

        # Teacher accesses Teacher Hub -> 200 OK
        res = self.client.get("/teacher/dashboard")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Teacher Management Hub", res.data)

        # Teacher accesses Quiz Builder -> 200 OK
        res = self.client.get("/teacher/quizzes/new")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Google Form Builder", res.data)

        # Teacher attempts to access Admin Console -> denied
        res = self.client.get("/admin/dashboard", follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Access Denied", res.data)

        # 4. Admin signs in via demo-login
        res = self.client.get("/demo-login/admin", follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"admin", res.data)

        # Admin accesses Admin Console -> 200 OK
        res = self.client.get("/admin/dashboard")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Admin Command Center", res.data)

        # Admin can also access Teacher Hub -> 200 OK
        res = self.client.get("/teacher/dashboard")
        self.assertEqual(res.status_code, 200)

    def test_quiz_attempt_and_teacher_grading_flow(self):
        # 1. Sign in as Student
        self.client.get("/demo-login/student", follow_redirects=True)

        # 2. Student views quiz questionnaire page (Google Form UI)
        res = self.client.get("/quizzes/1")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Submit Assessment", res.data)

        # 3. Submit quiz attempt for Quiz 1
        from app.repositories.quiz_repository import QuizRepository
        quiz = QuizRepository().get_by_id(1)
        form_payload = {}
        for q in quiz.questions:
            correct_opt = next((opt for opt in q.options if opt.is_correct), q.options[0])
            form_payload[f"question_{q.id}"] = str(correct_opt.id)

        res = self.client.post("/quizzes/1/submit", data=form_payload, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Assessment Results", res.data)
        self.assertIn(b"PASSED", res.data)

        # 3. Sign in as Teacher
        self.client.get("/demo-login/teacher", follow_redirects=True)

        # 4. Teacher views responses tab
        res = self.client.get("/teacher/quizzes/1/responses")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"student_john", res.data)

if __name__ == "__main__":
    unittest.main()
