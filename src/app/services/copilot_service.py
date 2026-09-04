# -*- coding: utf-8 -*-
"""
FinPilot AI — Grounded Copilot Service (real LLM reasoning over live data)
==========================================================================
Replaces template-only Copilot answers with a real pipeline:

  1. RETRIEVE — pull question-relevant figures fresh from the app's own
     data layer (budgets/burn, invoices by vendor, transactions, payroll,
     liquidity, cash horizons). Deterministic, RBAC-scoped.
  2. ROUTE — scenario questions ("what if", hiring, delays) keep the
     deterministic Digital Twin simulation (exact arithmetic, zero cost);
     causal/general questions go to the LLM.
  3. REASON — send the user's EXACT question plus the retrieved data as
     structured JSON to an OpenAI-compatible chat-completions endpoint
     (OpenAI / OpenCode / Groq-compatible). Bounded (timeout, max_tokens,
     per-user rate limit).
  4. VERIFY — recompute anchor figures deterministically in code, append a
     "Verified live figures" box, and flag any model-cited amount that
     matches nothing in the retrieved data. Policy status is ALWAYS
     computed in code, never declared by the model.
  5. FAIL LOUDLY — no key / API error / timeout returns an explicit
     "analysis unavailable, please retry" message. Never a fabricated
     scenario, never a raw traceback.
"""

import json
import logging
import re
import time
import uuid
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import httpx

from src.app.core.config import settings
from src.app.core.rate_limiter import rate_limiter
from src.app.services.llm_provider import get_llm_config
from src.app.services.digital_twin_service import digital_twin_service
from src.app.services.budget_service import budget_service
from src.app.services.invoice_service import invoice_service
from src.app.services.dataset_service import dataset_service
from src.app.services.cash_flow_service import cash_flow_service
from src.app.services.audit_service import audit_service

logger = logging.getLogger("GroundedCopilot")

LLM_TIMEOUT_S = 45.0
LLM_CONNECT_TIMEOUT_S = 10.0
LLM_MAX_TOKENS = 900
LLM_TEMPERATURE = 0.2

_SCENARIO_KEYWORDS = (
    "what if", "what-if", "suppose", "assume", "simulate",
    "if we delay", "if we spend", "if we hire",
)
_DEPARTMENTS = ("engineering", "marketing", "sales", "operations", "hr")
_UNVERIFIED_FIGURE_FLOOR = 10000.0


def _inr(value: float) -> str:
    return f"₹{value:,.0f}"


def classify_intent(question: str) -> str:
    """SCENARIO (has plannable parameters) vs ANALYSIS (causal/general)."""
    q = question.lower()
    if any(k in q for k in _SCENARIO_KEYWORDS):
        return "SCENARIO"
    return "ANALYSIS"


def _rbac_denied(user_role: str, user_department: Optional[str], question: str) -> bool:
    if user_role == "DEPARTMENT_HEAD" and user_department:
        q = question.lower()
        others = [d for d in ("marketing", "sales", "operations", "hr", "engineering")
                  if d != user_department.lower()]
        for od in others:
            if re.search(rf"\b{od}\b", q) and not re.search(rf"\b{user_department.lower()}\b", q):
                return True
    return False


def _dept_in_question(question: str) -> Optional[str]:
    q = question.lower()
    for dept in _DEPARTMENTS:
        if re.search(rf"\b{dept}\b", q):
            return dept.capitalize() if dept != "hr" else "HR"
    return None


def retrieve_context(
    question: str,
    user_role: str = "CFO",
    user_department: Optional[str] = None,
) -> Dict[str, Any]:
    """Pulls question-relevant live figures. All deterministic, RBAC-scoped."""
    dept = _dept_in_question(question)
    if user_role == "DEPARTMENT_HEAD" and user_department:
        dept = user_department if user_department != "HR" else "HR"

    state = digital_twin_service.get_live_state()
    budgets = state["budget_position"]
    cash = state["cash_position"]
    payroll = state["payroll_position"]

    dept_slice: Dict[str, Any] = {}
    for name, info in budgets["departments"].items():
        if dept and name.lower() != dept.lower() and not (
            user_role != "DEPARTMENT_HEAD" and dept is None
        ):
            if dept is not None and name.lower() != dept.lower():
                continue
        dept_slice[name] = {
            "allocated_budget": info["allocated_budget"],
            "spent_amount": info["spent_amount"],
            "remaining_budget": info["remaining_budget"],
            "monthly_burn_rate": info["monthly_burn_rate"],
            "daily_burn_rate": round(info["monthly_burn_rate"] / 30.0, 2),
            "projected_year_end": info["projected_year_end"],
            "manager": info.get("manager", ""),
        }

    invoices = invoice_service.get_all_invoices(user_role, user_department if user_role == "DEPARTMENT_HEAD" else None)
    scoped_inv = [i for i in invoices
                  if dept is None or str(i.get("department", "")).lower() == dept.lower()]
    vendor_totals: Dict[str, float] = defaultdict(float)
    vendor_counts: Dict[str, int] = defaultdict(int)
    cat_totals: Dict[str, float] = defaultdict(float)
    for inv in scoped_inv:
        try:
            amt = float(inv.get("total_amount", 0.0))
        except (TypeError, ValueError):
            amt = 0.0
        vendor_totals[str(inv.get("vendor_name", "Unknown"))] += amt
        vendor_counts[str(inv.get("vendor_name", "Unknown"))] += 1
        cat_totals[str(inv.get("category", "Uncategorised"))] += amt
    top_vendors = [
        {"vendor": v, "total": round(t, 2), "invoices": vendor_counts[v]}
        for v, t in sorted(vendor_totals.items(), key=lambda kv: -kv[1])[:5]
    ]
    recent = sorted(scoped_inv, key=lambda i: str(i.get("date", "")), reverse=True)[:5]
    recent_invoices = [
        {"id": i.get("invoice_id"), "vendor": i.get("vendor_name"),
         "amount": i.get("total_amount"), "date": i.get("date"),
         "status": i.get("status"), "category": i.get("category")}
        for i in recent
    ]

    try:
        txns = dataset_service.get_transactions(None, None, user_role,
                                               user_department if user_role == "DEPARTMENT_HEAD" else None)
    except Exception:
        txns = []
    scoped_tx = [t for t in txns
                 if (dept is None or str(t.get("department", "")).lower() == dept.lower())
                 and t.get("direction") == "Outflow"]
    txn_out_total = round(sum(float(t.get("amount", 0.0)) for t in scoped_tx), 2)

    forecast = cash_flow_service.generate_cash_forecast(user_role, user_department)
    horizons = {
        h: {"projected_liquidity": forecast["horizons"][h]["projected_liquidity"],
            "net_change": forecast["horizons"][h]["net_change"]}
        for h in ("seven_day", "thirty_day", "ninety_day")
    }

    # Deterministic anchors (the numbers the model must not contradict).
    reserves = float(cash["liquid_reserves"])
    safe = float(cash["safe_liquidity_threshold"])
    daily_net = round((budgets["total_monthly_burn"] + payroll["monthly_gross_total"] / 30.0)
                      - cash["inflows_daily_avg"], 2)
    runway = int((reserves - safe) / daily_net) if daily_net > 0 else 999
    runway = max(0, min(999, runway))

    return {
        "question": question,
        "focus_department": dept,
        "as_of": datetime.utcnow().isoformat(),
        "liquidity": {
            "liquid_reserves": reserves,
            "safe_threshold": safe,
            "daily_net_burn": daily_net,
            "runway_days_recomputed": runway,
            "inflows_daily_avg": cash["inflows_daily_avg"],
        },
        "budgets": {
            "total_allocated": budgets["total_allocated"],
            "total_spent": budgets["total_spent"],
            "total_remaining": budgets["total_remaining"],
            "total_monthly_burn": budgets["total_monthly_burn"],
            "utilization_pct": budgets["utilization_pct"],
            "departments": dept_slice,
        },
        "payroll": {
            "headcount": payroll["headcount"],
            "monthly_basic_total": payroll["monthly_basic_total"],
            "monthly_gross_total": payroll["monthly_gross_total"],
        },
        "invoices": {
            "scoped_count": len(scoped_inv),
            "scoped_total": round(sum(vendor_totals.values()), 2),
            "top_vendors": top_vendors,
            "category_totals": {k: round(v, 2) for k, v in sorted(cat_totals.items(), key=lambda kv: -kv[1])},
            "recent": recent_invoices,
        },
        "outflow_transactions": {
            "count": len(scoped_tx),
            "total": txn_out_total,
            "scope": dept or "all departments",
        },
        "cash_horizons": horizons,
    }


def resolve_chat_endpoint() -> Optional[Dict[str, str]]:
    """Derives an OpenAI-compatible (url, key, model) from configured provider.

    Supports openai / opencode / openai_compatible, plus groq via its
    OpenAI-compatible gateway. Returns None when nothing usable is set.
    """
    cfg = get_llm_config("supervisor")
    if not cfg.get("configured"):
        return None
    provider = cfg.get("provider", "")
    model = cfg.get("model", "") or "gpt-4o-mini"

    def _env(*names: str) -> str:
        for n in names:
            v = (getattr(settings, n, "") or "").strip() if hasattr(settings, n) else ""
            if not v:
                import os as _os
                v = (_os.getenv(n, "") or "").strip()
            if v:
                return v.strip('"').strip("'")
        return ""

    if provider == "groq":
        key = _env("GROQ_API_KEY")
        return {"url": "https://api.groq.com/openai/v1/chat/completions",
                "key": key, "model": _env("GROQ_MODEL") or "llama-3.3-70b-versatile",
                "provider": provider} if key else None
    if provider == "opencode":
        key = _env("OPENCODE_API_KEY", "OPENAI_API_KEY")
        base = _env("OPENCODE_BASE_URL") or "https://opencode.ai/zen/v1"
        return {"url": base.rstrip("/") + "/chat/completions",
                "key": key, "model": model, "provider": provider} if key else None
    # openai / openai_compatible
    key = _env("OPENAI_API_KEY", "LLM_API_KEY")
    base = _env("OPENAI_BASE_URL", "LLM_BASE_URL") or "https://api.openai.com/v1"
    if provider == "openai_compatible":
        key = _env("LLM_API_KEY", "OPENAI_API_KEY")
        base = _env("LLM_BASE_URL", "OPENAI_BASE_URL")
    return {"url": base.rstrip("/") + "/chat/completions",
            "key": key, "model": model, "provider": provider} if key else None


def build_grounded_messages(question: str, ctx: Dict[str, Any]) -> List[Dict[str, str]]:
    """System rules + exact user question + live data JSON. Nothing else."""
    data_json = json.dumps(ctx, indent=1, default=str)
    system = (
        "You are FinPilot, the CFO-grade financial analyst inside an enterprise "
        "finance app. Answer ONLY the user's exact question below using ONLY the "
        "LIVE FINANCIAL DATA provided. Rules:\n"
        "1. A causal 'why' question gets a causal explanation naming the specific "
        "vendors, categories and transactions driving it — NEVER describe a "
        "disbursement, hiring or simulation nobody asked for.\n"
        "2. Use the rupee figures EXACTLY as given (copy them digit-for-digit). "
        "Do NOT compute your own totals, runways or percentages.\n"
        "3. Keep it under 220 words, markdown with a short heading, bullets for "
        "evidence, and one closing recommendation line.\n"
        "4. Do NOT declare any approval/policy status — that is computed "
        "separately in code."
    )
    user = (
        f"USER QUESTION (answer exactly this, nothing else):\n{question}\n\n"
        f"LIVE FINANCIAL DATA (JSON, retrieved just now — treat as ground truth):\n"
        f"{data_json}"
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def call_llm(messages: List[Dict[str, str]], endpoint: Dict[str, str]) -> str:
    """POSTs to the chat-completions endpoint. Raises on any failure."""
    started = time.perf_counter()
    logger.info("[GroundedCopilot] LLM call provider=%s model=%s prompt_chars=%d timeout=%ss max_tokens=%d",
                endpoint["provider"], endpoint["model"],
                sum(len(m["content"]) for m in messages), LLM_TIMEOUT_S, LLM_MAX_TOKENS)
    resp = httpx.post(
        endpoint["url"],
        json={"model": endpoint["model"], "messages": messages,
              "temperature": LLM_TEMPERATURE, "max_tokens": LLM_MAX_TOKENS},
        headers={"Authorization": f"Bearer {endpoint['key']}",
                 "Content-Type": "application/json"},
        timeout=httpx.Timeout(LLM_TIMEOUT_S, connect=LLM_CONNECT_TIMEOUT_S),
    )
    elapsed = round(time.perf_counter() - started, 2)
    if resp.status_code != 200:
        raise RuntimeError(f"LLM HTTP {resp.status_code}: {resp.text[:200]}")
    try:
        content = resp.json()["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError, ValueError) as e:
        raise RuntimeError(f"LLM bad payload: {e}")
    if not content or not str(content).strip():
        raise RuntimeError("LLM empty response")
    logger.info("[GroundedCopilot] LLM ok provider=%s model=%s elapsed=%ss chars=%d",
                endpoint["provider"], endpoint["model"], elapsed, len(content))
    return str(content).strip()


def _extract_rupee_figures(text: str) -> List[float]:
    return [float(m.replace(",", "")) for m in
            re.findall(r"₹\s*([\d,]+(?:\.\d+)?)", text)]


def _anchor_values(ctx: Dict[str, Any]) -> List[Tuple[str, float]]:
    liq = ctx["liquidity"]
    anchors = [
        ("liquid_reserves", liq["liquid_reserves"]),
        ("safe_threshold", liq["safe_threshold"]),
        ("total_allocated", ctx["budgets"]["total_allocated"]),
        ("total_spent", ctx["budgets"]["total_spent"]),
        ("monthly_payroll_gross", ctx["payroll"]["monthly_gross_total"]),
    ]
    for name, info in ctx["budgets"]["departments"].items():
        anchors.append((f"{name} allocated", float(info["allocated_budget"])))
        anchors.append((f"{name} spent", float(info["spent_amount"])))
    for v in ctx["invoices"]["top_vendors"]:
        anchors.append((f"vendor {v['vendor']}", float(v["total"])))
    return anchors


def verify_figures(answer: str, ctx: Dict[str, Any]) -> Tuple[str, List[str]]:
    """Checks model-cited ₹ figures against retrieved anchors; appends a
    deterministic verified-figures box (code-computed, governs on conflict)."""
    liq = ctx["liquidity"]
    dept = ctx.get("focus_department")
    dept_line = ""
    if dept:
        for name, info in ctx["budgets"]["departments"].items():
            if name.lower() == dept.lower():
                dept_line = (f"- **{name}:** spent {_inr(info['spent_amount'])} of "
                             f"{_inr(info['allocated_budget'])} allocated "
                             f"(burn {_inr(info['monthly_burn_rate'])}/mo)\n")
    top = ctx["invoices"]["top_vendors"][0] if ctx["invoices"]["top_vendors"] else None
    box = (
        "\n\n**Verified live figures (recomputed in code — govern on any conflict):**\n"
        f"- Liquid reserves {_inr(liq['liquid_reserves'])}; safety threshold {_inr(liq['safe_threshold'])}; "
        f"runway **{liq['runway_days_recomputed']} days**\n"
        f"{dept_line}"
        f"- Top vendor: **{top['vendor']}** {_inr(top['total'])} across {top['invoices']} invoices\n"
        if top else "\n"
    )
    warnings: List[str] = []
    anchors = _anchor_values(ctx)
    for fig in _extract_rupee_figures(answer):
        if fig < _UNVERIFIED_FIGURE_FLOOR:
            continue
        if not any(abs(fig - val) <= max(1.0, val * 0.01) for _, val in anchors):
            warnings.append(_inr(fig))
    note = ""
    if warnings:
        note = ("\n> ⚠️ Could not tie " + ", ".join(warnings[:5]) +
                " to retrieved records — rely on the verified figures above.\n")
        logger.warning("[GroundedCopilot] unverified model figures: %s", warnings[:5])
    return answer.rstrip() + box + note, warnings


def _policy_note(question: str) -> str:
    """Deterministic policy line. The model never declares policy status."""
    amounts = [float(m.replace(",", "")) for m in
               re.findall(r"₹\s*([\d,]+(?:\.\d+)?)", question)]
    big = [a for a in amounts if a >= 50000.0]
    if big:
        return (f"\n\n**Policy note (deterministic):** amounts of "
                f"{', '.join(_inr(a) for a in big)} meet/exceed the ₹50,000 "
                f"human-approval gate — CFO authorization required before any disbursement.")
    if re.search(r"\b(buy|spend|pay|disburse|hire|approve)\b", question.lower()):
        return ("\n\n**Policy note (deterministic):** no figures in this question breach "
                "the ₹50,000 approval gate on their face; standard Finance Manager review applies.")
    return ("\n\n**Policy note (deterministic):** diagnostic question — no disbursement "
            "requested, no approval implications.")


def _retrieved_figures_box(ctx: Dict[str, Any]) -> str:
    liq = ctx["liquidity"]
    lines = [
        f"- Liquid reserves {_inr(liq['liquid_reserves'])}; runway {liq['runway_days_recomputed']} days",
        f"- Budget {_inr(ctx['budgets']['total_spent'])} spent of {_inr(ctx['budgets']['total_allocated'])} allocated",
        f"- Payroll {_inr(ctx['payroll']['monthly_gross_total'])}/mo across {ctx['payroll']['headcount']} staff",
    ]
    for v in ctx["invoices"]["top_vendors"][:3]:
        lines.append(f"- {v['vendor']}: {_inr(v['total'])} ({v['invoices']} invoices)")
    return "\n".join(lines)


class GroundedCopilot:
    """Question-aware Copilot: deterministic sims for scenarios, real grounded
    LLM reasoning for causal/general questions. No fabricated scenarios, ever."""

    def analyze(
        self,
        question: str,
        user_id: str = "usr_anon",
        user_role: str = "CFO",
        user_name: str = "Finance User",
        user_department: Optional[str] = None,
    ) -> Dict[str, Any]:
        trace_id = f"CPL-{uuid.uuid4().hex[:8].upper()}"
        q = (question or "").strip()

        if _rbac_denied(user_role, user_department, q):
            text = (
                f"## 🔒 Access Restricted (RBAC Policy)\n\n"
                f"You are authenticated as **{user_name}** ({user_department} Department Head).\n\n"
                f"Cross-department financial analysis is restricted to your own department. "
                f"Please scope the question to **{user_department}**."
            )
            return {"trace_id": trace_id, "intent": "RBAC_RESTRICTED", "response": text,
                    "status": "completed", "llm_used": False, "mode": "rbac",
                    "suggested_actions": [f"Ask about {user_department} spend"],
                    "agent_steps": [{"agent": "IntentAgent", "rbac_permitted": False}]}

        intent = classify_intent(q)
        ctx = retrieve_context(q, user_role, user_department)
        steps = [
            {"agent": "IntentAgent", "intent": intent, "rbac_permitted": True,
             "timestamp": datetime.utcnow().isoformat()},
            {"agent": "RetrievalAgent",
             "sources": ["budgets", "invoices", "transactions", "payroll", "liquidity", "cash_horizons"],
             "focus_department": ctx.get("focus_department"),
             "timestamp": datetime.utcnow().isoformat()},
        ]

        if intent == "SCENARIO":
            # Deterministic twin simulation: exact arithmetic, zero API cost.
            from src.app.services.multi_agent_orchestrator import multi_agent_orchestrator
            orch = multi_agent_orchestrator.process_query(
                query=q, user_role=user_role, user_name=user_name,
                user_department=user_department)
            raw = orch.get("response") or {}
            text = raw.get("text") if isinstance(raw, dict) else raw
            audit_service.log_action(
                user_id="sys_copilot", user_name="Grounded Copilot", role=user_role,
                action="AI_COPILOT_SCENARIO_SIM", entity="AI_COPILOT", entity_id=trace_id,
                details=f"Scenario sim for '{q[:80]}' verdict={orch.get('simulation', {}).get('verdict')}",
                risk_level="LOW")
            return {"trace_id": trace_id, "intent": "COUNTERFACTUAL_SIMULATION",
                    "response": text or "Simulation completed.",
                    "status": "completed", "llm_used": False,
                    "mode": "deterministic-simulation",
                    "simulation": orch.get("simulation"),
                    "suggested_actions": orch.get("suggested_actions", []),
                    "agent_steps": steps + orch.get("agent_steps", [])}

        # ANALYSIS → real grounded LLM call.
        endpoint = resolve_chat_endpoint()
        if endpoint is None:
            logger.warning("[GroundedCopilot] no LLM key configured (trace %s)", trace_id)
            return {"trace_id": trace_id, "intent": "CAUSAL_ANALYSIS",
                    "response": (
                        "## AI Analysis Unavailable\n\n"
                        "The AI model isn't configured on this deployment (no LLM API key), "
                        "so I can't generate a grounded answer right now — and I won't guess.\n\n"
                        "**Live figures retrieved for your question:**\n"
                        + _retrieved_figures_box(ctx) +
                        "\n\nPlease configure an LLM key and retry."),
                    "status": "llm_unavailable", "llm_used": False,
                    "mode": "unavailable",
                    "suggested_actions": ["Check AI status", "Retry analysis"],
                    "agent_steps": steps}

        messages = build_grounded_messages(q, ctx)
        prompt_est = sum(len(m["content"]) for m in messages) // 4
        rate_limiter.check_rate_limit(
            client_key=f"copilot:{user_id}", estimated_tokens=prompt_est + LLM_MAX_TOKENS)
        try:
            answer = call_llm(messages, endpoint)
        except Exception as e:
            logger.error("[GroundedCopilot] LLM call failed (trace %s): %s: %s",
                         trace_id, type(e).__name__, str(e)[:200])
            audit_service.log_action(
                user_id="sys_copilot", user_name="Grounded Copilot", role=user_role,
                action="AI_COPILOT_LLM_FAILED", entity="AI_COPILOT", entity_id=trace_id,
                details=f"LLM call failed: {type(e).__name__}", risk_level="MEDIUM")
            return {"trace_id": trace_id, "intent": "CAUSAL_ANALYSIS",
                    "response": (
                        "## Analysis Couldn't Complete — Please Retry\n\n"
                        "The AI analysis request failed before producing an answer "
                        f"({type(e).__name__}). No partial or estimated figures are shown "
                        "because they could be wrong.\n\n"
                        "Please retry in a moment. If this persists, check the AI status page. "
                        f"(Trace `{trace_id}`)"),
                    "status": "llm_unavailable", "llm_used": False,
                    "mode": "error",
                    "suggested_actions": ["Retry analysis", "Check AI status"],
                    "agent_steps": steps}

        final_text, unverified = verify_figures(answer, ctx)
        final_text += _policy_note(q)
        audit_service.log_action(
            user_id="sys_copilot", user_name="Grounded Copilot", role=user_role,
            action="AI_COPILOT_GROUNDED_ANALYSIS", entity="AI_COPILOT", entity_id=trace_id,
            details=f"Q: '{q[:80]}' provider={endpoint['provider']} model={endpoint['model']} "
                    f"unverified_figures={len(unverified)}",
            risk_level="LOW")
        steps.append({"agent": "VerifierAgent",
                      "provider": endpoint["provider"], "model": endpoint["model"],
                      "unverified_figures": unverified,
                      "timestamp": datetime.utcnow().isoformat()})
        return {"trace_id": trace_id, "intent": "CAUSAL_ANALYSIS",
                "response": final_text, "status": "completed", "llm_used": True,
                "mode": f"grounded-llm:{endpoint['provider']}:{endpoint['model']}",
                "suggested_actions": ["Run a what-if simulation", "Inspect vendor spend",
                                      "Review department runway"],
                "agent_steps": steps}


grounded_copilot = GroundedCopilot()
