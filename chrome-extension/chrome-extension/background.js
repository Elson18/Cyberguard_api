/**
 * NeuroGuard - Background Service Worker
 * Pipeline: detect_url → api_scan → block_website
 */

importScripts("config.js", "api.js", "workflow.js");

registerNode("detect_url", {
  label: "URL Detection",
  description: "Validates and extracts domain from the target URL",
  execute(context) {
    const { url } = context;

    if (!url || (!url.startsWith("http://") && !url.startsWith("https://"))) {
      return { _abort: true, skipReason: "Non-HTTP URL" };
    }

    if (url.startsWith("chrome-extension://") && url.includes("blocked.html")) {
      return { _abort: true, skipReason: "Blocked page" };
    }

    let domain = null;
    try {
      domain = new URL(url).hostname;
    } catch {
      domain = url;
    }

    return { domain, urlValid: true };
  },
});

registerNode("api_scan", {
  label: "FastAPI Threat Scan",
  description: "Server-side SerpApi + Groq analysis via CyberGuard API",
  async execute(context) {
    const { url, tabId } = context;

    try {
      const analysis = await scanUrlWithApi(url, tabId);

      await reportScanResult({
        url,
        domain: analysis.domain,
        decision: analysis.decision,
        explanation: analysis.explanation,
        serpRisky: analysis.serpRisky,
        serpMatchCount: analysis.serpMatchCount,
        riskLevel: analysis.riskLevel,
      });

      return {
        serpRisky: analysis.serpRisky,
        serpMatchCount: analysis.serpMatchCount,
        serpMatches: analysis.serpMatches || [],
        decision: analysis.decision,
        shouldBlock: analysis.shouldBlock,
        explanation: analysis.explanation,
        riskLevel: analysis.riskLevel,
        aiLabel: analysis.aiLabel,
      };
    } catch (error) {
      console.error("[NeuroGuard] API scan failed:", error.message);
      return {
        serpRisky: false,
        serpMatchCount: 0,
        serpMatches: [],
        decision: "ALLOWED",
        shouldBlock: false,
        explanation: "Scan unavailable — allowed with caution.",
        riskLevel: "LOW",
        apiError: error.message,
      };
    }
  },
});

registerNode("block_website", {
  label: "Block Website",
  description: "Redirects harmful websites to the blocked page",
  async execute(context) {
    const { shouldBlock, tabId, url, explanation, riskLevel } = context;

    if (!shouldBlock) {
      return { blocked: false };
    }

    await chrome.storage.local.set({
      blocked_info: {
        url,
        explanation:
          explanation || "This website was flagged as potentially dangerous.",
        riskLevel: riskLevel || "HIGH",
        timestamp: new Date().toISOString(),
      },
    });

    const blockedPageURL =
      chrome.runtime.getURL("blocked.html") + "?url=" + encodeURIComponent(url);
    chrome.tabs.update(tabId, { url: blockedPageURL });

    return { blocked: true };
  },
});

async function runThreatPipeline(url, source, tabId) {
  const timestamp = new Date().toISOString();
  const storageKey = `result_${tabId}`;
  let domain = null;

  try {
    domain = new URL(url).hostname;
  } catch {
    domain = url;
  }

  await chrome.storage.local.set({
    [storageKey]: {
      domain,
      url,
      serpRisky: false,
      serpMatchCount: 0,
      decision: null,
      timestamp,
    },
  });

  const engine = new WorkflowEngine(THREAT_DETECTION_WORKFLOW);
  const result = await engine.run({
    url,
    tabId,
    source,
    timestamp,
  });

  if (!result._abort) {
    const finalData = {
      domain: result.domain || domain,
      url,
      serpRisky: result.serpRisky || false,
      serpMatchCount: result.serpMatchCount || 0,
      decision: result.decision || "ALLOWED",
      explanation: result.explanation || null,
      riskLevel: result.riskLevel || null,
      aiLabel: result.aiLabel || null,
      timestamp,
      executionLog: result._executionLog,
      totalDurationMs: result._totalDurationMs,
    };

    await chrome.storage.local.set({ [storageKey]: finalData });

    try {
      const histData = await chrome.storage.local.get("neuroguard_history");
      const history = histData.neuroguard_history || [];

      history.unshift({
        url,
        domain: result.domain || domain,
        status: result.decision === "BLOCKED" ? "HARMFUL" : "SAFE",
        action: result.decision || "ALLOWED",
        serpRisky: result.serpRisky || false,
        serpMatchCount: result.serpMatchCount || 0,
        explanation: result.explanation || null,
        riskLevel: result.riskLevel || null,
        durationMs: result._totalDurationMs || 0,
        time: new Date().toLocaleString("en-US", {
          year: "numeric",
          month: "short",
          day: "numeric",
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
        }),
      });

      if (history.length > 500) {
        history.length = 500;
      }

      await chrome.storage.local.set({ neuroguard_history: history });
    } catch (histErr) {
      console.error("History tracking error:", histErr.message);
    }
  }
}

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === "complete" && tab.url) {
    runThreatPipeline(tab.url, "Tab Updated", tabId);
  }
});

chrome.tabs.onActivated.addListener(async (activeInfo) => {
  try {
    const tab = await chrome.tabs.get(activeInfo.tabId);
    if (tab.url) {
      runThreatPipeline(tab.url, "Tab Switched", activeInfo.tabId);
    }
  } catch (error) {
    console.error("[NeuroGuard] Error fetching tab info:", error.message);
  }
});

chrome.runtime.onInstalled.addListener((details) => {
  console.log(`NeuroGuard extension ${details.reason} — API pipeline active`);
});
