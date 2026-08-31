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
                "id": "CFO-001",
                "aliases": ["usr_cfo_001", "cfo"],
                "name": "Vikramaditya Singhania",
                "email": "cfo@aifinance.local",
                "password_hash": hashed,
                "role": Role.CFO.value,
                "department": None,
                "is_active": True,
                "created_at": datetime.now().isoformat(),
            },
            {
                "id": "FIN-MGR-001",
                "aliases": ["usr_fm_002", "fm", "financemanager"],
                "name": "Rahul Verma",
                "email": "finance.manager@aifinance.local",
                "password_hash": hashed,
                "role": Role.FINANCE_MANAGER.value,
                "department": None,
                "is_active": True,
                "created_at": datetime.now().isoformat(),
            },
            {
                "id": "ENG-HEAD-001",
                "aliases": ["usr_dh_003", "depthead", "head"],
                "name": "Arjun Mehta",
                "email": "engineering.head@aifinance.local",
                "password_hash": hashed,
                "role": Role.DEPARTMENT_HEAD.value,
                "department": "Engineering",
                "is_active": True,
                "created_at": datetime.now().isoformat(),
            },
            {
                "id": "MKT-HEAD-001",
                "aliases": ["mkt_head"],
                "name": "Sunita Rao",
                "email": "marketing.head@aifinance.local",
                "password_hash": hashed,
                "role": Role.DEPARTMENT_HEAD.value,
                "department": "Marketing",
                "is_active": True,
                "created_at": datetime.now().isoformat(),
            },
            {
                "id": "SALES-HEAD-001",
                "aliases": ["sales_head"],
                "name": "Rajesh Kapoor",
                "email": "sales.head@aifinance.local",
                "password_hash": hashed,
                "role": Role.DEPARTMENT_HEAD.value,
                "department": "Sales",
                "is_active": True,
                "created_at": datetime.now().isoformat(),
            },
            {
                "id": "HR-HEAD-001",
                "aliases": ["hr_head"],
                "name": "Meera Patel",
                "email": "hr.head@aifinance.local",
                "password_hash": hashed,
                "role": Role.DEPARTMENT_HEAD.value,
                "department": "HR",
                "is_active": True,
                "created_at": datetime.now().isoformat(),
            },
            {
                "id": "AUDITOR-001",
                "aliases": ["usr_aud_004", "auditor"],
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
        email_clean = email.strip().lower()
        user = self._users.get(email_clean)
        
        # Comprehensive alias & ID fallback lookup
        if not user:
            for u in self._users.values():
                aliases = [a.lower() for a in u.get("aliases", [])]
                email_prefix = email_clean.split("@")[0]
                user_email_prefix = u["email"].lower().split("@")[0]
                if (
                    email_clean == u["id"].lower()
                    or email_clean in aliases
                    or email_prefix in aliases
                    or email_prefix == u["id"].lower()
                    or email_prefix == user_email_prefix
                ):
                    user = u
                    break

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
        if not user_id:
            return None
        uid_clean = user_id.strip()
        for u in self._users.values():
            if u["id"] == uid_clean or uid_clean in u.get("aliases", []):
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
        if not email:
            return None
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
        """Returns all registered users."""
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

    def get_directory_for_user(self, current_user: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Returns the permitted list of recipient users for communication based on role routing rules:
        - CFO can communicate with: Finance Manager, Department Heads, Auditor
        - Finance Manager can communicate with: CFO, Department Heads, Auditor
        - Department Head can communicate with: Finance Manager, CFO
        - Auditor can communicate with: Finance Manager, CFO
        """
        role = current_user.get("role", "CFO")
        current_id = current_user.get("id")
        
        all_users = self.list_all_users()
        eligible = []
        
        for u in all_users:
            if u["id"] == current_id:
                continue # Skip self in direct recipient picker
                
            u_role = u["role"]
            if role == Role.CFO.value:
                # CFO can message anyone
                eligible.append(u)
            elif role == Role.FINANCE_MANAGER.value:
                # Finance Manager can message CFO, Dept Heads, Auditor
                eligible.append(u)
            elif role == Role.DEPARTMENT_HEAD.value:
                # Dept Head can message Finance Manager, CFO
                if u_role in [Role.FINANCE_MANAGER.value, Role.CFO.value]:
                    eligible.append(u)
            elif role == Role.AUDITOR.value:
                # Auditor can message Finance Manager, CFO
                if u_role in [Role.FINANCE_MANAGER.value, Role.CFO.value]:
                    eligible.append(u)
                    
        return eligible

    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        email = user_data["email"].strip().lower()
        if email in self._users:
            raise ValueError(f"User with email '{email}' already exists.")

        user_id = user_data.get("id") or f"usr_{int(datetime.now().timestamp())}"
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
            {"id": "CFO-001", "name": "Vikramaditya Singhania", "email": "cfo@aifinance.local", "role": "CFO", "dept": "Executive"},
            {"id": "FIN-MGR-001", "name": "Rahul Verma", "email": "finance.manager@aifinance.local", "role": "FINANCE_MANAGER", "dept": "Finance Ops"},
            {"id": "ENG-HEAD-001", "name": "Arjun Mehta", "email": "engineering.head@aifinance.local", "role": "DEPARTMENT_HEAD", "dept": "Engineering"},
            {"id": "MKT-HEAD-001", "name": "Sunita Rao", "email": "marketing.head@aifinance.local", "role": "DEPARTMENT_HEAD", "dept": "Marketing"},
            {"id": "AUDITOR-001", "name": "Kavita Iyer", "email": "auditor@aifinance.local", "role": "AUDITOR", "dept": "Compliance"},
        ]


auth_service = AuthService()
