let allHistory = [];

function getStatusBadge(status) {
  switch (status) {
    case "SAFE": return '<span class="badge badge-safe">🟢 Safe</span>';
    case "SUSPICIOUS": return '<span class="badge badge-suspicious">🟡 Suspicious</span>';
    case "HARMFUL": return '<span class="badge badge-harmful">🔴 Harmful</span>';
    default: return '<span class="badge badge-unknown">— Unknown</span>';
  }
}

function getActionHtml(action) {
  if (action === "BLOCKED") {
    return '<span class="action-blocked">🛡️ Blocked</span>';
  }
  return '<span class="action-allowed">✅ Allowed</span>';
}

function escapeHtml(str) {
  return String(str || "").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function renderTable(history) {
  const tbody = document.getElementById("activityBody");
  const empty = document.getElementById("emptyState");

  if (!history.length) {
    tbody.innerHTML = "";
    empty.style.display = "block";
    return;
  }

  empty.style.display = "none";
  tbody.innerHTML = history.map(function(entry) {
    const durationText = entry.durationMs ? (entry.durationMs / 1000).toFixed(1) + "s" : "—";
    return '<tr>' +
      '<td><div class="domain-cell">' +
        '<span class="domain-name">' + escapeHtml(entry.domain) + '</span>' +
        '<span class="domain-url" title="' + escapeHtml(entry.url) + '">' + escapeHtml(entry.url) + '</span>' +
      '</div></td>' +
      '<td>' + getStatusBadge(entry.status) + '</td>' +
      '<td>' + getActionHtml(entry.action) + '</td>' +
      '<td><span class="duration-cell">' + durationText + '</span></td>' +
      '<td><span class="time-cell">' + escapeHtml(entry.time) + '</span></td>' +
    '</tr>';
  }).join("");
}

function updateStats(history) {
  const total = history.length;
  const safe = history.filter(function(e) { return e.status === "SAFE"; }).length;
  const suspicious = history.filter(function(e) { return e.status === "SUSPICIOUS"; }).length;
  const harmful = history.filter(function(e) { return e.status === "HARMFUL"; }).length;
  const blocked = history.filter(function(e) { return e.action === "BLOCKED"; }).length;

  document.getElementById("totalScanned").textContent = total;
  document.getElementById("totalSafe").textContent = safe;
  document.getElementById("totalSuspicious").textContent = suspicious;
  document.getElementById("totalHarmful").textContent = harmful;
  document.getElementById("totalBlocked").textContent = blocked;
  document.getElementById("activityCount").textContent = total + (total === 1 ? " entry" : " entries");
}

async function loadHistory() {
  try {
    const data = await chrome.storage.local.get("neuroguard_history");
    allHistory = data.neuroguard_history || [];
    updateStats(allHistory);
    renderTable(allHistory);
  } catch (err) {
    console.error("Failed to load history:", err);
  }
}

// Search / filter
document.getElementById("searchBox").addEventListener("input", function() {
  const q = this.value.toLowerCase().trim();
  if (!q) {
    renderTable(allHistory);
    return;
  }
  var filtered = allHistory.filter(function(e) {
    return (e.domain || "").toLowerCase().includes(q) ||
           (e.url || "").toLowerCase().includes(q) ||
           (e.status || "").toLowerCase().includes(q);
  });
  renderTable(filtered);
});

// Refresh button
document.getElementById("refreshBtn").addEventListener("click", loadHistory);

// Clear history
document.getElementById("clearBtn").addEventListener("click", async function() {
  if (!confirm("Clear all NeuroGuard activity history?")) return;
  await chrome.storage.local.set({ neuroguard_history: [] });
  allHistory = [];
  updateStats([]);
  renderTable([]);
});

// Live updates when storage changes
chrome.storage.onChanged.addListener(function(changes, area) {
  if (area === "local" && changes.neuroguard_history) {
    allHistory = changes.neuroguard_history.newValue || [];
    updateStats(allHistory);
    var q = document.getElementById("searchBox").value.toLowerCase().trim();
    if (q) {
      var filtered = allHistory.filter(function(e) {
        return (e.domain || "").toLowerCase().includes(q) ||
               (e.url || "").toLowerCase().includes(q);
      });
      renderTable(filtered);
    } else {
      renderTable(allHistory);
    }
  }
});

// Initialize
loadHistory();
