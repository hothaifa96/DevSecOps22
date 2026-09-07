# Lesson 4: Actions and Marketplace

## Table of Contents

- [What Are Actions?](#what-are-actions)
- [Using Actions in Workflows](#using-actions-in-workflows)
- [Essential Official Actions](#essential-official-actions)
- [Popular Community Actions](#popular-community-actions)
- [GitHub Actions Marketplace](#github-actions-marketplace)
- [Action Versioning and Pinning](#action-versioning-and-pinning)
- [Creating Custom Actions](#creating-custom-actions)
  - [Composite Actions](#composite-actions)
  - [JavaScript Actions](#javascript-actions)
  - [Docker Actions](#docker-actions)
- [Publishing to the Marketplace](#publishing-to-the-marketplace)
- [Security Best Practices for Actions](#security-best-practices-for-actions)
- [Summary](#summary)

---

## What Are Actions?

An **action** is a reusable, self-contained unit of code that performs a specific task within a workflow. Actions are the building blocks that make GitHub Actions powerful.

### Three Types of Actions

| Type | Description | Best For |
|------|-------------|----------|
| **Composite** | YAML-based, combines multiple steps | Simple reusable step sequences |
| **JavaScript** | Node.js-based, runs directly on the runner | Complex logic, fast execution |
| **Docker** | Containerized, runs in a Docker container | Custom environments, any language |

### Where Actions Come From

```yaml
steps:
  # 1. Official GitHub actions (actions/ organization)
  - uses: actions/checkout@v4

  # 2. Community actions from the Marketplace
  - uses: docker/build-push-action@v5

  # 3. Actions from any public repository
  - uses: owner/repo@v1

  # 4. Local actions from your repository
  - uses: ./.github/actions/my-action

  # 5. Docker Hub images used as actions
  - uses: docker://alpine:3.18
```

---

## Using Actions in Workflows

### The `uses` Keyword

```yaml
steps:
  - name: Checkout code
    uses: actions/checkout@v4     # Organization/repo@version
    with:                          # Inputs (parameters) for the action
      fetch-depth: 0
      token: ${{ secrets.PAT }}
```

### Passing Inputs with `with`

Actions define inputs that configure their behavior:

```yaml
steps:
  - uses: actions/setup-node@v4
    with:
      node-version: '20'           # String input
      cache: 'npm'                 # String input
      registry-url: 'https://npm.pkg.github.com'

  - uses: actions/upload-artifact@v4
    with:
      name: my-artifact            # Artifact name
      path: |                      # Multi-line path input
        dist/
        build/
      retention-days: 5            # Number input
      if-no-files-found: error     # Enum input
```

### Reading Action Outputs

Actions can produce outputs that subsequent steps can use:

```yaml
steps:
  - id: get-version               # ID is required to reference outputs
    uses: some/action@v1

  - name: Use output
    run: echo "Version is ${{ steps.get-version.outputs.version }}"
```

---

## Essential Official Actions

These are maintained by GitHub and are the most commonly used actions:

### actions/checkout

Checks out your repository code. **Used in almost every workflow.**

```yaml
- uses: actions/checkout@v4
  with:
    # Common options:
    ref: 'develop'                    # Branch, tag, or SHA to checkout
    fetch-depth: 0                    # 0 = full history (needed for git log, tags)
    token: ${{ secrets.PAT }}         # Token for private repos or to trigger workflows
    submodules: 'recursive'           # Checkout submodules
    path: 'my-repo'                   # Checkout to a subdirectory
    repository: 'owner/other-repo'    # Checkout a different repository
```

### actions/setup-node

Sets up a Node.js environment:

```yaml
- uses: actions/setup-node@v4
  with:
    node-version: '20'               # Specific version
    node-version-file: '.nvmrc'      # Read from file
    cache: 'npm'                     # Cache npm dependencies
    registry-url: 'https://npm.pkg.github.com'  # For publishing
```

### actions/setup-python

Sets up a Python environment:

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: '3.12'           # Specific version
    python-version-file: '.python-version'  # Read from file
    cache: 'pip'                     # Cache pip dependencies
```

### actions/setup-java

Sets up a Java/JDK environment:

```yaml
- uses: actions/setup-java@v4
  with:
    distribution: 'temurin'          # Adoptium Temurin
    java-version: '21'
    cache: 'maven'                   # Or 'gradle'
```

### actions/setup-go

Sets up a Go environment:

```yaml
- uses: actions/setup-go@v5
  with:
    go-version: '1.22'
    cache: true                      # Cache Go modules
```

### actions/cache

Caches dependencies to speed up workflows:

```yaml
- uses: actions/cache@v4
  with:
    path: ~/.npm
    key: ${{ runner.os }}-npm-${{ hashFiles('**/package-lock.json') }}
    restore-keys: |
      ${{ runner.os }}-npm-
```

### actions/upload-artifact / actions/download-artifact

Share data between jobs:

```yaml
# In job 1: Upload
- uses: actions/upload-artifact@v4
  with:
    name: build-output
    path: dist/
    retention-days: 7

# In job 2: Download
- uses: actions/download-artifact@v4
  with:
    name: build-output
    path: dist/
```

### actions/github-script

Run JavaScript with access to the GitHub API:

```yaml
- uses: actions/github-script@v7
  with:
    script: |
      // Create a comment on a PR
      await github.rest.issues.createComment({
        owner: context.repo.owner,
        repo: context.repo.repo,
        issue_number: context.issue.number,
        body: 'CI passed! Ready for review.'
      });

      // Add a label
      await github.rest.issues.addLabels({
        owner: context.repo.owner,
        repo: context.repo.repo,
        issue_number: context.issue.number,
        labels: ['ci-passed']
      });
```

---

## Popular Community Actions

### Docker Build and Push

```yaml
- uses: docker/setup-buildx-action@v3

- uses: docker/login-action@v3
  with:
    registry: ghcr.io
    username: ${{ github.actor }}
    password: ${{ secrets.GITHUB_TOKEN }}

- uses: docker/build-push-action@v5
  with:
    context: .
    push: true
    tags: ghcr.io/${{ github.repository }}:latest
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

### Security Scanning

```yaml
# Trivy - Vulnerability scanner
- uses: aquasecurity/trivy-action@master
  with:
    scan-type: 'fs'
    format: 'sarif'
    output: 'trivy-results.sarif'

# CodeQL - GitHub's SAST tool
- uses: github/codeql-action/init@v3
  with:
    languages: javascript, python
- uses: github/codeql-action/analyze@v3

# Snyk - Dependency vulnerability scanning
- uses: snyk/actions/node@master
  env:
    SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
```

### Cloud Deployments

```yaml
# AWS
- uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::123456789:role/my-role
    aws-region: us-east-1

# Azure
- uses: azure/login@v2
  with:
    creds: ${{ secrets.AZURE_CREDENTIALS }}

# Google Cloud
- uses: google-github-actions/auth@v2
  with:
    workload_identity_provider: 'projects/123/locations/global/workloadIdentityPools/pool/providers/provider'
    service_account: 'sa@project.iam.gserviceaccount.com'
```

### Terraform

```yaml
- uses: hashicorp/setup-terraform@v3
  with:
    terraform_version: '1.7.0'

- name: Terraform Init
  run: terraform init

- name: Terraform Plan
  run: terraform plan -out=tfplan

- name: Terraform Apply
  if: github.ref == 'refs/heads/main'
  run: terraform apply -auto-approve tfplan
```

### Notifications

```yaml
# Slack notification
- uses: slackapi/slack-github-action@v1
  with:
    payload: |
      {
        "text": "Build ${{ job.status }} for ${{ github.repository }}"
      }
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

---

## GitHub Actions Marketplace

The [GitHub Marketplace](https://github.com/marketplace?type=actions) is a central place to find and share actions.

### How to Find Actions

1. **GitHub Marketplace:** https://github.com/marketplace?type=actions
2. **Search by category:** CI, security, deployment, monitoring, etc.
3. **Look for verified creators:** Blue checkmark indicates verified publishers

### Evaluating Actions Before Use

Before using a community action, check:

| Criteria | Why It Matters |
|----------|---------------|
| **Stars / Downloads** | Indicates community trust and adoption |
| **Last updated** | Stale actions may have unpatched vulnerabilities |
| **Open issues** | Many open issues may indicate poor maintenance |
| **Verified creator** | Verified publishers are more trustworthy |
| **Source code** | Review the action's code for security concerns |
| **License** | Ensure the license is compatible with your project |
| **Version pinning** | Always pin to a specific version or SHA |

---

## Action Versioning and Pinning

### Version Reference Methods

```yaml
steps:
  # 1. Major version tag (recommended for most cases)
  - uses: actions/checkout@v4       # Gets latest v4.x.x

  # 2. Exact version tag
  - uses: actions/checkout@v4.1.7   # Exact version

  # 3. Commit SHA (most secure — immutable)
  - uses: actions/checkout@8ade135a41bc03ea155e62e844d188df1ea18608

  # 4. Branch reference (NOT recommended — can change)
  - uses: actions/checkout@main     # Dangerous: code can change at any time
```

### Security Recommendation: Pin to SHA

For production workflows, pin actions to their commit SHA to prevent supply chain attacks:

```yaml
steps:
  # Instead of this:
  - uses: actions/checkout@v4

  # Use this (find SHA on the action's releases page):
  - uses: actions/checkout@8ade135a41bc03ea155e62e844d188df1ea18608  # v4.1.7
```

### Automating Version Updates with Dependabot

Create `.github/dependabot.yml` to automatically get PRs for action updates:

```yaml
version: 2
updates:
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    commit-message:
      prefix: "ci"
```

---

## Creating Custom Actions

### Composite Actions

Composite actions are the simplest to create — they're just YAML files that bundle multiple steps.

#### Directory Structure

```
.github/
  actions/
    setup-and-build/
      action.yml           # Required: action metadata
```

#### action.yml

```yaml
name: 'Setup and Build'
description: 'Install dependencies and build the project'
author: 'Your Name'

inputs:
  node-version:
    description: 'Node.js version to use'
    required: false
    default: '20'
  build-command:
    description: 'Build command to run'
    required: false
    default: 'npm run build'

outputs:
  build-path:
    description: 'Path to build output'
    value: ${{ steps.build.outputs.path }}

runs:
  using: 'composite'
  steps:
    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: ${{ inputs.node-version }}
        cache: 'npm'

    - name: Install dependencies
      shell: bash
      run: npm ci

    - name: Build
      id: build
      shell: bash
      run: |
        ${{ inputs.build-command }}
        echo "path=dist" >> "$GITHUB_OUTPUT"

    - name: Verify build
      shell: bash
      run: |
        if [ ! -d "dist" ]; then
          echo "Build output not found!"
          exit 1
        fi
        echo "Build successful! Output in dist/"
```

#### Using the Composite Action

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup and Build
        id: build
        uses: ./.github/actions/setup-and-build
        with:
          node-version: '20'
          build-command: 'npm run build:prod'

      - name: Show output
        run: echo "Build output at: ${{ steps.build.outputs.build-path }}"
```

### JavaScript Actions

JavaScript actions run directly on the runner using Node.js. They're faster than Docker actions and have access to the GitHub Actions toolkit.

#### Directory Structure

```
.github/
  actions/
    greet-user/
      action.yml
      index.js
      package.json
      node_modules/     # Must be committed!
```

#### action.yml

```yaml
name: 'Greet User'
description: 'Greets the user who triggered the workflow'

inputs:
  greeting:
    description: 'Custom greeting message'
    required: false
    default: 'Hello'

outputs:
  message:
    description: 'The greeting message that was generated'

runs:
  using: 'node20'
  main: 'index.js'
```

#### index.js

```javascript
const core = require('@actions/core');
const github = require('@actions/github');

async function run() {
  try {
    // Get inputs
    const greeting = core.getInput('greeting');
    const actor = github.context.actor;
    const repo = github.context.repo;

    // Create the greeting message
    const message = `${greeting}, ${actor}! Welcome to ${repo.owner}/${repo.repo}`;

    // Log the message
    core.info(message);

    // Set output
    core.setOutput('message', message);

    // Create a summary
    core.summary
      .addHeading('Greeting')
      .addRaw(message)
      .write();

  } catch (error) {
    core.setFailed(`Action failed: ${error.message}`);
  }
}

run();
```

#### package.json

```json
{
  "name": "greet-user-action",
  "version": "1.0.0",
  "description": "Greets the user who triggered the workflow",
  "main": "index.js",
  "dependencies": {
    "@actions/core": "^1.10.1",
    "@actions/github": "^6.0.0"
  }
}
```

> **Important:** You must commit `node_modules/` for JavaScript actions, or use a bundler like `@vercel/ncc` to compile everything into a single file.

#### Using ncc to Bundle

```bash
# Install ncc
npm install -g @vercel/ncc

# Bundle the action
ncc build index.js -o dist

# Update action.yml to point to dist/index.js
# runs:
#   using: 'node20'
#   main: 'dist/index.js'
```

### Docker Actions

Docker actions run in a container, giving you full control over the environment.

#### Directory Structure

```
.github/
  actions/
    security-scan/
      action.yml
      Dockerfile
      entrypoint.sh
```

#### action.yml

```yaml
name: 'Security Scanner'
description: 'Runs a custom security scan'

inputs:
  scan-path:
    description: 'Path to scan'
    required: false
    default: '.'
  severity:
    description: 'Minimum severity to report'
    required: false
    default: 'HIGH'

outputs:
  findings:
    description: 'Number of findings'

runs:
  using: 'docker'
  image: 'Dockerfile'
  args:
    - ${{ inputs.scan-path }}
    - ${{ inputs.severity }}
  env:
    SCAN_MODE: 'full'
```

#### Dockerfile

```dockerfile
FROM python:3.12-slim

LABEL maintainer="Your Name"
LABEL description="Custom security scanner action"

RUN pip install --no-cache-dir safety bandit

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
```

#### entrypoint.sh

```bash
#!/bin/bash
set -e

SCAN_PATH="${1:-.}"
SEVERITY="${2:-HIGH}"

echo "Scanning $SCAN_PATH for vulnerabilities (severity >= $SEVERITY)..."

# Run the scan
cd "$SCAN_PATH"

# Example: Run bandit for Python security analysis
if [ -f "requirements.txt" ]; then
  echo "Running dependency check..."
  safety check -r requirements.txt --output json || true
fi

if find . -name "*.py" -print -quit | grep -q .; then
  echo "Running static analysis..."
  FINDINGS=$(bandit -r . -f json -ll 2>/dev/null | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('results',[])))" 2>/dev/null || echo "0")
  echo "findings=$FINDINGS" >> "$GITHUB_OUTPUT"
  echo "Found $FINDINGS issues"
fi

echo "Scan complete!"
```

---

## Publishing to the Marketplace

### Requirements for Marketplace Actions

1. The action must be in a **public repository**
2. Each repository must contain a **single action**
3. The `action.yml` must be in the **root** of the repository
4. The action must have a **unique name** on the Marketplace

### action.yml for Marketplace

```yaml
name: 'My Published Action'
description: 'A detailed description of what this action does'
author: 'Your Name or Organization'

branding:
  icon: 'shield'           # Feather icon name
  color: 'blue'            # Badge color: white, yellow, blue, green, orange, red, purple, gray-dark

inputs:
  api-key:
    description: 'API key for the service'
    required: true
  environment:
    description: 'Target environment'
    required: false
    default: 'production'

outputs:
  result:
    description: 'The result of the action'

runs:
  using: 'node20'
  main: 'dist/index.js'
```

### Publishing Steps

1. **Create a public repository** for your action
2. **Add `action.yml`** to the repository root with `branding` section
3. **Tag a release** following semantic versioning:
   ```bash
   git tag -a v1.0.0 -m "Initial release"
   git push origin v1.0.0
   ```
4. **Create a GitHub Release** from the tag
5. Check the **"Publish this action to the GitHub Marketplace"** checkbox
6. **Maintain major version tags** for users who pin to `@v1`:
   ```bash
   git tag -fa v1 -m "Update v1 tag"
   git push origin v1 --force
   ```

### Versioning Strategy

```bash
# Specific version tags
git tag v1.0.0
git tag v1.0.1
git tag v1.1.0
git tag v2.0.0

# Major version tags (floating — update after each release)
git tag -fa v1 -m "Update v1 tag to v1.1.0"
git push origin v1 --force

git tag -fa v2 -m "Update v2 tag to v2.0.0"
git push origin v2 --force
```

Users reference your action as:
```yaml
- uses: your-org/your-action@v1      # Gets latest v1.x.x
- uses: your-org/your-action@v1.1.0  # Exact version
```

---

## Security Best Practices for Actions

### 1. Pin Actions to Commit SHAs

```yaml
# Secure: pinned to SHA
- uses: actions/checkout@8ade135a41bc03ea155e62e844d188df1ea18608  # v4.1.7

# Less secure: pinned to tag (tags can be moved)
- uses: actions/checkout@v4
```

### 2. Use Dependabot for Action Updates

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```

### 3. Minimize Permissions

```yaml
permissions:
  contents: read    # Only what's needed
```

### 4. Review Third-Party Actions

Before using a community action:
- Read the source code
- Check the action's `action.yml` for what permissions it needs
- Look for known vulnerabilities
- Prefer actions from verified creators

### 5. Use Environment Secrets Carefully

```yaml
# Don't pass secrets to untrusted actions
- uses: untrusted/action@v1
  with:
    token: ${{ secrets.GITHUB_TOKEN }}    # Risky!

# Better: use secrets only in your own run steps
- run: |
    curl -H "Authorization: Bearer $TOKEN" https://api.example.com
  env:
    TOKEN: ${{ secrets.API_TOKEN }}
```

### 6. Audit Action Usage

List all actions used in your workflows:

```bash
# Find all 'uses:' references in workflows
grep -r "uses:" .github/workflows/ | grep -v "#" | sort -u
```

---

## Summary

| Concept | Description |
|---------|-------------|
| **Actions** | Reusable building blocks for workflows |
| **Marketplace** | Central hub for discovering and sharing actions |
| **Composite Actions** | YAML-based; bundle multiple steps |
| **JavaScript Actions** | Node.js-based; fast execution, toolkit access |
| **Docker Actions** | Container-based; full environment control |
| **Version Pinning** | Always pin to SHA for security; use Dependabot for updates |

### Most Used Actions Quick Reference

| Action | Purpose |
|--------|---------|
| `actions/checkout@v4` | Check out repository code |
| `actions/setup-node@v4` | Set up Node.js |
| `actions/setup-python@v5` | Set up Python |
| `actions/cache@v4` | Cache dependencies |
| `actions/upload-artifact@v4` | Upload build artifacts |
| `actions/download-artifact@v4` | Download build artifacts |
| `actions/github-script@v7` | Run JavaScript with GitHub API |
| `docker/build-push-action@v5` | Build and push Docker images |
| `github/codeql-action/analyze@v3` | CodeQL security analysis |

### Key Takeaways

1. **Use official actions** (`actions/*`) whenever possible
2. **Pin actions to commit SHAs** in production workflows
3. **Use Dependabot** to keep actions up to date
4. **Composite actions** are the easiest way to create reusable steps
5. **Always review** third-party actions before using them
6. **Publish your own actions** to share reusable CI/CD logic

---

**Next Lesson:** [05 - Environment Variables and Secrets](./05-environment-variables-and-secrets.md) — Managing configuration and sensitive data.
