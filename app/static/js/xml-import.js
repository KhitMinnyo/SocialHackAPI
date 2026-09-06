document.addEventListener("DOMContentLoaded", () => {
  SH.requireAuth();

  const bodyInput = document.getElementById("xmlBody");
  const errorEl = document.getElementById("sh-error");
  const resultEl = document.getElementById("sh-xml-result");
  const form = document.getElementById("sh-xml-form");

  const SAFE_XML =
    "<profile>\n" +
    "  <username>alice_updated</username>\n" +
    "  <bio>Just a regular profile bio update.</bio>\n" +
    "</profile>";

  // Same canonical payload shape as the endpoint's own docstring: a
  // <!DOCTYPE> declares an external entity reading a file off the
  // server's disk, and <username> uses that entity instead of a normal
  // string. <bio> is left as an ordinary value on purpose, to show that
  // only the field using the entity is affected - everything else keeps
  // working exactly like it looks like it should.
  const XXE_XML =
    '<!DOCTYPE profile [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>\n' +
    "<profile>\n" +
    "  <username>&xxe;</username>\n" +
    "  <bio>This field is untouched - only username uses the entity.</bio>\n" +
    "</profile>";

  bodyInput.value = SAFE_XML;

  document.getElementById("sh-fill-safe").addEventListener("click", () => {
    bodyInput.value = SAFE_XML;
  });
  document.getElementById("sh-fill-xxe").addEventListener("click", () => {
    bodyInput.value = XXE_XML;
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    errorEl.classList.add("sh-hidden");
    resultEl.classList.add("sh-hidden");

    const xml = bodyInput.value;
    if (!xml.trim()) return;

    try {
      // Plain fetch(), not SH.apiFetch(): the body here is raw XML, not
      // JSON, and SH.apiFetch() always forces a JSON Content-Type - which
      // would make the server see the wrong body type entirely.
      const token = SH.getToken();
      const headers = { "Content-Type": "application/xml" };
      if (token) headers.Authorization = "Bearer " + token;

      const res = await fetch(SH.API_BASE + "/integrations/xml-import", {
        method: "POST",
        headers,
        body: xml,
      });
      const data = await res.json();
      if (!res.ok) {
        throw Object.assign(new Error(data.error || `Request failed (${res.status})`), { body: data });
      }

      resultEl.innerHTML =
        '<div class="sh-post">' +
        '<div style="font-weight:700;">' + SH.escapeHtml(data.message) + '</div>' +
        '<div class="sh-muted" style="margin-top:10px;">username:</div>' +
        '<pre style="background:#f5f5f5; padding:10px; border-radius:6px; overflow-x:auto; margin-top:4px; white-space:pre-wrap;">' +
        SH.escapeHtml(data.username) + '</pre>' +
        '<div class="sh-muted" style="margin-top:10px;">bio:</div>' +
        '<pre style="background:#f5f5f5; padding:10px; border-radius:6px; overflow-x:auto; margin-top:4px; white-space:pre-wrap;">' +
        SH.escapeHtml(data.bio) + '</pre>' +
        '<p class="sh-muted" style="margin-top:10px;">' +
        'If the request used the XXE example, the "username" text above is not ' +
        'really a username - it is the real content of a file read off the ' +
        "server's own disk when the XML was parsed." +
        '</p>' +
        '</div>';
      resultEl.classList.remove("sh-hidden");
    } catch (err) {
      SH.showError(errorEl, err);
    }
  });
});
