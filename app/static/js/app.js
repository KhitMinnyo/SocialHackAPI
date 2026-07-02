/**
 * SocialHack Web UI - shared client-side helpers.
 *
 * This file is the ONLY place that knows about localStorage keys and the
 * API base URL. Every page-specific script (feed.js, profile.js, ...) goes
 * through the SH.* helpers below instead of calling fetch()/localStorage
 * directly, so behavior stays consistent across the whole app.
 *
 * NOTE for students: this file itself has no intentional vulnerabilities.
 * The JWT is stored in localStorage (a realistic, common - if imperfect -
 * SPA pattern) and sent as `Authorization: Bearer <token>` on every API
 * call, exactly like the curl commands you've already been using in the
 * labs. Open your browser's DevTools > Application > Local Storage, or
 * just proxy this page through Burp Suite, and you'll see the exact same
 * requests you've been crafting by hand.
 */

const SH = (() => {
  const API_BASE = "/api/v1";
  const TOKEN_KEY = "socialhack_token";
  const USER_KEY = "socialhack_user";

  function getToken() {
    return localStorage.getItem(TOKEN_KEY);
  }

  function getUser() {
    const raw = localStorage.getItem(USER_KEY);
    if (!raw) return null;
    try {
      return JSON.parse(raw);
    } catch (e) {
      return null;
    }
  }

  function setSession(token, user) {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  }

  function clearSession() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  }

  function isLoggedIn() {
    return !!getToken();
  }

  function logout() {
    clearSession();
    window.location.href = "/app/login";
  }

  /**
   * Redirect to /app/login if there's no token stored. Call this at the
   * top of any page that should not be viewable while logged out. This is
   * a client-side-only gate (there is no server session) - the actual
   * protection, such as it is, comes entirely from the real API's own
   * @token_required checks when SH.apiFetch() is used.
   */
  function requireAuth() {
    if (!isLoggedIn()) {
      window.location.href = "/app/login";
    }
  }

  /**
   * Thin wrapper around fetch() that targets the real JSON API.
   * - Prepends API_BASE to `path`.
   * - Attaches Authorization: Bearer <token> automatically when logged in.
   * - Sends/expects JSON.
   * - On 401, clears the (expired/invalid) session and bounces to login.
   * Returns the parsed JSON body. Throws an Error with the API's own error
   * message on non-2xx responses so callers can display it.
   */
  async function apiFetch(path, options = {}) {
    const headers = Object.assign(
      { "Content-Type": "application/json" },
      options.headers || {}
    );
    const token = getToken();
    if (token) {
      headers["Authorization"] = "Bearer " + token;
    }

    const res = await fetch(API_BASE + path, Object.assign({}, options, { headers }));

    let body = null;
    const text = await res.text();
    if (text) {
      try {
        body = JSON.parse(text);
      } catch (e) {
        body = { raw: text };
      }
    }

    if (res.status === 401) {
      clearSession();
    }

    if (!res.ok) {
      const message = (body && (body.error || body.message)) || `Request failed (${res.status})`;
      const err = new Error(message);
      err.status = res.status;
      err.body = body;
      throw err;
    }

    return body;
  }

  function escapeHtml(str) {
    if (str === null || str === undefined) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function initials(username) {
    if (!username) return "?";
    return username.slice(0, 2).toUpperCase();
  }

  function formatDate(iso) {
    if (!iso) return "";
    try {
      const d = new Date(iso);
      return d.toLocaleString();
    } catch (e) {
      return iso;
    }
  }

  function showError(el, err) {
    if (!el) return;
    el.textContent = err && err.message ? err.message : String(err);
    el.classList.remove("sh-hidden");
  }

  function showSuccess(el, message) {
    if (!el) return;
    el.textContent = message;
    el.classList.remove("sh-hidden");
  }

  /**
   * Fill in the shared nav bar. Called once on every page (see base.html).
   * Purely cosmetic / client-side - hiding the "Admin" link here does not
   * add any real protection, see app/routes/web.py's docstring.
   */
  function renderNav() {
    const user = getUser();
    const loggedIn = isLoggedIn() && user;

    document.querySelectorAll("[data-sh-auth-only]").forEach((el) => {
      el.classList.toggle("sh-hidden", !loggedIn);
    });
    document.querySelectorAll("[data-sh-guest-only]").forEach((el) => {
      el.classList.toggle("sh-hidden", !!loggedIn);
    });
    document.querySelectorAll("[data-sh-admin-only]").forEach((el) => {
      el.classList.toggle("sh-hidden", !(loggedIn && user.role === "admin"));
    });

    if (loggedIn) {
      const nameEl = document.getElementById("sh-nav-username");
      if (nameEl) nameEl.textContent = user.username;

      const profileLink = document.getElementById("sh-nav-profile-link");
      if (profileLink) profileLink.setAttribute("href", "/app/profile/" + user.id);
    }

    const logoutBtn = document.getElementById("sh-nav-logout");
    if (logoutBtn) {
      logoutBtn.addEventListener("click", (e) => {
        e.preventDefault();
        logout();
      });
    }
  }

  return {
    API_BASE,
    getToken,
    getUser,
    setSession,
    clearSession,
    isLoggedIn,
    logout,
    requireAuth,
    apiFetch,
    escapeHtml,
    initials,
    formatDate,
    showError,
    showSuccess,
    renderNav,
  };
})();

document.addEventListener("DOMContentLoaded", () => {
  SH.renderNav();
});
