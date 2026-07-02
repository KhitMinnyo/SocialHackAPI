document.addEventListener("DOMContentLoaded", () => {
  if (SH.isLoggedIn()) {
    window.location.replace("/app/feed");
    return;
  }

  const form = document.getElementById("sh-login-form");
  const errorEl = document.getElementById("sh-error");
  const btn = document.getElementById("sh-login-btn");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    errorEl.classList.add("sh-hidden");
    btn.disabled = true;
    btn.textContent = "Logging in...";

    const payload = {
      username: document.getElementById("username").value.trim(),
      password: document.getElementById("password").value,
    };

    try {
      const data = await SH.apiFetch("/auth/login", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      SH.setSession(data.token, data.user);
      window.location.href = "/app/profile/" + data.user.id;
    } catch (err) {
      SH.showError(errorEl, err);
      btn.disabled = false;
      btn.textContent = "Log in";
    }
  });
});
