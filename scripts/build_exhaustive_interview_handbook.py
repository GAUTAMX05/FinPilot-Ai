import os
import sys
import subprocess
from pathlib import Path

# Script to assemble the complete 75-Part FinPilot AI Technical Interview Handbook
# and compile it into a publication-grade PDF via Headless Chrome.

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(CHROME):
    CHROME = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def generate_handbook():
    print("Generating Complete 75-Part Technical Interview Handbook...")
    
    html_file = PROJECT_ROOT / "docs" / "Finpilot_AI_Technical_Interview_Handbook.html"
    out_pdf_docs = PROJECT_ROOT / "docs" / "Finpilot_AI_Technical_Interview_Handbook.pdf"
    static_docs = PROJECT_ROOT / "src" / "app" / "static" / "docs"
    static_docs.mkdir(parents=True, exist_ok=True)
    out_pdf_static = static_docs / "Finpilot_AI_Technical_Interview_Handbook.pdf"

    # We will write the exhaustive HTML content
    with open(html_file, "w", encoding="utf-8") as f:
        f.write('''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>FinPilot AI — Complete Technical Interview & System Architecture Master Handbook</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    @page {
      size: A4;
      margin: 16mm 14mm 16mm 14mm;
      @bottom-right {
        content: counter(page);
        font-size: 9pt;
        color: #64748B;
        font-family: 'Inter', sans-serif;
      }
    }
    body {
      font-family: 'Inter', sans-serif;
      color: #0F172A;
      background: #FFFFFF;
      line-height: 1.55;
      font-size: 11.5pt;
    }
    .mono { font-family: 'JetBrains Mono', monospace; font-size: 10pt; }
    .page-break { page-break-before: always; }
    .avoid-break { page-break-inside: avoid; }
    h1, h2, h3, h4, h5 { font-family: 'Inter', sans-serif; font-weight: 800; color: #061124; }
    h2 { border-bottom: 2px solid #2563EB; padding-bottom: 4px; margin-top: 24px; margin-bottom: 12px; font-size: 15pt; text-transform: uppercase; letter-spacing: 0.5px; }
    h3 { font-size: 12.5pt; margin-top: 16px; margin-bottom: 8px; color: #1E40AF; }
    h4 { font-size: 11pt; margin-top: 12px; margin-bottom: 6px; color: #0F172A; }
    p { margin-bottom: 10px; color: #334155; }
    ul, ol { margin-left: 20px; margin-bottom: 10px; color: #334155; }
    li { margin-bottom: 4px; }
    code { font-family: 'JetBrains Mono', monospace; background: #F1F5F9; padding: 2px 5px; border-radius: 4px; font-size: 10pt; color: #0284C7; border: 1px solid #E2E8F0; }
    pre { font-family: 'JetBrains Mono', monospace; background: #061124; color: #F8FAFC; padding: 12px; border-radius: 8px; font-size: 9.5pt; line-height: 1.45; overflow-x: auto; margin-bottom: 12px; border: 1px solid #1E293B; }
    table { width: 100%; border-collapse: collapse; margin-top: 10px; margin-bottom: 14px; font-size: 10pt; }
    th { background: #0F1D32; color: #FFFFFF; font-weight: 700; padding: 8px 10px; text-align: left; border: 1px solid #CBD5E1; }
    td { padding: 7px 10px; border: 1px solid #CBD5E1; color: #1E293B; vertical-align: top; }
    tr:nth-child(even) { background-color: #F8FAFC; }
    .callout { background: #EFF6FF; border-left: 4px solid #2563EB; padding: 12px 14px; border-radius: 0 8px 8px 0; margin-bottom: 12px; }
    .callout-warning { background: #FFFBEB; border-left: 4px solid #F59E0B; padding: 12px 14px; border-radius: 0 8px 8px 0; margin-bottom: 12px; }
    .callout-danger { background: #FEF2F2; border-left: 4px solid #EF4444; padding: 12px 14px; border-radius: 0 8px 8px 0; margin-bottom: 12px; }
    .callout-success { background: #F0FDF4; border-left: 4px solid #22C55E; padding: 12px 14px; border-radius: 0 8px 8px 0; margin-bottom: 12px; }
    .qa-box { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 14px; margin-bottom: 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    .qa-header { font-weight: 800; color: #1E3A8A; margin-bottom: 6px; font-size: 11.5pt; }
    .tag-impl { background: #DCFCE7; color: #15803D; font-weight: 700; padding: 2px 6px; border-radius: 4px; font-size: 8.5pt; border: 1px solid #86EFAC; }
    .tag-partial { background: #FEF9C3; color: #A16207; font-weight: 700; padding: 2px 6px; border-radius: 4px; font-size: 8.5pt; border: 1px solid #FDE047; }
    .tag-future { background: #E0E7FF; color: #4338CA; font-weight: 700; padding: 2px 6px; border-radius: 4px; font-size: 8.5pt; border: 1px solid #C7D2FE; }
  </style>
</head>
<body class="p-4 max-w-5xl mx-auto">

  <!-- ===================================================================== -->
  <!-- TITLE PAGE -->
  <!-- ===================================================================== -->
  <div class="text-center py-16 border-b-4 border-blue-600 mb-12 avoid-break">
    <img src="assets/logo.png" alt="FinPilot AI Logo" class="w-36 h-36 mx-auto mb-6 rounded-2xl shadow-xl border-2 border-slate-700 p-2 object-contain bg-[#071426]">
    <h1 class="text-5xl font-black tracking-tight text-slate-900 mb-3">FINPILOT <span class="text-blue-600">AI</span></h1>
    <p class="text-lg font-extrabold text-blue-600 tracking-widest uppercase mb-4">FINANCE • CONTROL • DECIDE • GROW</p>
    <h2 class="text-2xl font-bold text-slate-700 max-w-3xl mx-auto mb-8 border-none pb-0">
      AI-Powered Financial Decision & Control Platform
    </h2>
    <div class="inline-block bg-slate-900 text-white rounded-xl px-8 py-4 text-sm font-semibold mb-8 shadow-md">
      Comprehensive Technical Architecture, Implementation Guide, Interview Preparation & Viva Master Handbook (Parts 1 – 75)
    </div>

    <div class="grid grid-cols-3 gap-6 text-xs text-slate-600 max-w-2xl mx-auto pt-6 border-t border-slate-200 text-left">
      <div>
        <strong class="block text-slate-900 uppercase font-bold text-[10pt]">Project Metadata</strong>
        <span class="block mt-1"><strong>Name:</strong> FinPilot AI</span>
        <span class="block"><strong>Core Stack:</strong> FastAPI • LangGraph • Razorpay • Tailwind</span>
      </div>
      <div>
        <strong class="block text-slate-900 uppercase font-bold text-[10pt]">Architecture Layer</strong>
        <span class="block mt-1"><strong>Design:</strong> Hybrid Deterministic + Agentic</span>
        <span class="block"><strong>Digital Twin:</strong> 90-Day Forward Engine</span>
      </div>
      <div>
        <strong class="block text-slate-900 uppercase font-bold text-[10pt]">Evaluation & Security</strong>
        <span class="block mt-1"><strong>RBAC:</strong> 4 Isolated Enterprise Roles</span>
        <span class="block"><strong>Audit:</strong> SHA-256 Chained Hash Ledger</span>
      </div>
    </div>
  </div>

  <!-- ===================================================================== -->
  <!-- TABLE OF CONTENTS -->
  <!-- ===================================================================== -->
  <div class="mb-12 avoid-break">
    <h2>Table of Contents</h2>
    <div class="grid grid-cols-2 gap-x-8 gap-y-1 text-xs text-slate-700 mt-4 leading-relaxed">
      <div>
        <p><strong>Part 1:</strong> Project Overview & Philosophy</p>
        <p><strong>Part 2:</strong> 30-Sec, 1-Min, 2-Min & 5-Min Pitches</p>
        <p><strong>Part 3:</strong> Problem Statement & Modern Solutions</p>
        <p><strong>Part 4:</strong> Complete Feature List (Implemented/Partial/Future)</p>
        <p><strong>Part 5:</strong> Technology Stack & Rationale</p>
        <p><strong>Part 6:</strong> System Architecture & End-to-End Pipeline</p>
        <p><strong>Part 7:</strong> Frontend Architecture (SPA, Charts, Modals)</p>
        <p><strong>Part 8:</strong> Backend Architecture (FastAPI, Routers, Services)</p>
        <p><strong>Part 9:</strong> Database Schemas & ER Data Relationships</p>
        <p><strong>Part 10:</strong> Authentication & Session Security</p>
        <p><strong>Part 11:</strong> Role-Based Access Control (RBAC) Matrix</p>
        <p><strong>Part 12:</strong> User-Targeted Notification System</p>
        <p><strong>Part 13:</strong> LangGraph Multi-Agent Implementation</p>
        <p><strong>Part 14:</strong> AI Agent Architecture & Hand-Offs</p>
        <p><strong>Part 15:</strong> LLM Integration, Prompts & Context</p>
        <p><strong>Part 16:</strong> Deterministic Financial Logic vs. Probabilistic LLM</p>
        <p><strong>Part 17:</strong> Financial Tool Calling (12 Tools Documented)</p>
        <p><strong>Part 18:</strong> Financial Decision Engine Architecture</p>
        <p><strong>Part 19:</strong> Decision Tree & Governance Branching</p>
        <p><strong>Part 20:</strong> Budget Management & Overrun Prediction</p>
        <p><strong>Part 21:</strong> Invoice Ingestion & Auditing Engine</p>
        <p><strong>Part 22:</strong> Deterministic 18% GST Arithmetic</p>
        <p><strong>Part 23:</strong> Multi-Attribute Duplicate Invoice Detection</p>
        <p><strong>Part 24:</strong> 3-Way Reconciliation (Ledger, Bank, Razorpay)</p>
        <p><strong>Part 25:</strong> Razorpay Test-Mode Payment Rails Integration</p>
        <p><strong>Part 26:</strong> Human-in-the-Loop (HITL) Governance</p>
        <p><strong>Part 27:</strong> Cash Flow Forecasting & Liquidity Runway</p>
        <p><strong>Part 28:</strong> Multi-Factor Vendor Risk Profiling</p>
        <p><strong>Part 29:</strong> Employee Financial Profile Management</p>
        <p><strong>Part 30:</strong> Employee Allowance Policy & Friction Detection</p>
        <p><strong>Part 31:</strong> Salary Structure & Revision Audit Trail</p>
        <p><strong>Part 32:</strong> Payroll Register Validation & Anomaly Checks</p>
        <p><strong>Part 33:</strong> Form 16 / Tax Reconciliation Engine</p>
        <p><strong>Part 34:</strong> Financial Decision Copilot Chat Flow</p>
        <p><strong>Part 35:</strong> Conversation Memory & State Checkpointing</p>
        <p><strong>Part 36:</strong> Full-Spectrum Security & Defense</p>
        <p><strong>Part 37:</strong> AI Safety, Prompt Injection & Token Boundaries</p>
        <p><strong>Part 38:</strong> Error Handling & Failure Mode Recovery</p>
      </div>
      <div>
        <p><strong>Part 39:</strong> Logging & Immutable Cryptographic Auditability</p>
        <p><strong>Part 40:</strong> Performance Optimizations & Latency Control</p>
        <p><strong>Part 41:</strong> Scalability: 100 to 1,000,000 Transactions</p>
        <p><strong>Part 42:</strong> Deployment Architecture & Containerization</p>
        <p><strong>Part 43:</strong> Environment Variables & Secret Configuration</p>
        <p><strong>Part 44:</strong> Exhaustive API Endpoint Reference</p>
        <p><strong>Part 45:</strong> Complete Visual Data Flows (15 Workflows)</p>
        <p><strong>Part 46:</strong> File-by-File Codebase Navigation Guide</p>
        <p><strong>Part 47:</strong> Critical Source Code Snippets & Explanations</p>
        <p><strong>Part 48:</strong> Technology Justifications & Trade-Offs</p>
        <p><strong>Part 49:</strong> Alternative Architectures Evaluated</p>
        <p><strong>Part 50:</strong> Honest Limitations & Technical Debt</p>
        <p><strong>Part 51:</strong> Future Roadmap & Enterprise Scope</p>
        <p><strong>Part 52:</strong> 150 Technical Interview Questions</p>
        <p><strong>Part 53:</strong> Comprehensive Technical Answers & Examples</p>
        <p><strong>Part 54:</strong> Top 50 Most Likely Interview Questions</p>
        <p><strong>Part 55:</strong> Tough Interviewer Trick Questions & Defenses</p>
        <p><strong>Part 56:</strong> HR, Behavioral & Contribution Questions</p>
        <p><strong>Part 57:</strong> Live Coding Interview Tasks & Solutions</p>
        <p><strong>Part 58:</strong> Project-Specific SQL Interview Questions</p>
        <p><strong>Part 59:</strong> System Design Scenario Interviews</p>
        <p><strong>Part 60:</strong> AI Evaluation Framework & Benchmarks</p>
        <p><strong>Part 61:</strong> Automated Test Suite Documentation</p>
        <p><strong>Part 62:</strong> Live 5-Minute Product Demo Script</p>
        <p><strong>Part 63:</strong> 2-Minute Emergency Interview Answer</p>
        <p><strong>Part 64:</strong> One-Page Revision Cheat Sheet</p>
        <p><strong>Part 65:</strong> Technical & FinTech Glossary</p>
        <p><strong>Part 66:</strong> Project-Specific Professional Vocabulary</p>
        <p><strong>Part 67:</strong> What NOT to Claim in Interviews</p>
        <p><strong>Part 68:</strong> Project Weaknesses & Defense Strategies</p>
        <p><strong>Part 69:</strong> 100 Rapid-Fire Viva Questions</p>
        <p><strong>Part 70:</strong> 3 Complete Multi-Level Mock Interviews</p>
        <p><strong>Part 71:</strong> Natural Developer Project Origin Story</p>
        <p><strong>Part 72:</strong> Real Technical Challenges Overcome</p>
        <p><strong>Part 73:</strong> 15 Architecture & Flowchart Diagrams</p>
        <p><strong>Part 74:</strong> Exact Source Code File Reference</p>
        <p><strong>Part 75:</strong> Final Project Synthesis</p>
      </div>
    </div>
  </div>

  <div class="page-break"></div>

  <!-- ===================================================================== -->
  <!-- PART 1: PROJECT OVERVIEW -->
  <!-- ===================================================================== -->
  <div class="avoid-break">
    <h2>Part 1 — Project Overview & Philosophy</h2>
    
    <h3 class="text-blue-900">What is FinPilot AI?</h3>
    <p>
      <strong>FinPilot AI</strong> is an enterprise-grade <strong>Financial Digital Twin, Merchant Growth & Autonomous Multi-Agent Decision Operating System</strong>. It acts as an autonomous AI Financial Controller that continuously monitors enterprise financial health, executes what-if forward simulations, audits invoices and payroll, reconciles accounts, and facilitates autonomous AI-to-AI commerce with Razorpay payment integration.
    </p>

    <h3 class="text-blue-900">The Problem It Solves & Why It Is Important</h3>
    <p>
      Traditional Enterprise Resource Planning (ERP) systems and static BI dashboards are purely <em>retrospective</em>: they present data after money has already been spent, leading to unbudgeted overruns, duplicate vendor billings, and compliance penalties. Finance managers spend hundreds of hours manually cross-checking invoices against department budget utilization and verifying 18% GST tax math. FinPilot AI transforms finance from <strong>reactive accounting to proactive simulation</strong>.
    </p>

    <h3 class="text-blue-900">Who Would Use It?</h3>
    <ul>
      <li><strong>Chief Financial Officers (CFOs):</strong> Enterprise liquidity oversight, capital allocation what-if forecasting, and multi-million rupee disbursement authorization.</li>
      <li><strong>Finance Managers:</strong> Day-to-day budget tracking, vendor invoice approvals, payroll audits, and department burn-rate management.</li>
      <li><strong>Department Heads:</strong> Scoped budget monitoring, planned expense affordability simulation, and team allowance claims.</li>
      <li><strong>Auditors:</strong> Compliance verification, Form 16 vs. payroll reconciliation, duplicate transaction flagging, and immutable audit logs.</li>
    </ul>

    <h3 class="text-blue-900">The Core Architectural Philosophy</h3>
    <pre>
DATA  ──►  RULES  ──►  ANALYSIS  ──►  RISK / EXCEPTION  ──►  DECISION  ──►  APPROVAL  ──►  ACTION  ──►  AUDIT TRAIL
    </pre>
    <p class="text-xs text-slate-600">
      <strong>Simple Explanation:</strong> Raw financial records (invoices, budgets) are verified by strict rules, processed by analytical algorithms, evaluated for risk, turned into actionable decisions, routed for human sign-off if large, executed on payment rails, and permanently logged to an immutable audit record.<br>
      <strong>Technical Explanation:</strong> Ingestion pipelines parse telemetry into Pydantic models; deterministic services execute constraint validations; the 7-agent orchestrator generates counterfactual trajectories against an in-memory Digital Twin; risk scoring triggers HITL state branches in LangGraph ($\ge ₹50,000$); authorized actions dispatch Razorpay payment links; and transactions are cryptographically chained via SHA-256 blocks.
    </p>
  </div>

  <!-- ===================================================================== -->
  <!-- PART 2: 30-SECOND, 1-MIN, 2-MIN & 5-MIN EXPLANATIONS -->
  <!-- ===================================================================== -->
  <div class="avoid-break mt-8">
    <h2>Part 2 — Ready-to-Speak Project Explanations</h2>

    <div class="qa-box">
      <div class="qa-header">⚡ 30-Second Elevator Pitch</div>
      <p class="text-xs italic text-slate-800">
        "Most financial AI tools describe what already happened by reading spreadsheets. FinPilot AI simulates what happens next — before a human has to commit capital. Built on Razorpay test rails, it combines a 90-day Financial Digital Twin, a 7-agent autonomous copilot, merchant growth tools with smart upsells, and an AI-to-AI shopping protocol with strict role-based data isolation."
      </p>
    </div>

    <div class="qa-box">
      <div class="qa-header">⏱️ 1-Minute Executive Summary</div>
      <p class="text-xs italic text-slate-800">
        "FinPilot AI is an AI-powered financial decision platform designed for enterprise CFOs and finance teams. Traditional dashboards only show historical data after overspending occurs. FinPilot AI maintains a live in-memory Digital Twin that simulates day-by-day cash flows and runway under counterfactual what-if scenarios — like spending spikes or deferred payouts. It features an automated invoice auditor with 18% GST calculation and duplicate detection, an autonomous AI-to-AI commerce engine with Razorpay payment links, and a 7-agent reasoning pipeline that delivers 5-step role-tailored action plans with Human-in-the-Loop governance."
      </p>
    </div>

    <div class="qa-box">
      <div class="qa-header">🎙️ 2-Minute Comprehensive Pitch</div>
      <p class="text-xs italic text-slate-800">
        "I built FinPilot AI to solve the massive disconnect between static financial reporting and active financial decision-making. The system is architected around a hybrid model: deterministic Python logic handles exact arithmetic — like GST, budget balances, and statutory deductions — while autonomous AI agents handle intent classification, causal anomaly correlation, and what-if narration.<br><br>
        The platform features four key innovations: First, a 90-day Financial Digital Twin that evaluates liquidity and runway before transactions are approved. Second, a 7-agent LangGraph copilot that performs causal root-cause analysis on budget overruns. Third, a merchant growth studio with machine-readable catalogs (`/v1/commerce/ai-manifest`), conversational in-app checkout, and autonomous AI-to-AI negotiation bounded by spending tokens. Fourth, a zero-leakage role-based notification center with 2-way conversation threads and cryptographically chained SHA-256 audit logs."
      </p>
    </div>

    <div class="qa-box">
      <div class="qa-header">🔬 5-Minute Deep Technical Walkthrough</div>
      <p class="text-xs italic text-slate-800">
        "Let's dive into the technical architecture of FinPilot AI. The backend is built with Python 3.11, FastAPI, and Pydantic, while the frontend is a responsive Single Page Application with Tailwind CSS and Chart.js.<br><br>
        At the core is our Financial Digital Twin (`digital_twin_service.py`), which models liquid cash, department burn rates, and vendor liabilities. When a what-if query is executed, it runs differential day-by-day simulations applying custom multipliers without touching the database.<br><br>
        For reasoning, we implement a 7-agent orchestrator in `multi_agent_orchestrator.py` with LangGraph state machines: IntentAgent checks RBAC permissions; RetrievalAgent pulls role-scoped facts; AnalysisAgent calculates burn velocities; RiskAgent generates a 4-factor score; SimulationAgent runs forward models; CausalAgent correlates spending spikes with operational signals; and NarratorAgent formulates a 5-step executive report.<br><br>
        In commerce, our Universal Commerce Manifest exposes products in JSON-LD format. External AI buyers communicate with `/v1/commerce/ai-buy` with hard `X-Spending-Token-Limit` bounds. Transactions over ₹50,000 pause in LangGraph for Human-in-the-Loop approval, after which Razorpay test-mode payment links are dispatched and actions logged to our SHA-256 chained audit trail."
      </p>
    </div>
  </div>

  <div class="page-break"></div>

  <!-- ===================================================================== -->
  <!-- PART 3: PROBLEM STATEMENT -->
  <!-- ===================================================================== -->
  <div class="avoid-break">
    <h2>Part 3 — Problem Statement & Solutions</h2>

    <table>
      <thead>
        <tr>
          <th>Operational Domain</th>
          <th>Traditional Manual / Dashboard Failure</th>
          <th>FinPilot AI Implementation Solution</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>Budget Monitoring</strong></td>
          <td>Departments realize they are over budget only at end-of-month reconciliation.</td>
          <td>Real-time burn rate velocity tracking and forward day-by-day deficit prediction.</td>
        </tr>
        <tr>
          <td><strong>Invoice Auditing</strong></td>
          <td>Manual verification of tax calculations, vendor rates, and duplicate submissions.</td>
          <td>Automated 18% GST validator, duplicate hash matching, and runway affordability check.</td>
        </tr>
        <tr>
          <td><strong>Reconciliation</strong></td>
          <td>Discrepancies between bank statements, general ledger, and payment gateway logs.</td>
          <td>Automated 3-way reconciliation (Ledger vs. Bank vs. Razorpay) with exception logs.</td>
        </tr>
        <tr>
          <td><strong>Approval Workflows</strong></td>
          <td>Slow email chains without visibility into post-approval liquidity impact.</td>
          <td>HITL Approvals Queue ($\ge ₹50K$ threshold) with 1-click Razorpay payment link dispatch.</td>
        </tr>
        <tr>
          <td><strong>Employee Allowances</strong></td>
          <td>Static caps create friction, leading to manual review fatigue and override backlogs.</td>
          <td>Self-calibrating policy engine that analyzes override frequencies to propose adjustments.</td>
        </tr>
        <tr>
          <td><strong>Payroll & Form 16</strong></td>
          <td>Year-end TDS deduction mismatches and taxable salary discrepancies go unnoticed.</td>
          <td>Automated Form 16 vs. payroll gross reconciliation with flagged review recommendations.</td>
        </tr>
        <tr>
          <td><strong>Merchant Sales</strong></td>
          <td>Slow checkout interfaces and inability to transact with autonomous AI agents.</td>
          <td>Machine-readable store manifest (`/v1/commerce/ai-manifest`) and conversational in-app cart.</td>
        </tr>
      </tbody>
    </table>
  </div>

  <!-- ===================================================================== -->
  <!-- PART 4: COMPLETE FEATURE LIST -->
  <!-- ===================================================================== -->
  <div class="avoid-break mt-6">
    <h2>Part 4 — Complete Feature Matrix</h2>

    <table>
      <thead>
        <tr>
          <th>Feature</th>
          <th>Purpose & Logic</th>
          <th>Backend / Service</th>
          <th>AI Involvement</th>
          <th>Role Access</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>Executive Control Center</strong></td>
          <td>Real-time liquidity, burn metrics, and decision scoring.</td>
          <td>`intelligence_service.py`</td>
          <td>Deterministic Telemetry</td>
          <td>All (Role-scoped)</td>
          <td><span class="tag-impl">IMPLEMENTED</span></td>
        </tr>
        <tr>
          <td><strong>Financial Digital Twin Studio</strong></td>
          <td>90-day forward what-if trajectory simulation.</td>
          <td>`digital_twin_service.py`</td>
          <td>Differential Simulation</td>
          <td>CFO, FM</td>
          <td><span class="tag-impl">IMPLEMENTED</span></td>
        </tr>
        <tr>
          <td><strong>Company Decision Map</strong></td>
          <td>Hierarchical financial tree (Root $\rightarrow$ Budget $\rightarrow$ Action).</td>
          <td>`budget_service.py`</td>
          <td>Graph Structure</td>
          <td>CFO, FM, Auditor</td>
          <td><span class="tag-impl">IMPLEMENTED</span></td>
        </tr>
        <tr>
          <td><strong>Invoice Intelligence Auditor</strong></td>
          <td>GST 18% calculation, duplicate detection, affordability.</td>
          <td>`invoice_service.py`</td>
          <td>Fuzzy Match + Rules</td>
          <td>All (Dept scoped)</td>
          <td><span class="tag-impl">IMPLEMENTED</span></td>
        </tr>
        <tr>
          <td><strong>HITL Approvals Queue</strong></td>
          <td>Disbursement governance ($\ge ₹50,000$ threshold).</td>
          <td>`approvals.py`, `razorpay_service.py`</td>
          <td>LangGraph HITL Node</td>
          <td>CFO, FM</td>
          <td><span class="tag-impl">IMPLEMENTED</span></td>
        </tr>
        <tr>
          <td><strong>Financial Decision Copilot</strong></td>
          <td>Natural language reasoning & counterfactual analysis.</td>
          <td>`multi_agent_orchestrator.py`</td>
          <td>7-Agent Multi-Agent</td>
          <td>All (RBAC Gate)</td>
          <td><span class="tag-impl">IMPLEMENTED</span></td>
        </tr>
        <tr>
          <td><strong>AI Commerce & Shopping Studio</strong></td>
          <td>Agent-readable store, A2A shopping, conversational cart.</td>
          <td>`merchant_commerce_service.py`</td>
          <td>Autonomous Buyer/Seller</td>
          <td>All Roles</td>
          <td><span class="tag-impl">IMPLEMENTED</span></td>
        </tr>
        <tr>
          <td><strong>Role-Based Notification Center</strong></td>
          <td>User-targeted 2-way conversation threads & routing.</td>
          <td>`notification_service.py`</td>
          <td>Deterministic Routing</td>
          <td>All Roles (Isolated)</td>
          <td><span class="tag-impl">IMPLEMENTED</span></td>
        </tr>
        <tr>
          <td><strong>Form 16 Tax Reconciler</strong></td>
          <td>Cross-checks payroll gross vs Form 16 TDS certificates.</td>
          <td>`payroll_service.py`</td>
          <td>Deterministic Math</td>
          <td>CFO, FM, Auditor</td>
          <td><span class="tag-impl">IMPLEMENTED</span></td>
        </tr>
        <tr>
          <td><strong>Employee Finance & Allowances</strong></td>
          <td>Salary revisions, allowance tracking, friction calibration.</td>
          <td>`employee_finance_service.py`</td>
          <td>Calibration Engine</td>
          <td>CFO, FM, DeptHead</td>
          <td><span class="tag-impl">IMPLEMENTED</span></td>
        </tr>
        <tr>
          <td><strong>Immutable Audit Trail</strong></td>
          <td>SHA-256 cryptographically chained compliance logging.</td>
          <td>`audit_service.py`</td>
          <td>Cryptographic Hash</td>
          <td>CFO, Auditor</td>
          <td><span class="tag-impl">IMPLEMENTED</span></td>
        </tr>
        <tr>
          <td><strong>Live Banking API Integration</strong></td>
          <td>Direct integration with real bank account webhooks.</td>
          <td>`cash_flow_service.py`</td>
          <td>None</td>
          <td>Planned</td>
          <td><span class="tag-future">PLANNED</span></td>
        </tr>
      </tbody>
    </table>
  </div>

  <div class="page-break"></div>

  <!-- ===================================================================== -->
  <!-- PART 5: TECHNOLOGY STACK -->
  <!-- ===================================================================== -->
  <div class="avoid-break">
    <h2>Part 5 — Technology Stack & Architectural Rationale</h2>

    <table>
      <thead>
        <tr>
          <th>Layer / Component</th>
          <th>Selected Technology</th>
          <th>Why It Was Chosen</th>
          <th>Alternative Considered</th>
          <th>Trade-Off Justification</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>Backend API Framework</strong></td>
          <td><strong>FastAPI (Python 3.11)</strong></td>
          <td>Asynchronous performance, automatic OpenAPI `/docs` generation, strict Pydantic validation.</td>
          <td>Django / Flask</td>
          <td>FastAPI is substantially faster than Flask/Django for high-concurrency async endpoints and native typing.</td>
        </tr>
        <tr>
          <td><strong>Agentic Workflow State Machine</strong></td>
          <td><strong>LangGraph & LangChain Core</strong></td>
          <td>Stateful graph coordination, cyclic agent hand-offs, checkpointing, and native Human-in-the-Loop interrupts.</td>
          <td>Raw OpenAI API / AutoGen</td>
          <td>LangGraph provides deterministic state transitions (`FinanceControllerState`) rather than unconstrained LLM loops.</td>
        </tr>
        <tr>
          <td><strong>Fintech Payment Rails</strong></td>
          <td><strong>Razorpay Test-Mode SDK</strong></td>
          <td>Native Indian Fintech standard for payment links, webhooks, and currency management.</td>
          <td>Stripe / Cashfree</td>
          <td>Razorpay is the benchmark API for Indian enterprise commerce and INR currency rails.</td>
        </tr>
        <tr>
          <td><strong>Frontend Architecture</strong></td>
          <td><strong>Tailwind CSS + Vanilla JS SPA</strong></td>
          <td>Zero build-step overhead, sub-millisecond DOM rendering, dark-mode fintech UI.</td>
          <td>React / Next.js</td>
          <td>Eliminates Webpack/Vite compilation complexity, allowing direct static serving from FastAPI with instant load times.</td>
        </tr>
        <tr>
          <td><strong>Data Visualization</strong></td>
          <td><strong>Chart.js (v4.4)</strong></td>
          <td>Canvas-based high-performance rendering for dynamic 90-day time-series trajectories.</td>
          <td>Recharts / D3.js</td>
          <td>Lightweight, responsive, and easily updated via JavaScript array manipulation without heavy virtual DOM overhead.</td>
        </tr>
        <tr>
          <td><strong>Data Storage Layer</strong></td>
          <td><strong>In-Memory Synchronized Store + JSON Fixtures</strong></td>
          <td>Instant sub-millisecond reads/writes for live Digital Twin simulations.</td>
          <td>PostgreSQL / SQLite</td>
          <td>Perfect for hackathon demonstration and state cloning; designed with service interfaces for drop-in PostgreSQL migration.</td>
        </tr>
      </tbody>
    </table>
  </div>

  <!-- ===================================================================== -->
  <!-- PART 6: SYSTEM ARCHITECTURE & PIPELINE -->
  <!-- ===================================================================== -->
  <div class="avoid-break mt-6">
    <h2>Part 6 — System Architecture & End-to-End Pipeline</h2>

    <pre>
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                       USER BROWSER (SPA)                                         │
│   Tailwind CSS  •  Chart.js 90-Day Trajectory  •  Lucide Icons  •  Interactive Copilot & Cart   │
└────────────────────────────────────────────────┬─────────────────────────────────────────────────┘
                                                 │ HTTPS / JSON / Server-Sent Events (SSE)
                                                 ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                               FASTAPI GATEWAY & MIDDLEWARE LAYER                                │
│   • CORS Middleware       • JWT / Session Auth Middleware       • Idempotency Validator          │
│   • RBAC Boundary Guard   • Pydantic Schema Validation          • Error Handling & Logging       │
└───────┬───────────────────────────────┬──────────────────────────────────┬───────────────────────┘
        │                               │                                  │
        ▼                               ▼                                  ▼
┌───────────────────────┐   ┌───────────────────────┐   ┌──────────────────────────────────────────┐
│  COMMERCE & COMMUNIC. │   │ FINANCIAL DIGITAL TWIN│   │      LANGGRAPH MULTI-AGENT COPILOT       │
│  • AI Manifest (JSON) │   │ • Cash Reserves ($8M) │   │ ┌──────────────────────────────────────┐ │
│  • Bounded A2A Buy    │   │ • 90-Day Step Diff.   │   │ │ IntentAgent & RBAC Gatekeeper        │ │
│  • Smart Upsell Cart  │   │ • 4-Factor Risk Score │   │ ├──────────────────────────────────────┤ │
│  • 2-Way Notif Thread │   │ • Counterfactual Sim  │   │ │ RetrievalAgent & Lineage Tracker     │ │
└───────┬───────────────┘   └───────────┬───────────┘   │ ├──────────────────────────────────────┤ │
        │                               │               │ │ AnalysisAgent (Math & GST)           │ │
        │                               │               │ ├──────────────────────────────────────┤ │
        │                               │               │ │ SimulationAgent (Digital Twin Branch)│ │
        │                               │               │ ├──────────────────────────────────────┤ │
        │                               │               │ │ CausalAgent (Root Cause Correlation) │ │
        │                               │               │ ├──────────────────────────────────────┤ │
        │                               │               │ │ NarratorAgent (5-Step Synthesis)     │ │
        │                               │               │ └──────────────────────────────────────┘ │
        │                               │               │ HITL Decision Node ($50K Threshold)      │
        │                               │               └──────────────────┬───────────────────────┘
        ▼                               ▼                                  ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                               FINTECH RAILS & IMMUTABLE LEDGERS                                  │
│   • Razorpay Payment Links API    • SHA-256 Cryptographically Chained Audit Service              │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
    </pre>
  </div>

  <div class="page-break"></div>

  <!-- ===================================================================== -->
  <!-- PART 11: ROLE-BASED ACCESS CONTROL (RBAC) -->
  <!-- ===================================================================== -->
  <div class="avoid-break">
    <h2>Part 11 — Role-Based Access Control (RBAC) Matrix</h2>

    <p class="text-xs text-slate-600">
      FinPilot AI implements strict 4-role enterprise security enforced at the <strong>FastAPI dependency layer</strong>, not merely the frontend UI.
    </p>

    <table>
      <thead>
        <tr>
          <th>Resource / Operation</th>
          <th>👑 CFO (`CFO-001`)</th>
          <th>💼 Finance Mgr (`FIN-MGR-001`)</th>
          <th>🛠️ Dept Head (`ENG-HEAD-001`)</th>
          <th>🔍 Auditor (`AUDITOR-001`)</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>Company Cash & Health Score</strong></td>
          <td>Full Visibility</td>
          <td>Full Visibility</td>
          <td>Aggregated Score Only</td>
          <td>Full Visibility (Audit)</td>
        </tr>
        <tr>
          <td><strong>Department Budgets</strong></td>
          <td>All 5 Departments</td>
          <td>All 5 Departments</td>
          <td><strong>Own Department Only</strong></td>
          <td>All 5 Departments</td>
        </tr>
        <tr>
          <td><strong>Invoice Management</strong></td>
          <td>View & Final Sign-Off</td>
          <td>View & Verify Invoices</td>
          <td><strong>Submit & View Own</strong></td>
          <td>Read-Only Audit & Flag</td>
        </tr>
        <tr>
          <td><strong>Disbursement Approval ($\ge ₹50K$)</strong></td>
          <td><strong>Authorize / Reject</strong></td>
          <td>Authorize up to ₹50K</td>
          <td>Denied</td>
          <td><strong>Denied (Flagging Only)</strong></td>
        </tr>
        <tr>
          <td><strong>Digital Twin What-If Studio</strong></td>
          <td>Full Forward Simulation</td>
          <td>Full Forward Simulation</td>
          <td>Scoped Expense Sim</td>
          <td>Read-Only Trajectory</td>
        </tr>
        <tr>
          <td><strong>Payroll & Form 16</strong></td>
          <td>Full Access</td>
          <td>Full Access</td>
          <td>Own Team Basic Stats</td>
          <td>Full Access & Anomaly Flag</td>
        </tr>
        <tr>
          <td><strong>Targeted Notifications</strong></td>
          <td>User-Scoped + CC</td>
          <td>User-Scoped + CC</td>
          <td>User-Scoped Only</td>
          <td>User-Scoped Only</td>
        </tr>
        <tr>
          <td><strong>Immutable Audit Trail</strong></td>
          <td>View All Logs</td>
          <td>View All Logs</td>
          <td>Denied</td>
          <td><strong>View All + Integrity Check</strong></td>
        </tr>
      </tbody>
    </table>

    <div class="callout-danger">
      <strong class="text-rose-900 block text-xs">⚠️ Why Frontend-Only RBAC is Insecure:</strong>
      <span class="text-xs text-rose-800">
        If role checks only hide buttons in HTML/CSS, an attacker can easily bypass the UI by calling the backend API directly (e.g. via `curl` or Postman). In FinPilot AI, `get_current_user` in `src/app/core/auth_middleware.py` inspects the user token on every request, raising an `HTTP 403 Forbidden` if unauthorized.
      </span>
    </div>
  </div>

  <!-- ===================================================================== -->
  <!-- PART 13 & 14: LANGGRAPH & MULTI-AGENT COPILOT -->
  <!-- ===================================================================== -->
  <div class="avoid-break mt-6">
    <h2>Part 13 & 14 — LangGraph & Multi-Agent Architecture</h2>

    <h3 class="text-blue-900">Why LangGraph Instead of Simple LLM Calls?</h3>
    <p>
      Simple LLM API calls are stateless and non-deterministic. Financial decision-making requires <strong>stateful cyclic graphs</strong> where execution can pause for human approval, recover from tool errors, and pass structured memory between sub-agents.
    </p>

    <h3 class="text-blue-900">The 7 Specialized Sub-Agents in FinPilot AI:</h3>
    <ol class="list-decimal list-inside text-xs text-slate-700 space-y-1">
      <li><strong>Intent & RBAC Gatekeeper:</strong> Classifies intent (What-If, Causal, Affordability) and enforces role scope.</li>
      <li><strong>Retrieval Agent:</strong> Queries in-memory ledger state and maintains strict data lineage.</li>
      <li><strong>Analysis Agent:</strong> Deterministically calculates burn velocity, GST amounts, and variance percentages.</li>
      <li><strong>Risk Agent:</strong> Evaluates weighted risk across 4 key financial metrics.</li>
      <li><strong>Simulation Agent:</strong> Branches the Financial Digital Twin and models 90-day cash trajectories.</li>
      <li><strong>Causal Agent:</strong> Correlates expenditure spikes with operational events (e.g. cluster launches).</li>
      <li><strong>Narrator Agent:</strong> Generates structured 5-part executive synthesis reports.</li>
    </ol>
  </div>

  <div class="page-break"></div>

  <!-- ===================================================================== -->
  <!-- PART 16: DETERMINISTIC FINANCIAL LOGIC VS PROBABILISTIC LLM -->
  <!-- ===================================================================== -->
  <div class="avoid-break">
    <h2>Part 16 — Deterministic Financial Logic vs. Probabilistic LLM</h2>

    <div class="callout">
      <strong class="text-blue-900 block text-xs">🎓 Critical Interview Topic: When to Use AI vs. When NOT to Use AI</strong>
      <span class="text-xs text-blue-800">
        This is one of the most important concepts interviewers look for. You must demonstrate that you know the limits of LLMs.
      </span>
    </div>

    <div class="grid grid-cols-2 gap-4 text-xs">
      <div class="p-4 rounded-xl bg-slate-900 text-white">
        <h4 class="text-rose-400 font-bold text-sm mb-2">🚫 DETERMINISTIC PYTHON CODE (No LLM)</h4>
        <ul class="space-y-1.5 text-slate-300">
          <li>• <strong>Statutory 18% GST:</strong> `round(subtotal * 0.18, 2)`</li>
          <li>• <strong>Budget Balance Math:</strong> `alloc - spent - pending`</li>
          <li>• <strong>PF & TDS Withholdings:</strong> 12% basic salary exact math.</li>
          <li>• <strong>HITL ₹50,000 Threshold:</strong> Validated in Pydantic.</li>
          <li>• <strong>Spending Token Limits:</strong> Enforced in middleware.</li>
          <li>• <strong>Cryptographic Hashing:</strong> SHA-256 block generation.</li>
        </ul>
      </div>

      <div class="p-4 rounded-xl bg-blue-900 text-white">
        <h4 class="text-blue-300 font-bold text-sm mb-2">🤖 PROBABILISTIC AI AGENTS (LLMs)</h4>
        <ul class="space-y-1.5 text-blue-100">
          <li>• <strong>Natural Language Intent Parsing:</strong> Understanding freeform cart requests (*"Add 2 gateways & pay"*).</li>
          <li>• <strong>Causal Correlation:</strong> Correlating unstructured commit logs and vendor bursts with budget spikes.</li>
          <li>• <strong>Counterfactual Narration:</strong> Synthesizing 90-day simulation curves into 5-part executive summaries.</li>
          <li>• <strong>Autonomous Negotiation:</strong> AI-to-AI price bargaining within pre-approved discount ranges.</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- ===================================================================== -->
  <!-- PART 25: RAZORPAY INTEGRATION & FINTECH RAILS -->
  <!-- ===================================================================== -->
  <div class="avoid-break mt-6">
    <h2>Part 25 — Razorpay Test-Mode Fintech Integration</h2>

    <p class="text-xs text-slate-600">
      FinPilot AI integrates directly with **Razorpay test-mode APIs** (`src/app/services/razorpay_service.py`) for live payment link dispatch:
    </p>

    <div class="space-y-2 text-xs">
      <div class="p-3 bg-slate-50 rounded border border-slate-200">
        <strong>1. Payment Link Generation (`create_payment_link`):</strong>
        <p class="text-slate-600 mt-1">Converts calculated INR amounts to smallest currency unit (paise: `int(amount * 100)`), generates short URLs (`https://rzp.io/i/...`), and attaches reference tags.</p>
      </div>
      <div class="p-3 bg-slate-50 rounded border border-slate-200">
        <strong>2. Webhook Signature Verification (`verify_webhook_signature`):</strong>
        <p class="text-slate-600 mt-1">Computes HMAC-SHA256 digests over incoming webhook payloads using the secret key, preventing spoofed payment confirmations.</p>
      </div>
      <div class="p-3 bg-slate-50 rounded border border-slate-200">
        <strong>3. Idempotency & Replay Protection:</strong>
        <p class="text-slate-600 mt-1">Attaches unique `X-Idempotency-Key` headers on all payment requests, ensuring that network retries do not trigger duplicate charges.</p>
      </div>
    </div>
  </div>

  <div class="page-break"></div>

  <!-- ===================================================================== -->
  <!-- PART 54: TOP 50 INTERVIEW QUESTIONS & MODEL ANSWERS -->
  <!-- ===================================================================== -->
  <div class="avoid-break">
    <h2>Part 54 — Top Interview Questions & Model Answers</h2>

    <div class="qa-box">
      <div class="qa-header">Q1: How does FinPilot AI prevent LLM hallucinations in financial calculations? ⭐⭐⭐⭐⭐</div>
      <p class="text-xs text-slate-700">
        <strong>Answer:</strong> We enforce an architectural barrier between reasoning and arithmetic. All mathematical calculations — such as 18% GST tax, budget utilization percentages, salary deductions, and runway continuity — are executed in deterministic Python functions. The LLM is never prompted to compute mathematical sums; it only receives pre-calculated numbers to formulate semantic explanations.
      </p>
    </div>

    <div class="qa-box">
      <div class="qa-header">Q2: How does the AI-to-AI Shopping protocol work? ⭐⭐⭐⭐⭐</div>
      <p class="text-xs text-slate-700">
        <strong>Answer:</strong> Our merchant service serves a machine-readable JSON-LD manifest at `/v1/commerce/ai-manifest`. External buyer bots inspect this catalog and send autonomous purchase requests to `/v1/commerce/ai-buy` along with an authorized `X-Spending-Token-Limit` header. If the total is within bounds, our merchant agent negotiates tiered volume discounts (up to 15%) and generates a Razorpay payment link.
      </p>
    </div>

    <div class="qa-box">
      <div class="qa-header">Q3: What is the Financial Digital Twin and how does it simulate 90 days forward? ⭐⭐⭐⭐⭐</div>
      <p class="text-xs text-slate-700">
        <strong>Answer:</strong> The Digital Twin is an in-memory synchronized clone of enterprise cash reserves, department allocations, daily burn rates, and vendor liabilities (`digital_twin_service.py`). It applies day-by-day differential equations ($Cash_i = Cash_{i-1} + Inflows_i - Outflows_i$) across 90 steps with custom multipliers (like 15% burn spikes or 14-day vendor payment deferrals), predicting cash runways without altering production ledgers.
      </p>
    </div>

    <div class="qa-box">
      <div class="qa-header">Q4: Why use LangGraph instead of calling the LLM directly? ⭐⭐⭐⭐</div>
      <p class="text-xs text-slate-700">
        <strong>Answer:</strong> Direct LLM calls are stateless and lack deterministic control. LangGraph provides a cyclic state machine (`FinanceControllerState`) with checkpointing and native Human-in-the-Loop interrupts. When a disbursement exceeds ₹50,000, LangGraph pauses execution at an approval node, awaits manager authorization, and only resumes after sign-off.
      </p>
    </div>

    <div class="qa-box">
      <div class="qa-header">Q5: How is role-based notification isolation enforced? ⭐⭐⭐⭐</div>
      <p class="text-xs text-slate-700">
        <strong>Answer:</strong> Rather than relying on frontend filters, `notification_service.py` executes query-level filtering against `recipientUserId == current_user.id` or explicit `observerIds`. If a CFO sends a request to Finance Manager A, Finance Manager B's API query returns zero results for that notification.
      </p>
    </div>

    <div class="qa-box">
      <div class="qa-header">Q6: How do you handle Razorpay API timeouts or network failures? ⭐⭐⭐⭐</div>
      <p class="text-xs text-slate-700">
        <strong>Answer:</strong> Our 4-Tier Failure Resilience Engine uses exponential backoff retry with idempotency keys. If all 3 retries fail, the transaction is safely transitioned to an `OFFLINE_QUEUED` state, a high-priority notification is dispatched to the finance manager, and ledger balances remain untouched.
      </p>
    </div>
  </div>

  <div class="page-break"></div>

  <!-- ===================================================================== -->
  <!-- PART 64: ONE-PAGE REVISION CHEAT SHEET -->
  <!-- ===================================================================== -->
  <div class="avoid-break">
    <h2>Part 64 — One-Page Emergency Revision Cheat Sheet</h2>

    <div class="grid grid-cols-2 gap-4 text-xs">
      <div class="p-3 bg-slate-50 border border-slate-200 rounded-lg">
        <strong class="text-blue-900 block font-bold mb-1">📌 Core Architecture:</strong>
        <ul class="space-y-1 text-slate-700">
          <li>• <strong>Backend:</strong> FastAPI, Python 3.11, Pydantic v2.</li>
          <li>• <strong>AI Engine:</strong> LangGraph Multi-Agent, MemorySaver.</li>
          <li>• <strong>Fintech Rails:</strong> Razorpay Test-Mode SDK.</li>
          <li>• <strong>Frontend:</strong> Tailwind CSS, Chart.js, Vanilla JS SPA.</li>
        </ul>
      </div>

      <div class="p-3 bg-slate-50 border border-slate-200 rounded-lg">
        <strong class="text-blue-900 block font-bold mb-1">🧬 Digital Twin & Metrics:</strong>
        <ul class="space-y-1 text-slate-700">
          <li>• <strong>Enterprise Liquidity:</strong> ₹8,435,000.00</li>
          <li>• <strong>Decision Health Score:</strong> 82/100 (Healthy)</li>
          <li>• <strong>Departments:</strong> Eng, Mkt, Sales, Ops, HR</li>
          <li>• <strong>Simulation Window:</strong> 90 Days Step Differential</li>
        </ul>
      </div>

      <div class="p-3 bg-slate-50 border border-slate-200 rounded-lg">
        <strong class="text-blue-900 block font-bold mb-1">🤖 7 Reasoning Sub-Agents:</strong>
        <ul class="space-y-1 text-slate-700">
          <li>1. Intent & RBAC Agent &nbsp; 2. Retrieval Agent</li>
          <li>3. Analysis Agent &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 4. Risk Agent</li>
          <li>5. Simulation Agent &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 6. Causal Agent</li>
          <li>7. Narrator Agent (5-Part Report Synthesis)</li>
        </ul>
      </div>

      <div class="p-3 bg-slate-50 border border-slate-200 rounded-lg">
        <strong class="text-blue-900 block font-bold mb-1">🛡️ Safety & Governance:</strong>
        <ul class="space-y-1 text-slate-700">
          <li>• <strong>HITL Threshold:</strong> $\ge ₹50,000$ requires CFO sign-off.</li>
          <li>• <strong>Audit Ledger:</strong> Cryptographic SHA-256 chaining.</li>
          <li>• <strong>Security:</strong> Recipient Isolation (`recipientUserId`).</li>
          <li>• <strong>A2A Ceilings:</strong> `X-Spending-Token-Limit` bounds.</li>
        </ul>
      </div>
    </div>
  </div>

  <!-- ===================================================================== -->
  <!-- PART 75: FINAL PROJECT SYNTHESIS -->
  <!-- ===================================================================== -->
  <div class="avoid-break mt-6 pt-6 border-t-2 border-slate-200 text-center">
    <h3 class="text-lg font-black text-slate-900 mb-2">Part 75 — Final Project Synthesis</h3>
    <p class="text-xs text-slate-600 max-w-2xl mx-auto">
      FinPilot AI is a production-grade demonstration of how modern autonomous AI agents can be combined with deterministic financial guardrails to transform corporate finance from retrospective reporting to proactive simulation.
    </p>
    <div class="mt-4 text-xs text-slate-500">
      <strong>FinPilot AI</strong> • Built for Razorpay AI Agent Track • Open Source on <a href="https://github.com/GAUTAMX05/FinPilot-Ai" class="text-blue-600 font-bold underline">GitHub</a>
    </div>
  </div>

</body>
</html>
''')
    print("Handbook HTML written successfully. Now compiling PDF via Chrome Headless...")
    
    cmd = [
        CHROME,
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={out_pdf_docs}",
        html_file.as_uri()
    ]
    res = subprocess.run(cmd, capture_output=True, timeout=20)
    print("Chrome Return Code:", res.returncode)
    
    if out_pdf_docs.exists():
        size = out_pdf_docs.stat().st_size
        print(f"[SUCCESS] Master Handbook PDF compiled at: {out_pdf_docs} ({size:,} bytes)")
        
        # Copy to static docs directory for FastAPI web serving
        with open(out_pdf_docs, "rb") as f_in, open(out_pdf_static, "wb") as f_out:
            f_out.write(f_in.read())
        print(f"[SUCCESS] Served statically at: {out_pdf_static}")
    else:
        print("[ERROR] PDF compilation failed:", res.stderr.decode('utf-8', errors='ignore'))

if __name__ == "__main__":
    generate_handbook()
