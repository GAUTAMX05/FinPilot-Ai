// =========================================================================
// FINPILOT AI — API CLIENT & AUTH UTILITIES
// =========================================================================

async function apiFetch(endpoint, options = {}) {
  const token = localStorage.getItem("finpilot_token") || (typeof authToken !== 'undefined' ? authToken : null);
  const headers = {
    ...(token ? { "Authorization": `Bearer ${token}` } : {}),
    ...(options.headers || {})
  };
  
  const res = await fetch(endpoint, { ...options, headers });
  if (!res.ok) {
    let errDetail = `API Error ${res.status}`;
    try {
      const errJson = await res.json();
      errDetail = errJson.detail || errJson.message || errDetail;
    } catch(e) {}
    throw new Error(errDetail);
  }
  return res;
}

function showToast(message, isError = false) {
  const toast = document.createElement("div");
  toast.className = `fixed bottom-5 right-5 px-4 py-3 rounded-2xl text-xs font-semibold shadow-2xl z-50 flex items-center gap-2 transition-all transform duration-300 ${isError ? 'bg-rose-600 text-white border border-rose-400/30' : 'bg-[#0B1729] text-emerald-400 border border-emerald-500/30 shadow-glow-blue'}`;
  toast.innerHTML = `
    <i data-lucide="${isError ? 'alert-circle' : 'check-circle-2'}" class="w-4 h-4"></i>
    <span>${message}</span>
  `;
  document.body.appendChild(toast);
  if (window.lucide && typeof window.lucide.createIcons === 'function') {
    window.lucide.createIcons();
  }

  setTimeout(() => {
    toast.classList.add("opacity-0", "translate-y-2");
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}
