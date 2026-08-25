# 💰 FinPilot AI — Financial Digital Twin & Multi-Agent Autonomous Decision Operating System

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-purple.svg)](https://langchain-ai.github.io/langgraph/)
[![Razorpay](https://img.shields.io/badge/Razorpay-FINTECH%20API-blue.svg)](https://razorpay.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **"Most finance AI tools describe what already happened. FinPilot AI simulates what happens next — before a human has to decide."**

---

## 📸 Interface & Capabilities Showcase

### 1. Financial Digital Twin & What-If Simulation Studio
*Live simulate-able model: Evaluate forward spend velocity, deferred vendor payouts, and headcount growth before executing transactions.*
![Financial Digital Twin Studio](docs/screenshots/02_digital_twin_studio.png)

---

### 2. Executive Control Center & Financial Decision Engine
*Real-time corporate positions, dynamic time-series analytics, and automated decision review triggers.*
![Executive Control Center](docs/screenshots/03_executive_control_center.png)

---

### 3. Company Financial Decision Map
*Hierarchical control graph mapping Enterprise Root $\rightarrow$ Budgets & Cash $\rightarrow$ Department Risks $\rightarrow$ Actions.*
![Company Decision Map](docs/screenshots/04_company_decision_map.png)

---

### 4. Invoice Intelligence & Expense Affordability Auditor
*Automated 18% GST tax auditor, duplicate submission detection, and department runway affordability simulations.*
![Invoice Intelligence](docs/screenshots/05_invoice_intelligence_auditor.png)

---

### 5. Human-in-the-Loop (HITL) Disbursement Approvals Queue
*Autonomous threshold enforcement with 1-click Razorpay payment link generation for disbursements $\ge$ ₹50,000.*
![Approvals Queue](docs/screenshots/06_hitl_approvals_queue.png)

---

### 6. Role-Based Access Control (RBAC) Authentication Screen
*Enterprise authentication with role-tailored workspaces for CFO, Finance Manager, Department Head, and Auditor.*
![Login Screen](docs/screenshots/01_login_screen.png)

---

## 🌟 Key Features

1. **Financial Digital Twin & 90-Day Forward Simulation**:
   - Clones real-time financial state and runs counterfactual "what-if" simulations on burn velocities, deferred payouts, and headcount growth.
2. **Autonomous Multi-Agent Orchestration**:
   - 7 specialized agents (*Intent*, *Retrieval*, *Analysis*, *Risk*, *Simulation*, *Causal*, *Narrator*) executing deterministic hand-offs.
3. **Causal Anomaly Detection**:
   - Correlates financial variances with nearby operational signals (submitter clustering, vendor additions, tax offsets) to explain root causes.
4. **Self-Calibrating Policy Engine**:
   - Tracks human reviewer overrides to detect policy friction and propose 1-click calibrations.
5. **Role-Based Access Control (RBAC) & Explainability**:
   - Enforces granular permissions and tailors explanation depth for CFO, Finance Manager, Department Head, and Auditor.
6. **Two-Stage Hybrid Reconciliation**:
   - Reconciles bank statements, gateway settlements, and internal ledgers.
7. **Razorpay Financial Gateway & HITL Governance**:
   - Dispatches automated payment links and requests human sign-off for expenses exceeding ₹50,000.

---

## 🏗️ Architecture

```
finpilot_ai/
├── src/
│   └── app/
│       ├── api/               # FastAPI route endpoints (Chat, Simulation, Invoices, Budgets, Approvals)
│       ├── core/              # Config, Security, Policy rules, RBAC
│       ├── data/              # Department budgets & sample invoice benchmarks
│       ├── graphs/            # LangGraph multi-agent controller state machine
│       ├── services/          # Digital Twin, Policy Calibration, Multi-Agent Orchestrator, etc.
│       ├── static/            # Dark Razorpay-style fintech frontend & What-If Studio
│       └── main.py            # Application entrypoint
├── docs/
│   └── screenshots/           # High-resolution UI captures
├── tests/                     # Automated test suites
├── WALKTHROUGH.md             # Complete system & architecture guide
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
- **Swagger Documentation**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/health`

---

## 🧪 Automated Test Suites (100% Pass)

```bash
# Digital Twin & Multi-Agent Tests
python tests/test_digital_twin_and_agents.py

# Decision Operating System Suite
python tests/test_decision_engine_upgrade.py

# AI Chat & Reasoning Pipeline
python tests/test_ai_chat_pipeline.py
```

---

## 📖 In-Depth System Documentation
For the full architectural breakdown, multi-agent state machines, and mathematical models, read [WALKTHROUGH.md](WALKTHROUGH.md).
