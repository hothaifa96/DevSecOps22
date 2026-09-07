# Lesson 7: CI/CD Security (DevSecOps)

## Overview

| Topic | Details |
|-------|---------|
| **Duration** | 90 minutes |
| **Level** | Intermediate |
| **Prerequisites** | Lessons 01–06 |
| **Objectives** | Understand DevSecOps principles; implement shift-left security; integrate SAST, DAST, SCA, and container scanning into CI/CD; manage secrets securely; understand supply chain security, SBOMs, and signed artifacts |

---

## 1. DevSecOps — Security as a First-Class Citizen

### The Problem

Traditional security is a **gate at the end** of the development process:

```
Traditional (Security as a Gate):

  Plan → Code → Build → Test → ──────────────────▶ Security Review → Deploy
                                                        │
                                                   "Here are 200
                                                    findings. Go
                                                    fix them."
                                                        │
                                                   ❌ 3-week delay
```

This approach creates bottlenecks, adversarial relationships between developers and security teams, and late-discovered vulnerabilities that are expensive to fix.

### The DevSecOps Approach

Integrate security into **every stage** of the CI/CD pipeline:

```
DevSecOps (Security Everywhere):

  Plan ──▶ Code ──▶ Build ──▶ Test ──▶ Deploy ──▶ Operate ──▶ Monitor
    │        │        │         │         │          │           │
    ▼        ▼        ▼         ▼         ▼          ▼           ▼
  Threat   Pre-     SAST     Security  Config     Runtime     Incident
  model    commit   SCA      tests     validation security    response
           hooks    Container DAST              Monitoring
           IDE      scanning
           plugins
```

### DevSecOps Principles

1. **Security is everyone's responsibility** — Not just the security team.
2. **Shift left** — Find and fix vulnerabilities as early as possible.
3. **Automate security** — Manual security reviews don't scale.
4. **Fail fast** — Block vulnerable code before it reaches production.
5. **Security as code** — Policies, scans, and configurations are version-controlled.
6. **Continuous security** — Security isn't a one-time check; it's ongoing.

---

## 2. Shift-Left Security

### What It Means

"Shift left" means moving security activities **earlier** (leftward) in the development lifecycle.

```
Cost to fix a vulnerability:

  ▲ Cost
  │
  │                                                    ████
  │                                                    ████
  │                                               ████ ████
  │                                          ████ ████ ████
  │                                     ████ ████ ████ ████
  │                                ████ ████ ████ ████ ████
  │                           ████ ████ ████ ████ ████ ████
  │     ████            ████ ████ ████ ████ ████ ████ ████
  └──────┼───────────────┼────┼────┼────┼────┼────┼────┼──────▶
        IDE          Pre-   Build  Test  Stage  Prod  Post-
        (cheapest)   commit                          incident
                                                     (most expensive)
```

### Shift-Left Security Activities by Stage

| Stage | Security Activity | Tools |
|-------|------------------|-------|
| **IDE / Development** | Real-time vulnerability warnings | Snyk IDE plugins, SonarLint, ESLint security rules |
| **Pre-commit** | Block secrets, lint security issues | Gitleaks, pre-commit hooks, Husky |
| **Pull Request** | SAST, SCA, code review for security | Semgrep, CodeQL, Dependabot |
| **Build** | Container scanning, dependency audit | Trivy, npm audit, pip-audit |
| **Test** | Security-focused tests, DAST | OWASP ZAP, Burp Suite, custom security tests |
| **Staging** | Penetration testing, DAST | OWASP ZAP, Nuclei |
| **Production** | Runtime protection, monitoring | Falco, WAF, SIEM |
| **Ongoing** | Vulnerability database monitoring | Dependabot, Snyk, Renovate |

---

## 3. SAST — Static Application Security Testing

### What It Is

SAST analyzes **source code** (without executing it) to find security vulnerabilities, coding errors, and insecure patterns.

### How It Works

```
Source Code → SAST Scanner → Findings Report
                  │
                  ├── SQL Injection in login.py:42
                  ├── XSS in template.html:15
                  ├── Hardcoded secret in config.js:8
                  └── Insecure random number in crypto.py:23
```

### What SAST Detects

| Vulnerability | Example |
|---|---|
| **SQL Injection** | `query = "SELECT * FROM users WHERE id = " + user_input` |
| **Cross-Site Scripting (XSS)** | `innerHTML = user_input` |
| **Path Traversal** | `open("/files/" + user_input)` |
| **Hardcoded Secrets** | `API_KEY = "sk-1234567890abcdef"` |
| **Insecure Cryptography** | Using MD5 for password hashing |
| **Command Injection** | `os.system("ping " + user_input)` |
| **Insecure Deserialization** | `pickle.loads(user_data)` |
| **Buffer Overflow** | (in C/C++) `strcpy(buffer, user_input)` |

### SAST Tools

| Tool | Languages | Type | Notes |
|------|-----------|------|-------|
| **Semgrep** | 30+ languages | Open source + SaaS | Rule-based, fast, customizable |
| **CodeQL** | 10+ languages | Free for OSS (GitHub) | Semantic analysis, very accurate |
| **SonarQube** | 30+ languages | Open source + Commercial | Broad coverage, quality + security |
| **Bandit** | Python | Open source | Python-specific, easy to use |
| **ESLint (security plugins)** | JavaScript | Open source | eslint-plugin-security |
| **Brakeman** | Ruby | Open source | Rails-specific |
| **SpotBugs + FindSecBugs** | Java | Open source | Java/JVM security checks |
| **Checkmarx** | 30+ languages | Commercial | Enterprise SAST leader |

### SAST in CI/CD Pipeline

```yaml
# Example: Semgrep in GitHub Actions
- name: Run SAST (Semgrep)
  uses: returntocorp/semgrep-action@v1
  with:
    config: >-
      p/security-audit
      p/owasp-top-ten
      p/secrets

# Example: CodeQL in GitHub Actions
- name: Initialize CodeQL
  uses: github/codeql-action/init@v3
  with:
    languages: javascript, python

- name: Perform CodeQL Analysis
  uses: github/codeql-action/analyze@v3
```

### Managing SAST Findings

Not all findings are equal. Categorize and triage:

```
SAST Finding Triage:
  ├── True Positive (real vulnerability)
  │   ├── Critical/High → Fix immediately, block pipeline
  │   ├── Medium → Fix within sprint, create ticket
  │   └── Low → Track, fix when convenient
  │
  ├── False Positive (not actually vulnerable)
  │   └── Suppress with inline comment + justification
  │       # nosemgrep: python.lang.security.audit.eval-detected
  │       # Reason: input is validated and comes from trusted internal service
  │
  └── Acceptable Risk (vulnerable but mitigated)
      └── Document in risk register, add compensating controls
```

---

## 4. DAST — Dynamic Application Security Testing

### What It Is

DAST tests a **running application** from the outside — like an attacker would. It sends malicious inputs and observes the application's responses.

### How It Works

```
                    ┌───────────────┐
                    │  DAST Scanner │
                    │  (OWASP ZAP)  │
                    └───────┬───────┘
                            │
                    Sends malicious requests:
                    - SQL injection payloads
                    - XSS payloads
                    - Authentication bypass attempts
                    - Directory traversal
                            │
                            ▼
                    ┌───────────────┐
                    │  Running App  │
                    │  (Staging)    │
                    └───────────────┘
                            │
                    Analyzes responses for:
                    - Error messages revealing info
                    - Reflected XSS
                    - Authentication failures
                    - Security header issues
```

### SAST vs. DAST

| Aspect | SAST | DAST |
|--------|------|------|
| **What it analyzes** | Source code (static) | Running application (dynamic) |
| **When it runs** | Build stage (before deployment) | After deployment (staging/QA) |
| **Finds** | Code-level vulnerabilities | Runtime vulnerabilities, misconfigurations |
| **Language-dependent** | Yes | No (tests via HTTP/API) |
| **False positives** | Higher | Lower |
| **Coverage** | All code paths (even unused) | Only reachable endpoints |
| **Speed** | Fast (minutes) | Slower (minutes to hours) |
| **Exact location** | File and line number | URL and request/response |

### DAST Tools

| Tool | Type | Notes |
|------|------|-------|
| **OWASP ZAP** | Open source | Most popular free DAST tool |
| **Burp Suite** | Commercial + Community | Industry standard for web security testing |
| **Nuclei** | Open source | Template-based vulnerability scanner |
| **Nikto** | Open source | Web server scanner |
| **OWASP Amass** | Open source | Attack surface discovery |
| **HCL AppScan** | Commercial | Enterprise DAST |

### DAST in CI/CD Pipeline

```
Pipeline:
  Build → Deploy to Staging → DAST Scan (against staging URL) → Report

  Typical DAST pipeline configuration:
    - Deploy application to ephemeral/staging environment
    - Wait for application to be healthy
    - Run OWASP ZAP baseline scan (5-10 minutes)
    - Generate report
    - Fail pipeline if high/critical findings
    - Clean up ephemeral environment
```

```bash
# OWASP ZAP baseline scan (Docker)
docker run -t owasp/zap2docker-stable zap-baseline.py \
  -t https://staging.myapp.com \
  -r zap-report.html \
  -l WARN \
  -z "-config rules.cookie.ignorelist=session_id"
```

---

## 5. SCA — Software Composition Analysis

### What It Is

SCA analyzes your **third-party dependencies** (open source libraries) for known vulnerabilities (CVEs), license compliance issues, and outdated components.

### Why SCA Is Critical

Modern applications are **mostly open-source code:**

```
Typical Application Composition:
┌────────────────────────────────────────────────────┐
│                                                    │
│  ██████████████████████████████████████  80-90%    │
│  Open Source Dependencies                          │
│                                                    │
│  ██████████  10-20%                                │
│  Your Code                                         │
│                                                    │
└────────────────────────────────────────────────────┘

If you only scan YOUR code (SAST), you're missing 80-90% of the attack surface.
```

### Real-World Examples

| Incident | Year | Impact |
|----------|------|--------|
| **Log4Shell (CVE-2021-44228)** | 2021 | Critical RCE in Log4j affected millions of Java applications |
| **event-stream malware** | 2018 | npm package was hijacked to steal cryptocurrency |
| **colors.js / faker.js** | 2022 | Maintainer intentionally corrupted popular npm packages |
| **ua-parser-js** | 2021 | Popular npm package was hijacked to install crypto miners |
| **SolarWinds** | 2020 | Supply chain attack through compromised build system |

### SCA Tools

| Tool | Type | Ecosystems | Notes |
|------|------|-----------|-------|
| **Dependabot** | Free (GitHub) | npm, pip, Maven, Go, etc. | Automated PR creation for updates |
| **Snyk** | Freemium + Commercial | All major | Developer-friendly, fix suggestions |
| **OWASP Dependency-Check** | Open source | Java, .NET, Node, Python | Checks against NVD |
| **npm audit** | Built-in | Node.js | `npm audit` / `npm audit fix` |
| **pip-audit** | Open source | Python | Checks against PyPI advisory DB |
| **Trivy** | Open source | All major | Also scans containers, IaC |
| **Renovate** | Open source | All major | Automated dependency updates |
| **Grype** | Open source | All major | Vulnerability scanner for SBOMs |

### SCA in CI/CD Pipeline

```bash
# npm audit
$ npm audit
found 3 vulnerabilities (1 low, 1 moderate, 1 high)
  run `npm audit fix` to fix them

# pip-audit
$ pip-audit
Found 2 known vulnerabilities in 1 package
  Name    Version  ID                  Fix Versions
  ------  -------  ------------------  ------------
  django  3.2.0    PYSEC-2021-0001     3.2.14

# Trivy filesystem scan
$ trivy fs --severity HIGH,CRITICAL .
```

### Automated Dependency Updates

```
Dependabot / Renovate Workflow:

  1. Bot scans your dependency files daily
  2. New version found for express (4.18.1 → 4.18.2, security fix)
  3. Bot creates a Pull Request:
     "chore(deps): bump express from 4.18.1 to 4.18.2"
  4. CI runs on the PR (tests, build, security scan)
  5. If CI passes, auto-merge (or developer reviews and merges)
  
  Result: Dependencies are kept up-to-date automatically.
```

---

## 6. Container Security Scanning

### What to Scan in a Container Image

```
Container Image Layers:
┌────────────────────────────────┐
│  Application Code              │ ← SAST
│  Application Dependencies      │ ← SCA
├────────────────────────────────┤
│  OS Packages (apt, apk)       │ ← Container scan
│  System libraries              │ ← Container scan
├────────────────────────────────┤
│  Base Image (e.g., debian:12) │ ← Container scan
└────────────────────────────────┘
```

### Container Scanning Tools

| Tool | Type | Notes |
|------|------|-------|
| **Trivy** | Open source | Most popular, scans images, filesystems, repos |
| **Grype** | Open source | Fast, pairs with Syft for SBOM |
| **Snyk Container** | Commercial | Developer-friendly, base image recommendations |
| **Clair** | Open source | Originally by CoreOS, used in Quay |
| **Docker Scout** | Docker Inc. | Built into Docker Desktop |
| **AWS ECR Scanning** | AWS | Built into ECR (uses Clair or Inspector) |
| **Harbor Scanner** | Open source | Built into Harbor registry |

### Container Security Best Practices

```dockerfile
# 1. Use minimal base images
FROM alpine:3.19              # ✅ Small attack surface
# FROM ubuntu:22.04           # ❌ Larger attack surface

# 2. Don't run as root
RUN adduser -D appuser
USER appuser                  # ✅ Runs as non-root

# 3. Use specific version tags (not latest)
FROM node:20.11.0-alpine      # ✅ Pinned version
# FROM node:latest            # ❌ Unknown version

# 4. Multi-stage builds (no build tools in production)
FROM node:20-alpine AS builder
RUN npm ci && npm run build

FROM node:20-alpine AS runtime
COPY --from=builder /app/dist ./dist  # ✅ Only production files

# 5. Scan and fix before pushing
# trivy image myapp:v1.2.3
```

---

## 7. Secrets Management

### The Problem

Secrets (passwords, API keys, tokens, certificates) must never be stored in code or CI/CD configuration files.

### Where Secrets Leak

```
Common Secret Leak Points:
  ❌ Hardcoded in source code:     API_KEY = "sk-abc123..."
  ❌ In Git history:               Secret was removed but exists in old commits
  ❌ In CI/CD logs:                echo $DATABASE_PASSWORD (printed to log)
  ❌ In Docker images:             ENV API_KEY=sk-abc123 (baked into layer)
  ❌ In environment variables:     Visible in process listings
  ❌ In config files committed:    .env file checked into Git
  ❌ In CI/CD pipeline config:     Secret in plaintext YAML
```

### Secret Detection Tools

| Tool | Type | How It Works |
|------|------|-------------|
| **Gitleaks** | Open source | Scans Git repos for secrets (regex + entropy) |
| **TruffleHog** | Open source | Deep Git history scanning |
| **detect-secrets** | Open source (Yelp) | Pre-commit hook for secret detection |
| **GitHub Secret Scanning** | Free (GitHub) | Scans repos and alerts on known patterns |
| **GitGuardian** | Commercial | Real-time secret detection |

### Pre-commit Secret Detection

```bash
# Install gitleaks as a pre-commit hook
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.0
    hooks:
      - id: gitleaks

# Run manually
$ gitleaks detect --source . --verbose

Finding:     AWS Access Key ID
Secret:      AKIAIOSFODNN7EXAMPLE
RuleID:      aws-access-key-id
File:        config/settings.py
Line:        42
Commit:      abc1234
Author:      developer@example.com
```

### Secrets Management Solutions

| Tool | Type | Best For |
|------|------|---------|
| **HashiCorp Vault** | Self-hosted / HCP | Enterprise, dynamic secrets, PKI |
| **AWS Secrets Manager** | SaaS (AWS) | AWS-native applications |
| **AWS Systems Manager Parameter Store** | SaaS (AWS) | Simple key-value secrets in AWS |
| **Azure Key Vault** | SaaS (Azure) | Azure-native applications |
| **Google Secret Manager** | SaaS (GCP) | GCP-native applications |
| **1Password (CI/CD integration)** | SaaS | Small teams, developer-friendly |
| **GitHub Actions Secrets** | SaaS | GitHub Actions pipelines |
| **GitLab CI Variables** | SaaS / Self-hosted | GitLab CI pipelines |
| **Sealed Secrets** | Open source | Kubernetes-native (encrypted in Git) |
| **External Secrets Operator** | Open source | Kubernetes + any external vault |

### Secrets in CI/CD — Best Practices

```
✅ DO:
  - Store secrets in a dedicated secrets manager (Vault, AWS SM)
  - Use CI/CD platform's secret storage (GitHub Secrets, GitLab Variables)
  - Rotate secrets regularly (automate with Vault)
  - Audit secret access (who accessed what, when)
  - Use short-lived credentials (OIDC tokens, temporary STS tokens)
  - Mask secrets in CI/CD logs

❌ DON'T:
  - Hardcode secrets in code
  - Store secrets in .env files committed to Git
  - Pass secrets as command-line arguments (visible in process list)
  - Use long-lived credentials when short-lived are available
  - Share secrets via Slack, email, or chat
  - Use the same secret across environments
```

### OIDC for Keyless CI/CD Authentication

Modern CI/CD avoids storing long-lived cloud credentials:

```
Traditional (risky):
  Store AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY as CI secrets
  → Keys are long-lived, can be leaked

OIDC (modern):
  CI platform (GitHub Actions) → OIDC token → AWS STS → Temporary credentials
  → No stored secrets, credentials expire in minutes

GitHub Actions OIDC to AWS:
  permissions:
    id-token: write
  steps:
    - uses: aws-actions/configure-aws-credentials@v4
      with:
        role-to-assume: arn:aws:iam::123456789:role/github-actions
        aws-region: us-east-1
        # No access keys needed!
```

---

## 8. Supply Chain Security

### What Is Software Supply Chain Security?

Your software supply chain includes everything that goes into building your software: source code, dependencies, build tools, CI/CD infrastructure, and deployment systems. An attack on **any** link in this chain can compromise your application.

### The Software Supply Chain

```
┌─────────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│   Source     │───▶│  Build   │───▶│  Package │───▶│ Registry │───▶│  Deploy  │
│   Code       │    │  System  │    │  & Sign  │    │  Storage │    │  System  │
│              │    │          │    │          │    │          │    │          │
│ Attack:      │    │ Attack:  │    │ Attack:  │    │ Attack:  │    │ Attack:  │
│ Malicious    │    │ Comp-    │    │ Tamper   │    │ Replace  │    │ Deploy   │
│ commit,      │    │ romised  │    │ with     │    │ artifact │    │ wrong    │
│ dep confusion│    │ build    │    │ artifact │    │ in       │    │ version  │
│              │    │ server   │    │          │    │ registry │    │          │
└─────────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
```

### Supply Chain Attack Examples

| Attack Type | Description | Example |
|---|---|---|
| **Dependency confusion** | Attacker publishes a malicious package with the same name as an internal package | Alex Birsan's research (2021) |
| **Typosquatting** | Package with a similar name to a popular one | `crossenv` instead of `cross-env` |
| **Compromised maintainer** | Attacker gains access to a legitimate package's npm/PyPI account | event-stream (2018) |
| **Build system compromise** | Attacker compromises the CI/CD system itself | SolarWinds (2020), CodeCov (2021) |
| **Registry compromise** | Attacker replaces a legitimate artifact in a registry | Theoretical but defended against |

### SLSA Framework (Supply-chain Levels for Software Artifacts)

SLSA (pronounced "salsa") defines four levels of supply chain security maturity:

| Level | Requirements | What It Prevents |
|-------|-------------|-----------------|
| **SLSA 1** | Build process is documented and automated | Ad-hoc builds, no provenance |
| **SLSA 2** | Build runs on a hosted service, generates signed provenance | Tampering after build |
| **SLSA 3** | Build platform is hardened, provenance is non-falsifiable | Compromised build process |
| **SLSA 4** | All dependencies are SLSA 4, hermetic builds | All known supply chain attacks |

### Implementing Supply Chain Security

```
Checklist:
  □ Sign all commits (GPG or SSH signatures)
  □ Require signed commits for merges to main
  □ Pin all dependency versions (lock files)
  □ Use hash pinning for CI/CD actions (not just version tags)
  □ Sign all container images (Cosign/Sigstore)
  □ Generate SBOM for every build
  □ Verify image signatures before deployment (Kyverno, OPA)
  □ Use OIDC instead of long-lived credentials
  □ Harden CI/CD runner environments
  □ Audit CI/CD pipeline access regularly
```

### Pinning CI/CD Action Versions

```yaml
# ❌ Risky: Tag can be moved to point to malicious code
- uses: actions/checkout@v4

# ✅ Safer: Pin to specific commit SHA
- uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11  # v4.1.1

# Why: If the action's repo is compromised, the tag could be updated
# to point to malicious code, but the SHA is immutable.
```

---

## 9. Software Bill of Materials (SBOM)

### Why SBOM Is Essential for Security

When a new vulnerability is announced (like Log4Shell), the first question is: **"Are we affected?"**

Without an SBOM:
```
Security Team: "Are we using Log4j?"
Dev Team A: "Let me check... maybe? I'll look at our pom.xml"
Dev Team B: "We don't use it directly, but maybe a dependency does?"
Dev Team C: "What's Log4j?"
Result: Days of investigation across 50 services.
```

With an SBOM:
```
Security Team: Query SBOM database for "log4j"
Result: 3 services affected, found in 30 seconds.
  - auth-service:v2.1.0 → log4j-core:2.14.0 (transitive via spring-boot)
  - payment-service:v1.5.2 → log4j-core:2.15.0 (direct dependency)
  - reporting-service:v3.0.1 → NOT affected
```

### Generating and Storing SBOMs

```bash
# Generate SBOM with Syft
syft myapp:v1.2.3 -o cyclonedx-json > sbom.cdx.json

# Generate SBOM with Trivy
trivy image --format cyclonedx --output sbom.cdx.json myapp:v1.2.3

# Attach SBOM to container image
cosign attach sbom --sbom sbom.cdx.json ghcr.io/myorg/myapp:v1.2.3

# Scan an SBOM for vulnerabilities
grype sbom:./sbom.cdx.json
```

---

## 10. Signed Commits and Images

### Signed Git Commits

Signed commits prove that a commit was made by the claimed author:

```bash
# Configure GPG signing
git config --global commit.gpgsign true
git config --global user.signingkey ABC123DEF456

# Or use SSH signing (simpler)
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/id_ed25519.pub

# Verify a commit
git log --show-signature
commit abc1234 (HEAD -> main)
gpg: Signature made Mon Jan 15 10:00:00 2024
gpg: Good signature from "Alice Developer <alice@example.com>"
```

### Signed Container Images

```bash
# Sign with Cosign (keyless via Sigstore)
cosign sign ghcr.io/myorg/myapp:v1.2.3

# Verify before deploying
cosign verify \
  --certificate-identity-regexp "https://github.com/myorg/.*" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  ghcr.io/myorg/myapp:v1.2.3

# Enforce in Kubernetes (Kyverno policy)
# Only allow images signed by our CI/CD pipeline
```

---

## 11. Putting It All Together — Secure Pipeline

```
Complete Secure CI/CD Pipeline:

┌─────────────────────────────────────────────────────────────────┐
│ PRE-COMMIT                                                       │
│  • Secret detection (gitleaks)                                   │
│  • Linting (security rules)                                      │
│  • Signed commits required                                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ SOURCE STAGE                                                     │
│  • Branch protection rules enforced                              │
│  • PR required with approvals                                    │
│  • Actions/workflows pinned to SHA                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ BUILD STAGE                                                      │
│  • SAST scan (Semgrep, CodeQL)                                   │
│  • SCA / Dependency check (npm audit, Snyk)                      │
│  • License compliance check                                      │
│  • Build container image (multi-stage, non-root)                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ SECURITY SCAN STAGE                                              │
│  • Container image scan (Trivy)                                  │
│  • SBOM generation (Syft)                                        │
│  • IaC scan (Checkov, tfsec) — if applicable                     │
│  • Policy evaluation (critical/high CVEs block pipeline)         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ PUBLISH STAGE                                                    │
│  • Sign container image (Cosign)                                 │
│  • Attach SBOM to image                                          │
│  • Push to registry                                              │
│  • Generate SLSA provenance                                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ DEPLOY STAGE                                                     │
│  • Verify image signature (Kyverno/OPA)                          │
│  • Deploy with OIDC credentials (no stored secrets)              │
│  • Configuration from secrets manager                            │
│  • DAST scan against staging (OWASP ZAP)                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ RUNTIME                                                          │
│  • Runtime security monitoring (Falco)                           │
│  • Web Application Firewall (WAF)                                │
│  • Continuous vulnerability scanning (new CVEs on existing images)│
│  • Incident response automation                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 12. Security Scanning Policy Template

Define clear policies for how security findings affect the pipeline:

| Finding Severity | Pipeline Action | SLA to Fix | Responsibility |
|---|---|---|---|
| **Critical** (CVSS 9.0-10.0) | Block pipeline, alert security team | 24 hours | Dev team + Security |
| **High** (CVSS 7.0-8.9) | Block pipeline | 7 days | Dev team |
| **Medium** (CVSS 4.0-6.9) | Warn, create Jira ticket | 30 days | Dev team |
| **Low** (CVSS 0.1-3.9) | Log, track trend | 90 days | Dev team |
| **Informational** | Log only | Best effort | Dev team |

### Exception Process

```
When a pipeline block cannot be fixed immediately:
  1. Developer requests exception via security ticketing system
  2. Security team evaluates risk and compensating controls
  3. If approved: exception is time-boxed (e.g., 7 days) with a ticket to fix
  4. Exception is logged in the security risk register
  5. Pipeline is configured to allow the specific finding temporarily
  6. After expiry, the block is re-enforced automatically
```

---

## 13. Review Questions

1. **Explain "shift-left security" and give three concrete examples** of how security moves earlier in the development lifecycle.
2. **What is the difference between SAST, DAST, and SCA?** When does each run in a CI/CD pipeline?
3. **A developer hardcoded an API key in code 6 months ago.** The key has been removed, but it's still in Git history. What steps would you take?
4. **What is a dependency confusion attack?** How do you prevent it?
5. **Your container scan found 47 vulnerabilities in the base image, but your application code is clean.** What do you do?
6. **Explain the SLSA framework.** What level would you recommend as a first goal for a team just starting with supply chain security?
7. **Why is OIDC preferred over stored credentials for CI/CD authentication to cloud providers?**
8. **Design a security scanning strategy** for a pipeline that builds a Python web application in a Docker container.

---

## 14. Further Reading

- **Framework:** [OWASP Top 10](https://owasp.org/www-project-top-ten/) — Most critical web application security risks
- **Framework:** [SLSA](https://slsa.dev/) — Supply-chain Levels for Software Artifacts
- **Tool:** [Sigstore](https://sigstore.dev/) — Keyless signing for software artifacts
- **Book:** *The DevSecOps Playbook* by Sean D. Mack
- **Article:** [Shift Left Security](https://snyk.io/learn/shift-left-security/) by Snyk
- **Tool:** [Trivy](https://trivy.dev/) — Comprehensive security scanner
- **Tool:** [Semgrep](https://semgrep.dev/) — Lightweight SAST
- **Standard:** [CycloneDX SBOM](https://cyclonedx.org/)
- **Guide:** [NIST SSDF](https://csrc.nist.gov/Projects/ssdf) — Secure Software Development Framework

---

*Previous: [06 - Branching Strategies](06-branching-strategies.md) | Next: [08 - CI/CD Best Practices](08-cicd-best-practices.md)*
