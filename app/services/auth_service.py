# app/services/auth_service.py
from typing import List, Dict, Optional
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.repositories.audit_repository import AuditRepository

class AuthService:
    def __init__(self, user_repo: UserRepository, audit_repo: Optional[AuditRepository] = None):
        self.user_repo = user_repo
        self.audit_repo = audit_repo or AuditRepository()

    def authenticate(self, username: str, raw_password: str) -> User:
        """Authenticate user credentials and return User hydrated with RBAC roles & permissions."""
        user = self.user_repo.get_by_username(username)
        if not user or not check_password_hash(user.password_hash, raw_password):
            raise PermissionError("Invalid username or password.")
        if not user.is_active:
            raise PermissionError("Your account has been deactivated. Please contact an administrator.")
        return user

    def register_user(self, username: str, email: str, raw_password: str, role_name: str = "Student") -> int:
        """Register a new user and assign them to an RBAC role."""
        if not username or not raw_password or not email:
            raise ValueError("Username, email, and password are all required.")
        if self.user_repo.get_by_username(username):
            raise ValueError(f"Username '{username}' is already taken.")

        hashed_pw = generate_password_hash(raw_password)
        new_user = User(
            id=None,
            username=username.strip(),
            email=email.strip().lower(),
            password_hash=hashed_pw,
            is_active=True
        )
        return self.user_repo.create(new_user, role_name=role_name)

    def register_student(self, username: str, email: str, password: str, confirm_password: str) -> User:
        """
        Validates student self-registration, checks duplicate username & email,
        hashes password, delegates creation to repository with 'Student' role,
        and returns the created User domain object.
        """
        if not username or not username.strip():
            raise ValueError("Username is required.")
        if not email or not email.strip():
            raise ValueError("Email address is required.")
        if not password:
            raise ValueError("Password is required.")
        if not confirm_password:
            raise ValueError("Please confirm your password.")
        if password != confirm_password:
            raise ValueError("Passwords do not match.")

        username_clean = username.strip()
        email_clean = email.strip().lower()

        if self.user_repo.get_by_username(username_clean):
            raise ValueError(f"Username '{username_clean}' is already taken.")
        if self.user_repo.get_by_email(email_clean):
            raise ValueError(f"Email '{email_clean}' is already registered.")

        hashed_pw = generate_password_hash(password)
        new_user = User(
            id=None,
            username=username_clean,
            email=email_clean,
            password_hash=hashed_pw,
            is_active=True
        )

        user_id = self.user_repo.register(new_user, role_name="Student")
        created_user = self.user_repo.get_by_id(user_id)
        if not created_user:
            raise RuntimeError("Failed to retrieve user after registration.")
        return created_user

    # Admin Management Methods
    def list_all_users(self) -> List[User]:
        return self.user_repo.list_all()

    def update_user_role(self, user_id: int, new_role_name: str) -> bool:
        return self.user_repo.update_role(user_id, new_role_name)

    def toggle_user_status(self, user_id: int, is_active: bool) -> bool:
        return self.user_repo.toggle_active(user_id, is_active)

    def delete_user(self, user_id: int) -> bool:
        return self.user_repo.delete(user_id)

    def get_available_roles(self) -> List[Dict]:
        return self.user_repo.list_roles()

    def emergency_break_glass_login(self, username: str, raw_password: str, reason: str, ip_address: Optional[str] = None) -> User:
        """
        Validates emergency break-glass login, verifies administrative authority,
        and logs the incident reason to the immutable audit trail.
        """
        clean_reason = (reason or "").strip()
        if not clean_reason or len(clean_reason) < 8:
            raise ValueError("A clear, valid emergency justification reason (minimum 8 characters) is required.")

        user = self.authenticate(username, raw_password)
        if not user.is_admin:
            raise PermissionError("Access Denied: Only accounts with Administrative authority can execute the Break-Glass protocol.")

        # Log emergency event into security audit trail
        self.audit_repo.create_log(
            user_id=user.id,
            action="EMERGENCY_BREAK_GLASS_LOGIN",
            reason=clean_reason,
            ip_address=ip_address
        )
        return user

    def get_audit_logs(self, limit: int = 50) -> List[Dict]:
        """Fetch security and emergency audit logs for the admin dashboard."""
        return self.audit_repo.list_logs(limit=limit)