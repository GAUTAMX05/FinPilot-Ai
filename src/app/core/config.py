import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "FinPilot AI"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/v1"

    # LLM Settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    SUPERVISOR_MODEL: str = os.getenv("SUPERVISOR_MODEL", "gpt-4o-mini")
    SUB_AGENT_MODEL: str = os.getenv("SUB_AGENT_MODEL", "gpt-4o-mini")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

    # Razorpay Settings
    RAZORPAY_KEY_ID: str = os.getenv("RAZORPAY_KEY_ID", "rzp_test_placeholder")
    RAZORPAY_KEY_SECRET: str = os.getenv("RAZORPAY_KEY_SECRET", "secret_placeholder")

    # Financial Governance & Policy Thresholds
    HITL_APPROVAL_THRESHOLD_INR: float = float(os.getenv("HITL_APPROVAL_THRESHOLD_INR", "50000.0"))
    AUTONOMOUS_PAYOUT_LIMIT_INR: float = float(os.getenv("AUTONOMOUS_PAYOUT_LIMIT_INR", "10000.0"))

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "allow"


settings = Settings()
