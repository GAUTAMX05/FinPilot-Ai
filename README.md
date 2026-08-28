<p align="center">
  <img src="docs/assets/logo.png" alt="FinPilot AI Logo" width="220" />
</p>

# 💰 FinPilot AI — Financial Digital Twin & Multi-Agent Autonomous Decision Operating System

<p align="center">
  <strong>FINANCE • CONTROL • DECIDE • GROW</strong>
</p>

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-purple.svg)](https://langchain-ai.github.io/langgraph/)
[![Razorpay](https://img.shields.io/badge/Razorpay-FINTECH%20API-blue.svg)](https://razorpay.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **"Most finance AI tools describe what already happened. FinPilot AI simulates what happens next — before a human has to decide."**

---

## 🎯 Razorpay AI Agent Track Compliance Matrix

| Track Requirement | Implementation in FinPilot AI | Interactive Endpoint / View |
|---|---|---|
| **🚀 Grows a Merchant's Sales** | **Smart Cross-Sell / Upsell Engine** (detects cart items & calculates synergistic bundle discounts) + **Autonomous Growth Campaign Orchestrator** (launches targeted promotional campaigns synced with marketing budget). | `POST /v1/commerce/campaigns/create`<br>`POST /v1/commerce/conversational-checkout`<br>*(Tab: AI Commerce & Growth)* |
| **🤖 Enables AI-to-AI Shopping** | **Agent-Readable Universal Catalog Manifest** (`/v1/commerce/ai-manifest` in JSON-LD / Schema.org) + **Bounded Autonomous Buyer Agent** (`/v1/commerce/ai-buy` with hard `X-Spending-Token-Limit` bounds & Razorpay rails). | `GET /v1/commerce/ai-manifest`<br>`POST /v1/commerce/ai-buy`<br>*(Tab: AI Commerce & Growth)* |
| **💬 Conversational In-App Checkout** | **In-App Cart & Checkout Assistant**: Natural language purchase parsing, live cart line items, statutory 18% GST calculation, and 1-click Razorpay test payment links. | `POST /v1/commerce/conversational-checkout`<br>*(Live Chat Panel in Tab 13)* |
| **📦 Agent-Readable Product Catalogs** | **Universal Machine Protocol**: Exposes product IDs, specifications, tax codes, live inventories, bulk pricing tiers, and policy ceilings to buyer bots. | `GET /v1/commerce/ai-manifest`<br>`GET /v1/commerce/catalog` |
| **✨ Automated Cross-Sell / Upsell Agents** | **Synergy Recommender**: Recommends complementary bundles (e.g. *API Gateway* $\rightarrow$ *Dedicated VPC* at 15% discount) with dynamic savings calculator. | Integrated into In-App Checkout & Conversational Chat |
| **📈 Autonomous Campaign Orchestrators** | **Autonomous Growth Engine**: Deducts spend from live department budget, deploys campaign payment links, and projects ROAS (3.8x - 4.2x). | `POST /v1/commerce/campaigns/create`<br>*(Panel 3 in Tab 13)* |
| **💳 Razorpay Test-Mode APIs** | **Fintech Rails**: Generates test-mode payment links (`https://rzp.io/i/...`), handles webhooks, idempotency keys, and payment state synchronization. | `src/app/services/razorpay_service.py` |

---

## 📸 Interface & Capabilities Showcase

### 1. Merchant Sales Growth & AI-to-AI Shopping Studio
*Agent-readable product catalog (`/v1/commerce/ai-manifest`), autonomous AI buyer volume negotiation within strict policy bounds, conversational in-app checkout with smart upsell bundles, and growth campaigns via Razorpay test rails.*
![Merchant Sales Growth & AI-to-AI Shopping Studio](docs/screenshots/09_merchant_ai_commerce.png)

---

### 2. Financial Digital Twin & What-If Simulation Studio
*Live simulate-able model: Evaluate forward spend velocity, deferred vendor payouts, and headcount growth before executing transactions.*
![Financial Digital Twin Studio](docs/screenshots/02_digital_twin_studio.png)

---

### 3. Executive Control Center & Financial Decision Engine
*Real-time corporate positions, dynamic time-series analytics, and automated decision review triggers.*
![Executive Control Center](docs/screenshots/03_executive_control_center.png)

---

### 4. Company Financial Decision Map
*Hierarchical control graph mapping Enterprise Root $\rightarrow$ Budgets & Cash $\rightarrow$ Department Risks $\rightarrow$ Actions.*
![Company Decision Map](docs/screenshots/04_company_decision_map.png)

---

### 5. Invoice Intelligence & Expense Affordability Auditor
*Automated 18% GST tax auditor, duplicate submission detection, and department runway affordability simulations.*
![Invoice Intelligence](docs/screenshots/05_invoice_intelligence_auditor.png)

---

### 6. Human-in-the-Loop (HITL) Disbursement Approvals Queue
*Autonomous threshold enforcement with 1-click Razorpay payment link generation for disbursements $\ge$ ₹50,000.*
![Approvals Queue](docs/screenshots/06_hitl_approvals_queue.png)

---

### 7. Role-Based Access Control (RBAC) Authentication Screen
*Enterprise authentication with official FinPilot AI branding and role-tailored workspaces for CFO, Finance Manager, Department Head, and Auditor.*
![Login Screen](docs/screenshots/01_login_screen.png)

---

### 8. Role-Based User-Targeted Notification & 2-Way Internal Communication
*Zero-leakage notification delivery scoped to authenticated users with threaded conversations and 1-click entity routing.*
![Role-Based Notifications Drawer](docs/screenshots/10_role_based_notifications_drawer.png)

---

## 🌟 Key Features

1. **Merchant Sales Growth & Smart Upsells**:
   - Conversational in-app checkout assistant with real-time dynamic cart, 18% GST calculation, and smart bundle discount incentives.
   - Autonomous Marketing Growth Campaign orchestrator that synchronizes spend with department budget balances, generating promotional Razorpay links and tracking ROAS.
2. **AI-to-AI Autonomous Shopping Protocol**:
   - Machine-readable Universal Commerce Manifest (`/v1/commerce/ai-manifest`) in JSON-LD / Schema.org format.
   - Bounded AI-to-AI purchasing: Autonomous AI buyers negotiate tiered bulk discounts (up to 15%) within hard spending token ceilings and Razorpay payment links.
3. **Financial Digital Twin & 90-Day Forward Simulation**:
   - Clones real-time financial state and runs counterfactual "what-if" simulations on burn velocities, deferred payouts, and headcount growth.
4. **Autonomous Multi-Agent Orchestration**:
   - 7 specialized agents (*Intent*, *Retrieval*, *Analysis*, *Risk*, *Simulation*, *Causal*, *Narrator*) executing deterministic hand-offs.
5. **Causal Anomaly Detection**:
   - Correlates financial variances with nearby operational signals (submitter clustering, vendor additions, tax offsets) to explain root causes.
6. **Self-Calibrating Policy Engine**:
   - Tracks human reviewer overrides to detect policy friction and propose 1-click calibrations.
7. **Four-Tier Failure Handling & Resilience Engine**:
   - **Gateway Drop / Timeout**: Exponential backoff with idempotency key and offline transaction queue.
   - **Malformed / Invalid Payload**: Field-level schema diagnostics with corrective guidance and zero ledger side-effects.
   - **Department Budget Cap Hit**: Pre-disbursement freeze and automated HITL escalation ticket.
   - **AI Spending Token Overage**: Token limit breach prevention and human override authorization link.

---

## 🏗️ Architecture

```
finpilot_ai/
├── src/
│   └── app/
│       ├── api/
│       │   └── endpoints/     # Commerce, Simulation, Invoices, Budgets, Approvals, Payroll, Chat
│       ├── core/              # Config, Security, Policy rules, RBAC
│       ├── data/              # Merchant catalog, Department budgets, Sample benchmarks
│       ├── graphs/            # LangGraph multi-agent controller state machine
│       ├── services/          # Merchant Commerce, Digital Twin, Policy Calibration, Multi-Agent Orchestrator
│       ├── static/            # Dark Razorpay-style fintech frontend & AI Commerce Studio
│       └── main.py            # Application entrypoint
├── docs/
│   └── screenshots/           # High-resolution UI captures (01 - 09)
├── tests/                     # 100% automated test suites
├── WALKTHROUGH.md             # Complete system & architecture guide
├── PITCH_DECK_GUIDE.md        # 5-minute executive pitch script & Q&A guide
└── pyproject.toml             # Project configuration & dependencies
```

---

## 🚀 Quickstart

### 1. Clone & Install
```bash
git clone https://github.com/GAUTAMX05/FinPilot-Ai.git
cd FinPilot-Ai
pip install -e .
```

### 2. Configure Environment
```bash
cp .env.example .env
# Add your OPENAI_API_KEY and RAZORPAY credentials
```

### 3. Launch Server
```bash
python run_server.py
```
- **Web Dashboard**: `http://localhost:8000/`
- **Commerce Studio**: `http://localhost:8000/?autologin=cfo&tab=commerce`
- **Agent Manifest (JSON-LD)**: `http://localhost:8000/v1/commerce/ai-manifest`
- **Swagger API Docs**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/health`

---

## 🧪 Automated Test Suites (100% Pass)

```bash
# Merchant Growth & AI-to-AI Shopping Suite
python tests/test_commerce_and_ai_shopping.py

# Digital Twin & Multi-Agent Tests
python tests/test_digital_twin_and_agents.py

# Decision Operating System Suite
python tests/test_decision_engine_upgrade.py

# AI Chat & Reasoning Pipeline
python tests/test_ai_chat_pipeline.py
```

---

## 📖 In-Depth System Documentation
- [WALKTHROUGH.md](WALKTHROUGH.md) — Comprehensive architectural breakdown, simulation math, and API schemas.
- [PITCH_DECK_GUIDE.md](PITCH_DECK_GUIDE.md) — Complete 5-minute executive pitch guide and judge Q&A cheat sheet.
