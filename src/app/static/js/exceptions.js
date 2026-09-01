// =========================================================================
// FINPILOT AI — EXCEPTION CENTER & HITL DECISION ENGINE
// =========================================================================

window.currentSelectedExceptionId = null;
window.allExceptionsCache = [];

async function loadExceptionsCenter() {
  try {
    const res = await apiFetch("/v1/controller/exceptions");
    const data = await res.json();
    window.allExceptionsCache = data.exceptions || [];
    updateExceptionFilterCounts(window.allExceptionsCache);
    renderExceptionsGrid(window.allExceptionsCache);
  } catch (err) {
    console.error("loadExceptionsCenter error:", err);
  }
}

function updateExceptionFilterCounts(exceptions) {
  const all = (exceptions || []).length;
  const review = (exceptions || []).filter(e => e.status === "REQUIRES_HUMAN_REVIEW").length;
  const esc = (exceptions || []).filter(e => e.status === "ESCALATED_TO_CFO").length;
  const auto = (exceptions || []).filter(e => e.status === "AUTO_RESOLVED").length;
  const app = (exceptions || []).filter(e => e.status === "HUMAN_APPROVED").length;

  const setTxt = (id, val) => { const el = document.getElementById(id); if (el) el.innerText = val; };
  setTxt("countExcAll", all);
  setTxt("countExcReview", review);
  setTxt("countExcEscalated", esc);
  setTxt("countExcAuto", auto);
  setTxt("countExcApproved", app);
}

function filterExceptionsList(statusFilter, evt) {
  document.querySelectorAll("#exceptionFilterPills button").forEach(b => {
    b.className = "px-3 py-1.5 rounded-xl text-xs font-semibold bg-[#0B1729] hover:bg-[#0F1D32] text-slate-300 border border-white/10";
  });
  const e = evt || (typeof event !== 'undefined' ? event : null);
  const activeBtn = e && e.target ? e.target.closest("button") : null;
  if (activeBtn) {
    activeBtn.className = "px-3 py-1.5 rounded-xl text-xs font-bold bg-blue-600 text-white shadow-glow-blue";
  }

  if (statusFilter === "ALL") {
    renderExceptionsGrid(window.allExceptionsCache || []);
  } else {
    const filtered = (window.allExceptionsCache || []).filter(item => item.status === statusFilter);
    renderExceptionsGrid(filtered);
  }
}

function renderDashboardExceptionsTable(exceptions) {
  const tbody = document.getElementById("dashExceptionsTableBody");
  if (!tbody) return;

  if (!exceptions || exceptions.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="p-4 text-center text-slate-400">All exceptions resolved. Zero open variances!</td></tr>`;
    return;
  }

  tbody.innerHTML = exceptions.map(e => `
    <tr class="hover:bg-white/[0.02] transition">
      <td class="p-3.5 font-mono font-bold text-blue-400">${e.exception_id}</td>
      <td class="p-3.5">
        <span class="font-semibold text-white block">${(e.exception_type || '').replace(/_/g, ' ')}</span>
        <span class="text-[10px] text-slate-400">${e.policy_triggered || 'Policy Check'}</span>
      </td>
      <td class="p-3.5 font-mono text-[11px] text-slate-300">
        <div>${e.transaction_id || '-'}</div>
        <div class="text-slate-400">${e.invoice_id || '-'}</div>
      </td>
      <td class="p-3.5 text-right font-mono font-bold text-white">
        ₹${(e.amount_difference || 0).toLocaleString()}
      </td>
      <td class="p-3.5">
        <span class="px-2 py-0.5 rounded text-[10px] font-extrabold ${e.severity === 'HIGH' ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' : (e.severity === 'MEDIUM' ? 'bg-amber-500/10 text-amber-300 border border-amber-500/20' : 'bg-blue-500/10 text-blue-400 border border-blue-500/20')}">
          ${e.severity}
        </span>
      </td>
      <td class="p-3.5">
        <span class="px-2 py-0.5 rounded text-[10px] font-semibold ${e.status === 'HUMAN_APPROVED' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : (e.status === 'ESCALATED_TO_CFO' ? 'bg-rose-500/10 text-rose-300 border border-rose-500/20' : 'bg-amber-500/10 text-amber-300 border border-amber-500/20')}">
          ${(e.status || '').replace(/_/g, ' ')}
        </span>
      </td>
      <td class="p-3.5 text-center">
        <button onclick="openExceptionInvestigation('${e.exception_id}')" class="btn-smooth px-2.5 py-1 rounded-lg bg-blue-600/20 hover:bg-blue-600 text-blue-300 hover:text-white border border-blue-500/30 text-[11px] font-bold transition">
          Investigate
        </button>
      </td>
    </tr>
  `).join("");
  if (window.lucide && typeof window.lucide.createIcons === 'function') {
    window.lucide.createIcons();
  }
}

function renderExceptionsGrid(exceptions) {
  const grid = document.getElementById("exceptionsGridContainer");
  if (!grid) return;

  if (!exceptions || exceptions.length === 0) {
    grid.innerHTML = `<div class="col-span-2 p-8 text-center bg-[#0B1729] rounded-3xl border border-white/10 text-slate-400">Zero exceptions in this queue.</div>`;
    return;
  }

  grid.innerHTML = exceptions.map(e => `
    <div class="bg-[#0B1729] p-5 rounded-3xl border border-white/10 space-y-3 hover:border-blue-500/30 transition shadow-card">
      <div class="flex items-start justify-between">
        <div>
          <div class="flex items-center gap-2">
            <span class="px-2 py-0.5 rounded text-[10px] font-extrabold bg-blue-500/20 text-blue-300 font-mono">${e.exception_id}</span>
            <span class="px-2 py-0.5 rounded text-[10px] font-extrabold ${e.severity === 'HIGH' ? 'bg-rose-500/20 text-rose-300' : (e.severity === 'MEDIUM' ? 'bg-amber-500/20 text-amber-300' : 'bg-blue-500/20 text-blue-300')}">${e.severity}</span>
            <span class="px-2 py-0.5 rounded text-[10px] font-semibold bg-white/5 text-slate-300">${(e.status || '').replace(/_/g, ' ')}</span>
          </div>
          <h4 class="font-bold text-white text-sm mt-1.5">${(e.exception_type || '').replace(/_/g, ' ')}</h4>
        </div>
        <div class="text-right">
          <span class="text-[10px] text-slate-400 block">Variance</span>
          <span class="font-mono font-bold text-rose-400 text-sm">₹${(e.amount_difference || 0).toLocaleString()}</span>
        </div>
      </div>

      <p class="text-xs text-slate-300 line-clamp-2">${e.ai_issue || e.ai_root_cause || ''}</p>

      <div class="pt-2 border-t border-white/5 flex items-center justify-between text-xs">
        <span class="text-[11px] text-slate-400 font-mono">${e.transaction_id || '-'}</span>
        <button onclick="openExceptionInvestigation('${e.exception_id}')" class="btn-smooth px-3 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs flex items-center gap-1.5 shadow-glow-blue">
          <i data-lucide="search" class="w-3.5 h-3.5"></i>
          <span>Investigate</span>
        </button>
      </div>
    </div>
  `).join("");
  if (window.lucide && typeof window.lucide.createIcons === 'function') {
    window.lucide.createIcons();
  }
}

async function openExceptionInvestigation(exceptionId) {
  window.currentSelectedExceptionId = exceptionId;
  try {
    const res = await apiFetch(`/v1/controller/exceptions/${exceptionId}/investigate`, { method: "POST" });
    const data = await res.json();

    const setTxt = (id, val) => { const el = document.getElementById(id); if (el) el.innerText = val; };
    setTxt("invModalExcId", data.exception_id);
    setTxt("invModalSeverity", data.severity);
    setTxt("invModalTxnId", data.transaction_id || "-");
    setTxt("invModalType", (data.exception_type || '').replace(/_/g, ' '));
    setTxt("invModalEvidence", data.ai_investigation?.evidence || "");
    setTxt("invModalIssue", data.ai_investigation?.issue || "");
    setTxt("invModalRootCause", data.ai_investigation?.root_cause || "");
    setTxt("invModalRecommendation", data.ai_investigation?.recommendation || "");
    setTxt("invModalPolicy", `Policy Triggered: ${data.policy_triggered || 'STANDARD_AUDIT'}`);
    
    const reviewerName = (typeof currentUser !== 'undefined' && currentUser && currentUser.name) ? currentUser.name : 'User';
    const reviewerRole = (typeof currentUser !== 'undefined' && currentUser && currentUser.role) ? currentUser.role : 'CFO';
    setTxt("invModalReviewer", `${reviewerName} (${reviewerRole})`);

    const modal = document.getElementById("controllerInvestigateModal");
    if (modal) modal.classList.remove("hidden");
    if (window.lucide && typeof window.lucide.createIcons === 'function') {
      window.lucide.createIcons();
    }
  } catch (err) {
    showToast(err.message, true);
  }
}

function closeInvestigateModal() {
  const modal = document.getElementById("controllerInvestigateModal");
  if (modal) modal.classList.add("hidden");
}

async function submitExceptionDecision(decision) {
  if (!window.currentSelectedExceptionId) return;

  try {
    const reviewerName = (typeof currentUser !== 'undefined' && currentUser && currentUser.name) ? currentUser.name : "Finance Manager";
    const reviewerRole = (typeof currentUser !== 'undefined' && currentUser && currentUser.role) ? currentUser.role : "FINANCE_MANAGER";

    const res = await apiFetch(`/v1/controller/exceptions/${window.currentSelectedExceptionId}/decide`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        decision: decision,
        actor_name: reviewerName,
        actor_role: reviewerRole,
        comments: `Action ${decision} submitted via FinPilot UI.`
      })
    });
    const data = await res.json();
    showToast(`Decision ${decision} recorded! Audit SHA: ${data.sha256_audit_hash?.substring(0, 10)}...`);
    closeInvestigateModal();
    fetchControllerDashboard();
    loadExceptionsCenter();
  } catch (err) {
    showToast(err.message, true);
  }
}
