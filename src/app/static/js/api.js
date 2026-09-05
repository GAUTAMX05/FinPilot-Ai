// =========================================================================
// FINPILOT AI — API CLIENT & AUTH UTILITIES (polished: timeout, a11y toasts)
// =========================================================================

function _escapeHtml(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

function getApiUrl(endpoint) {
  if (!endpoint) return endpoint;
  if (endpoint.startsWith("http://") || endpoint.startsWith("https://")) {
    return endpoint;
  }
  if (typeof window !== "undefined" && window.location) {
    const protocol = window.location.protocol;
    const port = window.location.port;
    if (protocol === "file:" || (port && port !== "8000")) {
      const cleanPath = endpoint.startsWith("/") ? endpoint : "/" + endpoint;
      return `http://127.0.0.1:8000${cleanPath}`;
    }
  }
  return endpoint;
}

async function apiFetch(endpoint, options = {}) {
  const fullUrl = getApiUrl(endpoint);
  const token = localStorage.getItem("ai_finance_token")
    || localStorage.getItem("finpilot_token")
    || (typeof authToken !== "undefined" && authToken ? authToken : null);
  const headers = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers || {}),
  };
  const controller = new AbortController();
  const timeoutMs = options.timeoutMs ?? 30000;
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(fullUrl, { ...options, headers, signal: controller.signal });
    if (!res.ok) {
      const text = await res.text().catch(() => "");
      console.warn(`[apiFetch] ${res.status} on ${fullUrl}:`, text.slice(0, 300));
    }
    return res;
  } catch (err) {
    if (err?.name === "AbortError") {
      console.warn(`[apiFetch] Timeout (${timeoutMs}ms) on ${fullUrl}`);
      showToast("Request timed out. Please retry.", true);
    } else {
      console.warn(`[apiFetch] Network warning on ${fullUrl}:`, err);
      showToast("Cannot connect to FinPilot AI backend. Please start the server on port 8000 (python run_server.py).", true);
    }
    throw err;
  } finally {
    clearTimeout(timer);
  }
}

function showToast(message, isError = false) {
  const toast = document.createElement("div");
  toast.setAttribute("role", isError ? "alert" : "status");
  toast.setAttribute("aria-live", "polite");
  toast.className = `fixed bottom-5 right-5 px-4 py-3 rounded-2xl text-xs font-semibold shadow-2xl z-50 flex items-center gap-2 transition-all transform duration-300 ${isError ? "bg-rose-600 text-white border border-rose-400/30" : "bg-[#0B1729] text-emerald-400 border border-emerald-500/30 shadow-glow-blue"}`;
  toast.innerHTML = `
    <i data-lucide="${isError ? "alert-circle" : "check-circle-2"}" class="w-4 h-4" aria-hidden="true"></i>
    <span>${_escapeHtml(message)}</span>
  `;
  document.body.appendChild(toast);
  if (window.lucide && typeof window.lucide.createIcons === "function") {
    window.lucide.createIcons();
  }

  setTimeout(() => {
    toast.classList.add("opacity-0", "translate-y-2");
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}
