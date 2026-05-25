window.AAP = (function () {
  const API_BASE = window.location.origin;

  function requireAuth() {
    const user =
      localStorage.getItem("username") || localStorage.getItem("user_id");
    if (!user) {
      window.location.href = "/login";
    }
  }

  function logout() {
    localStorage.removeItem("username");
    localStorage.removeItem("user_id");
    window.location.href = "/login";
  }

  async function api(path, options = {}) {
    const headers = {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    };
    const token = localStorage.getItem("user_id");
    if (token) {
      headers["X-User-Id"] = token;
    }

    const response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const errorBody = await response.json().catch(() => ({}));
      throw new Error(errorBody.detail || response.statusText);
    }

    return response.json();
  }

  return { API_BASE, requireAuth, logout, api };
})();
