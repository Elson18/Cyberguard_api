const params = new URLSearchParams(window.location.search);
const blockedUrl = params.get("url");

if (blockedUrl) {
  document.getElementById("blockedURL").textContent = blockedUrl;
}

// Load AI explanation from chrome.storage
async function loadExplanation() {
  try {
    const data = await chrome.storage.local.get("blocked_info");
    const info = data.blocked_info;

    if (info && info.explanation) {
      document.getElementById("explanationContent").innerHTML =
        `<p class="explanation-text">"${info.explanation}"</p>`;
    } else {
      document.getElementById("explanationContent").innerHTML =
        `<p class="explanation-text">"This website was flagged as potentially dangerous by our AI system."</p>`;
    }

    // Update risk badge
    if (info && info.riskLevel) {
      const badge = document.getElementById("riskBadge");
      if (info.riskLevel === "HIGH") {
        badge.className = "risk-badge risk-high";
        badge.textContent = "🔴 High Risk";
      } else if (info.riskLevel === "MEDIUM") {
        badge.className = "risk-badge risk-medium";
        badge.textContent = "🟡 Medium Risk";
      } else {
        badge.className = "risk-badge risk-low";
        badge.textContent = "🟢 Low Risk";
      }
    }
  } catch (err) {
    document.getElementById("explanationContent").innerHTML =
      `<p class="explanation-text">"This website was flagged as potentially dangerous."</p>`;
  }
}

loadExplanation();

// Bind button clicks to click events to comply with CSP 'unsafe-inline' restrictions on attributes
document.getElementById("safetyBtn").addEventListener("click", () => {
  window.location.href = "https://www.google.com";
});

document.getElementById("backBtn").addEventListener("click", () => {
  history.back();
});
