document.addEventListener("DOMContentLoaded", () => {
  SH.requireAuth();

  const providerInput = document.getElementById("rateProvider");
  const errorEl = document.getElementById("sh-error");
  const resultEl = document.getElementById("sh-rate-result");
  const form = document.getElementById("sh-rate-form");

  // Prefill with a same-origin static mock so this page works with zero
  // setup. Built from window.location.origin (not hardcoded) so it still
  // works if the lab's host/port ever changes.
  providerInput.value = window.location.origin + "/static/mock-partner/exchange-rate.json";

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    errorEl.classList.add("sh-hidden");
    resultEl.classList.add("sh-hidden");

    const provider = providerInput.value.trim();
    if (!provider) return;

    try {
      const data = await SH.apiFetch("/integrations/exchange-rate?provider=" + encodeURIComponent(provider));
      resultEl.innerHTML =
        '<div class="sh-post">' +
        '<div style="font-size:1.4em; font-weight:700;">Rate: ' + SH.escapeHtml(data.rate) + '</div>' +
        '<div class="sh-muted" style="margin-top:6px;">Provider: ' + SH.escapeHtml(data.provider) + '</div>' +
        '<pre style="background:#f5f5f5; padding:10px; border-radius:6px; overflow-x:auto; margin-top:10px;">' +
        SH.escapeHtml(JSON.stringify(data.raw_response, null, 2)) + '</pre>' +
        '</div>';
      resultEl.classList.remove("sh-hidden");
    } catch (err) {
      SH.showError(errorEl, err);
    }
  });
});
