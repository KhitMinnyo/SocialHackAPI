document.addEventListener("DOMContentLoaded", () => {
  SH.requireAuth();

  const domainInput = document.getElementById("dnsDomain");
  const errorEl = document.getElementById("sh-error");
  const resultEl = document.getElementById("sh-dns-result");
  const form = document.getElementById("sh-dns-form");

  domainInput.value = "google.com";

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    errorEl.classList.add("sh-hidden");
    resultEl.classList.add("sh-hidden");

    const domain = domainInput.value.trim();
    if (!domain) return;

    try {
      const data = await SH.apiFetch("/tools/dns-lookup", {
        method: "POST",
        body: JSON.stringify({ domain }),
      });
      let html =
        '<div class="sh-post">' +
        '<div class="sh-muted">Command run on the server:</div>' +
        '<code style="display:block; background:#f5f5f5; padding:8px; border-radius:6px; margin:6px 0; word-break:break-all;">' +
        SH.escapeHtml(data.command) + '</code>' +
        '<div class="sh-muted" style="margin-top:10px;">stdout:</div>' +
        '<pre style="background:#f5f5f5; padding:10px; border-radius:6px; overflow-x:auto; margin-top:6px; white-space:pre-wrap;">' +
        SH.escapeHtml(data.stdout) + '</pre>';
      if (data.stderr) {
        html +=
          '<div class="sh-muted" style="margin-top:10px;">stderr:</div>' +
          '<pre style="background:#f5f5f5; padding:10px; border-radius:6px; overflow-x:auto; margin-top:6px; white-space:pre-wrap;">' +
          SH.escapeHtml(data.stderr) + '</pre>';
      }
      html += '</div>';
      resultEl.innerHTML = html;
      resultEl.classList.remove("sh-hidden");
    } catch (err) {
      SH.showError(errorEl, err);
    }
  });
});
