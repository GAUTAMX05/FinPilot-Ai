// =========================================================================
// FINPILOT AI — 16-STAGE CONNECTED "MERCHANT DAY" SIMULATION
// =========================================================================

function openMerchantDayModal() {
  const modal = document.getElementById("merchantDayModal");
  if (modal) modal.classList.remove("hidden");
  runMerchantDaySimulation();
}

function closeMerchantDayModal() {
  const modal = document.getElementById("merchantDayModal");
  if (modal) modal.classList.add("hidden");
  if (typeof switchTab === 'function') {
    switchTab("dashboard");
  }
}

async function runMerchantDaySimulation() {
  const list = document.getElementById("merchantDayStepsList");
  const sumBox = document.getElementById("merchantDaySummaryBox");
  const sumTxt = document.getElementById("merchantDaySummaryText");

  if (!list) return;
  list.innerHTML = "";
  if (sumBox) sumBox.classList.add("hidden");

  try {
    const res = await apiFetch("/v1/controller/merchant-day/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({})
    });
    const data = await res.json();
    const steps = data.steps || [];

    for (let i = 0; i < steps.length; i++) {
      const s = steps[i];
      const div = document.createElement("div");
      div.className = "p-3.5 rounded-2xl bg-[#071426] border border-white/5 space-y-1 transition text-xs opacity-0 transform translate-y-2";
      div.innerHTML = `
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-[10px] font-bold">${i + 1}</span>
            <span class="font-bold text-white">${s.stage}</span>
          </div>
          <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-500/20 text-blue-300 font-mono">${s.status}</span>
        </div>
        <p class="text-slate-300 text-[11px] pl-7">${s.detail}</p>
      `;
      list.appendChild(div);

      await new Promise(r => setTimeout(r, 220));
      div.classList.remove("opacity-0", "translate-y-2");
    }

    if (sumBox && sumTxt) {
      sumTxt.innerText = `Merchant Day Cycle Completed • Trace: ${data.demo_trace_id} • Status: ${data.final_status} • Sealed with SHA-256 Audit Trail`;
      sumBox.classList.remove("hidden");
    }
  } catch (err) {
    showToast(err.message, true);
  }
}
