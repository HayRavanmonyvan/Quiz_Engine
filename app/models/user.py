# app/models/user.py
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class User:
    id: Optional[int]
    username: str
    email: str
    password_hash: str
    is_active: bool = True
    roles: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)

    def has_role(self, role_name: str) -> bool:
        """Check if the user is assigned a specific role (case-insensitive)."""
        return role_name.lower() in [r.lower() for r in self.roles]

    def has_permission(self, permission_name: str) -> bool:
        """
        Check if the user has a specific granular permission.
        Admins automatically bypass all permission checks per RBAC specifications.
        """
        if self.has_role("Admin"):
            return True
        return permission_name in self.permissions

    @property
    def is_admin(self) -> bool:
        return self.has_role("Admin")

    @property
    def is_teacher(self) -> bool:
        return self.has_role("Teacher") or self.has_role("Instructor")

    @property
    def is_student(self) -> bool:
        return self.has_role("Student")

    @property
    def primary_role(self) -> str:
        if self.is_admin:
            return "Admin"
        if self.is_teacher:
            return "Teacher"
        if self.is_student:
            return "Student"
        return self.roles[0] if self.roles else "User"