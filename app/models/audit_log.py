# app/models/audit_log.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class AuditLog:
    id: Optional[int]
    user_id: Optional[int]
    action: str
    reason: str
    ip_address: Optional[str] = None
    created_at: Optional[str] = None
    username: Optional[str] = None
