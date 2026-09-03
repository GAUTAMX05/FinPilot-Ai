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

    # LLM Provider Credentials (provider-agnostic, OpenCode-compatible)
    # See src/app/services/llm_provider.py for resolution order.
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "")
    SUPERVISOR_MODEL: str = os.getenv("SUPERVISOR_MODEL", os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    SUB_AGENT_MODEL: str = os.getenv("SUB_AGENT_MODEL", os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-latest")
    # OpenCode / generic OpenAI-compatible gateway
    OPENCODE_API_KEY: str = os.getenv("OPENCODE_API_KEY", "")
    OPENCODE_BASE_URL: str = os.getenv("OPENCODE_BASE_URL", "https://opencode.ai/zen/v1")
    OPENCODE_MODEL: str = os.getenv("OPENCODE_MODEL", "")
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "auto")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "")

    # Database (Postgres-ready: Supabase / Neon via DATABASE_URL, SQLite fallback)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")

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
