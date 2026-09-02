# -*- coding: utf-8 -*-
"""
FinPilot AI — Platform Configuration Settings
==============================================
Manages environment variables, LLM credentials, Razorpay API keys,
and operational governance thresholds with Pydantic validation.
"""

import os
from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "FinPilot AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/v1"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production" if os.getenv("RENDER") else "development")

    # LLM Provider Credentials
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    SUPERVISOR_MODEL: str = os.getenv("SUPERVISOR_MODEL", "gpt-4o-mini")
    SUB_AGENT_MODEL: str = os.getenv("SUB_AGENT_MODEL", "gpt-4o-mini")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

    # Razorpay Payment Rails & Gateway Configuration
    RAZORPAY_KEY_ID: str = os.getenv("RAZORPAY_KEY_ID", "rzp_test_placeholder")
    RAZORPAY_KEY_SECRET: str = os.getenv("RAZORPAY_KEY_SECRET", "secret_placeholder")

    # Financial Governance & Policy Thresholds (INR)
    HITL_APPROVAL_THRESHOLD_INR: float = float(os.getenv("HITL_APPROVAL_THRESHOLD_INR", "50000.0"))
    AUTONOMOUS_PAYOUT_LIMIT_INR: float = float(os.getenv("AUTONOMOUS_PAYOUT_LIMIT_INR", "10000.0"))

    model_config = ConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="allow"
    )


settings = Settings()
