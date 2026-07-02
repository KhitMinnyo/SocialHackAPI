/**
 * Admin dashboard. NOTE: the "Admin" nav link is only shown when the
 * locally-stored user object has role === "admin" (see app.js renderNav).
 * That is a purely cosmetic, client-side check. This page - and the real
 * /api/v1/admin/* endpoints it calls - perform NO server-side admin check
 * of their own (see app/routes/admin.py: every route there uses
 * @token_required, not @admin_required). Any logged-in user who simply
 * types /app/admin into the URL bar will see this exact page work.
 */
document.addEventListener("DOMContentLoaded", () => {
  SH.requireAuth();

  const statsEl = document.getElementById("sh-stats");
  const tbody = document.getElementById("sh-users-tbody");
  const errorEl = document.getElementById("sh-error");
  const me = SH.getUser();

  async function loadStats() {
    try {
      const stats = await SH.apiFetch("/admin/stats");
      statsEl.innerHTML = `
        <div class="sh-stats" style="flex-wrap:wrap;">
          <span><b>${stats.total_users}</b> users</span>
          <span><b>${stats.total_posts}</b> posts</span>
          <span><b>${stats.total_comments}</b> comments</span>
          <span><b>${stats.total_messages}</b> messages</span>
          <span><b>${stats.total_likes}</b> likes</span>
          <span><b>${stats.admin_users}</b> admins</span>
          <span><b>${stats.moderator_users}</b> moderators</span>
          <span><b>${stats.verified_users}</b> verified</span>
        </div>
      `;
    } catch (err) {
      statsEl.innerHTML = "";
      SH.showError(errorEl, err);
    }
  }

  function renderRow(user) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${user.id}</td>
      <td><a href="/app/profile/${user.id}">${SH.escapeHtml(user.username)}</a></td>
      <td>${SH.escapeHtml(user.email)}</td>
      <td>
        <select class="sh-input" data-role-select data-id="${user.id}" style="padding:4px;">
          <option value="user" ${user.role === "user" ? "selected" : ""}>user</option>
          <option value="moderator" ${user.role === "moderator" ? "selected" : ""}>moderator</option>
          <option value="admin" ${user.role === "admin" ? "selected" : ""}>admin</option>
        </select>
      </td>
      <td>${user.is_verified ? "✅" : "—"}</td>
      <td>
        <button class="sh-btn sh-btn-small sh-btn-outline" data-action="save-role" data-id="${user.id}">Save role</button>
        <button class="sh-btn sh-btn-small sh-btn-danger" data-action="delete-user" data-id="${user.id}" ${user.id === (me && me.id) ? "disabled" : ""}>Delete</button>
      </td>
    `;
    return tr;
  }

  async function loadUsers() {
    try {
      const data = await SH.apiFetch("/admin/users");
      tbody.innerHTML = "";
      (data.users || []).forEach((u) => tbody.appendChild(renderRow(u)));
    } catch (err) {
      tbody.innerHTML = "";
      SH.showError(errorEl, err);
    }
  }

  tbody.addEventListener("click", async (e) => {
    const btn = e.target.closest("button[data-action]");
    if (!btn) return;
    const id = btn.getAttribute("data-id");
    const action = btn.getAttribute("data-action");

    try {
      if (action === "save-role") {
        const select = tbody.querySelector(`select[data-role-select][data-id="${id}"]`);
        await SH.apiFetch(`/admin/users/${id}/role`, {
          method: "PUT",
          body: JSON.stringify({ role: select.value }),
        });
        loadUsers();
      } else if (action === "delete-user") {
        if (!confirm("Delete this user?")) return;
        await SH.apiFetch(`/admin/users/${id}`, { method: "DELETE" });
        loadUsers();
      }
    } catch (err) {
      SH.showError(errorEl, err);
    }
  });

  loadStats();
  loadUsers();
});
