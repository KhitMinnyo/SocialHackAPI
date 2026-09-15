document.addEventListener("DOMContentLoaded", () => {
  SH.requireAuth();

  const phoneInput = document.getElementById("otpPhone");
  const codeInput = document.getElementById("otpCode");
  const requestForm = document.getElementById("sh-otp-request-form");
  const verifyForm = document.getElementById("sh-otp-verify-form");
  const requestErrorEl = document.getElementById("sh-request-error");
  const requestResultEl = document.getElementById("sh-request-result");
  const verifyErrorEl = document.getElementById("sh-verify-error");
  const verifyResultEl = document.getElementById("sh-verify-result");

  requestForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    requestErrorEl.classList.add("sh-hidden");
    requestResultEl.classList.add("sh-hidden");

    const phone = phoneInput.value.trim();
    if (!phone) return;

    try {
      const data = await SH.apiFetch("/otp/request", {
        method: "POST",
        body: JSON.stringify({ phone_number: phone }),
      });
      codeInput.value = data.otp_code;
      requestResultEl.innerHTML =
        '<div class="sh-post">' +
        '<div style="font-weight:700;">' + SH.escapeHtml(data.message) + '</div>' +
        '<div class="sh-muted" style="margin-top:4px;">Code: <code>' + SH.escapeHtml(data.otp_code) + '</code> ' +
        '(auto-filled below - a real SMS provider would send this to the phone instead)</div>' +
        '<div class="sh-muted" style="margin-top:4px;">' + data.requests_remaining_in_window +
        ' request(s) remaining in this ' + data.window_seconds + 's window</div>' +
        '</div>';
      requestResultEl.classList.remove("sh-hidden");
    } catch (err) {
      SH.showError(requestErrorEl, err);
    }
  });

  verifyForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    verifyErrorEl.classList.add("sh-hidden");
    verifyResultEl.classList.add("sh-hidden");

    const phone = phoneInput.value.trim();
    const code = codeInput.value.trim();
    if (!phone || !code) return;

    try {
      const data = await SH.apiFetch("/otp/verify", {
        method: "POST",
        body: JSON.stringify({ phone_number: phone, code: code }),
      });
      verifyResultEl.innerHTML =
        '<div class="sh-post">' +
        '<div style="font-weight:700;">&#9989; ' + SH.escapeHtml(data.message) + '</div>' +
        '</div>';
      verifyResultEl.classList.remove("sh-hidden");
    } catch (err) {
      SH.showError(verifyErrorEl, err);
    }
  });
});
