document.addEventListener("DOMContentLoaded", () => {
  SH.requireAuth();

  const statusEl = document.getElementById("sh-status");
  const errorEl = document.getElementById("sh-error");
  const resultEl = document.getElementById("sh-apply-result");

  function renderStatus(data) {
    let body;
    if (data.already_verified) {
      body =
        '<div class="sh-post">' +
        '<div style="font-weight:700;">&#9989; @' + SH.escapeHtml(data.username) + ' is already verified.</div>' +
        '</div>';
    } else {
      body =
        '<div class="sh-post">' +
        '<div><b>' + data.followers_count + '</b> / ' + data.required_followers + ' followers</div>' +
        '<div class="sh-muted" style="margin-top:4px;">' +
        (data.eligible
          ? "You meet the follower threshold - you can apply now."
          : "Not enough followers yet.") +
        '</div>' +
        '<button class="sh-btn" id="sh-apply-btn" style="margin-top:10px;"' +
        (data.eligible ? "" : " disabled") + '>Apply for verified badge</button>' +
        '</div>';
    }
    statusEl.innerHTML = body;

    const btn = document.getElementById("sh-apply-btn");
    if (btn) btn.addEventListener("click", applyForBadge);
  }

  async function loadEligibility() {
    try {
      const data = await SH.apiFetch("/promotions/verification/eligibility");
      renderStatus(data);
    } catch (err) {
      statusEl.innerHTML = "";
      SH.showError(errorEl, err);
    }
  }

  async function applyForBadge() {
    errorEl.classList.add("sh-hidden");
    resultEl.classList.add("sh-hidden");
    try {
      const data = await SH.apiFetch("/promotions/verification/apply", { method: "POST" });
      resultEl.innerHTML =
        '<div class="sh-post">' +
        '<div style="font-weight:700;">&#127881; ' + SH.escapeHtml(data.message) + '</div>' +
        '</div>';
      resultEl.classList.remove("sh-hidden");
      loadEligibility();
    } catch (err) {
      SH.showError(errorEl, err);
    }
  }

  loadEligibility();
});
