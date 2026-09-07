# Lesson 8: Environments and Deployments

## Table of Contents

- [What Are GitHub Environments?](#what-are-github-environments)
- [Creating Environments](#creating-environments)
- [Using Environments in Workflows](#using-environments-in-workflows)
- [Protection Rules](#protection-rules)
  - [Required Reviewers](#required-reviewers)
  - [Wait Timers](#wait-timers)
  - [Deployment Branches and Tags](#deployment-branches-and-tags)
  - [Custom Branch Policies](#custom-branch-policies)
- [Environment Secrets and Variables](#environment-secrets-and-variables)
- [Deployment Workflows](#deployment-workflows)
- [Deployment Status and History](#deployment-status-and-history)
- [Rollback Strategies](#rollback-strategies)
- [Multi-Environment Pipeline](#multi-environment-pipeline)
- [Best Practices](#best-practices)
- [Summary](#summary)

---

## What Are GitHub Environments?

**GitHub Environments** represent deployment targets (e.g., staging, production) and provide:

- **Protection rules** — approval gates, wait timers, branch restrictions
- **Environment-specific secrets** — credentials scoped to a specific environment
- **Environment-specific variables** — configuration values per environment
- **Deployment history** — visual log of all deployments to each environment
- **Deployment URLs** — link to the deployed application

### Environment Hierarchy

```
Repository
├── Environment: development
│   ├── Secrets: DEV_API_KEY, DEV_DB_URL
│   ├── Variables: API_URL, DEBUG_MODE
│   └── Protection: None (auto-deploy)
│
├── Environment: staging
│   ├── Secrets: STAGING_API_KEY, STAGING_DB_URL
│   ├── Variables: API_URL, DEBUG_MODE
│   └── Protection: Deploy from main/develop only
│
└── Environment: production
    ├── Secrets: PROD_API_KEY, PROD_DB_URL
    ├── Variables: API_URL, DEBUG_MODE
    └── Protection: Required reviewers + wait timer + main branch only
```

---

## Creating Environments

### Via GitHub UI

1. Go to **Settings > Environments**
2. Click **New environment**
3. Enter a name (e.g., `production`)
4. Configure protection rules, secrets, and variables

### Via GitHub CLI

```bash
# Create an environment (environments are auto-created when referenced)
# But to configure protection rules, use the API:

# Create environment with the REST API
curl -X PUT \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/OWNER/REPO/environments/production \
  -d '{
    "wait_timer": 5,
    "reviewers": [
      {"type": "User", "id": 12345}
    ],
    "deployment_branch_policy": {
      "protected_branches": false,
      "custom_branch_policies": true
    }
  }'
```

### Via Terraform

```hcl
resource "github_repository_environment" "production" {
  environment = "production"
  repository  = github_repository.my_repo.name

  wait_timer = 5

  reviewers {
    users = [data.github_user.deployer.id]
    teams = [data.github_team.devops.id]
  }

  deployment_branch_policy {
    protected_branches     = false
    custom_branch_policies = true
  }
}

resource "github_repository_environment_deployment_policy" "production_main" {
  repository     = github_repository.my_repo.name
  environment    = github_repository_environment.production.environment
  branch_pattern = "main"
}
```

---

## Using Environments in Workflows

### Basic Environment Reference

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production          # Simple string reference
    steps:
      - run: echo "Deploying to production"
```

### Environment with URL

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://myapp.example.com     # Shows as a link in the Actions UI
    steps:
      - run: echo "Deploying to production"
```

### Dynamic Environment URL

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: staging
      url: ${{ steps.deploy.outputs.url }}
    steps:
      - id: deploy
        run: |
          # Deploy and get the URL
          DEPLOY_URL="https://staging-${{ github.sha }}.example.com"
          echo "url=$DEPLOY_URL" >> "$GITHUB_OUTPUT"
```

### Environment from Input

```yaml
on:
  workflow_dispatch:
    inputs:
      environment:
        description: 'Target environment'
        type: environment              # Special input type — shows environment dropdown
        required: true

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: ${{ inputs.environment }}
    steps:
      - run: echo "Deploying to ${{ inputs.environment }}"
```

---

## Protection Rules

Protection rules add safety gates to your deployment process.

### Required Reviewers

One or more people or teams must approve the deployment before it proceeds.

**Setup (UI):**
1. Go to Settings > Environments > production
2. Check "Required reviewers"
3. Add up to 6 reviewers (users or teams)

**Behavior:**
- When a workflow reaches a job with this environment, it **pauses**
- Reviewers receive a notification
- A reviewer must click **"Approve and deploy"** in the Actions UI
- If rejected, the workflow fails

```yaml
# When this job is reached, it pauses for approval
jobs:
  deploy-production:
    runs-on: ubuntu-latest
    environment: production         # Triggers the approval gate
    steps:
      - run: echo "This only runs after approval"
```

### Wait Timers

Add a delay before the deployment proceeds (even after approval). Useful for:
- Giving teams time to react
- Scheduling deployments during maintenance windows
- Allowing for last-minute cancellations

**Setup (UI):**
1. Go to Settings > Environments > production
2. Check "Wait timer"
3. Set minutes (0-43200, i.e., up to 30 days)

```yaml
# If production has a 5-minute wait timer:
# 1. Job reaches environment reference
# 2. Reviewer approves (if required)
# 3. 5-minute timer starts
# 4. After 5 minutes, deployment proceeds
```

### Deployment Branches and Tags

Restrict which branches or tags can deploy to an environment.

**Options:**
1. **All branches** — any branch can deploy (least restrictive)
2. **Protected branches only** — only branches with branch protection rules
3. **Selected branches and tags** — custom patterns (most restrictive)

**Setup (UI):**
1. Go to Settings > Environments > production
2. Under "Deployment branches and tags"
3. Choose your policy

### Custom Branch Policies

Define specific branch/tag patterns that can deploy:

```
Selected branches and tags:
  - main                    # Exact match
  - release/*              # Wildcard: release/1.0, release/2.0
  - v*                     # Tags: v1.0.0, v2.1.0
```

**Example:** Only `main` branch can deploy to production:

```yaml
# This job will FAIL if triggered from any branch other than main
# (when the production environment has branch restrictions)
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - run: echo "Only runs from allowed branches"
```

---

## Environment Secrets and Variables

### Environment Secrets

Secrets scoped to a specific environment. Only accessible to jobs that reference that environment.

```yaml
jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - run: echo "Using staging DB"
        env:
          DB_PASSWORD: ${{ secrets.DB_PASSWORD }}    # Staging-specific secret

  deploy-production:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - run: echo "Using production DB"
        env:
          DB_PASSWORD: ${{ secrets.DB_PASSWORD }}    # Production-specific secret
          # Same name, different value per environment!
```

### Environment Variables

Non-sensitive configuration values per environment:

```yaml
jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - run: |
          echo "API URL: ${{ vars.API_URL }}"         # https://api.staging.example.com
          echo "Debug: ${{ vars.DEBUG_MODE }}"          # true

  deploy-production:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - run: |
          echo "API URL: ${{ vars.API_URL }}"         # https://api.example.com
          echo "Debug: ${{ vars.DEBUG_MODE }}"          # false
```

### Secret/Variable Precedence

When the same name exists at multiple levels:

**Environment > Repository > Organization**

```
Organization secret: API_KEY = "org-key"
Repository secret:   API_KEY = "repo-key"
Environment secret:  API_KEY = "env-key"

→ Jobs with environment reference get: "env-key"
→ Jobs without environment reference get: "repo-key"
```

---

## Deployment Workflows

### Simple Deployment

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://myapp.example.com
    steps:
      - uses: actions/checkout@v4

      - name: Build
        run: npm ci && npm run build

      - name: Deploy
        run: |
          # Your deployment command here
          echo "Deploying to production..."
```

### Staged Deployment Pipeline

```yaml
name: Staged Deployment

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm run build
      - run: npm test
      - uses: actions/upload-artifact@v4
        with:
          name: app
          path: dist/

  deploy-staging:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: staging
      url: https://staging.example.com
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: app
          path: dist/

      - name: Deploy to staging
        run: |
          echo "Deploying to staging..."
          # rsync, aws s3 sync, kubectl apply, etc.
        env:
          DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}

  smoke-test:
    needs: deploy-staging
    runs-on: ubuntu-latest
    steps:
      - name: Smoke test staging
        run: |
          STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://staging.example.com/health)
          if [ "$STATUS" != "200" ]; then
            echo "Smoke test failed! Status: $STATUS"
            exit 1
          fi
          echo "Smoke test passed!"

  deploy-production:
    needs: smoke-test
    runs-on: ubuntu-latest
    environment:
      name: production                        # Requires approval
      url: https://example.com
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: app
          path: dist/

      - name: Deploy to production
        run: |
          echo "Deploying to production..."
        env:
          DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}

  verify-production:
    needs: deploy-production
    runs-on: ubuntu-latest
    steps:
      - name: Verify production deployment
        run: |
          STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://example.com/health)
          if [ "$STATUS" != "200" ]; then
            echo "Production verification failed!"
            exit 1
          fi
          echo "Production is healthy!"
```

### Deployment with Manual Trigger

```yaml
name: Manual Deployment

on:
  workflow_dispatch:
    inputs:
      environment:
        description: 'Target environment'
        type: environment
        required: true
      version:
        description: 'Version to deploy'
        type: string
        required: true

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: ${{ inputs.environment }}
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ inputs.version }}

      - name: Deploy ${{ inputs.version }} to ${{ inputs.environment }}
        run: |
          echo "Deploying version ${{ inputs.version }}"
          echo "Target: ${{ inputs.environment }}"
        env:
          DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}
```

### Blue-Green Deployment

```yaml
name: Blue-Green Deployment

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://example.com
    steps:
      - uses: actions/checkout@v4

      - name: Determine active slot
        id: slot
        run: |
          # Check which slot is currently active
          ACTIVE=$(curl -s https://api.example.com/active-slot)
          if [ "$ACTIVE" = "blue" ]; then
            echo "target=green" >> "$GITHUB_OUTPUT"
          else
            echo "target=blue" >> "$GITHUB_OUTPUT"
          fi
          echo "Current active: $ACTIVE, deploying to: $(cat $GITHUB_OUTPUT | grep target | cut -d= -f2)"

      - name: Deploy to ${{ steps.slot.outputs.target }}
        run: |
          echo "Deploying to ${{ steps.slot.outputs.target }} slot"
          # Deploy to the inactive slot

      - name: Run health check
        run: |
          echo "Testing ${{ steps.slot.outputs.target }} slot"
          # Test the new deployment

      - name: Switch traffic
        run: |
          echo "Switching traffic to ${{ steps.slot.outputs.target }}"
          # Update load balancer / DNS
```

---

## Deployment Status and History

### Viewing Deployments

- **Actions tab** — see all workflow runs with environment badges
- **Environments page** — Settings > Environments > click an environment
- **Deployments API** — programmatic access to deployment history

### Deployment Status Badge

Add to your README:

```markdown
![Deploy](https://github.com/OWNER/REPO/actions/workflows/deploy.yml/badge.svg)
```

### Querying Deployments via API

```bash
# List deployments for an environment
gh api repos/OWNER/REPO/deployments \
  --jq '.[] | {id: .id, environment: .environment, ref: .ref, created_at: .created_at}'

# Get deployment status
gh api repos/OWNER/REPO/deployments/DEPLOY_ID/statuses
```

---

## Rollback Strategies

### Strategy 1: Re-deploy Previous Version

```yaml
name: Rollback

on:
  workflow_dispatch:
    inputs:
      version:
        description: 'Version to rollback to'
        required: true
        type: string
      environment:
        description: 'Environment to rollback'
        required: true
        type: environment

jobs:
  rollback:
    runs-on: ubuntu-latest
    environment: ${{ inputs.environment }}
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ inputs.version }}

      - name: Build and deploy previous version
        run: |
          echo "Rolling back to ${{ inputs.version }}"
          npm ci
          npm run build
          # Deploy commands...
```

### Strategy 2: Re-run Previous Deployment

```bash
# Re-run a previous successful workflow via CLI
gh run rerun RUN_ID
```

### Strategy 3: Automated Rollback on Failure

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4

      - name: Get current version (for rollback)
        id: current
        run: echo "version=$(curl -s https://api.example.com/version)" >> "$GITHUB_OUTPUT"

      - name: Deploy new version
        id: deploy
        run: ./deploy.sh
        continue-on-error: true

      - name: Verify deployment
        id: verify
        if: steps.deploy.outcome == 'success'
        run: |
          STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://example.com/health)
          if [ "$STATUS" != "200" ]; then
            echo "Health check failed"
            exit 1
          fi
        continue-on-error: true

      - name: Rollback on failure
        if: steps.deploy.outcome == 'failure' || steps.verify.outcome == 'failure'
        run: |
          echo "Deployment failed! Rolling back to ${{ steps.current.outputs.version }}"
          ./rollback.sh ${{ steps.current.outputs.version }}

      - name: Fail the workflow if rollback was needed
        if: steps.deploy.outcome == 'failure' || steps.verify.outcome == 'failure'
        run: exit 1
```

---

## Multi-Environment Pipeline

### Complete Example: Dev → Staging → Production

```yaml
name: Multi-Environment Pipeline

on:
  push:
    branches: [main, develop]
  workflow_dispatch:
    inputs:
      skip-to-production:
        description: 'Skip staging and deploy directly to production'
        type: boolean
        default: false

env:
  APP_NAME: my-application

jobs:
  # ──────────────── Build ────────────────
  build:
    runs-on: ubuntu-latest
    outputs:
      version: ${{ steps.version.outputs.version }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npm test
      - run: npm run build
      - id: version
        run: echo "version=$(node -p 'require(\"./package.json\").version')-${{ github.sha }}" >> "$GITHUB_OUTPUT"
      - uses: actions/upload-artifact@v4
        with:
          name: app-${{ steps.version.outputs.version }}
          path: dist/

  # ──────────────── Deploy to Development ────────────────
  deploy-dev:
    needs: build
    if: github.ref == 'refs/heads/develop'
    runs-on: ubuntu-latest
    environment:
      name: development
      url: https://dev.example.com
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: app-${{ needs.build.outputs.version }}
          path: dist/
      - name: Deploy to development
        run: echo "Deploying ${{ needs.build.outputs.version }} to development"
        env:
          DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}

  # ──────────────── Deploy to Staging ────────────────
  deploy-staging:
    needs: build
    if: github.ref == 'refs/heads/main' && !inputs.skip-to-production
    runs-on: ubuntu-latest
    environment:
      name: staging
      url: https://staging.example.com
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: app-${{ needs.build.outputs.version }}
          path: dist/
      - name: Deploy to staging
        run: echo "Deploying ${{ needs.build.outputs.version }} to staging"
        env:
          DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}

  # ──────────────── Staging Tests ────────────────
  test-staging:
    needs: deploy-staging
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run E2E tests against staging
        run: |
          echo "Running E2E tests against staging"
          # npx playwright test --config=playwright.staging.config.ts

  # ──────────────── Deploy to Production ────────────────
  deploy-production:
    needs: [build, test-staging]
    if: |
      always() &&
      github.ref == 'refs/heads/main' &&
      (needs.test-staging.result == 'success' || inputs.skip-to-production)
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://example.com
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: app-${{ needs.build.outputs.version }}
          path: dist/
      - name: Deploy to production
        run: echo "Deploying ${{ needs.build.outputs.version }} to production"
        env:
          DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}

  # ──────────────── Notify ────────────────
  notify:
    needs: [deploy-dev, deploy-staging, deploy-production]
    if: always()
    runs-on: ubuntu-latest
    steps:
      - name: Deployment summary
        run: |
          echo "## Deployment Results" >> $GITHUB_STEP_SUMMARY
          echo "| Environment | Status |" >> $GITHUB_STEP_SUMMARY
          echo "|-------------|--------|" >> $GITHUB_STEP_SUMMARY
          echo "| Development | ${{ needs.deploy-dev.result || 'skipped' }} |" >> $GITHUB_STEP_SUMMARY
          echo "| Staging | ${{ needs.deploy-staging.result || 'skipped' }} |" >> $GITHUB_STEP_SUMMARY
          echo "| Production | ${{ needs.deploy-production.result || 'skipped' }} |" >> $GITHUB_STEP_SUMMARY
```

---

## Best Practices

### 1. Always Use Environments for Production

```yaml
# Environments provide audit trail, approvals, and scoped secrets
jobs:
  deploy:
    environment: production    # Never skip this for production
```

### 2. Require Reviewers for Critical Environments

- Production should always have at least one reviewer
- Consider requiring team-based reviews (e.g., `@devops-team`)

### 3. Use Branch Restrictions

```
production  → Only from: main
staging     → Only from: main, develop
development → Only from: develop, feature/*
```

### 4. Keep Secrets Environment-Scoped

```
Repository secrets:  GITHUB_TOKEN (auto), shared non-env configs
staging secrets:     STAGING_DB_URL, STAGING_API_KEY
production secrets:  PROD_DB_URL, PROD_API_KEY
```

### 5. Add Health Checks After Deployment

```yaml
- name: Verify deployment
  run: |
    for i in {1..10}; do
      STATUS=$(curl -s -o /dev/null -w "%{http_code}" $DEPLOY_URL/health)
      if [ "$STATUS" = "200" ]; then
        echo "Deployment verified!"
        exit 0
      fi
      echo "Attempt $i: Status $STATUS, retrying in 10s..."
      sleep 10
    done
    echo "Deployment verification failed!"
    exit 1
```

### 6. Use Deployment Summaries

```yaml
- name: Write deployment summary
  run: |
    echo "## Deployment Summary" >> $GITHUB_STEP_SUMMARY
    echo "" >> $GITHUB_STEP_SUMMARY
    echo "- **Environment:** production" >> $GITHUB_STEP_SUMMARY
    echo "- **Version:** ${{ needs.build.outputs.version }}" >> $GITHUB_STEP_SUMMARY
    echo "- **Deployed by:** @${{ github.actor }}" >> $GITHUB_STEP_SUMMARY
    echo "- **URL:** https://example.com" >> $GITHUB_STEP_SUMMARY
```

---

## Summary

| Feature | Description |
|---------|-------------|
| **Environments** | Named deployment targets with protection rules |
| **Required reviewers** | Approval gates before deployment |
| **Wait timers** | Delay after approval before deployment starts |
| **Branch restrictions** | Limit which branches can deploy to an environment |
| **Environment secrets** | Credentials scoped to a specific environment |
| **Environment variables** | Non-sensitive config per environment |
| **Deployment URL** | Link to the deployed application in the UI |
| **Deployment history** | Visual log of all deployments per environment |

### Key Takeaways

1. **Use environments** for all deployment targets — they provide security, auditability, and structure
2. **Configure protection rules** — required reviewers for production, branch restrictions everywhere
3. **Scope secrets per environment** — don't give staging jobs access to production credentials
4. **Build once, deploy many** — use artifacts to pass build output through the pipeline
5. **Add health checks** after every deployment to catch failures early
6. **Enable rollback** — manual or automated, always have a way to revert
7. **Use `workflow_dispatch`** for manual deployments and rollbacks

---

**Next Lesson:** [09 - Self-Hosted Runners](./09-self-hosted-runners.md) — Running workflows on your own infrastructure.
