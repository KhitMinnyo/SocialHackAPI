document.addEventListener("DOMContentLoaded", () => {
  SH.requireAuth();

  const queryInput = document.getElementById("searchQuery");
  const errorEl = document.getElementById("sh-error");
  const resultEl = document.getElementById("sh-search-result");
  const form = document.getElementById("sh-search-form");

  // Client-side-only filter so this page's own search box can never send
  // anything that breaks the query string it's built into.
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

    const raw = queryInput.value;
    if (!raw) return;
    const sanitized = sanitizeForApi(raw);

    try {
      const data = await SH.apiFetch("/users/search?q=" + encodeURIComponent(sanitized));

      const rows = (data.users || []).map((u) =>
        '<div class="sh-post" style="display:flex; align-items:center; gap:12px;">' +
        '<div class="sh-avatar">' + SH.escapeHtml(SH.initials(u.username)) + '</div>' +
        '<div>' +
        '<div style="font-weight:700;">' + SH.escapeHtml(u.username) +
        (u.is_verified ? ' <span class="sh-badge sh-badge-verified">verified</span>' : '') +
        '</div>' +
        (u.bio ? '<div class="sh-muted">' + SH.escapeHtml(u.bio) + '</div>' : '') +
        '</div></div>'
      ).join("");

      resultEl.innerHTML = rows || '<p class="sh-muted">No results.</p>';
    } catch (err) {
      SH.showError(errorEl, err);
    }
  });
});
