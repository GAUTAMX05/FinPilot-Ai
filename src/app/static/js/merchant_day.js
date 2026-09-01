// =========================================================================
// FINPILOT AI — GUIDED "MERCHANT DAY" SIMULATION WORKFLOW
// =========================================================================

async function runMerchantDayWorkflow() {
  const modal = document.getElementById("merchantDayModal");
  if (modal) modal.classList.remove("hidden");

  const container = document.getElementById("merchantDayStepsList");
  const summaryBox = document.getElementById("merchantDaySummaryBox");
  if (container) container.innerHTML = `<div class="p-6 text-center text-slate-400 flex items-center justify-center gap-2"><i data-lucide="loader" class="w-4 h-4 animate-spin text-blue-400"></i><span>Executing connected 9-stage Merchant Day governance cycle...</span></div>`;
  if (summaryBox) summaryBox.classList.add("hidden");
  lucide.createIcons();

  try {
    const res = await apiFetch("/v1/controller/merchant-day/run", { method: "POST" });
    const data = await res.json();

    if (container && data.steps) {
      container.innerHTML = "";
      for (const st of data.steps) {
        const div = document.createElement("div");
        div.className = "p-3.5 rounded-2xl bg-[#071426] border border-white/5 space-y-1.5 transition-all";
        div.innerHTML = `
          <div class="flex items-center justify-between">
            <span class="font-bold text-white text-xs">${st.title}</span>
            <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">PASSED</span>
          </div>
          <p class="text-slate-300 text-[11px] leading-relaxed">${st.detail}</p>
        `;
        container.appendChild(div);
        await new Promise(r => setTimeout(r, 120));
      }
    }

    if (summaryBox) {
      const txt = document.getElementById("merchantDaySummaryText");
      if (txt) {
        txt.innerText = `Successfully completed all ${data.total_steps} governance stages! Trace ID: ${data.demo_trace_id} • Status: ${data.final_status}`;
      }
      summaryBox.classList.remove("hidden");
    }

    fetchControllerDashboard();
    showToast("Merchant Day cycle completed and audited!");
    lucide.createIcons();
  } catch (err) {
    showToast(err.message, true);
  }
}

function closeMerchantDayModal() {
  const modal = document.getElementById("merchantDayModal");
  if (modal) modal.classList.add("hidden");
}
