# Lab 04: Secrets and Variables

## Overview

In this lab, you will learn how to securely manage sensitive data (API keys, tokens, passwords) and configuration variables in GitHub Actions. You will configure repository-level secrets, organization secrets, environment-specific secrets, and workflow variables while understanding how GitHub protects these values.

---

## Objectives

By the end of this lab, you will be able to:

- Create and manage repository secrets in GitHub
- Access secrets within a workflow using the `secrets` context
- Understand how GitHub masks secrets in logs
- Configure environment-level secrets for staging and production
- Use GitHub Actions variables for non-sensitive configuration
- Pass secrets between jobs securely
- Understand the security model for secrets in pull requests

---

## Prerequisites

- Completed **Lab 01** (repository `github-actions-labs` exists)
- Repository admin access (required to manage secrets)
- Familiarity with environment variables in shell scripting

---

## Step-by-Step Instructions

### Step 1: Create Repository Secrets

1. Go to your repository on GitHub.
2. Navigate to **Settings** > **Secrets and variables** > **Actions**.
3. Click **New repository secret**.
4. Create the following secrets:

| Name | Value (Example) |
|------|-----------------|
| `API_KEY` | `sk-test-abc123def456` |
| `DATABASE_URL` | `postgresql://user:pass@localhost:5432/mydb` |
| `NOTIFICATION_WEBHOOK` | `https://hooks.example.com/webhook/12345` |

> **Important**: These are example values for learning. In a real project, use actual credentials.

### Step 2: Create Repository Variables

1. On the same **Secrets and variables** > **Actions** page, click the **Variables** tab.
2. Click **New repository variable**.
3. Create the following variables:

| Name | Value |
|------|-------|
| `APP_NAME` | `my-devsecops-app` |
| `LOG_LEVEL` | `info` |
| `MAX_RETRIES` | `3` |

> Variables are for non-sensitive configuration. Unlike secrets, their values are visible in settings.

### Step 3: Create a Workflow That Uses Secrets

Create `.github/workflows/secrets-demo.yml`:

```yaml
name: Secrets and Variables Demo

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  demonstrate-secrets:
    name: Secrets Usage Demo
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Access secrets as environment variables
        env:
          MY_API_KEY: ${{ secrets.API_KEY }}
          MY_DB_URL: ${{ secrets.DATABASE_URL }}
        run: |
          echo "=== Demonstrating Secret Masking ==="

          # GitHub automatically masks secret values in logs
          echo "API Key value: $MY_API_KEY"
          echo "Notice: The above line shows *** because GitHub masks secrets"

          # Check if a secret is set (without revealing its value)
          if [ -n "$MY_API_KEY" ]; then
            echo "API_KEY is configured (length: ${#MY_API_KEY} characters)"
          else
            echo "API_KEY is NOT configured"
          fi

          if [ -n "$MY_DB_URL" ]; then
            echo "DATABASE_URL is configured (length: ${#MY_DB_URL} characters)"
          else
            echo "DATABASE_URL is NOT configured"
          fi

      - name: Access variables
        env:
          APP_NAME: ${{ vars.APP_NAME }}
          LOG_LEVEL: ${{ vars.LOG_LEVEL }}
          MAX_RETRIES: ${{ vars.MAX_RETRIES }}
        run: |
          echo "=== Repository Variables ==="
          echo "App Name: $APP_NAME"
          echo "Log Level: $LOG_LEVEL"
          echo "Max Retries: $MAX_RETRIES"

          echo "Note: Variables are NOT masked - their values are visible"

      - name: Use secrets in a simulated API call
        env:
          API_KEY: ${{ secrets.API_KEY }}
          WEBHOOK_URL: ${{ secrets.NOTIFICATION_WEBHOOK }}
        run: |
          echo "=== Simulated API Call ==="
          echo "Making request with API key to application endpoint..."

          # Simulating an authenticated API call
          # In a real workflow, you might use curl:
          # curl -H "Authorization: Bearer $API_KEY" https://api.example.com/data

          echo "Simulated request sent successfully"
          echo "Would notify webhook at the configured URL"

      - name: Demonstrate secret in conditional logic
        env:
          API_KEY: ${{ secrets.API_KEY }}
        run: |
          # You can use secrets in conditionals without exposing them
          if [ "$API_KEY" = "sk-test-abc123def456" ]; then
            echo "Using test API key"
          else
            echo "Using production API key"
          fi
```

### Step 4: Commit and Observe Secret Masking

```bash
git add .github/workflows/secrets-demo.yml
git commit -m "Add secrets and variables demo workflow"
git push origin main
```

Go to **Actions** and examine the logs. Notice:
- Secret values appear as `***` in the logs.
- Variable values are displayed in plain text.
- The length of secrets is visible but not their content.

### Step 5: Set Up Environments

GitHub Environments let you define secrets and protection rules for different deployment targets.

1. Go to **Settings** > **Environments**.
2. Click **New environment** and create **staging**.
3. Click **New environment** again and create **production**.

### Step 6: Configure Environment-Specific Secrets

For the **staging** environment:
1. Click on **staging**.
2. Under **Environment secrets**, click **Add secret**.
3. Add:

| Name | Value |
|------|-------|
| `DEPLOY_URL` | `https://staging.example.com` |
| `DEPLOY_TOKEN` | `staging-token-xyz789` |

For the **production** environment:
1. Click on **production**.
2. Add **required reviewers** (add your own username for this lab).
3. Under **Environment secrets**, click **Add secret**.
4. Add:

| Name | Value |
|------|-------|
| `DEPLOY_URL` | `https://production.example.com` |
| `DEPLOY_TOKEN` | `prod-token-abc123-secure` |

### Step 7: Add Environment Protection Rules

For the **production** environment:
1. Check **Required reviewers** and add yourself.
2. Optionally set a **wait timer** (e.g., 5 minutes).
3. Under **Deployment branches**, select **Selected branches** and add `main`.

### Step 8: Create an Environment-Aware Workflow

Create `.github/workflows/environment-secrets.yml`:

```yaml
name: Environment Secrets Demo

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    environment: staging

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Deploy to staging
        env:
          DEPLOY_URL: ${{ secrets.DEPLOY_URL }}
          DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}
        run: |
          echo "=== Deploying to Staging ==="
          echo "Target URL is configured: $([ -n '$DEPLOY_URL' ] && echo 'yes' || echo 'no')"
          echo "Token is configured: $([ -n '$DEPLOY_TOKEN' ] && echo 'yes' || echo 'no')"
          echo "Simulating deployment to staging..."
          sleep 2
          echo "Staging deployment complete!"

  deploy-production:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: deploy-staging
    environment: production

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Deploy to production
        env:
          DEPLOY_URL: ${{ secrets.DEPLOY_URL }}
          DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}
        run: |
          echo "=== Deploying to Production ==="
          echo "Target URL is configured: $([ -n '$DEPLOY_URL' ] && echo 'yes' || echo 'no')"
          echo "Token is configured: $([ -n '$DEPLOY_TOKEN' ] && echo 'yes' || echo 'no')"
          echo "Simulating deployment to production..."
          sleep 2
          echo "Production deployment complete!"
```

### Step 9: Commit, Push, and Approve

```bash
git add .github/workflows/environment-secrets.yml
git commit -m "Add environment-specific secrets workflow"
git push origin main
```

1. Watch the staging job run automatically.
2. The production job will pause and wait for approval (if you configured required reviewers).
3. Go to the workflow run and click **Review deployments**.
4. Approve the production deployment.
5. Watch the production job execute with its own set of secrets.

### Step 10: Passing Data Between Jobs

Secrets cannot be directly passed between jobs. Use outputs for non-sensitive data:

```yaml
jobs:
  generate:
    name: Generate Configuration
    runs-on: ubuntu-latest
    outputs:
      build-id: ${{ steps.build.outputs.build_id }}
      timestamp: ${{ steps.build.outputs.timestamp }}
    steps:
      - name: Generate build metadata
        id: build
        run: |
          BUILD_ID="build-$(date +%Y%m%d-%H%M%S)-${GITHUB_SHA::8}"
          echo "build_id=$BUILD_ID" >> $GITHUB_OUTPUT
          echo "timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $GITHUB_OUTPUT
          echo "Generated Build ID: $BUILD_ID"

  consume:
    name: Use Generated Data
    runs-on: ubuntu-latest
    needs: generate
    steps:
      - name: Use outputs from previous job
        run: |
          echo "Build ID: ${{ needs.generate.outputs.build-id }}"
          echo "Timestamp: ${{ needs.generate.outputs.timestamp }}"
```

### Step 11: Understanding the Security Model

Create a quick reference file in your repo. Create `docs/secrets-security.md`:

```markdown
# Secrets Security Model

## Key Rules
1. Secrets are NOT passed to workflows triggered by pull requests from forks
2. Secrets are encrypted at rest and masked in logs
3. Secrets are not available in composite actions as environment variables
4. Workflow runs can access secrets only if the workflow file is in the default branch
5. Anyone with write access to the repo can access all repository-level secrets in workflows
6. Environment secrets are only accessible to jobs that reference that environment

## Best Practices
- Rotate secrets regularly
- Use environment-specific secrets for deployment credentials
- Use OIDC (OpenID Connect) instead of long-lived credentials where possible
- Audit secret usage via the organization audit log
- Never echo or log secret values (even though GitHub masks them)
- Use least-privilege tokens with minimum required scopes
```

---

## Expected Outcomes

After completing this lab, you should see:

1. Repository secrets configured and masked (`***`) in workflow logs.
2. Repository variables displayed in plain text in workflow logs.
3. Two GitHub Environments (staging and production) with their own secrets.
4. The production environment requiring manual approval before deployment.
5. Environment-specific secrets resolving to different values in each environment's job.
6. Job outputs being used to pass non-sensitive data between jobs.

---

## Bonus Challenges

1. **Use GITHUB_TOKEN** the built-in secret, to create an issue via the GitHub API:
   ```yaml
   - name: Create an issue
     env:
       GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
     run: |
       gh issue create \
         --title "Automated: Build ${{ github.run_number }}" \
         --body "Build completed successfully at $(date)"
   ```

2. **Set up OIDC authentication** with a cloud provider (AWS, Azure, or GCP) to eliminate long-lived credentials:
   ```yaml
   - name: Configure AWS credentials
     uses: aws-actions/configure-aws-credentials@v4
     with:
       role-to-assume: arn:aws:iam::123456789012:role/github-actions
       aws-region: us-east-1
   ```

3. **Create an organization-level secret** (if you have an organization) and verify it is accessible from multiple repositories.

4. **Implement a secret rotation workflow** that periodically validates secrets are still functional and alerts if they have expired.

5. **Test the fork PR security model** by forking your repository and opening a PR, then observe that secrets are not available in the forked PR's workflow run.

---

## Key Concepts Learned

- **Repository Secrets**: Encrypted values accessible to all workflows in a repository
- **Environment Secrets**: Encrypted values scoped to a specific deployment environment
- **Variables**: Non-sensitive configuration values visible in settings and logs
- **Secret Masking**: GitHub automatically replaces secret values with `***` in logs
- **Environment Protection Rules**: Approval gates, wait timers, and branch restrictions
- **`GITHUB_TOKEN`**: An automatically generated token for authenticating with the GitHub API
- **`$GITHUB_OUTPUT`**: File used to set step outputs for passing data between steps and jobs
- **OIDC**: OpenID Connect enables short-lived, automatically rotated credentials for cloud providers
