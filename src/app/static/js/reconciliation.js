// =========================================================================
// FINPILOT AI — DETERMINISTIC 3-WAY RECONCILIATION TABLE LOGIC
// =========================================================================

async function loadReconciliationTable() {
  try {
    const res = await apiFetch("/v1/controller/reconciliation?limit=150");
    const data = await res.json();
    renderReconciliationTable(data.records || []);
  } catch (err) {
    console.error("loadReconciliationTable error:", err);
  }
}

function renderReconciliationTable(records) {
  const tbody = document.getElementById("fullReconciliationTableBody");
  if (!tbody) return;

  if (!records || records.length === 0) {
    tbody.innerHTML = `<tr><td colspan="9" class="p-6 text-center text-slate-400">Zero reconciliation records found.</td></tr>`;
    return;
  }

  tbody.innerHTML = records.map(r => `
    <tr class="hover:bg-white/[0.02] transition border-b border-white/5 text-xs">
      <td class="p-3.5 font-mono font-bold text-blue-400">${r.record_id}</td>
      <td class="p-3.5 font-mono text-[11px] text-white">${r.transaction_id || '-'}</td>
      <td class="p-3.5 font-mono text-[11px] text-slate-400">${r.invoice_id || '-'}</td>
      <td class="p-3.5">
        <span class="font-medium text-white block">${r.customer_name || '-'}</span>
        <span class="text-[10px] text-slate-400">${r.vendor_name || '-'}</span>
      </td>
      <td class="p-3.5 text-right font-mono font-bold text-white">₹${(r.payment_amount || 0).toLocaleString()}</td>
      <td class="p-3.5 text-right font-mono text-slate-300">₹${(r.invoice_amount || 0).toLocaleString()}</td>
      <td class="p-3.5 text-right font-mono text-emerald-400 font-bold">₹${(r.settled_amount || 0).toLocaleString()}</td>
      <td class="p-3.5 text-right font-mono text-slate-400">₹${(r.variance || 0).toLocaleString()}</td>
      <td class="p-3.5">
        <span class="px-2 py-0.5 rounded text-[10px] font-extrabold ${r.match_status === 'MATCHED' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : (r.match_status === 'HUMAN_APPROVED' ? 'bg-blue-500/10 text-blue-300 border border-blue-500/20' : 'bg-rose-500/10 text-rose-400 border border-rose-500/20')}">
          ${(r.match_status || '').replace(/_/g, ' ')}
        </span>
      </td>
    </tr>
  `).join("");
  if (window.lucide && typeof window.lucide.createIcons === 'function') {
    window.lucide.createIcons();
  }
}
