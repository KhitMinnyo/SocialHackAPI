document.addEventListener("DOMContentLoaded", () => {
  SH.requireAuth();

  const fileInput = document.getElementById("uploadFile");
  const filenameInput = document.getElementById("uploadFilename");
  const errorEl = document.getElementById("sh-error");
  const resultEl = document.getElementById("sh-upload-result");
  const form = document.getElementById("sh-upload-form");

  const SAFE_NAME = "hello.txt";
  // One "../" walks up from the uploads/ folder to the project root -
  // "app/" is a real, existing directory from there, so this actually
  // lands the file inside the app package instead of erroring out.
  const TRAVERSAL_NAME = "../app/INJECTED_via_web_ui.txt";

  filenameInput.value = SAFE_NAME;

  // Picking a file suggests its own name as a starting point, but the
  // filename actually SENT stays whatever is in the text box below - not
  // necessarily the picked file's real name.
  fileInput.addEventListener("change", () => {
    if (fileInput.files[0] && filenameInput.value === SAFE_NAME) {
      filenameInput.value = fileInput.files[0].name;
    }
  });

  document.getElementById("sh-fill-safe").addEventListener("click", () => {
    filenameInput.value = SAFE_NAME;
  });
  document.getElementById("sh-fill-traversal").addEventListener("click", () => {
    filenameInput.value = TRAVERSAL_NAME;
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    errorEl.classList.add("sh-hidden");
    resultEl.classList.add("sh-hidden");

    const filename = filenameInput.value.trim();
    if (!filename) return;

    // No file picked? Use a tiny synthesized text file so the page still
    // works with zero setup.
    const blob = fileInput.files[0] || new Blob(
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
        'If the filename above contained <code>../</code>, this really wrote outside ' +
        'the uploads/ folder on disk - there is no route serving files back in this ' +
        'lab, so check the project folder directly to confirm where it landed.' +
        '</p>' +
        '</div>';
      resultEl.classList.remove("sh-hidden");
    } catch (err) {
      SH.showError(errorEl, err);
    }
  });
});
