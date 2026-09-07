# Lab 06: Multi-Stage Deployment Pipeline

## Overview

In this lab, you will create a complete multi-stage deployment pipeline that mirrors a real-world production workflow: build, test, deploy to staging, obtain manual approval, and then deploy to production. You will use GitHub Environments, protection rules, deployment concurrency, and rollback strategies.

---

## Objectives

By the end of this lab, you will be able to:

- Design a multi-stage deployment pipeline (build -> test -> staging -> production)
- Configure GitHub Environments with protection rules and approvals
- Implement deployment concurrency to prevent conflicting deployments
- Add smoke tests to validate deployments
- Create rollback mechanisms
- Use deployment status and environment URLs
- Implement a canary/blue-green deployment pattern in CI

---

## Prerequisites

- Completed **Lab 04** (Secrets and Variables) and **Lab 05** (Docker Build and Push)
- GitHub Environments set up (staging and production)
- Understanding of deployment strategies

---

## Step-by-Step Instructions

### Step 1: Set Up Environments with Protection Rules

If you haven't already, configure your environments:

1. Go to **Settings** > **Environments**.

**Staging Environment:**
1. Create or edit the **staging** environment.
2. Add a **deployment branch rule** allowing only `main`.
3. Add environment secrets:
   - `DEPLOY_URL` = `https://staging.example.com`
   - `DEPLOY_TOKEN` = `staging-deploy-token-123`
4. Add environment variables:
   - `ENVIRONMENT_NAME` = `staging`

**Production Environment:**
1. Create or edit the **production** environment.
2. Enable **Required reviewers** and add yourself (or a teammate).
3. Add a **wait timer** of 2 minutes (optional, for demonstration).
4. Add a **deployment branch rule** allowing only `main`.
5. Add environment secrets:
   - `DEPLOY_URL` = `https://production.example.com`
   - `DEPLOY_TOKEN` = `prod-deploy-token-456`
6. Add environment variables:
   - `ENVIRONMENT_NAME` = `production`

### Step 2: Create a Deployment Script

Create `scripts/deploy.sh`:

```bash
#!/bin/bash
set -euo pipefail

# Deployment script that simulates deploying to an environment
ENVIRONMENT=${1:-"unknown"}
VERSION=${2:-"unknown"}
DEPLOY_URL=${3:-"http://localhost"}

echo "========================================"
echo "  Deploying to: $ENVIRONMENT"
echo "  Version:      $VERSION"
echo "  Target URL:   $DEPLOY_URL"
echo "  Timestamp:    $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "========================================"

echo ""
echo "[1/5] Validating deployment configuration..."
sleep 1
echo "  Configuration valid."

echo ""
echo "[2/5] Pulling container image..."
sleep 1
echo "  Image pulled: calculator-api:$VERSION"

echo ""
echo "[3/5] Running database migrations..."
sleep 1
echo "  Migrations complete (0 pending)."

echo ""
echo "[4/5] Deploying application..."
sleep 2
echo "  Application deployed successfully."

echo ""
echo "[5/5] Verifying deployment..."
sleep 1
echo "  Health check passed."

echo ""
echo "========================================"
echo "  Deployment SUCCESSFUL"
echo "  Environment: $ENVIRONMENT"
echo "  Live at:     $DEPLOY_URL"
echo "========================================"
```

Make it executable:

```bash
chmod +x scripts/deploy.sh
```

### Step 3: Create a Smoke Test Script

Create `scripts/smoke-test.sh`:

```bash
#!/bin/bash
set -euo pipefail

DEPLOY_URL=${1:-"http://localhost:3000"}
MAX_RETRIES=5
RETRY_DELAY=5

echo "Running smoke tests against: $DEPLOY_URL"
echo ""

# Simulate smoke test checks
run_check() {
  local name=$1
  local endpoint=$2
  local expected_status=$3

  echo -n "  Checking $name ($endpoint)... "

  # Simulating HTTP checks
  # In a real pipeline, you would use curl:
  # status=$(curl -s -o /dev/null -w "%{http_code}" "$DEPLOY_URL$endpoint")
  status=$expected_status  # Simulated

  if [ "$status" = "$expected_status" ]; then
    echo "PASSED (HTTP $status)"
    return 0
  else
    echo "FAILED (expected HTTP $expected_status, got HTTP $status)"
    return 1
  fi
}

echo "=== Smoke Tests ==="
FAILURES=0

run_check "Health endpoint" "/health" "200" || ((FAILURES++))
run_check "API endpoint" "/calculate" "200" || ((FAILURES++))
run_check "Not found handling" "/nonexistent" "404" || ((FAILURES++))

echo ""
if [ $FAILURES -eq 0 ]; then
  echo "All smoke tests PASSED"
  exit 0
else
  echo "$FAILURES smoke test(s) FAILED"
  exit 1
fi
```

Make it executable:

```bash
chmod +x scripts/smoke-test.sh
```

### Step 4: Create the Multi-Stage Deployment Workflow

Create `.github/workflows/deployment.yml`:

```yaml
name: Deployment Pipeline

on:
  push:
    branches: [main]
  workflow_dispatch:
    inputs:
      skip-tests:
        description: "Skip test stage"
        required: false
        type: boolean
        default: false
      deploy-to:
        description: "Deploy target"
        required: true
        type: choice
        options:
          - staging-only
          - staging-and-production
        default: staging-and-production

# Prevent concurrent deployments
concurrency:
  group: deployment-${{ github.ref }}
  cancel-in-progress: false

jobs:
  # ============================================
  # Stage 1: Build
  # ============================================
  build:
    name: Build Application
    runs-on: ubuntu-latest
    outputs:
      version: ${{ steps.version.outputs.version }}
      image-tag: ${{ steps.version.outputs.image_tag }}

    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Generate version
        id: version
        run: |
          # Generate a version based on date and short SHA
          VERSION="$(date +%Y%m%d)-${GITHUB_SHA::8}"
          echo "version=$VERSION" >> $GITHUB_OUTPUT
          echo "image_tag=calculator-api:$VERSION" >> $GITHUB_OUTPUT
          echo "Generated version: $VERSION"

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"

      - name: Install dependencies
        run: npm ci

      - name: Build application
        run: |
          echo "Building application version ${{ steps.version.outputs.version }}..."
          # If you had a build step (TypeScript, webpack, etc.):
          # npm run build
          echo "Build complete."

      - name: Upload build artifact
        uses: actions/upload-artifact@v4
        with:
          name: build-${{ steps.version.outputs.version }}
          path: |
            src/
            package.json
            package-lock.json
            Dockerfile
            scripts/
          retention-days: 7

  # ============================================
  # Stage 2: Test
  # ============================================
  test:
    name: Run Tests
    runs-on: ubuntu-latest
    needs: build
    if: ${{ !inputs.skip-tests }}

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

      - name: Run linter
        run: npm run lint

      - name: Run unit tests
        run: npm test

      - name: Run integration tests
        run: |
          echo "Running integration tests..."
          # npm run test:integration
          echo "Integration tests passed."

      - name: Test summary
        if: always()
        run: |
          echo "## Test Results" >> $GITHUB_STEP_SUMMARY
          echo "- Linting: Passed" >> $GITHUB_STEP_SUMMARY
          echo "- Unit Tests: Passed" >> $GITHUB_STEP_SUMMARY
          echo "- Integration Tests: Passed" >> $GITHUB_STEP_SUMMARY

  # ============================================
  # Stage 3: Deploy to Staging
  # ============================================
  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    needs: [build, test]
    if: always() && needs.build.result == 'success' && (needs.test.result == 'success' || needs.test.result == 'skipped')
    environment:
      name: staging
      url: https://staging.example.com

    concurrency:
      group: staging-deploy
      cancel-in-progress: false

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Download build artifact
        uses: actions/download-artifact@v4
        with:
          name: build-${{ needs.build.outputs.version }}
          path: ./build-output

      - name: Deploy to staging
        env:
          DEPLOY_URL: ${{ secrets.DEPLOY_URL }}
          DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}
        run: |
          chmod +x scripts/deploy.sh
          ./scripts/deploy.sh "staging" "${{ needs.build.outputs.version }}" "${DEPLOY_URL}"

      - name: Run smoke tests on staging
        run: |
          chmod +x scripts/smoke-test.sh
          ./scripts/smoke-test.sh "https://staging.example.com"

      - name: Staging deployment summary
        run: |
          echo "## Staging Deployment" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "| Property | Value |" >> $GITHUB_STEP_SUMMARY
          echo "|----------|-------|" >> $GITHUB_STEP_SUMMARY
          echo "| Version | \`${{ needs.build.outputs.version }}\` |" >> $GITHUB_STEP_SUMMARY
          echo "| Environment | staging |" >> $GITHUB_STEP_SUMMARY
          echo "| Status | Deployed |" >> $GITHUB_STEP_SUMMARY
          echo "| URL | https://staging.example.com |" >> $GITHUB_STEP_SUMMARY
          echo "| Smoke Tests | Passed |" >> $GITHUB_STEP_SUMMARY

  # ============================================
  # Stage 4: Deploy to Production (with approval)
  # ============================================
  deploy-production:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: [build, deploy-staging]
    if: |
      github.ref == 'refs/heads/main' &&
      needs.deploy-staging.result == 'success' &&
      (github.event.inputs.deploy-to != 'staging-only' || github.event.inputs.deploy-to == null)
    environment:
      name: production
      url: https://production.example.com

    concurrency:
      group: production-deploy
      cancel-in-progress: false

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Download build artifact
        uses: actions/download-artifact@v4
        with:
          name: build-${{ needs.build.outputs.version }}
          path: ./build-output

      - name: Pre-deployment checks
        run: |
          echo "=== Pre-Deployment Checks ==="
          echo "Version to deploy: ${{ needs.build.outputs.version }}"
          echo "Triggered by: ${{ github.actor }}"
          echo "Commit: ${{ github.sha }}"
          echo ""
          echo "Verifying staging deployment is healthy..."
          sleep 2
          echo "Staging is healthy. Proceeding with production deployment."

      - name: Deploy to production
        env:
          DEPLOY_URL: ${{ secrets.DEPLOY_URL }}
          DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}
        run: |
          chmod +x scripts/deploy.sh
          ./scripts/deploy.sh "production" "${{ needs.build.outputs.version }}" "${DEPLOY_URL}"

      - name: Run smoke tests on production
        run: |
          chmod +x scripts/smoke-test.sh
          ./scripts/smoke-test.sh "https://production.example.com"

      - name: Production deployment summary
        run: |
          echo "## Production Deployment" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "| Property | Value |" >> $GITHUB_STEP_SUMMARY
          echo "|----------|-------|" >> $GITHUB_STEP_SUMMARY
          echo "| Version | \`${{ needs.build.outputs.version }}\` |" >> $GITHUB_STEP_SUMMARY
          echo "| Environment | production |" >> $GITHUB_STEP_SUMMARY
          echo "| Status | Deployed |" >> $GITHUB_STEP_SUMMARY
          echo "| URL | https://production.example.com |" >> $GITHUB_STEP_SUMMARY
          echo "| Smoke Tests | Passed |" >> $GITHUB_STEP_SUMMARY
          echo "| Approved by | ${{ github.actor }} |" >> $GITHUB_STEP_SUMMARY

  # ============================================
  # Post-Deployment: Notification
  # ============================================
  notify:
    name: Deployment Notification
    runs-on: ubuntu-latest
    needs: [build, deploy-staging, deploy-production]
    if: always()

    steps:
      - name: Determine overall status
        id: status
        run: |
          if [ "${{ needs.deploy-production.result }}" = "success" ]; then
            echo "status=Production deployment successful" >> $GITHUB_OUTPUT
            echo "emoji=rocket" >> $GITHUB_OUTPUT
          elif [ "${{ needs.deploy-staging.result }}" = "success" ]; then
            echo "status=Staging deployment successful (production pending or skipped)" >> $GITHUB_OUTPUT
            echo "emoji=yellow_circle" >> $GITHUB_OUTPUT
          else
            echo "status=Deployment failed" >> $GITHUB_OUTPUT
            echo "emoji=red_circle" >> $GITHUB_OUTPUT
          fi

      - name: Send notification
        run: |
          echo "========================================"
          echo "  DEPLOYMENT NOTIFICATION"
          echo "========================================"
          echo "Status:  ${{ steps.status.outputs.status }}"
          echo "Version: ${{ needs.build.outputs.version }}"
          echo "Ref:     ${{ github.ref_name }}"
          echo "Actor:   ${{ github.actor }}"
          echo "Run:     ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}"
          echo "========================================"

          # In a real pipeline, send a Slack/Teams/email notification:
          # curl -X POST "$SLACK_WEBHOOK" \
          #   -H "Content-Type: application/json" \
          #   -d '{"text": "Deployment: ${{ steps.status.outputs.status }}"}'
```

### Step 5: Commit and Push

```bash
git add -A
git commit -m "Add multi-stage deployment pipeline"
git push origin main
```

### Step 6: Observe the Pipeline

1. Go to the **Actions** tab.
2. Watch the **Deployment Pipeline** workflow execute:
   - **Build** runs first.
   - **Test** runs after build completes.
   - **Deploy to Staging** runs after tests pass.
   - **Deploy to Production** pauses and waits for manual approval.
3. Click on the workflow run to see the approval prompt.
4. Click **Review deployments**, select the production environment, and approve.
5. Watch the production deployment execute.
6. Check the **Notification** job for the summary.

### Step 7: Test Manual Trigger with Options

1. Go to the **Actions** tab.
2. Click on **Deployment Pipeline** in the left sidebar.
3. Click **Run workflow**.
4. Select `staging-only` from the deploy target dropdown.
5. Observe that the production deployment is skipped.

### Step 8: View Deployment History

1. Go to **Settings** > **Environments** > **staging** (or **production**).
2. View the **Deployment history** showing all deployments to that environment.
3. This gives you an audit trail of what was deployed, when, and by whom.

---

## Expected Outcomes

After completing this lab, you should see:

1. A four-stage pipeline: build -> test -> staging -> production.
2. The production stage pausing for manual approval before executing.
3. Build artifacts being shared between the build and deploy stages.
4. Smoke tests running after each deployment to validate the release.
5. Deployment concurrency preventing conflicting simultaneous deployments.
6. A notification job summarizing the deployment result.
7. Environment deployment history visible in the GitHub Settings.

---

## Bonus Challenges

1. **Implement a rollback workflow** that deploys a previous version:
   ```yaml
   on:
     workflow_dispatch:
       inputs:
         version:
           description: "Version to rollback to"
           required: true
         environment:
           description: "Target environment"
           type: choice
           options: [staging, production]
   ```

2. **Add a canary deployment step** that deploys to a small percentage of traffic first, runs tests, then promotes to full traffic.

3. **Integrate Slack notifications** using `slackapi/slack-github-action@v1` to notify your team channel on deployment events.

4. **Add a deployment freeze mechanism** using a repository variable `DEPLOY_FREEZE=true` that blocks all deployments when active:
   ```yaml
   - name: Check deploy freeze
     if: vars.DEPLOY_FREEZE == 'true'
     run: |
       echo "Deployments are currently frozen!"
       exit 1
   ```

5. **Create a deployment dashboard** using GitHub Pages that reads the deployment API and displays the current version in each environment.

6. **Add database backup** as a pre-deployment step for production that creates a backup before any changes are applied.

---

## Key Concepts Learned

- **Multi-Stage Pipelines**: Sequential stages with gates between build, test, and deploy
- **GitHub Environments**: Named deployment targets with secrets, variables, and protection rules
- **Manual Approvals**: Required reviewer gates that pause the pipeline for human verification
- **Deployment Concurrency**: Using `concurrency` groups to prevent simultaneous conflicting deployments
- **Smoke Tests**: Quick post-deployment validation to confirm the application is functioning
- **Artifacts Between Jobs**: Using `upload-artifact` and `download-artifact` to pass build outputs across jobs
- **Workflow Dispatch Inputs**: Manual trigger parameters for controlling deployment behavior
- **Deployment History**: GitHub's built-in tracking of environment deployments
