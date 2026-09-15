document.addEventListener("DOMContentLoaded", () => {
  SH.requireAuth();

  const container = document.querySelector("[data-conversation-user-id]");
  const rawConvId = container.getAttribute("data-conversation-user-id");
  const conversationUserId = rawConvId ? parseInt(rawConvId, 10) : null;
  const errorEl = document.getElementById("sh-error");
  const me = SH.getUser();

  if (conversationUserId) {
    initConversation(conversationUserId);
  } else {
    initInbox();
  }

  // ---- Conversation view ----
  async function initConversation(otherUserId) {
    const listEl = document.getElementById("sh-conversation-messages");
    const titleEl = document.getElementById("sh-conversation-title");
    const form = document.getElementById("sh-reply-form");

    async function loadConversation() {
      try {
        const data = await SH.apiFetch(`/messages/conversation/${otherUserId}`);
        titleEl.textContent = "Conversation with " + data.conversation_with;
        listEl.innerHTML = "";
        (data.messages || []).forEach((m) => {
          const isMine = me && m.sender_id === me.id;
          const bubble = document.createElement("div");
          bubble.className = "sh-bubble " + (isMine ? "sh-bubble-me" : "sh-bubble-them");
          bubble.textContent = m.content;
          listEl.appendChild(bubble);
        });
        listEl.scrollTop = listEl.scrollHeight;
      } catch (err) {
        SH.showError(errorEl, err);
      }
    }

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const input = document.getElementById("sh-reply-content");
      const content = input.value.trim();
      if (!content) return;
      try {
        await SH.apiFetch("/messages", {
          method: "POST",
          body: JSON.stringify({ recipient_id: otherUserId, content }),
        });
        input.value = "";
        loadConversation();
      } catch (err) {
        SH.showError(errorEl, err);
      }
    });

    loadConversation();
  }

  // ---- Inbox view: one row per conversation, Messenger-style ----
  function initInbox() {
    const listEl = document.getElementById("sh-message-list");

    function renderRow(c) {
      const row = document.createElement("a");
      row.href = `/app/messages/conversation/${c.otherId}`;
      row.className = "sh-msg-row" + (c.hasUnread ? " unread" : "");
      row.style.display = "flex";
      row.innerHTML = `
        <span><strong>${SH.escapeHtml(c.otherUsername || "unknown")}</strong> - ${SH.escapeHtml(c.lastContent).slice(0, 60)}</span>
        <span class="sh-muted">${SH.formatDate(c.lastCreatedAt)}</span>
      `;
      return row;
    }

    // Folds /messages/inbox and /messages/sent into a single list of
    // conversations, one row per other user, keeping only the most
    // recent message with each person - like a real messenger inbox,
    // not a raw per-message log split into two tabs.
    function touch(byUser, otherId, otherUsername, message, unread) {
      const existing = byUser.get(otherId);
      const isNewer = !existing || new Date(message.created_at) > new Date(existing.lastCreatedAt);
      byUser.set(otherId, {
        otherId,
        otherUsername: isNewer ? otherUsername : existing.otherUsername,
        lastContent: isNewer ? message.content : existing.lastContent,
        lastCreatedAt: isNewer ? message.created_at : existing.lastCreatedAt,
        hasUnread: (existing && existing.hasUnread) || unread,
      });
    }

    async function loadConversations() {
      listEl.innerHTML = '<p class="sh-muted">Loading...</p>';
      try {
        const [inboxData, sentData] = await Promise.all([
          SH.apiFetch("/messages/inbox"),
          SH.apiFetch("/messages/sent"),
        ]);

        const byUser = new Map();
        (inboxData.messages || []).forEach((m) => {
          touch(byUser, m.sender_id, m.sender, m, !m.is_read);
        });
        (sentData.messages || []).forEach((m) => {
          touch(byUser, m.recipient_id, m.recipient, m, false);
        });

        const conversations = Array.from(byUser.values()).sort(
          (a, b) => new Date(b.lastCreatedAt) - new Date(a.lastCreatedAt)
        );

        listEl.innerHTML = "";
        if (conversations.length === 0) {
          listEl.innerHTML = '<p class="sh-muted">No conversations yet.</p>';
          return;
        }
        conversations.forEach((c) => listEl.appendChild(renderRow(c)));
      } catch (err) {
        SH.showError(errorEl, err);
      }
    }

    loadConversations();
  }
});
