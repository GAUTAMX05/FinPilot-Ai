# -*- coding: utf-8 -*-
"""
FinPilot AI — Platform Configuration Settings
==============================================
Manages environment variables, LLM credentials (OpenCode AI / OpenAI),
PostgreSQL / SQLite database connection, Razorpay API keys,
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

    # Database Configuration (PostgreSQL / Supabase / Render Postgres / SQLite fallback)
    # NOTE: No credentials are defaulted here. Set DATABASE_URL (or POSTGRES_URL /
    # SUPABASE_DB_URL) in the environment (.env locally, Render dashboard in prod).
    # Empty default => deterministic local SQLite fallback.
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        os.getenv("POSTGRES_URL", os.getenv("SUPABASE_DB_URL", ""))
    )
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "https://eymvupzaiqvhfawunyoa.supabase.co")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")

    # LLM Provider Credentials & Base URLs (Gemini / OpenCode AI / OpenAI)
    # NOTE: API keys must come from the environment. Never commit real keys.
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", ""))
    GEMINI_BASE_URL: str = os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

    OPENCODE_API_KEY: str = os.getenv("OPENCODE_API_KEY", "")
    OPENCODE_BASE_URL: str = os.getenv("OPENCODE_BASE_URL", "https://opencode.ai/zen/v1")
    OPENCODE_MODEL: str = os.getenv("OPENCODE_MODEL", "")
    
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "")
    
    SUPERVISOR_MODEL: str = os.getenv("SUPERVISOR_MODEL", "gpt-4o-mini")
    SUB_AGENT_MODEL: str = os.getenv("SUB_AGENT_MODEL", "gpt-4o-mini")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-latest")

    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "auto")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "")

    # Razorpay Payment Rails & Gateway Configuration
    RAZORPAY_KEY_ID: str = os.getenv("RAZORPAY_KEY_ID", "rzp_test_placeholder")
    RAZORPAY_KEY_SECRET: str = os.getenv("RAZORPAY_KEY_SECRET", "secret_placeholder")

    # Financial Governance & Policy Thresholds (INR)
    HITL_APPROVAL_THRESHOLD_INR: float = float(os.getenv("HITL_APPROVAL_THRESHOLD_INR", "50000.0"))
    AUTONOMOUS_PAYOUT_LIMIT_INR: float = float(os.getenv("AUTONOMOUS_PAYOUT_LIMIT_INR", "10000.0"))

    # CORS Allowed Origins
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "*")

    model_config = ConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="allow"
    )


settings = Settings()
