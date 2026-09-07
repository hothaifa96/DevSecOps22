# Lab 08: Security Scanning Pipeline

## Overview

In this lab, you will build a comprehensive security scanning pipeline that integrates multiple DevSecOps tools into your GitHub Actions workflow. You will implement Static Application Security Testing (SAST), dependency vulnerability scanning, container image scanning, and CodeQL semantic analysis to catch security issues early in the development lifecycle.

---

## Objectives

By the end of this lab, you will be able to:

- Implement SAST scanning using Semgrep
- Scan dependencies for known vulnerabilities using `npm audit` and Trivy
- Scan Docker images for OS-level and library vulnerabilities
- Set up GitHub CodeQL analysis for semantic code scanning
- Configure secret detection to prevent credential leaks
- Aggregate security findings into GitHub's Security tab
- Create a security gate that blocks merges when critical issues are found

---

## Prerequisites

- Completed **Lab 05** (Docker Build) for container scanning
- Completed **Lab 02** (Build and Test) for the Node.js project
- GitHub Advanced Security enabled (free for public repositories; requires GHAS license for private repositories)
- Understanding of common vulnerability types (CVE, CWE, OWASP Top 10)

---

## Step-by-Step Instructions

### Step 1: Understand the Security Scanning Layers

A comprehensive DevSecOps pipeline includes multiple scanning layers:

```
+-------------------------------------------------------------+
|                   Security Scanning Layers                   |
+-------------------------------------------------------------+
|                                                              |
|  1. SECRET DETECTION    - Prevent credential leaks           |
|  2. SAST (Semgrep)      - Find code-level vulnerabilities   |
|  3. DEPENDENCY SCAN     - Known CVEs in packages             |
|  4. CONTAINER SCAN      - OS and library vulns in images     |
|  5. CodeQL ANALYSIS     - Semantic code analysis by GitHub   |
|  6. LICENSE COMPLIANCE  - Open source license checks         |
|                                                              |
+-------------------------------------------------------------+
```

### Step 2: Create the Security Scanning Workflow

Create `.github/workflows/security-scanning.yml`:

```yaml
name: Security Scanning

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    # Run security scans daily at 6:00 AM UTC
    - cron: "0 6 * * *"
  workflow_dispatch:

permissions:
  contents: read
  security-events: write
  actions: read

jobs:
  # ============================================
  # 1. Secret Detection
  # ============================================
  secret-detection:
    name: Secret Detection
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Run Gitleaks
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Secret detection summary
        if: always()
        run: |
          echo "## Secret Detection" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "Scanned repository for hardcoded secrets, API keys, and credentials." >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "Tool: **Gitleaks**" >> $GITHUB_STEP_SUMMARY

  # ============================================
  # 2. SAST - Static Application Security Testing
  # ============================================
  sast:
    name: SAST Scanning
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Run Semgrep SAST scan
        uses: semgrep/semgrep-action@v1
        with:
          config: >-
            p/javascript
            p/nodejs
            p/owasp-top-ten
            p/security-audit
        env:
          SEMGREP_RULES: "p/javascript p/nodejs p/owasp-top-ten"

      - name: Run Semgrep (SARIF output)
        run: |
          pip install semgrep
          semgrep scan \
            --config "p/javascript" \
            --config "p/nodejs" \
            --config "p/owasp-top-ten" \
            --sarif \
            --output semgrep-results.sarif \
            . || true

      - name: Upload SARIF results to GitHub
        if: always()
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: semgrep-results.sarif
          category: semgrep

      - name: Upload scan results artifact
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: semgrep-results
          path: semgrep-results.sarif

  # ============================================
  # 3. Dependency Scanning
  # ============================================
  dependency-scan:
    name: Dependency Vulnerability Scan
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"

      - name: Install dependencies
        run: npm ci

      - name: Run npm audit
        id: npm-audit
        run: |
          echo "## npm Audit Results" >> $GITHUB_STEP_SUMMARY
          echo '```' >> $GITHUB_STEP_SUMMARY
          npm audit --production 2>&1 | tee npm-audit.txt >> $GITHUB_STEP_SUMMARY || true
          echo '```' >> $GITHUB_STEP_SUMMARY

          # Check for critical/high vulnerabilities
          CRITICAL=$(npm audit --production --json 2>/dev/null | jq '.metadata.vulnerabilities.critical // 0')
          HIGH=$(npm audit --production --json 2>/dev/null | jq '.metadata.vulnerabilities.high // 0')
          echo "critical=$CRITICAL" >> $GITHUB_OUTPUT
          echo "high=$HIGH" >> $GITHUB_OUTPUT

      - name: Run Trivy filesystem scan
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: "fs"
          scan-ref: "."
          format: "sarif"
          output: "trivy-fs-results.sarif"
          severity: "CRITICAL,HIGH,MEDIUM"

      - name: Upload Trivy SARIF to GitHub
        if: always()
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: trivy-fs-results.sarif
          category: trivy-dependency

      - name: Upload dependency scan results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: dependency-scan-results
          path: |
            npm-audit.txt
            trivy-fs-results.sarif

      - name: Fail on critical vulnerabilities
        if: steps.npm-audit.outputs.critical > 0
        run: |
          echo "CRITICAL vulnerabilities found in dependencies!"
          echo "Critical: ${{ steps.npm-audit.outputs.critical }}"
          echo "High: ${{ steps.npm-audit.outputs.high }}"
          exit 1

  # ============================================
  # 4. Container Scanning
  # ============================================
  container-scan:
    name: Container Image Scan
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Build Docker image for scanning
        run: |
          docker build -t scan-target:${{ github.sha }} .

      - name: Run Trivy container scan
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: "scan-target:${{ github.sha }}"
          format: "sarif"
          output: "trivy-container-results.sarif"
          severity: "CRITICAL,HIGH"
          ignore-unfixed: true

      - name: Upload Trivy SARIF to GitHub
        if: always()
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: trivy-container-results.sarif
          category: trivy-container

      - name: Run Trivy (table output for summary)
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: "scan-target:${{ github.sha }}"
          format: "table"
          severity: "CRITICAL,HIGH,MEDIUM"
          output: "trivy-table.txt"

      - name: Display container scan results
        if: always()
        run: |
          echo "## Container Vulnerability Scan" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "Image: \`scan-target:${{ github.sha }}\`" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo '```' >> $GITHUB_STEP_SUMMARY
          cat trivy-table.txt >> $GITHUB_STEP_SUMMARY 2>/dev/null || echo "No vulnerabilities found" >> $GITHUB_STEP_SUMMARY
          echo '```' >> $GITHUB_STEP_SUMMARY

      - name: Upload container scan results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: container-scan-results
          path: |
            trivy-container-results.sarif
            trivy-table.txt

  # ============================================
  # 5. CodeQL Analysis
  # ============================================
  codeql:
    name: CodeQL Analysis
    runs-on: ubuntu-latest

    permissions:
      actions: read
      contents: read
      security-events: write

    strategy:
      fail-fast: false
      matrix:
        language: ["javascript"]
        # Add more languages as needed: python, java, go, ruby, etc.

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Initialize CodeQL
        uses: github/codeql-action/init@v3
        with:
          languages: ${{ matrix.language }}
          # Use default queries plus security-extended
          queries: security-extended,security-and-quality

      - name: Auto-build
        uses: github/codeql-action/autobuild@v3

      - name: Perform CodeQL analysis
        uses: github/codeql-action/analyze@v3
        with:
          category: "/language:${{ matrix.language }}"

  # ============================================
  # 6. License Compliance
  # ============================================
  license-check:
    name: License Compliance
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"

      - name: Install dependencies
        run: npm ci

      - name: Install license checker
        run: npm install -g license-checker

      - name: Check licenses
        run: |
          echo "## License Compliance Report" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY

          # List all licenses
          echo "### All Dependencies" >> $GITHUB_STEP_SUMMARY
          echo '```' >> $GITHUB_STEP_SUMMARY
          license-checker --summary >> $GITHUB_STEP_SUMMARY 2>&1 || true
          echo '```' >> $GITHUB_STEP_SUMMARY

          # Check for forbidden licenses
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "### Forbidden License Check" >> $GITHUB_STEP_SUMMARY
          FORBIDDEN="GPL-3.0;AGPL-3.0;SSPL-1.0"
          echo "Checking for forbidden licenses: $FORBIDDEN" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY

          if license-checker --failOn "$FORBIDDEN" > /dev/null 2>&1; then
            echo "No forbidden licenses found." >> $GITHUB_STEP_SUMMARY
          else
            echo "**WARNING**: Forbidden licenses detected!" >> $GITHUB_STEP_SUMMARY
            echo '```' >> $GITHUB_STEP_SUMMARY
            license-checker --failOn "$FORBIDDEN" 2>&1 >> $GITHUB_STEP_SUMMARY || true
            echo '```' >> $GITHUB_STEP_SUMMARY
          fi

      - name: Generate license report
        run: |
          license-checker --json --out license-report.json || true
          license-checker --csv --out license-report.csv || true

      - name: Upload license report
        uses: actions/upload-artifact@v4
        with:
          name: license-report
          path: |
            license-report.json
            license-report.csv

  # ============================================
  # Security Gate (aggregates all results)
  # ============================================
  security-gate:
    name: Security Gate
    runs-on: ubuntu-latest
    needs: [secret-detection, sast, dependency-scan, container-scan, codeql, license-check]
    if: always()

    steps:
      - name: Evaluate security scan results
        run: |
          echo "## Security Gate Results" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "| Scan | Result |" >> $GITHUB_STEP_SUMMARY
          echo "|------|--------|" >> $GITHUB_STEP_SUMMARY
          echo "| Secret Detection | ${{ needs.secret-detection.result }} |" >> $GITHUB_STEP_SUMMARY
          echo "| SAST (Semgrep) | ${{ needs.sast.result }} |" >> $GITHUB_STEP_SUMMARY
          echo "| Dependency Scan | ${{ needs.dependency-scan.result }} |" >> $GITHUB_STEP_SUMMARY
          echo "| Container Scan | ${{ needs.container-scan.result }} |" >> $GITHUB_STEP_SUMMARY
          echo "| CodeQL | ${{ needs.codeql.result }} |" >> $GITHUB_STEP_SUMMARY
          echo "| License Check | ${{ needs.license-check.result }} |" >> $GITHUB_STEP_SUMMARY

      - name: Check for failures
        run: |
          FAILED=false

          if [ "${{ needs.secret-detection.result }}" = "failure" ]; then
            echo "CRITICAL: Secret detection found leaked credentials!"
            FAILED=true
          fi

          if [ "${{ needs.sast.result }}" = "failure" ]; then
            echo "WARNING: SAST scan found security issues"
            FAILED=true
          fi

          if [ "${{ needs.dependency-scan.result }}" = "failure" ]; then
            echo "CRITICAL: Dependency scan found critical vulnerabilities!"
            FAILED=true
          fi

          if [ "${{ needs.container-scan.result }}" = "failure" ]; then
            echo "WARNING: Container scan found vulnerabilities"
            # Container scan warnings don't block (adjust per your policy)
          fi

          if [ "${{ needs.codeql.result }}" = "failure" ]; then
            echo "WARNING: CodeQL found potential security issues"
            FAILED=true
          fi

          if [ "$FAILED" = "true" ]; then
            echo ""
            echo "========================================"
            echo "  SECURITY GATE: FAILED"
            echo "  Review findings in the Security tab"
            echo "========================================"
            exit 1
          else
            echo ""
            echo "========================================"
            echo "  SECURITY GATE: PASSED"
            echo "  All security scans completed"
            echo "========================================"
          fi
```

### Step 3: Create a Custom Semgrep Configuration (Optional)

For project-specific SAST rules, create `.semgrep.yml`:

```yaml
rules:
  - id: no-hardcoded-credentials
    patterns:
      - pattern: |
          $VAR = "..."
      - metavariable-regex:
          metavariable: $VAR
          regex: (password|secret|api_key|token|credential)
    message: "Potential hardcoded credential found in variable '$VAR'"
    languages: [javascript, typescript]
    severity: ERROR
    metadata:
      category: security
      cwe: "CWE-798: Use of Hard-coded Credentials"

  - id: no-eval
    pattern: eval(...)
    message: "Use of eval() is a security risk (code injection)"
    languages: [javascript]
    severity: ERROR
    metadata:
      category: security
      cwe: "CWE-95: Eval Injection"

  - id: no-sql-string-concat
    patterns:
      - pattern: |
          $QUERY = "..." + $INPUT
      - metavariable-regex:
          metavariable: $QUERY
          regex: .*(SELECT|INSERT|UPDATE|DELETE|DROP).*
    message: "Potential SQL injection via string concatenation"
    languages: [javascript]
    severity: ERROR
    metadata:
      category: security
      cwe: "CWE-89: SQL Injection"
```

### Step 4: Create a Gitleaks Configuration

Create `.gitleaks.toml` for custom secret detection rules:

```toml
title = "Custom Gitleaks Configuration"

[allowlist]
description = "Global allowlist"
paths = [
  '''node_modules''',
  '''\.github/workflows''',
  '''test''',
  '''tests''',
  '''__tests__''',
]

[[rules]]
id = "custom-api-key"
description = "Custom API Key Pattern"
regex = '''(?i)api[_-]?key\s*[:=]\s*['"][a-zA-Z0-9]{20,}['"]'''
tags = ["key", "API"]

[[rules]]
id = "custom-password"
description = "Hardcoded Password"
regex = '''(?i)password\s*[:=]\s*['"][^'"]{8,}['"]'''
tags = ["password"]
```

### Step 5: Create a Vulnerable Code Sample (For Testing)

Create `src/vulnerable-example.js` to test your scanners (this file intentionally contains security issues):

```javascript
// WARNING: This file contains intentional vulnerabilities for security scanning lab.
// DO NOT use any of these patterns in production code.

const express = require("express");

// Vulnerability 1: SQL Injection (string concatenation)
function getUserByName(name) {
  const query = "SELECT * FROM users WHERE name = '" + name + "'";
  console.log("Executing query:", query);
  // In reality, use parameterized queries
  return query;
}

// Vulnerability 2: Command Injection
const { exec } = require("child_process");
function runDiagnostics(userInput) {
  exec("ping " + userInput, (error, stdout) => {
    console.log(stdout);
  });
}

// Vulnerability 3: Cross-Site Scripting (XSS)
function renderUserProfile(req, res) {
  const username = req.query.username;
  res.send("<h1>Welcome " + username + "</h1>");
}

// Vulnerability 4: Insecure Randomness
function generateToken() {
  return Math.random().toString(36).substring(2);
}

// Vulnerability 5: Path Traversal
const fs = require("fs");
const path = require("path");
function readFile(filename) {
  // Missing path validation
  return fs.readFileSync(filename, "utf8");
}

module.exports = {
  getUserByName,
  runDiagnostics,
  renderUserProfile,
  generateToken,
  readFile,
};
```

### Step 6: Configure Branch Protection with Security Checks

1. Go to **Settings** > **Branches** > **Branch protection rules**.
2. Click **Add rule** for the `main` branch.
3. Enable **Require status checks to pass before merging**.
4. Add the following required checks:
   - `Security Gate`
   - `Secret Detection`
   - `SAST Scanning`
   - `Dependency Vulnerability Scan`
5. Click **Save changes**.

This ensures no code can be merged to `main` without passing all security scans.

### Step 7: Commit and Push

```bash
git add -A
git commit -m "Add comprehensive security scanning pipeline"
git push origin main
```

### Step 8: Review Security Findings

1. Go to the **Actions** tab and watch all security jobs execute.
2. Navigate to the **Security** tab in your repository.
3. Click on **Code scanning alerts** to see findings from Semgrep and CodeQL.
4. Click on **Dependabot alerts** (if enabled) for dependency vulnerabilities.
5. Review each finding, its severity, CWE mapping, and recommended fix.

### Step 9: Fix the Vulnerabilities

After reviewing the findings, create `src/secure-example.js` to demonstrate the fixed versions:

```javascript
// Secure versions of the vulnerable patterns

const crypto = require("crypto");
const { execFile } = require("child_process");
const path = require("path");
const fs = require("fs");

// Fix 1: Use parameterized queries (shown as concept)
function getUserByName(name) {
  // Use parameterized queries with your database library
  // Example with pg: client.query('SELECT * FROM users WHERE name = $1', [name])
  return { query: "SELECT * FROM users WHERE name = $1", params: [name] };
}

// Fix 2: Use execFile with argument array (prevents command injection)
function runDiagnostics(host) {
  // Validate input
  const hostRegex = /^[a-zA-Z0-9.-]+$/;
  if (!hostRegex.test(host)) {
    throw new Error("Invalid hostname");
  }
  return new Promise((resolve, reject) => {
    execFile("ping", ["-c", "4", host], (error, stdout) => {
      if (error) reject(error);
      else resolve(stdout);
    });
  });
}

// Fix 3: Escape output or use a template engine
function renderUserProfile(req, res) {
  const username = req.query.username;
  // Escape HTML entities
  const escaped = username
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
  res.send(`<h1>Welcome ${escaped}</h1>`);
}

// Fix 4: Use cryptographically secure random values
function generateToken() {
  return crypto.randomBytes(32).toString("hex");
}

// Fix 5: Validate and sanitize file paths
function readFile(filename) {
  const SAFE_DIR = path.resolve("/app/public");
  const resolved = path.resolve(SAFE_DIR, filename);

  // Prevent path traversal
  if (!resolved.startsWith(SAFE_DIR)) {
    throw new Error("Access denied: path traversal detected");
  }

  return fs.readFileSync(resolved, "utf8");
}

module.exports = {
  getUserByName,
  runDiagnostics,
  renderUserProfile,
  generateToken,
  readFile,
};
```

### Step 10: Enable Dependabot

Create `.github/dependabot.yml` for automated dependency updates:

```yaml
version: 2
updates:
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
    open-pull-requests-limit: 10
    labels:
      - "dependencies"
      - "security"
    reviewers:
      - "your-username"
    commit-message:
      prefix: "deps"
      include: "scope"

  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    labels:
      - "ci"
      - "dependencies"
    commit-message:
      prefix: "ci"
```

---

## Expected Outcomes

After completing this lab, you should see:

1. **Six security scanning jobs** running in parallel on every push and PR.
2. **Security findings** appearing in the GitHub Security tab under "Code scanning alerts."
3. **SARIF results** uploaded from Semgrep, Trivy, and CodeQL providing unified vulnerability tracking.
4. **Vulnerability reports** in the intentionally vulnerable file detected by both Semgrep and CodeQL.
5. **Dependency vulnerabilities** identified via `npm audit` and Trivy filesystem scan.
6. **Container vulnerabilities** found in the Docker image.
7. A **Security Gate** job that aggregates all results and blocks the pipeline on critical findings.
8. **Branch protection** enforcing that security scans pass before merging.

---

## Bonus Challenges

1. **Add DAST (Dynamic Application Security Testing)** using OWASP ZAP against a running instance of your application:
   ```yaml
   - name: Start application
     run: |
       npm start &
       sleep 5
   - name: Run OWASP ZAP scan
     uses: zaproxy/action-baseline@v0.10.0
     with:
       target: "http://localhost:3000"
   ```

2. **Create a security dashboard** that generates a markdown report summarizing all findings across all tools, posted as a PR comment.

3. **Implement a vulnerability SLA** that:
   - Critical: Must be fixed within 24 hours
   - High: Must be fixed within 7 days
   - Medium: Must be fixed within 30 days
   - Low: Must be fixed within 90 days

4. **Add Software Bill of Materials (SBOM) generation** using Syft:
   ```yaml
   - name: Generate SBOM
     uses: anchore/sbom-action@v0
     with:
       image: scan-target:${{ github.sha }}
       format: spdx-json
       output-file: sbom.spdx.json
   ```

5. **Set up security scanning for Infrastructure as Code** (IaC) using Checkov or tfsec if you have Terraform/CloudFormation files.

6. **Implement a custom CodeQL query** that detects project-specific anti-patterns. Create `.github/codeql/custom-queries/`:
   ```ql
   /**
    * @name Missing authentication check
    * @description API endpoints should verify authentication
    * @kind problem
    * @problem.severity warning
    */
   import javascript
   // ... custom query logic
   ```

---

## Key Concepts Learned

- **SAST (Static Application Security Testing)**: Analyzing source code for vulnerabilities without executing it
- **SCA (Software Composition Analysis)**: Scanning dependencies for known CVEs
- **Container Scanning**: Detecting OS and library vulnerabilities in Docker images
- **CodeQL**: GitHub's semantic analysis engine that treats code as data to find vulnerability patterns
- **SARIF**: Static Analysis Results Interchange Format, the standard for uploading findings to GitHub
- **Secret Detection**: Scanning commits and code for accidentally committed credentials
- **Gitleaks**: Open-source tool that scans Git history for secrets
- **Semgrep**: Lightweight SAST tool supporting custom rules with simple pattern syntax
- **Trivy**: All-in-one security scanner for containers, filesystems, and IaC
- **Security Gate**: A pipeline stage that aggregates scan results and enforces a pass/fail policy
- **Dependabot**: GitHub's automated dependency update bot that creates PRs for vulnerable packages
- **Shift Left**: The practice of moving security testing earlier in the development lifecycle
