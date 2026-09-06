document.addEventListener("DOMContentLoaded", () => {
  SH.requireAuth();

  const fileInput = document.getElementById("uploadFile");
  const filenameInput = document.getElementById("uploadFilename");
  const errorEl = document.getElementById("sh-error");
  const resultEl = document.getElementById("sh-upload-result");
  const viewResultEl = document.getElementById("sh-view-result");
  const form = document.getElementById("sh-upload-form");

  const SAFE_NAME = "hello.txt";
  // Matches Chapter 24's own worked example exactly: UPLOAD_FOLDER already
  // ends in "app/../uploads", so a single "../" cancels that back out to
  // the project root - "../INJECTED.txt" lands at <project_root>/INJECTED.txt,
  // outside uploads/ entirely, exactly per the book's arithmetic.
  const TRAVERSAL_NAME = "../INJECTED.txt";
  // Ch24 step 3: no extension allowlist, so a ".py" filename uploads with
  // zero resistance - proves the bug without needing the file to ever run
  // (the book is explicit that an uploaded .py here is never auto-executed).
  const UNRESTRICTED_TYPE_NAME = "shell.py";
  // Ch24 step 5: an SVG carrying an inline <script>. Proves the same
  // unrestricted-upload bug, and sets up the stored-XSS/XXE chain the
  // book describes IF this file is later served back with its real
  // image/svg+xml content-type - see the View button below.
  const SVG_NAME = "evil.svg";
  const SVG_CONTENT =
    '<svg xmlns="http://www.w3.org/2000/svg">\n' +
    "  <script>alert('XSS')</script>\n" +
    "</svg>";

  // Non-null only right after clicking "SVG example", where the content
  // itself (not just the filename) matters. A real picked file always
  // wins over this; picking one, or clicking any other example, clears it.
  let contentOverride = null;
  let lastObjectUrl = null;

  filenameInput.value = SAFE_NAME;

  // Picking a file suggests its own name as a starting point, but the
  // filename actually SENT stays whatever is in the text box below - not
  // necessarily the picked file's real name.
  fileInput.addEventListener("change", () => {
    if (fileInput.files[0] && filenameInput.value === SAFE_NAME) {
      filenameInput.value = fileInput.files[0].name;
    }
    contentOverride = null;
  });

  document.getElementById("sh-fill-safe").addEventListener("click", () => {
    filenameInput.value = SAFE_NAME;
    fileInput.value = "";
    contentOverride = null;
  });
  document.getElementById("sh-fill-traversal").addEventListener("click", () => {
    filenameInput.value = TRAVERSAL_NAME;
    fileInput.value = "";
    contentOverride = null;
  });
  document.getElementById("sh-fill-unrestricted").addEventListener("click", () => {
    filenameInput.value = UNRESTRICTED_TYPE_NAME;
    fileInput.value = "";
    contentOverride = null;
  });
  document.getElementById("sh-fill-svg").addEventListener("click", () => {
    filenameInput.value = SVG_NAME;
    fileInput.value = "";
    contentOverride = new Blob([SVG_CONTENT], { type: "image/svg+xml" });
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    errorEl.classList.add("sh-hidden");
    resultEl.classList.add("sh-hidden");

    const filename = filenameInput.value.trim();
    if (!filename) return;

    // No file picked? Fall back to an example's own content if one is
    // pending (SVG example), else a tiny synthesized text file so the
    // page still works with zero setup.
    const blob = fileInput.files[0] || contentOverride || new Blob(
      ["Hello from the SocialHack web UI upload demo.\n"],
      { type: "text/plain" }
    );

    const formData = new FormData();
    formData.append("file", blob, filename);

    try {
      // Plain fetch(), not SH.apiFetch(): a multipart body needs the
      // browser to set its own Content-Type (with boundary) - the JSON
      // Content-Type SH.apiFetch() always sends would break this upload.
      const token = SH.getToken();
      const res = await fetch(SH.API_BASE + "/upload/document", {
        method: "POST",
        headers: token ? { Authorization: "Bearer " + token } : {},
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) {
        throw Object.assign(new Error(data.error || `Request failed (${res.status})`), { body: data });
      }

      resultEl.innerHTML =
        '<div class="sh-post">' +
        '<div style="font-weight:700;">' + SH.escapeHtml(data.message) + '</div>' +
        '<div class="sh-muted" style="margin-top:6px;">Server-reported path: <code>' + SH.escapeHtml(data.path) + '</code></div>' +
        '<div class="sh-muted">Size: ' + SH.escapeHtml(data.size) + ' bytes</div>' +
        '<p class="sh-muted" style="margin-top:10px;">' +
        'Click "View / Open file" above (same box) to read this back through ' +
        'the API - the read side has the exact same unsanitized-path bug as ' +
        'this upload, so it can open a file that escaped uploads/ just as ' +
        'easily as one that did not.' +
        '</p>' +
        '</div>';
      resultEl.classList.remove("sh-hidden");
    } catch (err) {
      SH.showError(errorEl, err);
    }
  });

  document.getElementById("sh-view-btn").addEventListener("click", async () => {
    errorEl.classList.add("sh-hidden");
    viewResultEl.classList.add("sh-hidden");

    const path = filenameInput.value.trim();
    if (!path) return;

    try {
      // Plain fetch() again: the response here is a raw file, not JSON,
      // so SH.apiFetch()'s JSON parsing would not be the right shape.
      const token = SH.getToken();
      const res = await fetch(
        SH.API_BASE + "/upload/view?path=" + encodeURIComponent(path),
        { headers: token ? { Authorization: "Bearer " + token } : {} }
      );

      if (!res.ok) {
        let data = {};
        try { data = await res.json(); } catch (e) { /* non-JSON error body */ }
        throw Object.assign(new Error(data.error || `Request failed (${res.status})`), { body: data });
      }

      const blob = await res.blob();
      const contentType = blob.type || res.headers.get("Content-Type") || "";

      if (lastObjectUrl) URL.revokeObjectURL(lastObjectUrl);
      const objectUrl = URL.createObjectURL(blob);
      lastObjectUrl = objectUrl;

      let previewHtml = "";
      const isTextLike = contentType.startsWith("text/") || contentType.includes("xml") || contentType.includes("json") || contentType === "";
      if (isTextLike) {
        const text = await blob.text();
        previewHtml =
          '<div class="sh-muted" style="margin-top:10px;">Raw content:</div>' +
          '<pre style="background:#f5f5f5; padding:10px; border-radius:6px; overflow-x:auto; margin-top:4px; white-space:pre-wrap;">' +
          SH.escapeHtml(text) + '</pre>';
      }

      viewResultEl.innerHTML =
        '<div class="sh-post">' +
        '<div style="font-weight:700;">Fetched <code>' + SH.escapeHtml(path) + '</code></div>' +
        '<div class="sh-muted" style="margin-top:6px;">Content-Type: <code>' + SH.escapeHtml(contentType || "(unknown)") + '</code> - ' + blob.size + ' bytes</div>' +
        '<div style="margin-top:8px;"><a href="' + objectUrl + '" target="_blank" rel="noopener">Open in a new tab</a></div>' +
        previewHtml +
        '<p class="sh-muted" style="margin-top:10px;">' +
        'This came from <code>GET /api/v1/upload/view?path=...</code>, which joins ' +
        'your path onto the same upload folder with no traversal check - it can ' +
        'open anything the upload side can write to.' +
        '</p>' +
        '</div>';
      viewResultEl.classList.remove("sh-hidden");
    } catch (err) {
      SH.showError(errorEl, err);
    }
  });
});
