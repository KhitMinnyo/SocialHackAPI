# Lab: nuclei — Custom Template Scanning

## Overview

| Field          | Details                                               |
|----------------|-------------------------------------------------------|
| **Objective**  | Write and run custom nuclei templates against SocialHack API's own vulnerabilities |
| **Difficulty** | ⭐⭐ Medium                                           |
| **Time**       | 40 minutes                                            |
| **Category**   | Reconnaissance / Tooling                                |
| **OWASP**      | API9:2023 - Improper Inventory Management (info disclosure detection) |

---

## Prerequisites

- A running instance of **SocialHack API** at `http://localhost:5001`
- `nuclei` installed (`go install ... nuclei/v3/cmd/nuclei@latest` or `brew install nuclei`) — if unavailable, use the Python fallback in the solution script
- Completion of Lab (ffuf/gobuster fuzzing) and Lab (OpenAPI/Swagger Recon) is recommended — this lab detects the same issues those labs found manually, but via reusable templates

---

## Background

Public nuclei templates target well-known software (CVEs, common panels, default credentials). A custom-built lab application like SocialHack API has no public templates — so this lab has you write your own, targeting the specific information-disclosure issues discovered in earlier labs: the leaky debug endpoint, the over-shared OpenAPI spec, and the exposed `.env` file. Three starter templates are provided in `api-hacking/nuclei-templates/`; you'll also write one from scratch.

---

## Tasks

### Task 1: Run a Single Provided Template

**Steps:**
1. Run the debug-exposure template against the API

**nuclei example:**
```bash
nuclei -u http://localhost:5001 \
       -t api-hacking/nuclei-templates/socialhack-debug-exposure.yaml
```

**🚩 FLAG 1: Does the template report a match? What severity does it assign?**

<details>
<summary>💡 Hint 1</summary>
If the debug endpoint is live and unauthenticated (it is, by design), you should see a "critical" finding print to the console.
</details>

---

### Task 2: Run the Whole Template Directory

**Steps:**
1. Point nuclei at the whole `nuclei-templates/` directory instead of a single file
2. Filter to only critical/high severity

**nuclei example:**
```bash
nuclei -u http://localhost:5001 \
       -t api-hacking/nuclei-templates/ \
       -severity critical,high
```

**🚩 FLAG 2: How many findings total, and how many are critical vs. high?**

<details>
<summary>💡 Hint 1</summary>
All three provided templates should fire against an unmodified SocialHack API install.
</details>

---

### Task 3: Export Results as JSON

**Steps:**
1. Run a scan with JSON-lines output
2. Parse the output with `jq`

**nuclei example:**
```bash
nuclei -u http://localhost:5001 -t api-hacking/nuclei-templates/ -jsonl -o results.jsonl
cat results.jsonl | jq -r '.["template-id"] + " | " + .info.severity'
```

**🚩 FLAG 3: List the template IDs of everything that fired, sorted by severity**

---

### Task 4: Write a New Template From Scratch

**Steps:**
1. Write a template that detects the `/admin_old` endpoint discovered in the ffuf/gobuster lab
2. Save it as `api-hacking/nuclei-templates/socialhack-old-admin-panel.yaml`
3. Run it to confirm it fires

**🚩 FLAG 4: Your template correctly reports a finding for `/admin_old`**

<details>
<summary>💡 Hint 1</summary>
Match on the `FLAG{old_admin_panel_still_deployed}` string in the response body, combined with a status-200 matcher, using `matchers-condition: and`.
</details>

<details>
<summary>💡 Hint 2</summary>
See Tutorial 3.6's "Solution Template" collapsible section if you get stuck — but try writing it yourself first.
</details>

---

## Flags to Find

| Flag   | Description                                                | Hint                                       |
|--------|--------------------------------------------------------------|-----------------------------------------------|
| FLAG 1 | Debug-exposure template result + severity                     | Run the single template                        |
| FLAG 2 | Total findings, critical vs. high count                       | Run the whole directory with severity filter    |
| FLAG 3 | Template IDs from JSON output                                  | `-jsonl -o results.jsonl` + `jq`                |
| FLAG 4 | New custom template detects `/admin_old`                       | Write and run your own YAML template            |

---

## Remediation

### 1. Fix the Underlying Issues (templates only detect, they don't fix)
- See Stage 3.4/3.5/8.2 remediation sections for the debug endpoint, `.env`, and OpenAPI spec leaks respectively.

### 2. Bake Custom Templates Into CI/CD
```yaml
# Concept: run on every deploy to staging
- name: nuclei regression scan
  run: nuclei -u https://staging.internal -t custom-templates/ -severity critical,high -fail-on-findings
```

### 3. Maintain an Internal Template Library
- Every time a real finding is fixed, write a template for it so a regression is caught automatically on the next deploy.

---

## References

- [nuclei documentation](https://docs.projectdiscovery.io/tools/nuclei/overview)
- [nuclei-templates (public library)](https://github.com/projectdiscovery/nuclei-templates)
