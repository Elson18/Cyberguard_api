/**
 * NeuroGuard - Configuration
 * API keys are kept server-side. Extension talks to FastAPI only.
 */

const API_BASE = "http://localhost:8765";
const SCAN_ENDPOINT = `${API_BASE}/api/extension/scan-url`;
const REPORT_ENDPOINT = `${API_BASE}/api/extension/report`;
const STATUS_ENDPOINT = `${API_BASE}/api/extension/status`;
