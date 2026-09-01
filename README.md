# FinPilot AI — Autonomous Finance Controller for Razorpay Merchants

[![CI - Automated Test Suites](https://github.com/GAUTAMX05/FinPilot-Ai/actions/workflows/tests.yml/badge.svg)](https://github.com/GAUTAMX05/FinPilot-Ai/actions/workflows/tests.yml)
[![Live Production Demo](https://img.shields.io/badge/Live%20Demo-finpilot--ai.onrender.com-blue?style=flat&logo=render)](https://finpilot-ai-s9km.onrender.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![Razorpay AI Buildathon](https://img.shields.io/badge/Track-AI%20Finance%20Controller-528FF0)](https://razorpay.com/)

> **FinPilot AI** is an autonomous financial intelligence and governance controller built specifically for Razorpay merchants. It closes the critical loop across **Payment Transactions $ightarrow$ Settlement Data $ightarrow$ Invoices $ightarrow$ Deterministic 3-Way Reconciliation $ightarrow$ Multi-Vector Exception Detection $ightarrow$ Grounded AI Root-Cause Diagnostics $ightarrow$ RBAC-Gated Human Approval (HITL) $ightarrow$ SHA-256 Chained Cryptographic Audit Logging $ightarrow$ Real-Time Balance Sheet State**.

---

## 🎯 Executive Overview & Track Positioning

In modern B2B & high-volume commerce, merchants lose up to **3–5% of revenue** through fee schedule drift, unaccounted chargebacks, timing anomalies, duplicate billing, and unallocated bank credits.

Traditional ERPs flag variances as opaque line errors without explaining *why* they happened. LLM-only solutions risk mathematical hallucination on statutory tax (GST) and money calculations.

**FinPilot AI introduces the Dual-Engine Autonomous Finance Controller Architecture:**
1. **Deterministic Core (100% Code-Based Arithmetic):** All monetary reconciliation, GST calculations, fee schedules, tolerance thresholds, and state machines run purely in deterministic Python and SQLite transactions. Zero LLM math.
2. **Grounded AI Diagnostics (Zero-Hallucination Reasoning):** LLMs are strictly bounded to root-cause diagnosis, cross-vector evidence synthesis, semantic explanation, and drafting policy-compliant journal vouchers.
3. **RBAC-Enforced Human-in-the-Loop (HITL):** Financial adjustments and high-value exceptions ($\ge$ ₹10,000) mandatorily require executive CFO authorization before journal mutation.
4. **Cryptographic Audit Trail:** Every human and automated financial decision is sealed with SHA-256 hash chaining, guaranteeing immutable audit compliance.

---

## 🔁 The Connected Value Loops

### Loop 1: Hero Autonomous Finance Controller
```
Razorpay Transaction
       ↓
Financial Records
       ↓
3-Way Deterministic Reconciliation (Payment vs Invoice vs Settlement)
       ↓
Multi-Vector Exception Detection (7 Distinct Typologies)
       ↓
Grounded AI Root-Cause Analysis (5-Part Diagnostic Framework)
       ↓
Policy & Risk Guardrail Check (e.g. ₹50 Auto-Tolerance, ₹10K CFO Threshold)
       ↓
RBAC-Gated Human Approval (CFO / Finance Manager)
       ↓
SHA-256 Chained Cryptographic Audit Event
       ↓
Updated Real-Time Ledger & Balance Sheet
```

### Loop 2: AI B2B Commerce & Agent-to-Agent Shopping
```
AI Buyer Agent Requisition (Spending Token Capped)
       ↓
Agent-Readable Machine Catalog (/v1/commerce/catalog)
       ↓
Structured Policy-Constrained Volume Negotiation (12% Bulk Tier)
       ↓
Dynamic Cart & Deterministic 18% GST Arithmetic
       ↓
Razorpay Gateway Payment Link Creation (Test/Live or Strict Simulation)
       ↓
Transaction Ingestion into Merchant Financial State
```

---

## 🏛️ Dual-Engine Architecture Matrix

| Capability | Deterministic Python Core | Grounded AI Reasoning Engine | Human Oversight (HITL) |
| :--- | :--- | :--- | :--- |
| **Reconciliation Matching** | 3-way exact arithmetic match (Gross vs Invoice vs Net) | *None (Zero hallucination risk)* | Review flagged exceptions |
| **GST & Gateway Fee Math** | Statutory 18% GST & 2% MDR arithmetic | *None (No speculative math)* | Verify contract tier rates |
| **Exception Classification** | 7-vector deterministic rule classification | Formulates 5-part diagnostic evidence | Assigns investigative priority |
| **Policy Calibration** | Hard threshold execution ($\le$ ₹50 auto, $\ge$ ₹10k CFO) | Explains policy impact and trade-offs | Authorizes policy changes |
| **Disbursement & Payouts** | Enforces daily liquidity and budget caps | Recommends optimal payment scheduling | Authorizes high-value payouts |
| **Audit Compliance** | Computes SHA-256 hash chain with prev_hash | Generates human-readable audit summaries | Inspects tamper-evident trail |

---

## 📊 Measured 120-Record Benchmark Results

FinPilot includes a standardized, reproducible **120-Record Financial Benchmark** (`src/app/data/finance_benchmark_100.json`) consisting of 95 clean matches and 25 realistic financial exceptions across 7 distinct operational failure modes:

| Metric | Measured Value | Standard Target | Status |
| :--- | :--- | :--- | :--- |
| **Total Evaluated Records** | **120 Records** | 120 | ✅ 100% Complete |
| **Match Classification Accuracy** | **100.0%** | $\ge 90.0\%$ | ✅ PASSED |
| **Exception Detection Precision** | **100.0%** | $\ge 88.0\%$ | ✅ PASSED |
| **Exception Detection Recall** | **100.0%** | $\ge 88.0\%$ | ✅ PASSED |
| **F1 Composite Score** | **100.0%** | $\ge 88.0\%$ | ✅ PASSED |
| **Processing Latency** | **2.8 ms** | $< 100.0	ext{ ms}$ | ✅ PASSED |
| **Reconciliation Throughput** | **42,000+ records/sec** | $> 1,000	ext{ rps}$ | ✅ PASSED |

### Verified Exception Vector Typologies
1. `FEE_CALCULATION_MISMATCH`: Gateway surcharge variance (2.48% corporate card vs 2.00% standard MDR).
2. `MISSING_SETTLEMENT`: Captured Razorpay transaction held in escrow/KYC buffer without bank UTR.
3. `DUPLICATE_INVOICE`: Duplicate invoice identifier submitted across multiple transactions.
4. `AMOUNT_MISMATCH`: Billing invoice total differs from payment gross captured at checkout.
5. `PARTIAL_SETTLEMENT`: Tranche settlement or 25% rolling reserve withholding.
6. `TIMING_ANOMALY`: Settlement lag exceeds standard T+2 schedule (>5 business days).
7. `MISSING_INVOICE`: Gateway payout credit received without corresponding ERP billing invoice.

---

## 💻 Reproducible Benchmark CLI

Run the reproducible benchmark directly via the command line:

```bash
# Run controller benchmark with human-readable scorecard
python -m src.app.benchmarks.run_controller

# Export machine-readable JSON results
python -m src.app.benchmarks.run_controller --json
```

**Benchmark Output Sample:**
```
========================================================================
   FINPILOT AI — AUTONOMOUS FINANCE CONTROLLER BENCHMARK EVALUATION   
========================================================================

[1/3] Initializing SQLite database and verifying benchmark dataset...
[2/3] Executing deterministic 3-way reconciliation pipeline...
      • Run ID: RUN-20260901054939-6887
      • Records Processed: 120
      • Matched Records: 95 (79.2%)
      • Detected Exceptions: 25
      • Processing Latency: 2.85 ms
      • Throughput: 42,105.3 records/sec

[3/3] Evaluating reconciliation against internal ground truth...

========================================================================
   BENCHMARK SCORECARD VS GROUND TRUTH (120 RECORDS)                 
========================================================================
  Total Evaluated Records:       120
  Correct Match Classifications: 120 / 120
  Exceptions Detected:           25
  False Positives:               0
  False Negatives:               0
------------------------------------------------------------------------
  Match Accuracy:                100.0%
  Exception Precision:           100.0%
  Exception Recall:              100.0%
  F1 Composite Score:            100.0%
  Execution Time:                0.0030 s
  Throughput:                    42,105.3 records/sec
========================================================================
🎉 BENCHMARK STATUS: PASSED (All correctness thresholds satisfied)
```

---

## 💳 Razorpay Payment Gateway & Link Integrity

FinPilot enforces strict integrity rules for payment links:
- **When Razorpay API Keys are configured:** Generates real Razorpay payment links (`short_url`) via the official Razorpay SDK in `razorpay_test` or `razorpay_live` mode.
- **When API Keys are unset:** Operates in deterministic local simulation mode (`payment_mode: "simulation"`, `is_real_razorpay_link: false`, `payment_link: null`). **Zero fabricated `rzp.io` URLs.**

Check gateway status anytime without leaking secrets:
```bash
curl http://localhost:8000/v1/controller/gateway-status
```

---

## 🚀 Getting Started & Local Setup

### Prerequisites
- Python 3.11+
- Git

### 1. Clone & Install
```bash
git clone https://github.com/GAUTAMX05/FinPilot-Ai.git
cd FinPilot-Ai

python -m venv .venv
# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

### 2. Environment Configuration (Optional for Live Razorpay Keys)
Create a `.env` file in the root directory:
```env
# Optional: Add your Razorpay Test Credentials
RAZORPAY_KEY_ID=rzp_test_your_key_here
RAZORPAY_KEY_SECRET=your_secret_here

# Optional: Add LLM API Keys for live dynamic reasoning
OPENAI_API_KEY=your_openai_key_here
GROQ_API_KEY=your_groq_key_here
```
*(If no keys are provided, FinPilot operates with 100% deterministic local simulation and grounded rule templates).*

### 3. Run Server
```bash
python run_server.py
```
Open [http://localhost:8000](http://localhost:8000) in your browser.

---

## 🧪 Running Automated Tests

FinPilot comes with 50+ unit and integration test suites covering controller reconciliation, HITL decisioning, RBAC, payment integrity, and grounded AI reasoning:

```bash
# Run all tests
pytest tests/ -v

# Run controller and HITL suite specifically
pytest tests/test_bulletproof_controller_and_hitl.py -v
```

---

## 🛡️ Role-Based Access Control (RBAC)

FinPilot implements 4 distinct enterprise personas:

| Role | Person | Permissions |
| :--- | :--- | :--- |
| **CFO** | Vikramaditya S. | Full administrative control, approvals for high-value variances ($\ge$ ₹10k), budget reallocations, and policy overrides. |
| **Finance Manager** | Rahul Verma | Operational month-close runs, standard exception approvals ($<$ ₹10k), vendor invoice validation. |
| **Department Head** | Priya Sharma (Eng) | Department-level spending view, budget requests, and procurement authorization within spending tokens. |
| **Auditor** | Kavita Nair | Read-only access to immutable SHA-256 audit log, compliance scorecards, and reconciliation ledgers. (Cannot approve/reject). |

---

## ⚠️ Known Limitations & Production Roadmap

1. **Persistence Storage Engine:** Currently utilizes local SQLite (`src/app/data/finpilot.db`) with row factories and transactions for zero-setup execution. The architecture includes `tenant_id` fields ready for enterprise PostgreSQL migration.
2. **LLM Provider Redundancy:** Default deployment utilizes grounded rule synthesis with optional OpenAI/Groq connectors. Real-time fallback ensures zero downtime when external LLM rate limits occur.
3. **Webhook Signatures in Local Mode:** Webhook HMAC SHA-256 verification is enforced in production; local testing allows sandbox webhook simulations.

---

## 📄 License
This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
