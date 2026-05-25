/**
 * NeuroGuard - Secure API client for FastAPI backend.
 */

async function ngFetch(url, options = {}, retries = 2) {
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  const stored = await chrome.storage.local.get("api_token");
  if (stored.api_token) {
    headers["X-User-Id"] = stored.api_token;
  }

  let lastError = null;
  for (let attempt = 0; attempt <= retries; attempt += 1) {
    try {
      const response = await fetch(url, { ...options, headers });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail || response.statusText);
      }
      return await response.json();
    } catch (error) {
      lastError = error;
      if (attempt < retries) {
        await new Promise((resolve) => setTimeout(resolve, 400 * (attempt + 1)));
      }
    }
  }

  throw lastError;
}

async function scanUrlWithApi(url, tabId) {
  return ngFetch(SCAN_ENDPOINT, {
    method: "POST",
    body: JSON.stringify({ url, tab_id: tabId }),
  });
}

async function reportScanResult(payload) {
  try {
    await ngFetch(REPORT_ENDPOINT, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  } catch (error) {
    console.warn("[NeuroGuard] Report failed:", error.message);
  }
}
