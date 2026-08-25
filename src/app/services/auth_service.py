import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from src.app.core.rbac import (
    Role,
    Permission,
    ROLE_PERMISSIONS,
    hash_password,
    verify_password,
    create_access_token,
)

logger = logging.getLogger("AuthService")


class AuthService:
    def __init__(self):
        self._users: Dict[str, Dict[str, Any]] = {}
        self._init_demo_users()

    def _init_demo_users(self):
        """Initializes demo accounts with hashed passwords."""
        default_password = "password123"
        hashed = hash_password(default_password)

        demo_users = [
            {
                "id": "usr_cfo_001",
                "name": "Vikramaditya Singhania",
                "email": "cfo@aifinance.local",
                "password_hash": hashed,
                "role": Role.CFO.value,
                "department": None,
                "is_active": True,
                "created_at": datetime.now().isoformat(),
            },
            {
                "id": "usr_fm_002",
                "name": "Rahul Sharma",
                "email": "finance.manager@aifinance.local",
                "password_hash": hashed,
                "role": Role.FINANCE_MANAGER.value,
                "department": None,
                "is_active": True,
                "created_at": datetime.now().isoformat(),
            },
            {
                "id": "usr_dh_003",
                "name": "Priya Verma",
                "email": "engineering.head@aifinance.local",
                "password_hash": hashed,
                "role": Role.DEPARTMENT_HEAD.value,
                "department": "Engineering",
                "is_active": True,
                "created_at": datetime.now().isoformat(),
            },
            {
                "id": "usr_aud_004",
                "name": "Kavita Iyer",
                "email": "auditor@aifinance.local",
                "password_hash": hashed,
                "role": Role.AUDITOR.value,
                "department": None,
                "is_active": True,
                "created_at": datetime.now().isoformat(),
            },
        ]

        for u in demo_users:
            self._users[u["email"]] = u

    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticates user credentials and returns user payload + token if valid."""
        user = self._users.get(email.strip().lower())
        if not user or not user.get("is_active"):
            return None

        if not verify_password(password, user["password_hash"]):
            return None

        # Build clean user data without password hash
        user_info = {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
            "department": user["department"],
            "is_active": user["is_active"],
            "permissions": [p.value for p in ROLE_PERMISSIONS.get(Role(user["role"]), set())],
        }

        token = create_access_token(user_info)
        return {
            "user": user_info,
            "access_token": token,
            "token_type": "bearer",
        }

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        for u in self._users.values():
            if u["id"] == user_id:
                return {
                    "id": u["id"],
                    "name": u["name"],
                    "email": u["email"],
                    "role": u["role"],
                    "department": u["department"],
                    "is_active": u["is_active"],
                    "permissions": [p.value for p in ROLE_PERMISSIONS.get(Role(u["role"]), set())],
                }
        return None

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        u = self._users.get(email.strip().lower())
        if u:
            return {
                "id": u["id"],
                "name": u["name"],
                "email": u["email"],
                "role": u["role"],
                "department": u["department"],
                "is_active": u["is_active"],
                "permissions": [p.value for p in ROLE_PERMISSIONS.get(Role(u["role"]), set())],
            }
        return None

    def list_all_users(self) -> List[Dict[str, Any]]:
        """Returns all registered users (for CFO administration)."""
        res = []
        for u in self._users.values():
            res.append({
                "id": u["id"],
                "name": u["name"],
                "email": u["email"],
                "role": u["role"],
                "department": u["department"],
                "is_active": u["is_active"],
                "created_at": u.get("created_at"),
            })
        return res

    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        email = user_data["email"].strip().lower()
        if email in self._users:
            raise ValueError(f"User with email '{email}' already exists.")

        user_id = f"usr_{int(datetime.now().timestamp())}"
        hashed = hash_password(user_data.get("password", "password123"))

        new_user = {
            "id": user_id,
            "name": user_data["name"],
            "email": email,
            "password_hash": hashed,
            "role": user_data["role"],
            "department": user_data.get("department"),
            "is_active": True,
            "created_at": datetime.now().isoformat(),
        }
        self._users[email] = new_user
        return new_user

    def get_demo_accounts(self) -> List[Dict[str, str]]:
        """Returns demo accounts for quick switcher."""
        return [
            {"name": "Vikramaditya Singhania", "email": "cfo@aifinance.local", "role": "CFO", "dept": "Executive"},
            {"name": "Rahul Sharma", "email": "finance.manager@aifinance.local", "role": "FINANCE_MANAGER", "dept": "Finance Ops"},
            {"name": "Priya Verma", "email": "engineering.head@aifinance.local", "role": "DEPARTMENT_HEAD", "dept": "Engineering"},
            {"name": "Kavita Iyer", "email": "auditor@aifinance.local", "role": "AUDITOR", "dept": "Compliance"},
        ]


auth_service = AuthService()
