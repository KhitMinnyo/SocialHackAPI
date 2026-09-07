document.addEventListener("DOMContentLoaded", () => {
  SH.requireAuth();

  const queryInput = document.getElementById("searchQuery");
  const errorEl = document.getElementById("sh-error");
  const resultEl = document.getElementById("sh-search-result");
  const form = document.getElementById("sh-search-form");

  const NORMAL_EXAMPLE = "ali";
  // A classic tautology payload - against the raw API (called directly,
  // bypassing this page) this returns every row in the users table. See
  // app/routes/users.py's search_users(). Typed into THIS page, the
  // filter below strips it down to something harmless before it is ever
  // sent anywhere.
  const INJECTION_EXAMPLE = "' OR '1'='1' --";

  document.getElementById("sh-fill-normal").addEventListener("click", () => {
    queryInput.value = NORMAL_EXAMPLE;
  });
  document.getElementById("sh-fill-injection").addEventListener("click", () => {
    queryInput.value = INJECTION_EXAMPLE;
  });

  /**
   * Client-side-only filter. Strips characters commonly used to break out
   * of the vulnerable SQL string on the server (', --, /* *\/, ;) so this
   * page can never send anything that would produce a SQL syntax error or
   * an injection, no matter what is typed into #searchQuery.
   *
   * IMPORTANT - this is a UI convenience, not a security control. It runs
   * only in the browser and is trivially bypassed by calling
   * GET /api/v1/users/search?q=... directly. app/routes/users.py is not
   * touched by this page at all and stays exactly as vulnerable as it
   * always was.
   */
  function sanitizeForApi(raw) {
    return raw
      .replace(/'/g, "")
      .replace(/--/g, "")
      .replace(/\/\*/g, "")
      .replace(/\*\//g, "")
      .replace(/;/g, "");
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    errorEl.classList.add("sh-hidden");
    resultEl.classList.add("sh-hidden");

    const raw = queryInput.value;
    if (!raw) return;
    const sanitized = sanitizeForApi(raw);

    try {
      const data = await SH.apiFetch("/users/search?q=" + encodeURIComponent(sanitized));

      const rows = (data.users || []).map((u) =>
        '<div class="sh-post">' +
        '<div style="font-weight:700;">' + SH.escapeHtml(u.username) +
        (u.role ? ' <span class="sh-muted">(' + SH.escapeHtml(u.role) + ')</span>' : '') +
        '</div>' +
        '<div class="sh-muted">' + SH.escapeHtml(u.email) + '</div>' +
        (u.bio ? '<div style="margin-top:4px;">' + SH.escapeHtml(u.bio) + '</div>' : '') +
        '</div>'
      ).join("");

      resultEl.innerHTML =
        '<div class="sh-muted">You typed: <code>' + SH.escapeHtml(raw) + '</code></div>' +
        '<div class="sh-muted" style="margin-top:4px;">Sent to the API after this page&#39;s front-end filter: <code>' +
        (sanitized ? SH.escapeHtml(sanitized) : '(empty)') + '</code></div>' +
        '<div style="margin-top:10px; font-weight:700;">' + data.count + ' result(s)</div>' +
        '<div style="margin-top:8px;">' + (rows || '<p class="sh-muted">No matches.</p>') + '</div>';
      resultEl.classList.remove("sh-hidden");
    } catch (err) {
      SH.showError(errorEl, err);
    }
  });
});
