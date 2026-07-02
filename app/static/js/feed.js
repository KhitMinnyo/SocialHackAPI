document.addEventListener("DOMContentLoaded", () => {
  SH.requireAuth();

  const postsEl = document.getElementById("sh-posts");
  const errorEl = document.getElementById("sh-error");
  const form = document.getElementById("sh-new-post-form");
  const me = SH.getUser();

  function renderPost(post) {
    const isMine = me && post.user_id === me.id;
    const div = document.createElement("div");
    div.className = "sh-post";
    div.innerHTML = `
      <div class="sh-post-header">
        <div class="sh-avatar">${SH.escapeHtml(SH.initials(post.author))}</div>
        <div>
          <a href="/app/profile/${post.user_id}"><strong>${SH.escapeHtml(post.author || "unknown")}</strong></a>
          ${post.is_public ? "" : '<span class="sh-badge sh-badge-private">private</span>'}
          <div class="sh-muted">${SH.formatDate(post.created_at)}</div>
        </div>
      </div>
      <div class="sh-post-content">${SH.escapeHtml(post.content)}</div>
      <div class="sh-post-actions">
        <button class="sh-btn sh-btn-small sh-btn-outline" data-action="like" data-id="${post.id}">❤️ Like (${post.likes_count})</button>
        <a class="sh-btn sh-btn-small sh-btn-outline" href="/app/post/${post.id}">💬 Comments (${post.comments_count})</a>
        ${isMine ? `<button class="sh-btn sh-btn-small sh-btn-danger" data-action="delete" data-id="${post.id}">Delete</button>` : ""}
      </div>
    `;
    return div;
  }

  async function loadFeed() {
    try {
      const data = await SH.apiFetch("/posts?per_page=50");
      postsEl.innerHTML = "";
      if (!data.posts || data.posts.length === 0) {
        postsEl.innerHTML = '<p class="sh-muted">No posts yet. Be the first to post!</p>';
        return;
      }
      data.posts.forEach((post) => postsEl.appendChild(renderPost(post)));
    } catch (err) {
      SH.showError(errorEl, err);
    }
  }

  postsEl.addEventListener("click", async (e) => {
    const btn = e.target.closest("button[data-action]");
    if (!btn) return;
    const id = btn.getAttribute("data-id");
    const action = btn.getAttribute("data-action");

    try {
      if (action === "like") {
        await SH.apiFetch(`/posts/${id}/like`, { method: "POST" });
        loadFeed();
      } else if (action === "delete") {
        if (!confirm("Delete this post?")) return;
        await SH.apiFetch(`/posts/${id}`, { method: "DELETE" });
        loadFeed();
      }
    } catch (err) {
      SH.showError(errorEl, err);
    }
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    errorEl.classList.add("sh-hidden");
    const content = document.getElementById("sh-post-content").value.trim();
    const isPublic = document.getElementById("sh-post-public").checked;
    if (!content) return;

    try {
      await SH.apiFetch("/posts", {
        method: "POST",
        body: JSON.stringify({ content, is_public: isPublic }),
      });
      document.getElementById("sh-post-content").value = "";
      loadFeed();
    } catch (err) {
      SH.showError(errorEl, err);
    }
  });

  loadFeed();
});
