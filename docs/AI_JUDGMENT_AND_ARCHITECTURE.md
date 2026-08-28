# 🧠 AI Judgment & Production Build Quality Architecture

<p align="center">
  <img src="assets/logo.png" alt="FinPilot AI Logo" width="200" />
</p>

## 📌 Executive Summary

FinPilot AI is built upon two uncompromising engineering tenets:
1. **Production-Ready Build Quality**: Clean, strongly typed, modular, and resilient software architecture.
2. **Disciplined AI Judgment**: Smart utilization of autonomous AI agents for high-dimensional semantic reasoning while **strictly prohibiting probabilistic LLMs from executing deterministic arithmetic, security boundaries, or cryptographic tasks**.

---

## ⚖️ AI Judgment Matrix: When to Use AI vs. When NOT to Use AI

```
                                  ┌─────────────────────────────────────────┐
                                  │       FINPILOT AI ARCHITECTURE          │
                                  └────────────────────┬────────────────────┘
                                                       │
                     ┌─────────────────────────────────┴─────────────────────────────────┐
                     ▼                                                                   ▼
       ┌───────────────────────────┐                                       ┌───────────────────────────┐
       │   DETERMINISTIC ENGINE    │                                       │    PROBABILISTIC AGENTS   │
       │    (Zero AI Hallucination)│                                       │   (High-Dimension Reason) │
       ├───────────────────────────┤                                       ├───────────────────────────┤
       │ • Exact GST & Ledger Math │                                       │ • Natural Language Intent │
       │ • Hard Budget Ceilings    │                                       │ • Causal Signal Synthesis │
       │ • Spending Token Bounds   │                                       │ • What-If Hypotheses      │
       │ • RBAC & Recipient Guard  │                                       │ • Role-Aware Narration    │
       │ • SHA-256 Hash Chaining   │                                       │ • Autonomous Negotiation  │
       └───────────────────────────┘                                       └───────────────────────────┘
```

| Functional Domain | Methodology | Why This Architecture Was Chosen |
|---|---|---|
| **💰 Ledger & Tax Math (GST, Deductions)** | **Deterministic Rules Engine** (`merchant_commerce_service.py`, `tax_service.py`) | **NEVER use LLMs for addition or multiplication.** Probabilistic token generation introduces hallucination risks in financial accounting. All taxes (18% GST), PF withholdings (12%), and subtotals use floating-point Python precision. |
| **🛡️ Spending Token Ceilings & HITL Thresholds** | **Hard Deterministic Guardrails** (`razorpay_service.py`, `config.py`) | Hard thresholds (e.g. ₹50,000 HITL approval rule, buyer spending tokens) must be enforced at the Python/Pydantic validation layer before transactions execute. |
| **🔒 Security, RBAC & Isolation** | **Deterministic Identity Middleware** (`auth_middleware.py`, `notification_service.py`) | Recipient routing and RBAC filtering are enforced via explicit identity checks (`recipientUserId == current_user.id`), preventing prompt injection leaks. |
| **🔗 Cryptographic Audit Trail** | **SHA-256 Chaining** (`audit_service.py`) | Every financial action is hashed using deterministic SHA-256 blocks (`prev_hash` $\rightarrow$ `audit_hash`), guaranteeing tamper-evident auditability. |
| **💬 Natural Language Parsing** | **Semantic AI Agent** (`ai_reasoning_engine.py`) | Discovers user intent from unstructured text (*"Add 2 API Gateways and apply bundle savings"*). |
| **🔍 Causal Root-Cause Correlation** | **Causal Analysis Agent** (`multi_agent_orchestrator.py`) | Correlates operational signals (e.g., Kubernetes cluster launches) with spending spikes to determine root cause. |
| **🧬 Counterfactual What-If Narration** | **Narrator Agent** (`multi_agent_orchestrator.py`) | Synthesizes complex 90-day Digital Twin projections into structured 5-part role-tailored narratives (What Happened, Why It Matters, What Should Be Done, Who Needs to Act, What Happens Next). |
| **🤝 Autonomous AI-to-AI Negotiation** | **Bounded Agent Protocol** (`merchant_commerce_service.py`) | Negotiates tiered bulk discounts (up to 15%) within pre-approved merchant bounds. |

---

## 🏗️ Production-Ready Build Quality Highlights

1. **Modular Code Separation**:
   - `src/app/core/`: Security configs, JWT authentication, and idempotency middlewares.
   - `src/app/models/`: Strongly typed Pydantic validation schemas.
   - `src/app/services/`: Pure business logic services with deterministic math and logging.
   - `src/app/api/endpoints/`: FastAPI REST routers with clean dependency injection.
   - `tests/`: 7 automated test suites spanning unit, integration, security, and browser CDP tests.
2. **Four-Tier Failure Resilience**:
   - Automated exponential backoff on network timeouts.
   - Field-level schema diagnostics on malformed payloads.
   - Pre-disbursement freeze and HITL ticket on budget cap breaches.
   - Token limit breach prevention and human override links.
3. **Automated Test Coverage (100% Pass Rate)**:
   - `test_ai_judgment_and_deterministic_guards.py`
   - `test_role_based_notifications.py`
   - `test_commerce_and_ai_shopping.py`
   - `test_digital_twin_and_agents.py`
   - `test_copilot_browser.py`
   - `test_compose_request_ui.py`
   - `test_browser_interactions.py`
