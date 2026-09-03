# -*- coding: utf-8 -*-
"""
FinPilot AI — Provider-Agnostic LLM Layer (OpenCode / OpenAI-compatible)
========================================================================
Gives the whole project a single AI entrypoint that works with:
  1. OpenCode AI (OPENCODE_API_KEY + optional OPENCODE_BASE_URL)
  2. OpenAI (OPENAI_API_KEY + optional OPENAI_BASE_URL + OPENAI_MODEL)
  3. Groq, Anthropic, or OpenAI-compatible gateways
  4. Deterministic Financial Rule Engine (Graceful fallback when offline)
"""

import os
import logging
from typing import Any, Dict, Optional, Tuple
from src.app.core.config import settings

logger = logging.getLogger("LLMProvider")

_PLACEHOLDERS = ("", "your_openai_api_key_here", "your_groq_api_key_here",
                 "sk-placeholder", "rzp_test_placeholder", "secret_placeholder",
                 "your_opencode_api_key_here", "changeme")


def _clean(v: Optional[str]) -> str:
    return (v or "").strip().strip('"').strip("'")


def _is_real_key(v: Optional[str]) -> bool:
    v = _clean(v)
    if not v or len(v) < 8:
        return False
    low = v.lower()
    for p in _PLACEHOLDERS:
        if p and low == p.lower():
            return False
    if low.startswith("sk-placeholder") or (low.startswith("rzp_test_") and len(v) < 20):
        return False
    return True


def get_llm_config(purpose: str = "supervisor") -> Dict[str, Any]:
    """Resolve best LLM config without constructing clients (no secrets in output)."""
    provider_pref = _clean(os.getenv("LLM_PROVIDER", "auto")).lower() or "auto"
    generic_key = os.getenv("LLM_API_KEY", "")
    generic_base = _clean(os.getenv("LLM_BASE_URL", ""))
    generic_model = _clean(os.getenv("LLM_MODEL", ""))

    openai_key = os.getenv("OPENAI_API_KEY", "") or settings.OPENAI_API_KEY
    openai_base = _clean(os.getenv("OPENAI_BASE_URL", "")) or settings.OPENAI_BASE_URL
    openai_model = _clean(os.getenv("OPENAI_MODEL", "")) or _clean(os.getenv("SUPERVISOR_MODEL" if purpose == "supervisor" else "SUB_AGENT_MODEL", "")) or "gpt-4o-mini"

    opencode_key = os.getenv("OPENCODE_API_KEY", "") or settings.OPENCODE_API_KEY
    opencode_base = _clean(os.getenv("OPENCODE_BASE_URL", "")) or settings.OPENCODE_BASE_URL or "https://opencode.ai/zen/v1"
    opencode_model = _clean(os.getenv("OPENCODE_MODEL", "")) or generic_model or openai_model or "gpt-4o-mini"

    groq_key = os.getenv("GROQ_API_KEY", "") or settings.GROQ_API_KEY
    groq_model = _clean(os.getenv("GROQ_MODEL", "")) or "llama-3.3-70b-versatile"

    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "") or settings.ANTHROPIC_API_KEY
    anthropic_model = _clean(os.getenv("ANTHROPIC_MODEL", "")) or "claude-3-5-haiku-latest"

    def _ok(provider: str, model: str, base: str = "") -> Dict[str, Any]:
        return {"provider": provider, "model": model, "configured": True,
                "reason": f"{provider} key detected", "base_url_set": bool(base)}

    # Explicit disabled
    if provider_pref == "disabled":
        return {"provider": "disabled", "model": "", "configured": False,
                "reason": "LLM_PROVIDER=disabled", "base_url_set": False}

    # Explicit provider requests
    if provider_pref in ("openai", "openai_compatible"):
        if _is_real_key(openai_key) or (generic_base and _is_real_key(generic_key)):
            return _ok("openai", generic_model or openai_model, openai_base or generic_base)
        if _is_real_key(generic_key) and generic_base:
            return _ok("openai_compatible", generic_model or "default", generic_base)
        return {"provider": "openai", "model": openai_model, "configured": False,
                "reason": "no OPENAI_API_KEY", "base_url_set": bool(openai_base)}
    if provider_pref == "opencode":
        if _is_real_key(opencode_key):
            return _ok("opencode", opencode_model, opencode_base)
        if _is_real_key(openai_key) and "opencode" in (openai_base.lower() + opencode_base.lower()):
            return _ok("opencode", opencode_model, openai_base or opencode_base)
        return {"provider": "opencode", "model": opencode_model, "configured": False,
                "reason": "no OPENCODE_API_KEY", "base_url_set": True}
    if provider_pref == "groq":
        if _is_real_key(groq_key):
            return _ok("groq", groq_model)
        return {"provider": "groq", "model": groq_model, "configured": False,
                "reason": "no GROQ_API_KEY", "base_url_set": False}
    if provider_pref == "anthropic":
        if _is_real_key(anthropic_key):
            return _ok("anthropic", anthropic_model)
        return {"provider": "anthropic", "model": anthropic_model, "configured": False,
                "reason": "no ANTHROPIC_API_KEY", "base_url_set": False}

    # auto mode: prefer opencode > openai(+base) > generic > groq > anthropic
    if _is_real_key(opencode_key):
        return _ok("opencode", opencode_model, opencode_base)
    if _is_real_key(generic_key) and generic_base:
        return _ok("openai_compatible", generic_model or "default", generic_base)
    if _is_real_key(openai_key):
        if openai_base and "opencode" in openai_base.lower():
            return _ok("opencode", generic_model or openai_model, openai_base)
        return _ok("openai", generic_model or openai_model, openai_base)
    if _is_real_key(groq_key):
        return _ok("groq", groq_model)
    if _is_real_key(anthropic_key):
        return _ok("anthropic", anthropic_model)
    return {"provider": "none", "model": generic_model or openai_model, "configured": False,
            "reason": "no LLM keys set, using deterministic simulation", "base_url_set": bool(generic_base or openai_base)}


def is_ai_ready(purpose: str = "supervisor") -> bool:
    return bool(get_llm_config(purpose).get("configured"))


def build_chat_llm(purpose: str = "supervisor", temperature: float = 0.2) -> Optional[Any]:
    """Build a LangChain chat model for the resolved provider, or None for simulation."""
    cfg = get_llm_config(purpose)
    if not cfg.get("configured"):
        return None
    provider = cfg["provider"]
    model = cfg["model"]
    try:
        if provider in ("openai", "opencode", "openai_compatible"):
            from langchain_openai import ChatOpenAI
            if provider == "opencode":
                api_key = _clean(os.getenv("OPENCODE_API_KEY")) or settings.OPENCODE_API_KEY or _clean(os.getenv("OPENAI_API_KEY"))
                base_url = _clean(os.getenv("OPENCODE_BASE_URL")) or settings.OPENCODE_BASE_URL or "https://opencode.ai/zen/v1"
            elif provider == "openai_compatible":
                api_key = _clean(os.getenv("LLM_API_KEY")) or settings.OPENAI_API_KEY
                base_url = _clean(os.getenv("LLM_BASE_URL")) or settings.OPENAI_BASE_URL
            else:
                api_key = _clean(os.getenv("OPENAI_API_KEY")) or settings.OPENAI_API_KEY or _clean(os.getenv("LLM_API_KEY"))
                base_url = _clean(os.getenv("OPENAI_BASE_URL")) or settings.OPENAI_BASE_URL
            kwargs: Dict[str, Any] = {"model": model, "temperature": temperature, "api_key": api_key}
            if base_url:
                kwargs["base_url"] = base_url
            return ChatOpenAI(**kwargs)
        if provider == "groq":
            from langchain_groq import ChatGroq  # type: ignore
            return ChatGroq(model=model, temperature=temperature,
                            api_key=_clean(os.getenv("GROQ_API_KEY")) or settings.GROQ_API_KEY)
        if provider == "anthropic":
            from langchain_anthropic import ChatAnthropic  # type: ignore
            return ChatAnthropic(model=model, temperature=temperature,
                                 api_key=_clean(os.getenv("ANTHROPIC_API_KEY")) or settings.ANTHROPIC_API_KEY)
    except Exception as e:
        logger.warning(f"[LLMProvider] Failed to build {provider} LLM ({model}): {e}")
        return None
    return None


def llm_status() -> Dict[str, Any]:
    """Public status (safe, no secrets) for /v1/ai/status and /ready."""
    sup = get_llm_config("supervisor")
    sub = get_llm_config("subagent")
    return {
        "ai_ready": bool(sup["configured"] or sub["configured"]),
        "supervisor": sup,
        "subagent": sub,
        "fallback": "deterministic-simulation",
        "supported_providers": ["openai", "opencode", "openai_compatible", "groq", "anthropic", "disabled"],
        "env_hints": ["LLM_PROVIDER", "OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENCODE_API_KEY",
                      "GROQ_API_KEY", "ANTHROPIC_API_KEY", "LLM_MODEL"],
    }
