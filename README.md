# 💰 FinPilot AI

**FinPilot AI** is an autonomous multi-agent financial digital twin and decision operating system powered by **FastAPI**, **LangGraph**, and **Razorpay**.

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
│       ├── core/              # Config, Security, Policy rules
│       ├── data/              # Department budgets & sample invoice benchmarks
│       ├── graphs/            # LangGraph multi-agent controller state machine
│       ├── services/          # Digital Twin, Policy Calibration, Multi-Agent Orchestrator, etc.
│       ├── static/            # Dark Razorpay-style fintech frontend & What-If Studio
│       └── main.py            # Application entrypoint
├── tests/                     # Automated test suites
└── pyproject.toml             # Project configuration & dependencies
```

---

## 🚀 Quickstart

1. **Install Dependencies**:
   ```bash
   pip install -e .
   ```

2. **Configure Environment Variables**:
   ```bash
   cp .env.example .env
   # Edit .env and supply your OPENAI_API_KEY and RAZORPAY credentials
   ```

3. **Start the API Server**:
   ```bash
   uvicorn src.app.main:app --reload --port 8000
   ```

4. **Access the API Docs**:
   - Swagger UI: `http://localhost:8000/docs`
   - Health Check: `http://localhost:8000/health`
