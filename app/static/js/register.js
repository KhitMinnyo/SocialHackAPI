document.addEventListener("DOMContentLoaded", () => {
  if (SH.isLoggedIn()) {
    window.location.replace("/app/feed");
    return;
  }

  const form = document.getElementById("sh-register-form");
  const errorEl = document.getElementById("sh-error");
  const btn = document.getElementById("sh-register-btn");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    errorEl.classList.add("sh-hidden");
    btn.disabled = true;
    btn.textContent = "Signing up...";

    const payload = {
      username: document.getElementById("username").value.trim(),
      email: document.getElementById("email").value.trim(),
      password: document.getElementById("password").value,
      bio: document.getElementById("bio").value,
    };

    try {
      const data = await SH.apiFetch("/auth/register", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      SH.setSession(data.token, data.user);
      window.location.href = "/app/profile/" + data.user.id;
    } catch (err) {
      SH.showError(errorEl, err);
      btn.disabled = false;
      btn.textContent = "Sign up";
    }
  });
});
