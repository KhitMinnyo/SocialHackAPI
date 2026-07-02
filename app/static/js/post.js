document.addEventListener("DOMContentLoaded", () => {
  SH.requireAuth();

  const container = document.querySelector("[data-post-id]");
  const postId = container.getAttribute("data-post-id");
  const postCard = document.getElementById("sh-post-card");
  const commentsEl = document.getElementById("sh-comments");
  const errorEl = document.getElementById("sh-error");
  const form = document.getElementById("sh-comment-form");
  const me = SH.getUser();

  function renderPostCard(post) {
    const isMine = me && post.user_id === me.id;
    postCard.innerHTML = `
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
        <button class="sh-btn sh-btn-small sh-btn-outline" id="sh-like-btn">❤️ Like (${post.likes_count})</button>
        ${isMine ? `<button class="sh-btn sh-btn-small sh-btn-danger" id="sh-delete-post-btn">Delete post</button>` : ""}
      </div>
    `;

    document.getElementById("sh-like-btn").addEventListener("click", async () => {
      try {
        await SH.apiFetch(`/posts/${postId}/like`, { method: "POST" });
        loadPost();
      } catch (err) {
        SH.showError(errorEl, err);
      }
    });

    const deleteBtn = document.getElementById("sh-delete-post-btn");
    if (deleteBtn) {
      deleteBtn.addEventListener("click", async () => {
        if (!confirm("Delete this post?")) return;
        try {
          await SH.apiFetch(`/posts/${postId}`, { method: "DELETE" });
          window.location.href = "/app/feed";
        } catch (err) {
          SH.showError(errorEl, err);
        }
      });
    }
  }

  function renderComment(comment) {
    const isMine = me && comment.user_id === me.id;
    const div = document.createElement("div");
    div.className = "sh-comment";
    div.innerHTML = `
      <a href="/app/profile/${comment.user_id}"><strong>${SH.escapeHtml(comment.author || "unknown")}</strong></a>
      <span class="sh-muted">· ${SH.formatDate(comment.created_at)}</span>
      ${isMine ? `<button class="sh-btn sh-btn-small sh-btn-danger" style="float:right;" data-action="delete-comment" data-id="${comment.id}">Delete</button>` : ""}
      <div>${SH.escapeHtml(comment.content)}</div>
    `;
    return div;
  }

  async function loadPost() {
    try {
      const data = await SH.apiFetch(`/posts/${postId}`);
      renderPostCard(data.post);
    } catch (err) {
      postCard.innerHTML = "";
      SH.showError(errorEl, err);
    }
  }

  async function loadComments() {
    try {
      const data = await SH.apiFetch(`/posts/${postId}/comments`);
      commentsEl.innerHTML = "";
      if (!data.comments || data.comments.length === 0) {
        commentsEl.innerHTML = '<p class="sh-muted">No comments yet.</p>';
        return;
      }
      data.comments.forEach((c) => commentsEl.appendChild(renderComment(c)));
    } catch (err) {
      SH.showError(errorEl, err);
    }
  }

  commentsEl.addEventListener("click", async (e) => {
    const btn = e.target.closest('button[data-action="delete-comment"]');
    if (!btn) return;
    if (!confirm("Delete this comment?")) return;
    try {
      await SH.apiFetch(`/comments/${btn.getAttribute("data-id")}`, { method: "DELETE" });
      loadComments();
    } catch (err) {
      SH.showError(errorEl, err);
    }
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    errorEl.classList.add("sh-hidden");
    const content = document.getElementById("sh-comment-content").value.trim();
    if (!content) return;
    try {
      await SH.apiFetch(`/posts/${postId}/comments`, {
        method: "POST",
        body: JSON.stringify({ content }),
      });
      document.getElementById("sh-comment-content").value = "";
      loadComments();
      loadPost();
    } catch (err) {
      SH.showError(errorEl, err);
    }
  });

  loadPost();
  loadComments();
});
