# app/models/role.py
from dataclasses import dataclass

@dataclass(frozen=True)
class Permission:
    id: int
    name: str
    description: str

@dataclass(frozen=True)
class Role:
    id: int
    name: str
    description: str