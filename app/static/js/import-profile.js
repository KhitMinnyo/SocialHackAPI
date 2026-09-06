document.addEventListener("DOMContentLoaded", () => {
  SH.requireAuth();

  const sourceInput = document.getElementById("sourceUrl");
  const errorEl = document.getElementById("sh-error");
  const resultEl = document.getElementById("sh-import-result");
  const form = document.getElementById("sh-import-form");

  // Same-origin static mocks so this page works with zero setup, built
  // from window.location.origin (not hardcoded) so it still works if the
  // lab's host/port ever changes.
  const origin = window.location.origin;
  const benignUrl = origin + "/static/mock-partner/profile-benign.json";
  const evilUrl = origin + "/static/mock-partner/profile-malicious.json";

  sourceInput.value = benignUrl;

  document.getElementById("sh-fill-benign").addEventListener("click", () => {
    sourceInput.value = benignUrl;
  });
  document.getElementById("sh-fill-evil").addEventListener("click", () => {
    sourceInput.value = evilUrl;
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    errorEl.classList.add("sh-hidden");
    resultEl.classList.add("sh-hidden");

    const sourceUrl = sourceInput.value.trim();
    if (!sourceUrl) return;

    try {
      const data = await SH.apiFetch("/integrations/import-profile", {
        method: "POST",
        body: JSON.stringify({ source_url: sourceUrl }),
      });

      const fields = data.fields_applied_from_partner || {};
      const fieldKeys = Object.keys(fields);
      const fieldRows = fieldKeys.length
        ? fieldKeys.map((k) =>
            "<li><code>" + SH.escapeHtml(k) + "</code> = " + SH.escapeHtml(JSON.stringify(fields[k])) + "</li>"
          ).join("")
        : '<li class="sh-muted">(no fields were applied)</li>';

      resultEl.innerHTML =
        '<div class="sh-post">' +
        '<div style="font-weight:700;">' + SH.escapeHtml(data.message) + '</div>' +
        '<div class="sh-muted" style="margin:6px 0;">Fields the "partner" set on your account:</div>' +
        '<ul>' + fieldRows + '</ul>' +
        '<div class="sh-muted" style="margin-top:10px;">Your account now looks like:</div>' +
        '<pre style="background:#f5f5f5; padding:10px; border-radius:6px; overflow-x:auto; margin-top:6px;">' +
        SH.escapeHtml(JSON.stringify(data.user, null, 2)) + '</pre>' +
        '</div>';
      resultEl.classList.remove("sh-hidden");
    } catch (err) {
      SH.showError(errorEl, err);
    }
  });
});
