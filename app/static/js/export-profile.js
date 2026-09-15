document.addEventListener("DOMContentLoaded", () => {
  SH.requireAuth();

  const btn = document.getElementById("sh-export-btn");
  const errorEl = document.getElementById("sh-error");
  const resultEl = document.getElementById("sh-export-result");

  let lastObjectUrl = null;

  btn.addEventListener("click", async () => {
    errorEl.classList.add("sh-hidden");
    resultEl.classList.add("sh-hidden");
    btn.disabled = true;

    try {
      const data = await SH.apiFetch("/export/profile");

      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      if (lastObjectUrl) URL.revokeObjectURL(lastObjectUrl);
      lastObjectUrl = URL.createObjectURL(blob);

      resultEl.innerHTML =
        '<div class="sh-post">' +
        '<div style="font-weight:700;">Your data is ready.</div>' +
        '<div style="margin-top:8px;"><a href="' + lastObjectUrl + '" download="socialhack-export.json">Download JSON file</a></div>' +
        '</div>';
      resultEl.classList.remove("sh-hidden");
    } catch (err) {
      SH.showError(errorEl, err);
    } finally {
      btn.disabled = false;
    }
  });
});
