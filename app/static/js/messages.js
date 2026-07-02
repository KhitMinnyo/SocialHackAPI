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

  // ---- Inbox / Sent view ----
  function initInbox() {
    const listEl = document.getElementById("sh-message-list");
    const tabs = document.querySelectorAll(".sh-tab");
    const newMessageForm = document.getElementById("sh-new-message-form");
    let currentTab = "inbox";

    function renderRow(m, direction) {
      const otherUsername = direction === "inbox" ? m.sender : m.recipient;
      const otherUserId = direction === "inbox" ? m.sender_id : m.recipient_id;
      const row = document.createElement("a");
      row.href = `/app/messages/conversation/${otherUserId}`;
      row.className = "sh-msg-row" + (direction === "inbox" && !m.is_read ? " unread" : "");
      row.style.display = "flex";
      row.innerHTML = `
        <span>${direction === "inbox" ? "From" : "To"}: <strong>${SH.escapeHtml(otherUsername || "unknown")}</strong> - ${SH.escapeHtml(m.content).slice(0, 60)}</span>
        <span class="sh-muted">${SH.formatDate(m.created_at)}</span>
      `;
      return row;
    }

    async function loadTab(tab) {
      currentTab = tab;
      listEl.innerHTML = '<p class="sh-muted">Loading...</p>';
      try {
        const data = await SH.apiFetch(tab === "inbox" ? "/messages/inbox" : "/messages/sent");
        listEl.innerHTML = "";
        const messages = data.messages || [];
        if (messages.length === 0) {
          listEl.innerHTML = '<p class="sh-muted">Nothing here yet.</p>';
          return;
        }
        messages.forEach((m) => listEl.appendChild(renderRow(m, tab)));
      } catch (err) {
        SH.showError(errorEl, err);
      }
    }

    tabs.forEach((tab) => {
      tab.addEventListener("click", () => {
        tabs.forEach((t) => t.classList.remove("active"));
        tab.classList.add("active");
        loadTab(tab.getAttribute("data-tab"));
      });
    });

    newMessageForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const recipientId = parseInt(document.getElementById("sh-recipient-id").value, 10);
      const content = document.getElementById("sh-new-message-content").value.trim();
      if (!recipientId || !content) return;
      try {
        await SH.apiFetch("/messages", {
          method: "POST",
          body: JSON.stringify({ recipient_id: recipientId, content }),
        });
        document.getElementById("sh-new-message-content").value = "";
        loadTab(currentTab);
      } catch (err) {
        SH.showError(errorEl, err);
      }
    });

    loadTab("inbox");
  }
});
