# tests/test_break_glass.py
import unittest
from unittest.mock import MagicMock, patch
from app.models.user import User
from app.services.auth_service import AuthService
from app.repositories.user_repository import UserRepository
from app.repositories.audit_repository import AuditRepository

class BreakGlassTestSuite(unittest.TestCase):
    def setUp(self):
        self.mock_user_repo = MagicMock(spec=UserRepository)
        self.mock_audit_repo = MagicMock(spec=AuditRepository)
        self.auth_service = AuthService(self.mock_user_repo, self.mock_audit_repo)

        # Mock Admin User
        self.admin_user = User(
            id=99,
            username="emergency_admin",
            email="emergency@institute.edu",
            password_hash="scrypt:dummy_hash",
            is_active=True,
            roles=["Admin"],
            permissions=["user:manage", "quiz:create"]
        )

        # Mock Teacher User (Non-Admin)
        self.teacher_user = User(
            id=2,
            username="teacher_jane",
            email="jane@institute.edu",
            password_hash="scrypt:dummy_hash",
            is_active=True,
            roles=["Teacher"],
            permissions=["quiz:create", "quiz:score"]
        )

    def test_break_glass_fails_on_empty_reason(self):
        with self.assertRaises(ValueError) as ctx:
            self.auth_service.emergency_break_glass_login("emergency_admin", "pass", reason="")
        self.assertIn("minimum 8 characters", str(ctx.exception))

    def test_break_glass_fails_on_short_reason(self):
        with self.assertRaises(ValueError) as ctx:
            self.auth_service.emergency_break_glass_login("emergency_admin", "pass", reason="sick")
        self.assertIn("minimum 8 characters", str(ctx.exception))

    @patch("app.services.auth_service.check_password_hash")
    def test_break_glass_fails_for_non_admin_account(self, mock_check_hash):
        mock_check_hash.return_value = True
        self.mock_user_repo.get_by_username.return_value = self.teacher_user

        with self.assertRaises(PermissionError) as ctx:
            self.auth_service.emergency_break_glass_login(
                "teacher_jane", "pass", 
                reason="Primary administrator is absent due to illness."
            )
        self.assertIn("Only accounts with Administrative authority", str(ctx.exception))

    @patch("app.services.auth_service.check_password_hash")
    def test_break_glass_succeeds_for_admin_and_records_audit_log(self, mock_check_hash):
        mock_check_hash.return_value = True
        self.mock_user_repo.get_by_username.return_value = self.admin_user

        reason = "Primary admin hospitalized; urgent authorization by Department Head."
        user = self.auth_service.emergency_break_glass_login(
            "emergency_admin", "valid_pass",
            reason=reason,
            ip_address="192.168.1.100"
        )

        self.assertEqual(user.username, "emergency_admin")
        self.assertTrue(user.is_admin)

        # Verify audit log was recorded with exact parameters
        self.mock_audit_repo.create_log.assert_called_once_with(
            user_id=99,
            action="EMERGENCY_BREAK_GLASS_LOGIN",
            reason=reason,
            ip_address="192.168.1.100"
        )

    def test_break_glass_route_get(self):
        from app import create_app
        test_app = create_app()
        test_app.config["TESTING"] = True
        client = test_app.test_client()

        response = client.get("/break-glass")
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")
        self.assertIn("Emergency Break-Glass Access", html)
        self.assertIn("RESTRICTED ACCESS PROTOCOL", html)
        self.assertIn("Mandatory Incident Justification", html)

    def test_break_glass_route_post_success(self):
        from app import create_app
        test_app = create_app()
        test_app.config["TESTING"] = True
        client = test_app.test_client()

        with patch("app.routes.web_bp.auth_service.emergency_break_glass_login") as mock_login:
            mock_login.return_value = self.admin_user

            response = client.post("/break-glass", data={
                "username": "emergency_admin",
                "password": "BreakGlass@911",
                "reason": "Primary Administrator is on emergency leave; authorized by Dean."
            }, follow_redirects=False)

            self.assertEqual(response.status_code, 302)
            self.assertIn("/admin/dashboard", response.headers["Location"])

            # Verify emergency session was activated
            with client.session_transaction() as sess:
                self.assertTrue(sess.get("is_emergency_session"))
                self.assertIn("Primary Administrator is on emergency leave", sess.get("emergency_reason"))

if __name__ == "__main__":
    unittest.main()
