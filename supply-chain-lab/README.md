# Supply-Chain Lab

**Beyond the Lab** extension — teaches Software Composition Analysis (SCA) and
dependency-vulnerability scanning. Unlike the exploit labs, this is a
**scanning / analysis** lab: you find known-vulnerable dependencies, not craft a
payload (shipping a real malicious package would be unsafe).

## File

- `requirements-vulnerable.txt` — a set of **intentionally old, CVE-laden**
  pinned dependencies. Do NOT install these into the running app; they exist
  only to be scanned.

## Exercise

1. Install a scanner:
   ```bash
   pip install pip-audit          # or: pip install safety
   ```

2. Scan the vulnerable manifest:
   ```bash
   pip-audit --no-deps -r supply-chain-lab/requirements-vulnerable.txt
   # (--no-deps keeps it fast; drop it to also pull transitive deps)
   ```
   You should see advisories fire for `requests 2.19.1` (PYSEC-2018-28),
   `PyYAML 5.1`, `Jinja2 2.10` (CVE-2019-10906), `Werkzeug 0.15.2`,
   `urllib3 1.24.1`, `cryptography 2.3`, `Django 2.2.0`, etc.

3. Compare against the app's **real** manifest (which is current/clean):
   ```bash
   pip-audit -r requirements.txt
   ```

4. Container scanning (optional): if you have Docker/Trivy:
   ```bash
   trivy fs supply-chain-lab/
   ```

## What to learn

- **Known-vulnerable dependencies** — most real breaches via supply chain start
  with an outdated library with a public CVE. SCA tools catch these.
- **Transitive dependencies** — a vuln can hide in a dependency-of-a-dependency
  (drop `--no-deps` to see them).
- **Dependency confusion / typosquatting** (concept) — if a build pulls an
  internal package name from a public index, an attacker can publish a
  malicious package under that name. Mitigation: scoped/private registries,
  pinned hashes (`pip install --require-hashes`), and namespace reservation.
- **CI/CD as an attack surface** — a compromised build step can inject code into
  every artifact. Mitigation: signed builds (SLSA), least-privilege CI tokens.

## Remediation

- Pin dependencies **with hashes** and update regularly (Dependabot/Renovate).
- Run SCA (`pip-audit`, Snyk, Trivy) in CI and fail the build on high severity.
- Use a private/proxying registry; reserve internal package names publicly.
- Generate an SBOM (`pip-audit --format=cyclonedx-json`) for inventory.
