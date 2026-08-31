# FinPilot AI — Multi-Agent System Audit

This document provides a technical audit of the agents implemented across `src/app/services/multi_agent_orchestrator.py`, `src/app/graphs/`, `src/app/services/digital_twin_service.py`, and `src/app/services/merchant_commerce_service.py`.

---

## 📊 Core 7-Agent Pipeline Audit Table

| Agent Name | Core Location(s) | Approx. LOC | Calls an LLM? | Has Automated Test? | One-Line Honest Technical Assessment |
|---|---|:---:|:---:|:---:|---|
| **1. IntentAgent** | `src/app/services/multi_agent_orchestrator.py`<br>`src/app/graphs/supervisor.py` | ~105 LOC | **Optional**<br>*(Regex default, GPT-4o-mini when key set)* | **YES**<br>`test_digital_twin_and_agents.py`<br>`test_ai_chat_pipeline.py` | Fast deterministic keyword classifier and RBAC policy router; gracefully falls back to regex when API keys are unset. |
| **2. RetrievalAgent** | `src/app/services/multi_agent_orchestrator.py`<br>`src/app/services/dataset_service.py` | ~205 LOC | **NO**<br>*(Direct in-memory fetch)* | **YES**<br>`test_digital_twin_and_agents.py` | Deterministic data extractor pulling live balances, headcount, commitments, and department slices with lineage tracking. |
| **3. AnalysisAgent** | `src/app/services/multi_agent_orchestrator.py`<br>`src/app/services/ai_reasoning_engine.py`<br>`src/app/graphs/invoice_auditor.py` | ~245 LOC | **NO**<br>*(Pure Python arithmetic)* | **YES**<br>`test_digital_twin_and_agents.py`<br>`test_ai_chat_pipeline.py` | Purely deterministic mathematical rules engine computing burn velocity, 18% GST variance, and budget ratios without token hallucinations. |
| **4. RiskAgent** | `src/app/services/multi_agent_orchestrator.py`<br>`src/app/services/digital_twin_service.py` | ~80 LOC | **NO**<br>*(Weighted factor scoring)* | **YES**<br>`test_digital_twin_and_agents.py`<br>`test_decision_engine_upgrade.py` | Deterministic 4-factor weighted scoring model (Budget 30%, Policy 25%, Stability 25%, Approval 20%) mapping variance to risk tiers. |
| **5. SimulationAgent** | `src/app/services/multi_agent_orchestrator.py`<br>`src/app/services/digital_twin_service.py` | ~165 LOC | **NO**<br>*(90-Day discrete mathematical model)* | **YES**<br>`test_digital_twin_and_agents.py` | High-depth mathematical counterfactual state simulator calculating day-by-day liquidity deltas, runway shifts, and before/after transaction states. |
| **6. CausalAgent** | `src/app/services/multi_agent_orchestrator.py`<br>`src/app/services/ai_reasoning_engine.py` | ~125 LOC | **Optional**<br>*(Rule-based default, LLM-augmented)* | **YES**<br>`test_digital_twin_and_agents.py`<br>`test_ai_chat_pipeline.py` | Contextual signal-correlation engine matching financial anomalies to concrete operational events (cloud scaling, ad front-loading, Annexure B omissions). |
| **7. NarratorAgent** | `src/app/services/multi_agent_orchestrator.py`<br>`src/app/services/ai_reasoning_engine.py` | ~265 LOC | **Optional**<br>*(Structured markdown template default, LLM-augmented)* | **YES**<br>`test_digital_twin_and_agents.py`<br>`test_ai_chat_pipeline.py` | Role-aware executive synthesis engine generating structured "What Happened / Why It Matters / What To Do / Who Acts / What Next" briefs tailored to CFO, Dept Head, or Auditor personas. |

---

## 🛍️ Specialized Commerce & Governance Agents

| Agent Name | Location | Approx. LOC | Calls an LLM? | Has Automated Test? | One-Line Honest Technical Assessment |
|---|---|:---:|:---:|:---:|---|
| **Autonomous AI Buyer Agent** | `src/app/services/merchant_commerce_service.py` | ~120 LOC | **NO**<br>*(Bounded rule algorithm)* | **YES**<br>`test_commerce_and_ai_shopping.py` | Simulates an external buyer bot negotiating tiered volume discounts (capped at 15%) within hard spending token limits and Razorpay payment links. |
| **Conversational In-App Checkout Agent** | `src/app/services/merchant_commerce_service.py` | ~140 LOC | **Optional**<br>*(Semantic parser + fallback)* | **YES**<br>`test_commerce_and_ai_shopping.py` | Parses natural language purchase requests into cart items, calculates 18% GST, and dispatches 1-click Razorpay test links. |
| **Policy Self-Calibration Agent** | `src/app/services/policy_calibration_service.py` | ~220 LOC | **NO**<br>*(Statistical friction detector)* | **YES**<br>`test_digital_twin_and_agents.py` | Analyzes human reviewer override rates on expense claims to detect policy friction and generate 1-click policy threshold revisions. |

---

## 🔑 Key Engineering Observations for Pitch / Video:
1. **Ledger Arithmetic is 100% Deterministic:** Tax calculations, GST audits, payroll deductions, and 90-day cash curve formulas are deliberately executed in pure Python floats to prevent LLM hallucinations.
2. **Resilient Dual-Mode Execution:** All agents function in two modes: (a) deterministic fast-path mode (zero API key dependency, instant local execution, 100% unit test reproducible), and (b) OpenAI LangGraph-augmented mode when `OPENAI_API_KEY` is provided.
3. **Hard Governance Guardrails:** Token spending limits and ₹50,000 HITL approval gates are enforced at the API validation layer before transactions can reach Razorpay payment rails.
