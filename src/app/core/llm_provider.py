# -*- coding: utf-8 -*-
"""
FinPilot AI — LLM Provider & AI Gateway Manager
================================================
Manages seamless multi-provider LLM initialization across:
1. OpenCode AI (OPENCODE_API_KEY + OPENCODE_BASE_URL)
2. OpenAI (OPENAI_API_KEY + OPENAI_BASE_URL)
3. Deterministic Financial Rule Engine (Graceful fallback when offline)
"""

import os
import logging
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from src.app.core.config import settings

logger = logging.getLogger("LLMProvider")


def mask_key(key: str) -> str:
    """Masks secret key safely for debugging and status responses (e.g. sk-Q3vn...swbK)."""
    if not key or len(key) < 10 or key.startswith("your_") or key.startswith("sk-placeholder"):
        return ""
    return f"{key[:7]}...{key[-5:]}"


class LLMProviderManager:
    """Singleton resolving and caching active LLM provider connections."""

    def __init__(self):
        self._llm: Optional[ChatOpenAI] = None
        self._active_provider: str = "Deterministic Rule Engine"
        self._initialize_llm()

    def _initialize_llm(self):
        # 1. Check for Gemini credentials (free tier or paid)
        gemini_key = (settings.GEMINI_API_KEY or "").strip()
        if gemini_key and not gemini_key.startswith("sk-placeholder") and not gemini_key.startswith("your_") and len(gemini_key) > 10:
            base_url = (settings.GEMINI_BASE_URL or "https://generativelanguage.googleapis.com/v1beta/openai/").strip()
            model = settings.GEMINI_MODEL or "gemini-3.5-flash"
            try:
                self._llm = ChatOpenAI(
                    model=model,
                    api_key=gemini_key,
                    base_url=base_url,
                    temperature=0.2,
                    timeout=30.0,
                    max_retries=2,
                )
                self._active_provider = "Google Gemini"
                logger.info(f"[LLMProvider] Initialized Google Gemini with model '{model}' at '{base_url}'")
                return
            except Exception as e:
                logger.warning(f"[LLMProvider] Failed initializing Google Gemini: {e}")

        # 2. Check for OpenCode AI credentials
        opencode_key = (settings.OPENCODE_API_KEY or "").strip()
        if opencode_key and not opencode_key.startswith("sk-placeholder") and len(opencode_key) > 15:
            base_url = (settings.OPENCODE_BASE_URL or "https://opencode.ai/zen/v1").strip()
            model = settings.SUPERVISOR_MODEL or "gpt-4o-mini"
            try:
                self._llm = ChatOpenAI(
                    model=model,
                    api_key=opencode_key,
                    base_url=base_url,
                    temperature=0.2,
                    timeout=30.0,
                    max_retries=2,
                )
                self._active_provider = "OpenCode AI"
                logger.info(f"[LLMProvider] Initialized OpenCode AI with model '{model}' at '{base_url}'")
                return
            except Exception as e:
                logger.warning(f"[LLMProvider] Failed initializing OpenCode AI: {e}")

        # 3. Check for OpenAI credentials
        openai_key = (settings.OPENAI_API_KEY or "").strip()
        if openai_key and not openai_key.startswith("sk-placeholder") and len(openai_key) > 15:
            base_url = (settings.OPENAI_BASE_URL or "").strip() or None
            model = settings.SUPERVISOR_MODEL or "gpt-4o-mini"
            try:
                kwargs = {
                    "model": model,
                    "api_key": openai_key,
                    "temperature": 0.2,
                    "timeout": 30.0,
                    "max_retries": 2,
                }
                if base_url:
                    kwargs["base_url"] = base_url
                self._llm = ChatOpenAI(**kwargs)
                self._active_provider = "OpenAI"
                logger.info(f"[LLMProvider] Initialized OpenAI with model '{model}'")
                return
            except Exception as e:
                logger.warning(f"[LLMProvider] Failed initializing OpenAI: {e}")

        self._llm = None
        self._active_provider = "Deterministic Rule Engine"
        logger.info("[LLMProvider] Operating in Deterministic Financial Rule Engine mode (Zero LLM math / zero hallucination).")

    def get_llm(self, temperature: float = 0.2) -> Optional[ChatOpenAI]:
        """Returns the configured LLM client instance or None if operating in rule engine mode."""
        return self._llm

    def get_status(self) -> Dict[str, Any]:
        """Returns AI readiness, provider details, and masked key preview."""
        has_gemini = bool(settings.GEMINI_API_KEY and not settings.GEMINI_API_KEY.startswith("your_") and len(settings.GEMINI_API_KEY) > 10)
        has_opencode = bool(settings.OPENCODE_API_KEY and not settings.OPENCODE_API_KEY.startswith("your_") and not settings.OPENCODE_API_KEY.startswith("sk-placeholder") and len(settings.OPENCODE_API_KEY) > 15)
        has_openai = bool(settings.OPENAI_API_KEY and not settings.OPENAI_API_KEY.startswith("your_") and not settings.OPENAI_API_KEY.startswith("sk-placeholder") and len(settings.OPENAI_API_KEY) > 15)
        active_key = settings.GEMINI_API_KEY if has_gemini else (settings.OPENCODE_API_KEY if has_opencode else (settings.OPENAI_API_KEY if has_openai else ""))
        active_model = settings.GEMINI_MODEL if has_gemini else (settings.SUPERVISOR_MODEL or "gpt-4o-mini")
        active_base = settings.GEMINI_BASE_URL if has_gemini else (settings.OPENCODE_BASE_URL if has_opencode else (settings.OPENAI_BASE_URL or "https://api.openai.com/v1"))

        return {
            "ai_ready": self._llm is not None,
            "active_provider": self._active_provider,
            "model": active_model,
            "base_url": active_base,
            "providers_configured": {
                "gemini": has_gemini,
                "opencode_ai": has_opencode,
                "openai": has_openai,
            },
            "key_preview": mask_key(active_key) if active_key else "None (Using Deterministic Financial Engine)",
            "governance_mode": "Zero-Trust Deterministic Financial Rails",
        }


llm_manager = LLMProviderManager()
