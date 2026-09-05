# -*- coding: utf-8 -*-
"""
============================================================================
FINPILOT AI — GROUNDED COPILOT REGRESSION TEST (mocked LLM)
============================================================================
Pins the rebuild: the user's exact question + freshly retrieved live data
must reach the model prompt; the handler must return the model's answer
(never a fabricated fallback scenario); failures must surface an explicit
retry message; cited figures get code-verified.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import httpx
import pytest
from fastapi.testclient import TestClient
from src.app.main import app
from src.app.core.rbac import create_access_token
from src.app.services.auth_service import auth_service
from src.app.services import copilot_service as copilot

client = TestClient(app)

QUESTION = "Why is Engineering overspending on cloud? Pinpoint causal root cause."


def _cfo_headers() -> dict:
    user = auth_service.get_user_by_email("cfo@aifinance.local")
    token = create_access_token({"id": user["id"], "role": user["role"], "name": user["name"]})
    return {"Authorization": f"Bearer {token}"}


class _FakeResp:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status
        self.text = "fake-body"
    def json(self):
        return self._payload


def _no_keys(monkeypatch):
    for var in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GEMINI_MODEL", "GEMINI_BASE_URL",
                "OPENAI_API_KEY", "OPENCODE_API_KEY", "GROQ_API_KEY",
                "ANTHROPIC_API_KEY", "LLM_API_KEY", "LLM_PROVIDER"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setattr(copilot.settings, "GEMINI_API_KEY", "")
    monkeypatch.setattr(copilot.settings, "OPENAI_API_KEY", "")
    monkeypatch.setattr(copilot.settings, "OPENCODE_API_KEY", "")
    monkeypatch.setattr(copilot.settings, "GROQ_API_KEY", "")
    monkeypatch.setattr(copilot.settings, "ANTHROPIC_API_KEY", "")
    monkeypatch.setattr(copilot.settings, "LLM_API_KEY", "")


def test_prompt_contains_question_and_live_data(monkeypatch):
    """The outgoing prompt must carry the exact question + retrieved figures."""
    captured = {}

    def fake_post(url, json=None, headers=None, timeout=None):
        captured["url"] = url
        captured["messages"] = (json or {}).get("messages", [])
        captured["max_tokens"] = (json or {}).get("max_tokens")
        captured["auth"] = bool((headers or {}).get("Authorization"))
        return _FakeResp({"choices": [{"message": {"content": "Grounded test answer."}}]})

    monkeypatch.setattr(httpx, "post", fake_post)
    ctx = copilot.retrieve_context(QUESTION, "CFO", None)
    reserves_plain = str(int(ctx['liquidity']['liquid_reserves']))  # JSON carries no commas
    messages = copilot.build_grounded_messages(QUESTION, ctx)
    blob = "\n".join(m["content"] for m in messages)
    assert QUESTION in blob, "exact user question missing from prompt"
    assert reserves_plain in blob, "live reserves figure missing from prompt"
    assert "CloudOps" in blob, "live vendor evidence missing from prompt"
    assert "cost" in blob.lower() or "monthly" in blob.lower()

    ep = {"url": "https://x.test/v1/chat/completions", "key": "k", "model": "m", "provider": "t"}
    text, meta = copilot.call_llm(messages, ep)
    assert text == "Grounded test answer."
    assert meta["finish_reason"] == "unknown"
    assert captured["max_tokens"] == copilot.LLM_MAX_TOKENS
    assert captured["auth"] is True
    print("[PASSED] prompt carries question + live data; call bounded + authed")


def test_endpoint_returns_llm_answer_not_fallback(monkeypatch):
    """End-to-end via HTTP with mocked model: model's words come back verbatim."""
    monkeypatch.setenv("OPENCODE_API_KEY", "test-key-1234567890")
    monkeypatch.setenv("LLM_PROVIDER", "opencode")

    def fake_post(url, json=None, headers=None, timeout=None):
        return _FakeResp({"choices": [{"message": {
            "content": "Engineering cloud overspend is driven by CloudOps vendor run-rate; reserves hold."}}]})
    monkeypatch.setattr(httpx, "post", fake_post)
    res = client.post("/v1/agent/chat",
                      json={"message": QUESTION, "thread_id": "t-mock"},
                      headers=_cfo_headers())
    assert res.status_code == 200
    body = res.json()
    assert isinstance(body["response"], str)
    assert "driven by CloudOps vendor run-rate" in body["response"]
    assert "Disburse planned expense" not in body["response"]
    assert "Verified live figures" in body["response"]
    print("[PASSED] endpoint returns model answer, no fabricated scenario")


def test_llm_timeout_yields_retry_not_fallback(monkeypatch):
    """A dead model must produce an explicit retry message, never a scenario."""
    monkeypatch.setenv("OPENCODE_API_KEY", "test-key-1234567890")
    monkeypatch.setenv("LLM_PROVIDER", "opencode")

    def boom(url, json=None, headers=None, timeout=None):
        raise httpx.TimeoutException("timed out")
    monkeypatch.setattr(httpx, "post", boom)
    res = client.post("/v1/agent/chat",
                      json={"message": QUESTION, "thread_id": "t-mock-fail"},
                      headers=_cfo_headers())
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "llm_unavailable"
    assert "retry" in body["response"].lower()
    assert "Disburse planned expense" not in body["response"]
    assert "Traceback" not in body["response"]
    print("[PASSED] model failure -> retry message, no silent fallback")


def test_no_key_yields_unavailable_not_fallback(monkeypatch):
    """No configured key must not silently degrade into a fake analysis."""
    _no_keys(monkeypatch)
    res = client.post("/v1/agent/chat",
                      json={"message": QUESTION, "thread_id": "t-mock-nokey"},
                      headers=_cfo_headers())
    assert res.status_code == 200
    body = res.json()
    assert "no LLM API key" in body["response"]
    assert "Disburse planned expense" not in body["response"]
    print("[PASSED] missing key -> explicit unavailable message")


def test_verifier_flags_unmatched_figures():
    """Model-cited amounts absent from retrieved data get flagged; anchors govern."""
    ctx = copilot.retrieve_context(QUESTION, "CFO", None)
    reserves = f"{ctx['liquidity']['liquid_reserves']:,.0f}"
    ok_text, warnings = copilot.verify_figures(
        f"Reserves stand at \u20b9{reserves} and runway is fine.", ctx)
    assert warnings == [], f"false positive: {warnings}"
    assert "Verified live figures" in ok_text

    bad_text, warnings2 = copilot.verify_figures(
        "A surprise \u20b999,999,999 liability dwarfs everything.", ctx)
    assert any("99,999,999" in w for w in warnings2)
    assert "rely on the verified figures above" in bad_text
    print("[PASSED] verifier accepts anchors, flags invented figures")


def test_provider_rejection_hint_is_safe_and_specific(monkeypatch):
    """A provider HTTP rejection surfaces provider+status, never bodies/keys."""
    monkeypatch.setenv("OPENCODE_API_KEY", "test-key-1234567890")
    monkeypatch.setenv("LLM_PROVIDER", "opencode")

    class Forbidden:
        status_code = 403
        text = '{"error": "forbidden"}'
        def json(self):
            return {"error": "forbidden"}

    monkeypatch.setattr(httpx, "post", lambda *a, **k: Forbidden())
    res = client.post("/v1/agent/chat",
                      json={"message": QUESTION, "thread_id": "t-mock-403"},
                      headers=_cfo_headers())
    body = res.json()
    assert body["status"] == "llm_unavailable"
    assert "opencode API, HTTP 403" in body["response"]
    assert "test-key" not in body["response"]
    assert '{"error"' not in body["response"]
    print("[PASSED] provider rejection hint is safe + specific")


def _clean_llm_env(monkeypatch):
    for var in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GEMINI_MODEL", "GEMINI_BASE_URL",
                "OPENAI_API_KEY", "OPENCODE_API_KEY", "GROQ_API_KEY",
                "ANTHROPIC_API_KEY", "LLM_API_KEY", "OPENAI_MODEL",
                "OPENCODE_MODEL", "LLM_MODEL", "OPENAI_BASE_URL",
                "OPENCODE_BASE_URL", "LLM_BASE_URL", "LLM_PROVIDER",
                "SUPERVISOR_MODEL", "SUB_AGENT_MODEL"):
        monkeypatch.delenv(var, raising=False)
    for attr in ("GEMINI_API_KEY", "GEMINI_MODEL", "GEMINI_BASE_URL",
                 "OPENAI_API_KEY", "OPENCODE_API_KEY", "GROQ_API_KEY",
                 "ANTHROPIC_API_KEY", "LLM_API_KEY", "OPENAI_MODEL",
                 "OPENCODE_MODEL", "LLM_MODEL", "OPENAI_BASE_URL",
                 "OPENCODE_BASE_URL", "LLM_BASE_URL", "SUPERVISOR_MODEL",
                 "SUB_AGENT_MODEL"):
        monkeypatch.setattr(copilot.settings, attr, "", raising=False)


def test_gemini_provider_resolution(monkeypatch):
    """Setting GEMINI_API_KEY configures Gemini provider with default model."""
    from src.app.services.llm_provider import get_llm_config
    _clean_llm_env(monkeypatch)
    monkeypatch.setenv("GEMINI_API_KEY", "AIzaSyTestGeminiKey1234567890")
    cfg = get_llm_config("supervisor")
    assert cfg["provider"] == "gemini" and cfg["configured"] is True
    assert cfg["model"] == "gemini-3.5-flash"
    print("[PASSED] gemini provider resolution and default model verified")


def test_gemini_endpoint_resolution(monkeypatch):
    """Gemini endpoint points to Google generative language OpenAI-compatible API."""
    _clean_llm_env(monkeypatch)
    monkeypatch.setenv("GEMINI_API_KEY", "AIzaSyTestGeminiKey1234567890")
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    ep = copilot.resolve_chat_endpoint()
    assert ep is not None
    assert ep["provider"] == "gemini"
    assert "googleapis.com" in ep["url"]
    assert ep["key"] == "AIzaSyTestGeminiKey1234567890"
    print("[PASSED] gemini chat completions endpoint verified")


def test_opencode_default_model_is_zen_served(monkeypatch):
    """Bare gpt-4o-mini is not in Zen's catalogue; default must be served."""
    from src.app.services.llm_provider import get_llm_config
    _clean_llm_env(monkeypatch)
    monkeypatch.setenv("OPENCODE_API_KEY", "test-key-1234567890")
    cfg = get_llm_config("supervisor")
    assert cfg["provider"] == "opencode" and cfg["configured"] is True
    assert cfg["model"] == "gpt-5-nano", f"got {cfg['model']}"
    print("[PASSED] opencode default model is zen-served")


def test_explicit_opencode_model_wins(monkeypatch):
    """An explicit OPENCODE_MODEL must override the default."""
    from src.app.services.llm_provider import get_llm_config
    _clean_llm_env(monkeypatch)
    monkeypatch.setenv("OPENCODE_API_KEY", "test-key-1234567890")
    monkeypatch.setenv("OPENCODE_MODEL", "gpt-5.4-mini")
    assert get_llm_config("supervisor")["model"] == "gpt-5.4-mini"
    print("[PASSED] explicit OPENCODE_MODEL respected")


def test_model_not_served_hint(monkeypatch):
    """A ModelError payload must point at the model setting, not just 401."""
    monkeypatch.setenv("OPENCODE_API_KEY", "test-key-1234567890")
    monkeypatch.setenv("LLM_PROVIDER", "opencode")

    class ModelErr:
        status_code = 401
        text = '{"type":"error","error":{"type":"ModelError","message":"Model x is not supported"}}'
        def json(self):
            return {"error": "ModelError"}

    monkeypatch.setattr(httpx, "post", lambda *a, **k: ModelErr())
    res = client.post("/v1/agent/chat",
                      json={"message": QUESTION, "thread_id": "t-mock-model"},
                      headers=_cfo_headers())
    body = res.json()
    assert body["status"] == "llm_unavailable"
    assert "OPENCODE_MODEL" in body["response"]
    assert "test-key" not in body["response"]
    print("[PASSED] unserved-model hint names the setting, leaks nothing")


def test_billing_error_hint(monkeypatch):
    """A CreditsError must point at billing, never echo provider body/URLs."""
    monkeypatch.setenv("OPENCODE_API_KEY", "test-key-1234567890")
    monkeypatch.setenv("LLM_PROVIDER", "opencode")

    class BillingErr:
        status_code = 401
        text = '{"type":"error","error":{"type":"CreditsError","message":"No payment method. Add one here: https://example.invalid/billing"}}'
        def json(self):
            return {"error": "CreditsError"}

    monkeypatch.setattr(httpx, "post", lambda *a, **k: BillingErr())
    res = client.post("/v1/agent/chat",
                      json={"message": QUESTION, "thread_id": "t-mock-billing"},
                      headers=_cfo_headers())
    body = res.json()
    assert body["status"] == "llm_unavailable"
    assert "no payment method" in body["response"]
    assert "test-key" not in body["response"]
    assert "example.invalid" not in body["response"]
    print("[PASSED] billing error hint is actionable, leaks nothing")


def _chat_with_body(monkeypatch, status, text):
    monkeypatch.setenv("OPENCODE_API_KEY", "test-key-1234567890")
    monkeypatch.setenv("LLM_PROVIDER", "opencode")

    class Resp:
        status_code = status
        def json(self):
            raise ValueError("no json")

    monkeypatch.setattr(httpx, "post", lambda *a, **k: Resp())
    Resp.text = text
    res = client.post("/v1/agent/chat",
                      json={"message": QUESTION, "thread_id": "t-mock-etype"},
                      headers=_cfo_headers())
    return res.json()


def test_auth_error_type_named(monkeypatch):
    """A typed AuthenticationError names key rejection, not generic 401."""
    body = _chat_with_body(
        monkeypatch, 401,
        '{"type":"error","error":{"type":"AuthenticationError","message":"bad key"}}')
    assert body["status"] == "llm_unavailable"
    assert "rejected the configured key" in body["response"]
    assert "bad key" not in body["response"]
    print("[PASSED] typed auth error pinpoints the key")


def test_html_block_named_as_egress(monkeypatch):
    """A non-JSON edge block is reported as such, body never echoed."""
    body = _chat_with_body(
        monkeypatch, 403, "<html><head><title>Access Denied</title></head></html>")
    assert "blocked before reaching the AI provider" in body["response"]
    assert "Access Denied" not in body["response"]
    print("[PASSED] edge block reported without echoing body")


def test_completion_budget_field_per_provider():
    """Gemini gets max_completion_tokens; others keep max_tokens (strict APIs
    reject unknown pairings). Guards the live 32-token truncation fix."""
    msgs = [{"role": "user", "content": "hi"}]
    gem = copilot._chat_payload(
        {"url": "https://x", "key": "k", "model": "m", "provider": "gemini"}, msgs)
    assert gem.get("max_completion_tokens") == copilot.LLM_MAX_TOKENS
    assert "max_tokens" not in gem
    for prov in ("openai", "opencode", "openai_compatible"):
        p = copilot._chat_payload(
            {"url": "https://x", "key": "k", "model": "m", "provider": prov}, msgs)
        assert p.get("max_tokens") == copilot.LLM_MAX_TOKENS
        assert "max_completion_tokens" not in p
    print("[PASSED] provider-aware completion budget")


if __name__ == "__main__":
    test_verifier_flags_unmatched_figures()
    print("mocked tests run via: pytest tests/test_grounded_copilot_regression.py -v")
