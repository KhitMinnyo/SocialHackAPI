document.addEventListener("DOMContentLoaded", () => {
  SH.requireAuth();

  const gridEl = document.getElementById("sh-avatar-grid");
  const errorEl = document.getElementById("sh-error");
  const resultEl = document.getElementById("sh-avatar-result");

  // 5 built-in presets, same-origin so the demo works with zero setup -
  // same reasoning as exchange-rate.js's mock provider URL. Built from
  // window.location.origin (not hardcoded) so it still works if the
  // lab's host/port ever changes.
  const PRESETS = [1, 2, 3, 4, 5].map(
    (n) => window.location.origin + "/static/mock-partner/avatars/" + n + ".png"
  );

  // url -> Blob, so a chosen avatar's confirmation preview can reuse the
  // exact bytes already fetched for its thumbnail instead of fetching
  // (and thereby re-displaying) a URL a second time.
  const blobCache = new Map();
  let lastPreviewUrl = null;

  async function loadThumbnail(url, imgEl) {
    try {
      const res = await fetch(url);
      const blob = await res.blob();
      blobCache.set(url, blob);
      imgEl.src = URL.createObjectURL(blob);
    } catch (err) {
      imgEl.alt = "failed to load";
    }
  }

  function renderGrid() {
    gridEl.innerHTML = "";
    PRESETS.forEach((url, i) => {
      const tile = document.createElement("button");
      tile.type = "button";
      tile.className = "sh-btn sh-btn-outline";
      tile.style.cssText =
        "padding:10px; display:flex; flex-direction:column; align-items:center; gap:8px; width:100px;";

      const img = document.createElement("img");
      img.width = 72;
      img.height = 72;
      img.style.cssText = "border-radius:50%; object-fit:cover; background:#eee;";
      img.alt = "Avatar option " + (i + 1);

      const label = document.createElement("span");
      label.textContent = "Option " + (i + 1);
      label.style.fontSize = "0.85em";

      tile.appendChild(img);
      tile.appendChild(label);
      tile.addEventListener("click", () => selectAvatar(url, tile));
      gridEl.appendChild(tile);

      loadThumbnail(url, img);
    });
  }

  async function selectAvatar(url, tile) {
    errorEl.classList.add("sh-hidden");
    resultEl.classList.add("sh-hidden");
    gridEl.querySelectorAll("button").forEach((b) => (b.disabled = true));

    try {
      const data = await SH.apiFetch("/upload/avatar", {
        method: "POST",
        body: JSON.stringify({ url: url }),
      });

      // Reuse the bytes already fetched for this preset's thumbnail
      // instead of loading data.avatar_url - that keeps every URL
      // involved (the preset source AND the resulting local path) out
      // of the page's visible text and out of any <img src> attribute.
      const cached = blobCache.get(url);
      if (lastPreviewUrl) URL.revokeObjectURL(lastPreviewUrl);
      lastPreviewUrl = cached ? URL.createObjectURL(cached) : null;

      resultEl.innerHTML =
        '<div class="sh-post" style="display:flex; align-items:center; gap:14px;">' +
        (lastPreviewUrl
          ? '<img src="' + lastPreviewUrl + '" width="64" height="64" style="border-radius:50%; object-fit:cover;">'
          : "") +
        '<div>' +
        '<div style="font-weight:700;">' + SH.escapeHtml(data.message || "Avatar updated!") + '</div>' +
        '<div class="sh-muted" style="margin-top:4px;">Content-Type: ' + SH.escapeHtml(data.content_type) +
        ' &middot; ' + data.size + ' bytes</div>' +
        '</div></div>';
      resultEl.classList.remove("sh-hidden");
    } catch (err) {
      SH.showError(errorEl, err);
    } finally {
      gridEl.querySelectorAll("button").forEach((b) => (b.disabled = false));
    }
  }

  renderGrid();
});
