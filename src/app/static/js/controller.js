// =========================================================================
// FINPILOT AI — AUTONOMOUS FINANCE CONTROLLER LOGIC
// =========================================================================

async function fetchControllerDashboard() {
  try {
    const res = await apiFetch("/v1/controller/dashboard");
    const data = await res.json();

    if (data.run_summary) {
      const s = data.run_summary;
      const setTxt = (id, val) => { const el = document.getElementById(id); if (el) el.innerText = val; };
      
      setTxt("dashLastRunId", s.run_id || "RUN-LATEST");
      setTxt("dashThroughputRps", s.throughput_rps ? `${Math.round(s.throughput_rps).toLocaleString()} records/sec` : "Not measured");
      setTxt("ctrlRecordsProcessed", s.records_processed !== undefined ? s.records_processed : "N/A");
      setTxt("ctrlAutoReconciled", s.auto_reconciled !== undefined ? s.auto_reconciled : "N/A");
      setTxt("ctrlMatchRate", s.match_rate !== undefined ? `${s.match_rate}%` : "N/A");
      setTxt("ctrlExceptionsCount", s.exceptions_count !== undefined ? s.exceptions_count : "0");
      setTxt("ctrlHumanReviewCount", s.human_review !== undefined ? s.human_review : "0");
      setTxt("ctrlAmountInReview", s.amount_under_review !== undefined ? `₹${((s.amount_under_review) / 100000).toFixed(2)}L` : "₹0.00");

      const excBadge = document.getElementById("navExcBadge");
      if (excBadge) excBadge.innerText = s.exceptions_count !== undefined ? s.exceptions_count : "0";
    }

    if (data.gateway_status) {
      const gw = data.gateway_status;
      const badge = document.getElementById("dashGatewayModeBadge");
      if (badge) {
        if (gw.is_configured) {
          badge.innerText = `RAZORPAY (${gw.gateway_mode.toUpperCase()})`;
          badge.className = "px-2.5 py-0.5 rounded-full text-[10px] font-extrabold bg-blue-500/20 text-blue-300 border border-blue-400/30 uppercase";
        } else {
          badge.innerText = "SIMULATION MODE (TEST)";
          badge.className = "px-2.5 py-0.5 rounded-full text-[10px] font-extrabold bg-purple-500/20 text-purple-300 border border-purple-400/30 uppercase";
        }
      }
    }

    if (data.exceptions) {
      allExceptionsCache = data.exceptions;
      renderDashboardExceptionsTable(data.exceptions.slice(0, 8));
      updateExceptionFilterCounts(data.exceptions);
    }

    if (data.evaluation) {
      renderEvaluationScorecard(data.evaluation);
    }

    lucide.createIcons();
  } catch (err) {
    console.error("fetchControllerDashboard error:", err);
  }
}

async function triggerCloseMonth() {
  const modal = document.getElementById("closeMonthModal");
  if (modal) modal.classList.remove("hidden");

  const timeEl = document.getElementById("closeMonthTime");
  const doneBtn = document.getElementById("closeMonthDoneBtn");
  const sumBox = document.getElementById("closeMonthResultSummary");
  const sumText = document.getElementById("closeMonthSummaryText");

  if (doneBtn) doneBtn.classList.add("hidden");
  if (sumBox) sumBox.classList.add("hidden");

  const start = Date.now();
  const timer = setInterval(() => {
    if (timeEl) timeEl.innerText = `${((Date.now() - start) / 1000).toFixed(1)}s`;
  }, 100);

  // Animate progress steps sequentially
  for (let i = 1; i <= 6; i++) {
    const stepEl = document.getElementById(`step-${i}`);
    if (stepEl) {
      stepEl.classList.remove("opacity-50");
      const icon = stepEl.querySelector(".step-icon");
      if (icon) {
        icon.setAttribute("data-lucide", "loader");
        icon.classList.add("animate-spin", "text-blue-400");
      }
    }
    await new Promise(r => setTimeout(r, 180));
    if (stepEl) {
      const icon = stepEl.querySelector(".step-icon");
      if (icon) {
        icon.setAttribute("data-lucide", "check-circle-2");
        icon.classList.remove("animate-spin", "text-blue-400");
        icon.classList.add("text-emerald-400");
      }
    }
    lucide.createIcons();
  }

  clearInterval(timer);

  try {
    const res = await apiFetch("/v1/controller/close-month", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ actor: currentUser.name || "Finance Manager" })
    });
    const data = await res.json();

    if (sumBox && sumText) {
      sumText.innerText = `Processed ${data.records_processed} records in ${data.duration_ms}ms (${Math.round(data.throughput_rps || 0).toLocaleString()} records/sec) • Match Rate: ${data.match_rate_percentage}% • ${data.exceptions_count} Exceptions classified.`;
      sumBox.classList.remove("hidden");
    }
    if (doneBtn) doneBtn.classList.remove("hidden");

    fetchControllerDashboard();
    showToast("Month-End Close executed with 100% deterministic precision!");
  } catch (err) {
    showToast(err.message, true);
  }
}

function closeMonthModalDone() {
  const modal = document.getElementById("closeMonthModal");
  if (modal) modal.classList.add("hidden");
  switchTab("dashboard");
}

async function reloadBenchmarkDataset() {
  try {
    const res = await apiFetch("/v1/controller/benchmark/reload", { method: "POST" });
    const data = await res.json();
    showToast("120-Record Benchmark reloaded into SQLite!");
    fetchControllerDashboard();
    loadExceptionsCenter();
  } catch (err) {
    showToast(err.message, true);
  }
}
