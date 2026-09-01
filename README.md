<p align="center">
  <img src="docs/assets/logo.png" alt="FinPilot AI Logo" width="220" />
</p>

# FinPilot AI — Autonomous Finance Controller for Razorpay Merchants

**Live Demo:** [https://finpilot-ai-s9km.onrender.com/](https://finpilot-ai-s9km.onrender.com/)

> [!NOTE]
> **Cold Start Notice:** First load may take up to 60 seconds while the Render free-tier instance wakes up.

### 1-Click Demo Role Logins
| Role | Email / Identifier | Password | 1-Click Autologin Link |
|---|---|---|---|
| **CFO** | `cfo@aifinance.local` | `password123` | [Launch CFO Workspace](https://finpilot-ai-s9km.onrender.com/?autologin=cfo) |
| **Finance Manager** | `financemanager@aifinance.local` | `password123` | [Launch Finance Manager Workspace](https://finpilot-ai-s9km.onrender.com/?autologin=fm) |
| **Department Head** | `depthead@aifinance.local` | `password123` | [Launch Department Head Workspace](https://finpilot-ai-s9km.onrender.com/?autologin=head) |
| **Auditor** | `auditor@aifinance.local` | `password123` | [Launch Auditor Workspace](https://finpilot-ai-s9km.onrender.com/?autologin=auditor) |

[![CI Tests](https://github.com/GAUTAMX05/FinPilot-Ai/actions/workflows/tests.yml/badge.svg)](https://github.com/GAUTAMX05/FinPilot-Ai/actions/workflows/tests.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-purple.svg)](https://langchain-ai.github.io/langgraph/)
[![Razorpay](https://img.shields.io/badge/Razorpay-FINTECH%20API-blue.svg)](https://razorpay.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🎯 Executive Summary

FinPilot AI is an **Autonomous Finance Controller for Razorpay Merchants** that closes the reconciliation loop:

$$	ext{Transactions} \longrightarrow 	ext{Settlements} \longrightarrow 	ext{Invoices} \longrightarrow 	ext{3-Way Match} \longrightarrow 	ext{Exception Detection} \longrightarrow 	ext{AI Root Cause} \longrightarrow 	ext{Policy Checks} \longrightarrow 	ext{Human Approval} \longrightarrow 	ext{Audit Trail}$$

FinPilot processes 100+ payment, settlement, and invoice records simultaneously. It automatically executes deterministic 3-way reconciliation, audits Razorpay 2% processing fees and 18% GST deductions, diagnoses root causes using grounded AI reasoning, and routes high-value adjustments to human reviewers with an immutable SHA-256 chained audit trail.

---

## 📊 Measured Benchmark Performance (120-Record Ground Truth)

FinPilot includes a deterministic 120-record financial benchmark (`src/app/data/finance_benchmark_100.json`) with 95 normal transactions and 25 realistic multi-vector known exceptions.

| Metric | Measured Result | Benchmark Standard | Verification Method |
|---|:---:|:---:|---|
| **Total Processed Records** | **120 Records** | $\ge 100$ records | SQLite batch run via `POST /v1/controller/close-month` |
| **Match Accuracy** | **100.0%** | $\ge 90.0\%$ | `(Correct Matches + Detected Exceptions) / 120` |
| **Exception Precision** | **100.0%** | $\ge 88.0\%$ | $TP / (TP + FP)$ — Zero false alarms on clean records |
| **Exception Recall** | **100.0%** | $\ge 88.0\%$ | $TP / (TP + FN)$ — All 25 known exceptions detected |
| **F1 Composite Score** | **100.0%** | $\ge 88.0\%$ | Harmonic mean of Precision and Recall |
| **Processing Throughput** | **32,500+ records/sec** | $\ge 50$ records/sec | `120 records / 0.0037s` execution latency |

---

## 🏗️ Dual Engine Architecture: Deterministic vs AI vs Human

FinPilot strictly separates deterministic code logic from probabilistic AI reasoning:

| Layer | Implementation Mechanism | Responsibilities & Scope |
|---|---|---|
| **1. Deterministic Engine** | Pure Python Arithmetic & SQLite (`database.py`) | • 100% exact float arithmetic (Zero LLM math)<br>• Razorpay fee math ($	ext{Gross} 	imes 0.02$) & statutory 18% GST<br>• 3-Way Payment vs Invoice vs Settlement matching<br>• Hard ₹10,000 threshold & duplicate detection<br>• SHA-256 cryptographic hash chaining |
| **2. AI Reasoning Engine** | Grounded Multi-Agent Service (`ai_reasoning_engine.py`) | • Multi-vector exception classification<br>• Grounded root-cause diagnosis from verified numbers<br>• 5-step structured finance team explanations<br>• Natural-language copilot summaries |
| **3. Human In The Loop** | Interactive Review Drawer (`controller.py`) | • 1-Click Approve / Reject / Escalate actions<br>• Mandatory approval on high-value adjustments (> ₹10k)<br>• Overrides for ambiguous business exceptions<br>• Recorded approver identity in audit trail |

---

## 🎬 3-to-5 Minute Live Demo Flow

1. **Step 1 — Open Dashboard:** Immediately view the **Autonomous Finance Controller** header and real-time KPI cards.
2. **Step 2 — Click `[⚡ CLOSE MONTH]`:** The system executes the 6-stage autonomous reconciliation pipeline across 120 records in milliseconds.
3. **Step 3 — Inspect Real KPIs:** Dynamically calculated values display: `120 Processed`, `95 Reconciled (79.2%)`, `25 Exceptions`, `₹14.51L Under Review`, `32,500 records/sec`.
4. **Step 4 — Open Exception Center:** View active exceptions with categorized variances (e.g. `EXC-0001` Settlement Fee Variance of ₹105.80).
5. **Step 5 — Run AI Investigation:** Click `[Investigate]` to open the grounded 5-part AI diagnostic report:
   - **What Happened:** *Settlement payout reflects fee deduction variance of ₹105.80 INR.*
   - **Why It Happened:** *Razorpay applied international/corporate surcharge rate (2.48%) instead of contracted 2.00% schedule.*
   - **Evidence:** *Invoice: ₹84,500.00 \| Gross: ₹84,500.00 \| Fee: ₹2,100.00 \| Expected Net: ₹82,505.80 \| Actual Settled: ₹82,400.00.*
   - **Recommendation:** *Create reconciliation fee adjustment journal entry for ₹105.80.*
   - **Triggered Policy:** `REVIEW_GATEWAY_SURCHARGE`.
6. **Step 6 — Human-in-the-Loop Action:** Click `[Approve Adjustment]` $ightarrow$ updates live status to `HUMAN_APPROVED`.
7. **Step 7 — Inspect Audit Trail:** Navigate to **Immutable Audit Trail** to verify the chronological log entry with actor name, timestamp, and SHA-256 hash.
8. **Step 8 — Open Benchmark & Evaluation:** Navigate to **Benchmark & Evaluation** to review the objective scorecard (100% Accuracy, 100% Precision, 100% Recall, 100% F1).

---

## 🛍️ Secondary Financial Intelligence & Operations Features

While the Finance Controller is the primary hero functionality, FinPilot preserves supporting enterprise finance tools in secondary navigation:
- **Financial Copilot (`/v1/chat`):** Natural-language financial Q&A and runway analysis.
- **Financial Digital Twin (`/v1/simulation`):** 90-day forward cash-flow simulation with parameter sliders.
- **Company Decision Map (`/decisionmap`):** Hierarchical governance graph mapping budgets to department risks.
- **AI Commerce Studio (`/v1/commerce`):** Agent-readable product catalog (`/v1/commerce/ai-manifest`), AI-to-AI shopping simulator, and Razorpay test checkout links.
- **Department Budgets & Approvals:** Real-time department ledger burn rates and ₹50,000 disbursement approval queues.

---

## 🚀 Quickstart & Setup

### 1. Clone & Install
```bash
git clone https://github.com/GAUTAMX05/FinPilot-Ai.git
cd FinPilot-Ai
pip install -r requirements.txt
pip install -e .
```

### 2. Configure Environment (Optional)
```bash
cp .env.example .env
# App boots in fallback test mode if external API keys are omitted
```

### 3. Launch Server
```bash
python run_server.py
```
- **Web Dashboard:** `http://localhost:8000/`
- **Reconciliation Engine:** `http://localhost:8000/?autologin=cfo&tab=reconciliation`
- **Exception Center:** `http://localhost:8000/?autologin=cfo&tab=exceptions`
- **Benchmark Evaluation:** `http://localhost:8000/?autologin=cfo&tab=evaluation`
- **Swagger API Docs:** `http://localhost:8000/docs`

---

## 🧪 Automated Test Verification

All 5 test suites run on every commit and pull request via GitHub Actions CI:

```bash
# 1. Autonomous Finance Controller Benchmark Test Suite
python tests/test_finance_controller_benchmark.py

# 2. Merchant Commerce & AI Shopping Suite
python tests/test_commerce_and_ai_shopping.py

# 3. Financial Digital Twin & Multi-Agent Tests
python tests/test_digital_twin_and_agents.py

# 4. Financial Decision Engine Upgrade Suite
python tests/test_decision_engine_upgrade.py

# 5. AI Chat & Comprehensive Reasoning Pipeline
python tests/test_ai_chat_pipeline.py
```

---

## ⚠️ Known Limitations & Production Roadmap

1. **Synthetic Benchmark Dataset:** Benchmark records represent realistic simulated Razorpay transactions, settlements, and invoices rather than live merchant banking feeds.
2. **Test-Mode Payment Rails:** Razorpay integration operates on test API keys and sandbox payment links (`https://rzp.io/i/...`).
3. **Database Architecture:** Uses lightweight embedded SQLite (`finpilot.db`) for zero-dependency local and container deployment; production deployment would transition to a distributed PostgreSQL cluster.
4. **Single-Tenant Workspace:** Simulates multi-role enterprise RBAC (CFO, Finance Manager, Department Head, Auditor) across a single merchant dataset rather than isolated multi-tenant organizations.
