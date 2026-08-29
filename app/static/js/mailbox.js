function shQueryParam(name) {
  return new URLSearchParams(window.location.search).get(name);
}

async function shCheckInbox(email) {
  const mailCard = document.getElementById("sh-mail-card");
  const resetCard = document.getElementById("sh-reset-card");

  mailCard.classList.remove("sh-hidden");
  mailCard.innerHTML = '<p class="sh-muted">Checking...</p>';
  resetCard.classList.add("sh-hidden");

  let data;
  try {
    // New, read-only endpoint (app/routes/web_password_reset.py) - just
    // re-reads the same reset_token POST /api/v1/auth/reset-password
    // already returns directly.
    const res = await fetch("/api/v1/auth/mailbox?email=" + encodeURIComponent(email));
    data = await res.json();
    if (!res.ok) {
      mailCard.innerHTML = '<div class="sh-error">' + (data.error || "Something went wrong") + "</div>";
      return;
    }
  } catch (err) {
    mailCard.innerHTML = '<div class="sh-error">Could not reach the server.</div>';
    return;
  }

  const safeEmail = SH.escapeHtml(data.email);

  if (data.empty) {
    mailCard.innerHTML =
      '<h3>Inbox</h3><p class="sh-muted">No pending reset email for <b>' +
      safeEmail + '</b>. Request one from the <a href="/app/forgot-password">forgot password page</a> first.</p>';
    return;
  }

  const safeSubject = SH.escapeHtml(data.subject);
  const safeBody = SH.escapeHtml(data.body_preview);
  const safeToken = SH.escapeHtml(data.reset_token);
  const safeFrom = SH.escapeHtml(data.from);

  mailCard.innerHTML =
    '<h3>Inbox</h3>' +
    '<div class="sh-post">' +
    '<div class="sh-muted">From: ' + safeFrom + '</div>' +
    '<div class="sh-muted">To: ' + safeEmail + '</div>' +
    '<div style="font-weight:700; margin:6px 0;">' + safeSubject + '</div>' +
    '<p>' + safeBody + '</p>' +
    '<code style="display:block; background:#f5f5f5; padding:10px; border-radius:6px; word-break:break-all;">' +
    safeToken + '</code>' +
    '</div>';

  resetCard.classList.remove("sh-hidden");
  document.getElementById("resetToken").value = data.reset_token;
}

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("sh-mailbox-form");
  const emailInput = document.getElementById("mbEmail");

  const prefill = shQueryParam("email");
  if (prefill) {
    emailInput.value = prefill;
    shCheckInbox(prefill);
  }

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    shCheckInbox(emailInput.value.trim());
  });

  const resetForm = document.getElementById("sh-reset-form");
  const resetError = document.getElementById("sh-reset-error");
  const resetSuccess = document.getElementById("sh-reset-success");
  const resetBtn = document.getElementById("sh-reset-btn");

  resetForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    resetError.classList.add("sh-hidden");
    resetSuccess.classList.add("sh-hidden");
    resetBtn.disabled = true;

    try {
      // Existing, unmodified endpoint (app/routes/auth.py, ch11).
      await SH.apiFetch("/auth/reset-password/confirm", {
        method: "POST",
        body: JSON.stringify({
          token: document.getElementById("resetToken").value.trim(),
          new_password: document.getElementById("newPassword").value,
        }),
      });
      resetSuccess.textContent = "Password reset! You can log in with your new password now.";
      resetSuccess.classList.remove("sh-hidden");
    } catch (err) {
      SH.showError(resetError, err);
    } finally {
      resetBtn.disabled = false;
    }
  });
});
