document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("sh-forgot-form");
  const errorEl = document.getElementById("sh-error");
  const successEl = document.getElementById("sh-success");
  const inboxLinkEl = document.getElementById("sh-inbox-link");
  const btn = document.getElementById("sh-forgot-btn");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    errorEl.classList.add("sh-hidden");
    successEl.classList.add("sh-hidden");
    inboxLinkEl.innerHTML = "";
    btn.disabled = true;
    btn.textContent = "Sending...";

    const email = document.getElementById("email").value.trim();

    try {
      // Existing, unmodified endpoint (app/routes/auth.py, ch11).
      await SH.apiFetch("/auth/reset-password", {
        method: "POST",
        body: JSON.stringify({ email }),
      });

      successEl.textContent = "Reset email sent (SocialHack doesn't send real mail in this lab).";
      successEl.classList.remove("sh-hidden");

      inboxLinkEl.innerHTML =
        '<a class="sh-btn" style="margin-top:10px; display:inline-block;" href="/app/mailbox?email=' +
        encodeURIComponent(email) + '">📧 Open inbox (lab only)</a>';
    } catch (err) {
      SH.showError(errorEl, err);
    } finally {
      btn.disabled = false;
      btn.textContent = "Send reset email";
    }
  });
});
