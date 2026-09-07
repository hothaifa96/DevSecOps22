# Lesson 5: Environment Variables and Secrets

## Table of Contents

- [Overview](#overview)
- [The env Keyword](#the-env-keyword)
- [Setting Environment Variables Dynamically](#setting-environment-variables-dynamically)
- [Default Environment Variables](#default-environment-variables)
- [Configuration Variables (vars)](#configuration-variables-vars)
- [GITHUB_TOKEN](#github_token)
- [Encrypted Secrets](#encrypted-secrets)
  - [Repository Secrets](#repository-secrets)
  - [Organization Secrets](#organization-secrets)
  - [Environment Secrets](#environment-secrets)
- [Using Secrets in Workflows](#using-secrets-in-workflows)
- [OIDC for Cloud Authentication](#oidc-for-cloud-authentication)
- [Secrets Security Best Practices](#secrets-security-best-practices)
- [Summary](#summary)

---

## Overview

GitHub Actions provides multiple ways to manage configuration and sensitive data:

| Mechanism | Purpose | Encrypted | Scope |
|-----------|---------|-----------|-------|
| `env` keyword | Non-sensitive configuration | No | Workflow/Job/Step |
| Default env vars | GitHub-provided context | No | All steps |
| `vars` | Non-sensitive repo/org settings | No | Repo/Org/Environment |
| `secrets` | Sensitive credentials | Yes | Repo/Org/Environment |
| `GITHUB_TOKEN` | Auto-generated auth token | Yes | Workflow run |
| OIDC tokens | Cloud authentication | Yes | Workflow run |

---

## The env Keyword

The `env` keyword sets environment variables at three levels:

### Workflow Level

Available to **all jobs and steps**:

```yaml
name: CI Pipeline

env:
  NODE_ENV: production
  APP_NAME: my-application
  REGISTRY: ghcr.io

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: echo "Building $APP_NAME for $NODE_ENV"
```

### Job Level

Available to **all steps in that job** (overrides workflow-level):

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    env:
      DATABASE_URL: postgres://localhost:5432/testdb
      NODE_ENV: test
    steps:
      - run: echo "Testing with $DATABASE_URL"

  deploy:
    runs-on: ubuntu-latest
    env:
      NODE_ENV: production
    steps:
      - run: echo "Deploying in $NODE_ENV mode"
```

### Step Level

Available to **that step only** (overrides job-level):

```yaml
steps:
  - name: Run tests
    env:
      DATABASE_URL: postgres://localhost:5432/testdb
      DEBUG: 'true'
    run: npm test

  - name: Build for production
    env:
      NODE_ENV: production
      DEBUG: 'false'
    run: npm run build
```

### Precedence Order

**Step > Job > Workflow** — the most specific level wins:

```yaml
env:
  MY_VAR: workflow-value         # 1. Workflow level

jobs:
  example:
    env:
      MY_VAR: job-value          # 2. Job level (overrides workflow)
    runs-on: ubuntu-latest
    steps:
      - name: Step with override
        env:
          MY_VAR: step-value     # 3. Step level (overrides job)
        run: echo "$MY_VAR"      # Prints: step-value

      - name: Step without override
        run: echo "$MY_VAR"      # Prints: job-value
```

### Using env in Expressions vs Shell

```yaml
env:
  MY_VAR: hello

steps:
  # In shell commands — use $ prefix
  - run: echo "$MY_VAR"

  # In GitHub expressions — use env context
  - run: echo "Value is ${{ env.MY_VAR }}"

  # In conditionals — use env context
  - name: Only in production
    if: env.NODE_ENV == 'production'
    run: echo "Production mode"
```

---

## Setting Environment Variables Dynamically

You can set environment variables during workflow execution using `GITHUB_ENV`:

### Using GITHUB_ENV

```yaml
steps:
  - name: Set variables dynamically
    run: |
      echo "VERSION=$(cat version.txt)" >> "$GITHUB_ENV"
      echo "BUILD_DATE=$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$GITHUB_ENV"
      echo "SHORT_SHA=${GITHUB_SHA::7}" >> "$GITHUB_ENV"

  - name: Use the variables
    run: |
      echo "Version: $VERSION"
      echo "Build Date: $BUILD_DATE"
      echo "Short SHA: $SHORT_SHA"
```

### Setting Multi-Line Variables

```yaml
steps:
  - name: Set multi-line variable
    run: |
      echo "CHANGELOG<<EOF" >> "$GITHUB_ENV"
      git log --oneline -5 >> "$GITHUB_ENV"
      echo "EOF" >> "$GITHUB_ENV"

  - name: Use multi-line variable
    run: echo "$CHANGELOG"
```

### Setting Step Outputs with GITHUB_OUTPUT

For passing values between steps within the same job:

```yaml
steps:
  - name: Set output
    id: my-step
    run: |
      echo "version=1.2.3" >> "$GITHUB_OUTPUT"
      echo "should-deploy=true" >> "$GITHUB_OUTPUT"

  - name: Use output
    run: echo "Version: ${{ steps.my-step.outputs.version }}"

  - name: Conditional on output
    if: steps.my-step.outputs.should-deploy == 'true'
    run: echo "Deploying..."
```

---

## Default Environment Variables

GitHub automatically sets these environment variables for every workflow run:

### Most Useful Default Variables

| Variable | Description | Example Value |
|----------|-------------|---------------|
| `GITHUB_REPOSITORY` | Owner/repo name | `octocat/my-repo` |
| `GITHUB_REPOSITORY_OWNER` | Repository owner | `octocat` |
| `GITHUB_REF` | Full ref that triggered the run | `refs/heads/main` |
| `GITHUB_REF_NAME` | Short ref name | `main` |
| `GITHUB_SHA` | Full commit SHA | `a1b2c3d4e5f6...` |
| `GITHUB_ACTOR` | User who triggered the workflow | `octocat` |
| `GITHUB_EVENT_NAME` | Event that triggered the run | `push` |
| `GITHUB_WORKSPACE` | Runner workspace path | `/home/runner/work/repo/repo` |
| `GITHUB_RUN_ID` | Unique run identifier | `123456789` |
| `GITHUB_RUN_NUMBER` | Sequential run number | `42` |
| `GITHUB_RUN_ATTEMPT` | Re-run attempt number | `1` |
| `GITHUB_JOB` | Current job ID | `build` |
| `GITHUB_ACTION` | Current action name | `run1` |
| `GITHUB_WORKFLOW` | Workflow name | `CI Pipeline` |
| `GITHUB_SERVER_URL` | GitHub server URL | `https://github.com` |
| `GITHUB_API_URL` | GitHub API URL | `https://api.github.com` |
| `RUNNER_OS` | Runner operating system | `Linux` |
| `RUNNER_ARCH` | Runner architecture | `X64` |
| `RUNNER_TEMP` | Temp directory path | `/home/runner/work/_temp` |

### Accessing Default Variables

```yaml
steps:
  - name: Show context (shell variables)
    run: |
      echo "Repository: $GITHUB_REPOSITORY"
      echo "Branch: $GITHUB_REF_NAME"
      echo "Commit: $GITHUB_SHA"
      echo "Actor: $GITHUB_ACTOR"
      echo "Runner: $RUNNER_OS / $RUNNER_ARCH"

  - name: Show context (expressions)
    run: |
      echo "Repository: ${{ github.repository }}"
      echo "Branch: ${{ github.ref_name }}"
      echo "Commit: ${{ github.sha }}"
      echo "Actor: ${{ github.actor }}"
      echo "Runner: ${{ runner.os }} / ${{ runner.arch }}"
```

---

## Configuration Variables (vars)

**Configuration variables** (also called repository variables) are non-sensitive values stored in GitHub settings and accessible via `${{ vars.VARIABLE_NAME }}`.

### Creating Variables

1. Go to **Settings > Secrets and variables > Actions**
2. Click the **Variables** tab
3. Click **New repository variable**
4. Enter a name and value

### Using Variables

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to configured URL
        run: |
          echo "Deploying to: ${{ vars.DEPLOY_URL }}"
          echo "App name: ${{ vars.APP_NAME }}"
          echo "Region: ${{ vars.AWS_REGION }}"
```

### Variables vs Secrets vs env

| Feature | `vars` | `secrets` | `env` |
|---------|--------|-----------|-------|
| **Where defined** | GitHub UI / API | GitHub UI / API | Workflow YAML |
| **Encrypted** | No | Yes | No |
| **Visible in logs** | Yes | Masked (***) | Yes |
| **Use case** | Non-sensitive config | Passwords, tokens, keys | Build-time config |
| **Syntax** | `${{ vars.NAME }}` | `${{ secrets.NAME }}` | `${{ env.NAME }}` or `$NAME` |

---

## GITHUB_TOKEN

The `GITHUB_TOKEN` is an **automatically generated** token for each workflow run. It provides authenticated access to the GitHub API for the current repository.

### Default Permissions

The token's default permissions depend on your repository settings:

| Scope | Default (Permissive) | Default (Restricted) |
|-------|---------------------|---------------------|
| `contents` | `write` | `read` |
| `metadata` | `read` | `read` |
| `packages` | `write` | `read` |
| `pull-requests` | `write` | `none` |
| All others | varies | `none` |

> **Recommendation:** Set your repository's default token permissions to **restricted** (read-only) and explicitly grant permissions per workflow.

### Using GITHUB_TOKEN

```yaml
permissions:
  contents: read
  pull-requests: write
  packages: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      # Method 1: Automatically available as secrets.GITHUB_TOKEN
      - name: Create PR comment
        uses: actions/github-script@v7
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          script: |
            await github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              body: 'Build passed!'
            });

      # Method 2: Use in shell via environment variable
      - name: Push to GHCR
        run: |
          echo "${{ secrets.GITHUB_TOKEN }}" | docker login ghcr.io -u ${{ github.actor }} --password-stdin
          docker push ghcr.io/${{ github.repository }}:latest

      # Method 3: GitHub CLI auto-detects it
      - name: Create release
        run: gh release create v1.0.0 --generate-notes
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### GITHUB_TOKEN Limitations

| Limitation | Description |
|-----------|-------------|
| **Single repo** | Only has access to the current repository |
| **Cannot trigger workflows** | Pushes using GITHUB_TOKEN won't trigger other workflows |
| **Expires** | Token expires when the job completes |
| **Fork PRs** | Read-only for pull requests from forks |

### When to Use a Personal Access Token (PAT) Instead

```yaml
# Use PAT when you need to:
# - Trigger other workflows on push
# - Access other repositories
# - Perform admin-level operations

steps:
  - uses: actions/checkout@v4
    with:
      token: ${{ secrets.PAT }}    # PAT stored as a secret

  - name: Push changes (will trigger other workflows)
    run: |
      git add .
      git commit -m "Automated update"
      git push
```

---

## Encrypted Secrets

Secrets are encrypted values that you can use in workflows. They are **never exposed in logs** — GitHub automatically masks them with `***`.

### Repository Secrets

Scoped to a single repository. Set in **Settings > Secrets and variables > Actions > Secrets**.

```yaml
steps:
  - name: Deploy with API key
    run: |
      curl -X POST \
        -H "Authorization: Bearer $API_KEY" \
        https://api.example.com/deploy
    env:
      API_KEY: ${{ secrets.DEPLOY_API_KEY }}
```

### Organization Secrets

Scoped to an entire organization. Can be limited to specific repositories or made available to all.

```yaml
# Organization secret shared across repos
steps:
  - name: Use org-level secret
    run: echo "Using shared credentials"
    env:
      SHARED_TOKEN: ${{ secrets.ORG_DEPLOY_TOKEN }}
```

**Setting org secrets visibility:**
- **All repositories** — every repo in the org can use it
- **Private repositories** — only private repos can use it
- **Selected repositories** — manually pick which repos have access

### Environment Secrets

Scoped to a specific GitHub Environment. Only available to jobs that reference that environment.

```yaml
jobs:
  deploy-production:
    runs-on: ubuntu-latest
    environment: production          # Must reference the environment
    steps:
      - name: Deploy
        run: |
          echo "Using production-specific secrets"
          ./deploy.sh
        env:
          DB_PASSWORD: ${{ secrets.DB_PASSWORD }}         # Environment secret
          API_KEY: ${{ secrets.PRODUCTION_API_KEY }}       # Environment secret
```

### Secret Precedence

When secrets with the same name exist at multiple levels:

**Environment > Repository > Organization**

### Creating Secrets

#### Via GitHub UI

1. Go to **Settings > Secrets and variables > Actions**
2. Click **New repository secret**
3. Enter name (e.g., `DEPLOY_TOKEN`) and value
4. Click **Add secret**

#### Via GitHub CLI

```bash
# Set a repository secret
gh secret set DEPLOY_TOKEN --body "your-secret-value"

# Set from a file
gh secret set SSH_KEY < ~/.ssh/id_rsa

# Set an environment secret
gh secret set DB_PASSWORD --env production --body "super-secret"

# Set an organization secret
gh secret set ORG_TOKEN --org my-org --visibility all --body "token-value"

# List secrets
gh secret list
gh secret list --env production
```

---

## Using Secrets in Workflows

### Basic Usage

```yaml
steps:
  # As environment variable (recommended)
  - name: Use secret as env var
    run: |
      echo "Deploying with credentials..."
      ./deploy.sh
    env:
      API_KEY: ${{ secrets.API_KEY }}
      DB_PASSWORD: ${{ secrets.DB_PASSWORD }}

  # As action input
  - uses: docker/login-action@v3
    with:
      registry: ghcr.io
      username: ${{ github.actor }}
      password: ${{ secrets.GITHUB_TOKEN }}
```

### Secrets Are Automatically Masked

```yaml
steps:
  - name: This will be masked
    run: echo "My token is ${{ secrets.API_KEY }}"
    # Output: My token is ***

  - name: Even in multi-line output
    run: |
      echo "Token: $TOKEN"
      curl -H "Authorization: Bearer $TOKEN" https://api.example.com
    env:
      TOKEN: ${{ secrets.API_KEY }}
    # TOKEN value will be replaced with *** in logs
```

### Passing Secrets to Reusable Workflows

```yaml
jobs:
  deploy:
    uses: ./.github/workflows/deploy.yml
    with:
      environment: production
    secrets:
      deploy-token: ${{ secrets.DEPLOY_TOKEN }}
      api-key: ${{ secrets.API_KEY }}

  # Or pass ALL secrets
  deploy-all:
    uses: ./.github/workflows/deploy.yml
    secrets: inherit
```

### Secrets in Conditionals

You cannot directly use secrets in `if` conditions. Use an intermediate step:

```yaml
steps:
  - name: Check if secret exists
    id: check-secret
    run: |
      if [ -n "$SECRET_VALUE" ]; then
        echo "has-secret=true" >> "$GITHUB_OUTPUT"
      else
        echo "has-secret=false" >> "$GITHUB_OUTPUT"
      fi
    env:
      SECRET_VALUE: ${{ secrets.OPTIONAL_SECRET }}

  - name: Use secret if available
    if: steps.check-secret.outputs.has-secret == 'true'
    run: echo "Secret is available, proceeding..."
    env:
      SECRET: ${{ secrets.OPTIONAL_SECRET }}
```

---

## OIDC for Cloud Authentication

**OpenID Connect (OIDC)** allows your workflows to authenticate with cloud providers **without storing long-lived credentials as secrets**. This is the recommended approach for cloud deployments.

### How OIDC Works

```
┌──────────────┐     1. Request OIDC token     ┌──────────────┐
│   GitHub      │ ─────────────────────────────▶ │  GitHub OIDC │
│   Actions     │                                │  Provider    │
│   Workflow    │ ◀───────────────────────────── │              │
│               │     2. Return JWT token        └──────────────┘
│               │
│               │     3. Present JWT to cloud    ┌──────────────┐
│               │ ─────────────────────────────▶ │  Cloud       │
│               │                                │  Provider    │
│               │ ◀───────────────────────────── │  (AWS/Azure/ │
│               │     4. Return temporary creds  │   GCP)       │
└──────────────┘                                 └──────────────┘
```

### Benefits Over Static Secrets

| Feature | Static Secrets | OIDC |
|---------|---------------|------|
| **Credential rotation** | Manual | Automatic (short-lived tokens) |
| **Blast radius** | Long-lived, broad access | Short-lived, scoped |
| **Secret management** | Must store and rotate | No secrets to manage |
| **Audit trail** | Limited | Full trace via cloud provider |
| **Revocation** | Must update secret | Modify trust policy |

### AWS OIDC Authentication

#### 1. Set Up AWS Trust Policy

Create an IAM role with a trust policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:my-org/my-repo:*"
        }
      }
    }
  ]
}
```

#### 2. Use in Workflow

```yaml
permissions:
  id-token: write    # Required for OIDC
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials via OIDC
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/github-actions-role
          aws-region: us-east-1
          # No access keys needed!

      - name: Deploy to AWS
        run: |
          aws s3 sync dist/ s3://my-bucket/
          aws ecs update-service --cluster my-cluster --service my-service --force-new-deployment
```

### Azure OIDC Authentication

```yaml
permissions:
  id-token: write
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Azure Login via OIDC
        uses: azure/login@v2
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
          # No client secret needed!

      - name: Deploy to Azure
        run: az webapp deploy --name my-app --src-path dist/
```

### Google Cloud OIDC Authentication

```yaml
permissions:
  id-token: write
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Authenticate to Google Cloud via OIDC
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: 'projects/123456789/locations/global/workloadIdentityPools/github-pool/providers/github-provider'
          service_account: 'deploy-sa@my-project.iam.gserviceaccount.com'
          # No service account key needed!

      - name: Deploy to Cloud Run
        uses: google-github-actions/deploy-cloudrun@v2
        with:
          service: my-service
          region: us-central1
          image: gcr.io/my-project/my-app:${{ github.sha }}
```

---

## Secrets Security Best Practices

### 1. Never Hardcode Secrets

```yaml
# NEVER do this
steps:
  - run: curl -H "Authorization: Bearer abc123secret" https://api.example.com

# Always use secrets
steps:
  - run: curl -H "Authorization: Bearer $TOKEN" https://api.example.com
    env:
      TOKEN: ${{ secrets.API_TOKEN }}
```

### 2. Use Least Privilege Principle

```yaml
permissions:
  contents: read        # Only what's needed
  packages: write       # Only if publishing packages

# Don't use:
# permissions: write-all
```

### 3. Prefer OIDC Over Static Secrets

For cloud providers (AWS, Azure, GCP), always prefer OIDC tokens over stored access keys.

### 4. Use Environment-Scoped Secrets

```yaml
# Environment secrets require approval and limit exposure
jobs:
  deploy:
    environment: production    # Requires approval to access secrets
    runs-on: ubuntu-latest
    steps:
      - run: echo "Using production secrets"
        env:
          DB_PASSWORD: ${{ secrets.PROD_DB_PASSWORD }}
```

### 5. Rotate Secrets Regularly

- Set reminders to rotate secrets periodically
- Use OIDC where possible to eliminate manual rotation
- Audit secret usage via GitHub's audit log

### 6. Don't Print Secrets

```yaml
# GitHub masks known secrets, but be careful with transformations
steps:
  # BAD: Secret might not be masked if encoded/transformed
  - run: echo "${{ secrets.TOKEN }}" | base64

  # GOOD: Use secrets directly where needed
  - run: ./deploy.sh
    env:
      TOKEN: ${{ secrets.TOKEN }}
```

### 7. Limit Secret Exposure in Pull Requests

- Secrets are **not available** to workflows triggered by `pull_request` from forks
- This is a security feature — don't work around it
- Use `pull_request_target` carefully if you need secrets in PR workflows

---

## Summary

| Feature | Access Syntax | Encrypted | Use For |
|---------|-------------|-----------|---------|
| **env (YAML)** | `${{ env.NAME }}` or `$NAME` | No | Build configuration |
| **Default env vars** | `$GITHUB_SHA`, `$GITHUB_REF` | No | Workflow context |
| **vars** | `${{ vars.NAME }}` | No | Non-sensitive repo settings |
| **secrets** | `${{ secrets.NAME }}` | Yes | Passwords, tokens, keys |
| **GITHUB_TOKEN** | `${{ secrets.GITHUB_TOKEN }}` | Yes | GitHub API access |
| **GITHUB_ENV** | Write to `$GITHUB_ENV` | No | Dynamic env vars |
| **GITHUB_OUTPUT** | Write to `$GITHUB_OUTPUT` | No | Step-to-step data |
| **OIDC** | `id-token: write` permission | Yes | Cloud authentication |

### Key Takeaways

1. **Use `env`** for non-sensitive build configuration
2. **Use `secrets`** for any sensitive data — they're automatically masked in logs
3. **Use `GITHUB_TOKEN`** for GitHub API operations — no setup needed
4. **Use OIDC** for cloud authentication — eliminates long-lived secrets
5. **Follow least privilege** — restrict token permissions to the minimum needed
6. **Use environment secrets** for production credentials with approval gates
7. **Never hardcode secrets** in workflow files or repository code

---

**Next Lesson:** [06 - Jobs and Matrices](./06-jobs-and-matrices.md) — Parallel jobs, matrix builds, and reusable workflows.
