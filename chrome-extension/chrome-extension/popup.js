/**
 * NeuroGuard - Popup Script
 *
 * Reads analysis results from chrome.storage.local
 * and displays real-time safety status for the active tab.
 */

// ─── DOM Elements ──────────────────────────────────────────────────────────
const statusBanner = document.getElementById("statusBanner");
const statusIcon = document.getElementById("statusIcon");
const statusLabel = document.getElementById("statusLabel");
const statusSublabel = document.getElementById("statusSublabel");
const domainValue = document.getElementById("domainValue");
const serpBadge = document.getElementById("serpBadge");
const footerDot = document.getElementById("footerDot");

// ─── Render the UI based on stored result ──────────────────────────────────
function renderResult(result) {
  if (!result) {
    statusBanner.className = "status-banner loading";
    statusIcon.textContent = "🔍";
    statusLabel.textContent = "Analyzing...";
    statusSublabel.textContent = "Waiting for analysis results";
    serpBadge.className = "row-badge badge-loading";
    serpBadge.innerHTML = '<span class="spinner"></span> Pending';
    footerDot.className = "dot dot-blue";
    return;
  }

  // Domain
  domainValue.textContent = result.domain || "Unknown";

  // ── SerpApi badge ──
  if (result.serpRisky) {
    serpBadge.className = "row-badge badge-risky";
    serpBadge.textContent = `🚨 Risky (${result.serpMatchCount})`;
  } else {
    serpBadge.className = "row-badge badge-clean";
    serpBadge.textContent = "✅ Clean";
  }

  // ── Overall status banner ──
  const decision = result.decision; // "BLOCKED" or "ALLOWED"

  if (decision === "BLOCKED") {
    statusBanner.className = "status-banner harmful";
    statusIcon.textContent = "🚨";
    statusLabel.textContent = "Harmful — Blocked";
    statusSublabel.textContent = result.explanation || "This website has been blocked by AI";
    footerDot.className = "dot dot-red";
  } else {
    statusBanner.className = "status-banner safe";
    statusIcon.textContent = "✅";
    statusLabel.textContent = "Safe";
    statusSublabel.textContent = "No threats detected";
    footerDot.className = "dot dot-green";
  }
}

// ─── Load result for the current active tab ────────────────────────────────
async function loadCurrentTabResult() {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    if (!tab || !tab.url) {
      domainValue.textContent = "No website open";
      return;
    }

    // Show domain immediately
    try {
      domainValue.textContent = new URL(tab.url).hostname;
    } catch {
      domainValue.textContent = tab.url;
    }

    // Check for chrome:// or extension pages
    if (!tab.url.startsWith("http://") && !tab.url.startsWith("https://")) {
      statusBanner.className = "status-banner safe";
      statusIcon.textContent = "🏠";
      statusLabel.textContent = "Internal Page";
      statusSublabel.textContent = "Browser pages are not analyzed";
      serpBadge.className = "row-badge badge-error";
      serpBadge.textContent = "— N/A";
      footerDot.className = "dot dot-blue";
      return;
    }

    // Fetch stored result
    const key = `result_${tab.id}`;
    const data = await chrome.storage.local.get(key);
    renderResult(data[key] || null);
  } catch (error) {
    console.error("[NeuroGuard Popup] Error:", error.message);
  }
}

// ─── Listen for real-time updates ──────────────────────────────────────────
chrome.storage.onChanged.addListener((changes, area) => {
  if (area === "local") {
    // Re-render when any result changes
    loadCurrentTabResult();
  }
});

// ─── Dashboard button ──────────────────────────────────────────────────────
document.getElementById("openDashboard").addEventListener("click", () => {
  chrome.tabs.create({ url: chrome.runtime.getURL("history.html") });
});

// ─── Initialize ────────────────────────────────────────────────────────────
loadCurrentTabResult();
