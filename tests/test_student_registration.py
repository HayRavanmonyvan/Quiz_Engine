# tests/test_student_registration.py
import unittest
from unittest.mock import MagicMock
from app import create_app
from app.models.user import User
from app.services.auth_service import AuthService
from app.repositories.user_repository import UserRepository

class StudentRegistrationUnitTest(unittest.TestCase):
    def setUp(self):
        self.mock_user_repo = MagicMock()
        self.auth_service = AuthService(self.mock_user_repo)

    def test_registration_fails_missing_fields(self):
        with self.assertRaises(ValueError) as ctx:
            self.auth_service.register_student("", "email@test.com", "pass123", "pass123")
        self.assertIn("Username is required", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            self.auth_service.register_student("user1", "", "pass123", "pass123")
        self.assertIn("Email address is required", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            self.auth_service.register_student("user1", "email@test.com", "", "pass123")
        self.assertIn("Password is required", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            self.auth_service.register_student("user1", "email@test.com", "pass123", "")
        self.assertIn("Please confirm your password", str(ctx.exception))

    def test_registration_fails_password_mismatch(self):
        with self.assertRaises(ValueError) as ctx:
            self.auth_service.register_student("user1", "email@test.com", "Password@123", "Mismatch@456")
        self.assertIn("Passwords do not match", str(ctx.exception))

    def test_registration_fails_duplicate_username(self):
        existing_user = User(id=1, username="taken_user", email="other@test.com", password_hash="hash")
        self.mock_user_repo.get_by_username.return_value = existing_user

        with self.assertRaises(ValueError) as ctx:
            self.auth_service.register_student("taken_user", "new@test.com", "Pass@123", "Pass@123")
        self.assertIn("already taken", str(ctx.exception))

    def test_registration_fails_duplicate_email(self):
        self.mock_user_repo.get_by_username.return_value = None
        existing_user = User(id=1, username="other_user", email="taken@test.com", password_hash="hash")
        self.mock_user_repo.get_by_email.return_value = existing_user

        with self.assertRaises(ValueError) as ctx:
            self.auth_service.register_student("new_user", "taken@test.com", "Pass@123", "Pass@123")
        self.assertIn("already registered", str(ctx.exception))

    def test_registration_successful_assigns_student_role(self):
        self.mock_user_repo.get_by_username.return_value = None
        self.mock_user_repo.get_by_email.return_value = None
        self.mock_user_repo.register.return_value = 99

        hydrated_user = User(
            id=99,
            username="student_new",
            email="new@student.edu",
            password_hash="hashed_pw",
            is_active=True,
            roles=["Student"],
            permissions=["quiz:view", "quiz:submit", "report:view_own"]
        )
        self.mock_user_repo.get_by_id.return_value = hydrated_user

        created = self.auth_service.register_student(
            username="student_new",
            email="new@student.edu",
            password="Password@123",
            confirm_password="Password@123"
        )

        self.mock_user_repo.register.assert_called_once()
        args, kwargs = self.mock_user_repo.register.call_args
        self.assertEqual(kwargs.get("role_name"), "Student")
        self.assertEqual(created.id, 99)
        self.assertEqual(created.username, "student_new")
        self.assertIn("Student", created.roles)
        self.assertTrue(created.is_student)
        self.assertTrue(created.has_permission("quiz:view"))
        self.assertTrue(created.has_permission("quiz:submit"))
        self.assertFalse(created.has_permission("quiz:create"))


class StudentRegistrationIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.user_repo = UserRepository()

    def test_registration_flow_and_session(self):
        import uuid
        unique_suffix = str(uuid.uuid4())[:8]
        username = f"sam_{unique_suffix}"
        email = f"sam_{unique_suffix}@student.edu"

        # 1. Anonymous user visits /register
        res = self.client.get("/register")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Student Sign Up", res.data)

        # 2. Submit with password mismatch -> fails gracefully
        payload_mismatch = {
            "username": username,
            "email": email,
            "password": "Password@123",
            "confirm_password": "WrongPassword"
        }
        res = self.client.post("/register", data=payload_mismatch, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Passwords do not match", res.data)

        # 3. Submit valid student registration
        payload_valid = {
            "username": username,
            "email": email,
            "password": "Password@123",
            "confirm_password": "Password@123"
        }
        res = self.client.post("/register", data=payload_valid, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Welcome", res.data)
        self.assertIn(b"Available Assessments", res.data)

        # 4. Verify user in database has 'Student' role
        created_user = self.user_repo.get_by_username(username)
        self.assertIsNotNone(created_user)
        self.assertIn("Student", created_user.roles)
        self.assertTrue(created_user.is_student)
        self.assertTrue(created_user.has_permission("quiz:view"))
        self.assertTrue(created_user.has_permission("quiz:submit"))
        self.assertFalse(created_user.has_permission("user:manage"))

        # 5. Accessing /register while logged in redirects to /quizzes
        res = self.client.get("/register", follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertIn("/quizzes", res.headers["Location"])

        # 6. Attempting duplicate registration triggers validation error
        # Log out first
        self.client.get("/logout", follow_redirects=True)
        dup_payload = {
            "username": username,
            "email": f"diff_{unique_suffix}@student.edu",
            "password": "Password@123",
            "confirm_password": "Password@123"
        }
        res = self.client.post("/register", data=dup_payload, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"already taken", res.data)

        # Clean up created test user from database
        if created_user and created_user.id:
            self.user_repo.delete(created_user.id)

if __name__ == "__main__":
    unittest.main()
