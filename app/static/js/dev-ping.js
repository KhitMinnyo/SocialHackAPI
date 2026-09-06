document.addEventListener("DOMContentLoaded", () => {
  SH.requireAuth();

  const hostInput = document.getElementById("pingHost");
  const errorEl = document.getElementById("sh-error");
  const resultEl = document.getElementById("sh-ping-result");
  const form = document.getElementById("sh-ping-form");

  hostInput.value = "localhost";

  document.getElementById("sh-fill-safe").addEventListener("click", () => {
    hostInput.value = "localhost";
  });
  document.getElementById("sh-fill-injection").addEventListener("click", () => {
    hostInput.value = "localhost; whoami";
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    errorEl.classList.add("sh-hidden");
    resultEl.classList.add("sh-hidden");

    const host = hostInput.value.trim();
    if (!host) return;

    try {
      const data = await SH.apiFetch("/tools/ping", {
        method: "POST",
        body: JSON.stringify({ host }),
      });
      resultEl.innerHTML =
        '<div class="sh-post">' +
        '<div class="sh-muted">Command run on the server:</div>' +
        '<code style="display:block; background:#f5f5f5; padding:8px; border-radius:6px; margin:6px 0; word-break:break-all;">' +
        SH.escapeHtml(data.command) + '</code>' +
        '<div class="sh-muted" style="margin-top:10px;">Output:</div>' +
        '<pre style="background:#f5f5f5; padding:10px; border-radius:6px; overflow-x:auto; margin-top:6px; white-space:pre-wrap;">' +
        SH.escapeHtml(data.output) + '</pre>' +
        '</div>';
      resultEl.classList.remove("sh-hidden");
    } catch (err) {
      SH.showError(errorEl, err);
    }
  });
});
