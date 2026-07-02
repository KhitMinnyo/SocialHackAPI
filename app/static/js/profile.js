document.addEventListener("DOMContentLoaded", () => {
  SH.requireAuth();

  const container = document.querySelector("[data-user-id]");
  const userId = parseInt(container.getAttribute("data-user-id"), 10);
  const headerEl = document.getElementById("sh-profile-header");
  const editCard = document.getElementById("sh-edit-card");
  const editForm = document.getElementById("sh-edit-form");
  const postsEl = document.getElementById("sh-user-posts");
  const errorEl = document.getElementById("sh-error");
  const me = SH.getUser();
  const isOwnProfile = me && me.id === userId;

  let followState = { isFollowing: false, followersCount: 0, followingCount: 0 };

  function badge(text, cls) {
    return `<span class="sh-badge ${cls}">${SH.escapeHtml(text)}</span>`;
  }

  function renderHeader(user) {
    let badges = "";
    if (user.is_verified) badges += badge("verified", "sh-badge-verified");
    if (user.role && user.role !== "user") badges += badge(user.role, "sh-badge-role");
    if (user.is_private) badges += badge("private", "sh-badge-private");

    headerEl.innerHTML = `
      <div class="sh-profile-header">
        <div class="sh-avatar">${SH.escapeHtml(SH.initials(user.username))}</div>
        <div>
          <h2 style="margin:0;">${SH.escapeHtml(user.username)} ${badges}</h2>
          <div class="sh-muted">Joined ${SH.formatDate(user.created_at)}</div>
        </div>
        <div style="margin-left:auto;" id="sh-profile-action"></div>
      </div>
      <p>${SH.escapeHtml(user.bio || "")}</p>
      <div class="sh-stats">
        <span><b id="sh-followers-count">${followState.followersCount}</b> followers</span>
        <span><b id="sh-following-count">${followState.followingCount}</b> following</span>
      </div>
    `;

    const actionEl = document.getElementById("sh-profile-action");
    if (isOwnProfile) {
      const editBtn = document.createElement("button");
      editBtn.className = "sh-btn sh-btn-outline sh-btn-small";
      editBtn.textContent = "Edit profile";
      editBtn.addEventListener("click", () => {
        document.getElementById("edit-bio").value = user.bio || "";
        document.getElementById("edit-pic").value = user.profile_pic || "";
        document.getElementById("edit-private").checked = !!user.is_private;
        editCard.classList.remove("sh-hidden");
      });
      actionEl.appendChild(editBtn);
    } else {
      const followBtn = document.createElement("button");
      followBtn.className = "sh-btn sh-btn-small";
      followBtn.id = "sh-follow-btn";
      updateFollowButton(followBtn);
      followBtn.addEventListener("click", async () => {
        try {
          const endpoint = followState.isFollowing ? "unfollow" : "follow";
          await SH.apiFetch(`/users/${userId}/${endpoint}`, { method: "POST" });
          followState.isFollowing = !followState.isFollowing;
          updateFollowButton(followBtn);
          loadFollowCounts();
        } catch (err) {
          SH.showError(errorEl, err);
        }
      });
      actionEl.appendChild(followBtn);
    }
  }

  function updateFollowButton(btn) {
    if (followState.isFollowing) {
      btn.textContent = "Unfollow";
      btn.classList.remove("sh-btn-outline");
    } else {
      btn.textContent = "Follow";
      btn.classList.add("sh-btn-outline");
    }
  }

  function renderPostRow(post) {
    const div = document.createElement("div");
    div.className = "sh-post";
    div.innerHTML = `
      <a href="/app/post/${post.id}"><div class="sh-post-content">${SH.escapeHtml(post.content)}</div></a>
      <div class="sh-muted">${SH.formatDate(post.created_at)} · ❤️ ${post.likes_count} · 💬 ${post.comments_count}
      ${post.is_public ? "" : "· private"}</div>
    `;
    return div;
  }

  async function loadProfile() {
    try {
      const data = await SH.apiFetch(`/users/${userId}`);
      renderHeader(data.user);
    } catch (err) {
      headerEl.innerHTML = "";
      SH.showError(errorEl, err);
    }
  }

  async function loadFollowCounts() {
    try {
      const [followers, following] = await Promise.all([
        SH.apiFetch(`/users/${userId}/followers`),
        SH.apiFetch(`/users/${userId}/following`),
      ]);
      followState.followersCount = followers.followers_count;
      followState.followingCount = following.following_count;
      followState.isFollowing = me
        ? followers.followers.some((f) => f.id === me.id)
        : false;

      const fEl = document.getElementById("sh-followers-count");
      const gEl = document.getElementById("sh-following-count");
      if (fEl) fEl.textContent = followState.followersCount;
      if (gEl) gEl.textContent = followState.followingCount;
      const followBtn = document.getElementById("sh-follow-btn");
      if (followBtn) updateFollowButton(followBtn);
    } catch (err) {
      // Non-fatal - profile header still renders without counts.
    }
  }

  async function loadUserPosts() {
    try {
      const data = await SH.apiFetch(`/posts?per_page=100`);
      const userPosts = (data.posts || []).filter((p) => p.user_id === userId);
      postsEl.innerHTML = "";
      if (userPosts.length === 0) {
        postsEl.innerHTML = '<p class="sh-muted">No posts yet.</p>';
        return;
      }
      userPosts.forEach((p) => postsEl.appendChild(renderPostRow(p)));
    } catch (err) {
      SH.showError(errorEl, err);
    }
  }

  editForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    errorEl.classList.add("sh-hidden");
    try {
      await SH.apiFetch(`/users/${userId}`, {
        method: "PUT",
        body: JSON.stringify({
          bio: document.getElementById("edit-bio").value,
          profile_pic: document.getElementById("edit-pic").value,
          is_private: document.getElementById("edit-private").checked,
        }),
      });
      editCard.classList.add("sh-hidden");
      loadProfile();
    } catch (err) {
      SH.showError(errorEl, err);
    }
  });

  loadProfile();
  loadFollowCounts();
  loadUserPosts();
});
