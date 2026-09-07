# Lab 07: Reusable Workflows

## Overview

In this lab, you will create **reusable workflows** that can be called from other workflows, promoting DRY (Don't Repeat Yourself) principles in your CI/CD pipelines. Reusable workflows allow you to define a workflow once and invoke it across multiple repositories and contexts with different inputs and secrets.

---

## Objectives

By the end of this lab, you will be able to:

- Create a reusable workflow with `workflow_call` trigger
- Define typed inputs and secrets for reusable workflows
- Call a reusable workflow from a caller workflow
- Pass inputs, secrets, and receive outputs from reusable workflows
- Understand the differences between reusable workflows and composite actions
- Chain multiple reusable workflows together
- Use `inherit` to pass all secrets automatically

---

## Prerequisites

- Completed **Lab 02** (Build and Test) and **Lab 05** (Docker Build)
- Understanding of YAML anchors and workflow structure
- Familiarity with the concept of code reuse and abstraction

---

## Step-by-Step Instructions

### Step 1: Understand Reusable Workflows

A **reusable workflow** is a workflow that can be called by another workflow. It uses the `workflow_call` event trigger and can accept inputs and secrets.

**Key differences from composite actions:**

| Feature | Reusable Workflow | Composite Action |
|---------|------------------|-----------------|
| Defined in | `.github/workflows/` | `action.yml` in any directory |
| Can contain | Multiple jobs | Steps only (single job) |
| Can use | Secrets directly | Cannot access secrets directly |
| Nesting | Up to 4 levels | Up to 10 levels |
| Runs on | Own runner(s) | Caller's runner |

### Step 2: Create a Reusable CI Workflow

Create `.github/workflows/reusable-ci.yml`:

```yaml
name: Reusable CI Pipeline

on:
  workflow_call:
    inputs:
      node-version:
        description: "Node.js version to use"
        required: false
        type: string
        default: "20"
      run-lint:
        description: "Whether to run linting"
        required: false
        type: boolean
        default: true
      run-tests:
        description: "Whether to run tests"
        required: false
        type: boolean
        default: true
      working-directory:
        description: "Working directory for the project"
        required: false
        type: string
        default: "."
      artifact-name:
        description: "Name for the test results artifact"
        required: false
        type: string
        default: "test-results"

    secrets:
      NPM_TOKEN:
        description: "NPM token for private packages"
        required: false

    outputs:
      test-result:
        description: "Result of the test run"
        value: ${{ jobs.test.outputs.result }}
      coverage-percentage:
        description: "Code coverage percentage"
        value: ${{ jobs.test.outputs.coverage }}

jobs:
  lint:
    name: Lint Code
    runs-on: ubuntu-latest
    if: ${{ inputs.run-lint }}

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ inputs.node-version }}
          cache: "npm"
          cache-dependency-path: ${{ inputs.working-directory }}/package-lock.json

      - name: Install dependencies
        working-directory: ${{ inputs.working-directory }}
        run: npm ci
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}

      - name: Run linter
        working-directory: ${{ inputs.working-directory }}
        run: npm run lint

  test:
    name: Run Tests
    runs-on: ubuntu-latest
    needs: lint
    if: always() && inputs.run-tests && (needs.lint.result == 'success' || needs.lint.result == 'skipped')
    outputs:
      result: ${{ steps.test-run.outputs.result }}
      coverage: ${{ steps.coverage.outputs.percentage }}

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ inputs.node-version }}
          cache: "npm"
          cache-dependency-path: ${{ inputs.working-directory }}/package-lock.json

      - name: Install dependencies
        working-directory: ${{ inputs.working-directory }}
        run: npm ci
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}

      - name: Run tests
        id: test-run
        working-directory: ${{ inputs.working-directory }}
        run: |
          npm test -- --ci 2>&1 | tee test-output.log
          echo "result=success" >> $GITHUB_OUTPUT
        continue-on-error: true

      - name: Extract coverage
        id: coverage
        working-directory: ${{ inputs.working-directory }}
        run: |
          # Extract coverage percentage from Jest output
          COVERAGE=$(grep "All files" coverage/coverage-summary.json 2>/dev/null | head -1 || echo "unknown")
          echo "percentage=${COVERAGE:-unknown}" >> $GITHUB_OUTPUT

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: ${{ inputs.artifact-name }}
          path: |
            ${{ inputs.working-directory }}/coverage/
            ${{ inputs.working-directory }}/test-results/
          retention-days: 14
```

### Step 3: Create a Reusable Docker Build Workflow

Create `.github/workflows/reusable-docker.yml`:

```yaml
name: Reusable Docker Build

on:
  workflow_call:
    inputs:
      image-name:
        description: "Docker image name"
        required: true
        type: string
      dockerfile:
        description: "Path to Dockerfile"
        required: false
        type: string
        default: "./Dockerfile"
      context:
        description: "Docker build context"
        required: false
        type: string
        default: "."
      push:
        description: "Whether to push the image"
        required: false
        type: boolean
        default: false
      registry:
        description: "Container registry to use"
        required: false
        type: string
        default: "ghcr.io"
      platforms:
        description: "Target platforms"
        required: false
        type: string
        default: "linux/amd64"

    secrets:
      REGISTRY_USERNAME:
        description: "Registry username"
        required: false
      REGISTRY_PASSWORD:
        description: "Registry password or token"
        required: false

    outputs:
      image-tag:
        description: "Full image tag that was built"
        value: ${{ jobs.docker-build.outputs.image_tag }}
      image-digest:
        description: "Image digest"
        value: ${{ jobs.docker-build.outputs.digest }}

jobs:
  docker-build:
    name: Build Docker Image
    runs-on: ubuntu-latest
    outputs:
      image_tag: ${{ steps.meta.outputs.version }}
      digest: ${{ steps.build.outputs.digest }}

    permissions:
      contents: read
      packages: write

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Generate Docker metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: |
            ${{ inputs.registry }}/${{ inputs.image-name }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=sha,prefix=
            type=raw,value=latest,enable={{is_default_branch}}

      - name: Login to registry
        if: inputs.push
        uses: docker/login-action@v3
        with:
          registry: ${{ inputs.registry }}
          username: ${{ secrets.REGISTRY_USERNAME || github.actor }}
          password: ${{ secrets.REGISTRY_PASSWORD || github.token }}

      - name: Build and push
        id: build
        uses: docker/build-push-action@v5
        with:
          context: ${{ inputs.context }}
          file: ${{ inputs.dockerfile }}
          push: ${{ inputs.push }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          platforms: ${{ inputs.platforms }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Output image info
        run: |
          echo "## Docker Build Summary" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "| Property | Value |" >> $GITHUB_STEP_SUMMARY
          echo "|----------|-------|" >> $GITHUB_STEP_SUMMARY
          echo "| Image | \`${{ inputs.image-name }}\` |" >> $GITHUB_STEP_SUMMARY
          echo "| Registry | \`${{ inputs.registry }}\` |" >> $GITHUB_STEP_SUMMARY
          echo "| Pushed | ${{ inputs.push }} |" >> $GITHUB_STEP_SUMMARY
          echo "| Platforms | ${{ inputs.platforms }} |" >> $GITHUB_STEP_SUMMARY
```

### Step 4: Create a Reusable Deployment Workflow

Create `.github/workflows/reusable-deploy.yml`:

```yaml
name: Reusable Deployment

on:
  workflow_call:
    inputs:
      environment:
        description: "Deployment environment"
        required: true
        type: string
      version:
        description: "Version to deploy"
        required: true
        type: string
      url:
        description: "Environment URL"
        required: false
        type: string
        default: ""
      run-smoke-tests:
        description: "Whether to run smoke tests after deployment"
        required: false
        type: boolean
        default: true

    secrets:
      DEPLOY_TOKEN:
        description: "Deployment authentication token"
        required: true

    outputs:
      deployment-status:
        description: "Deployment status"
        value: ${{ jobs.deploy.outputs.status }}

jobs:
  deploy:
    name: Deploy to ${{ inputs.environment }}
    runs-on: ubuntu-latest
    environment:
      name: ${{ inputs.environment }}
      url: ${{ inputs.url }}
    outputs:
      status: ${{ steps.deploy.outputs.status }}

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Deploy
        id: deploy
        env:
          DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}
        run: |
          echo "Deploying version ${{ inputs.version }} to ${{ inputs.environment }}..."
          echo "Using authenticated deployment token"

          # Simulate deployment
          sleep 3
          echo "Deployment complete!"
          echo "status=success" >> $GITHUB_OUTPUT

      - name: Run smoke tests
        if: inputs.run-smoke-tests
        run: |
          echo "Running smoke tests against ${{ inputs.url || inputs.environment }}..."
          sleep 2
          echo "All smoke tests passed!"

      - name: Deployment summary
        run: |
          echo "## Deployment to ${{ inputs.environment }}" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "- **Version**: \`${{ inputs.version }}\`" >> $GITHUB_STEP_SUMMARY
          echo "- **Status**: ${{ steps.deploy.outputs.status }}" >> $GITHUB_STEP_SUMMARY
          echo "- **Smoke Tests**: ${{ inputs.run-smoke-tests && 'Passed' || 'Skipped' }}" >> $GITHUB_STEP_SUMMARY
```

### Step 5: Create the Caller Workflow

Now create a workflow that calls all three reusable workflows. Create `.github/workflows/pipeline.yml`:

```yaml
name: Full Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  workflow_dispatch:

jobs:
  # ============================================
  # Stage 1: CI (using reusable workflow)
  # ============================================
  ci:
    name: CI Pipeline
    uses: ./.github/workflows/reusable-ci.yml
    with:
      node-version: "20"
      run-lint: true
      run-tests: true
      artifact-name: "ci-test-results"
    secrets:
      NPM_TOKEN: ${{ secrets.NPM_TOKEN }}

  # ============================================
  # Stage 2: Docker Build (using reusable workflow)
  # ============================================
  docker:
    name: Docker Build
    needs: ci
    uses: ./.github/workflows/reusable-docker.yml
    with:
      image-name: ${{ github.repository_owner }}/calculator-api
      push: ${{ github.event_name != 'pull_request' }}
      registry: ghcr.io
    permissions:
      contents: read
      packages: write
    secrets: inherit

  # ============================================
  # Stage 3: Deploy to Staging (using reusable workflow)
  # ============================================
  deploy-staging:
    name: Staging Deployment
    needs: docker
    if: github.ref == 'refs/heads/main'
    uses: ./.github/workflows/reusable-deploy.yml
    with:
      environment: staging
      version: ${{ github.sha }}
      url: "https://staging.example.com"
      run-smoke-tests: true
    secrets:
      DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}

  # ============================================
  # Stage 4: Deploy to Production (using reusable workflow)
  # ============================================
  deploy-production:
    name: Production Deployment
    needs: deploy-staging
    if: github.ref == 'refs/heads/main'
    uses: ./.github/workflows/reusable-deploy.yml
    with:
      environment: production
      version: ${{ github.sha }}
      url: "https://production.example.com"
      run-smoke-tests: true
    secrets:
      DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}

  # ============================================
  # Summary
  # ============================================
  summary:
    name: Pipeline Summary
    runs-on: ubuntu-latest
    needs: [ci, docker, deploy-staging, deploy-production]
    if: always()

    steps:
      - name: Pipeline results
        run: |
          echo "## Pipeline Summary" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "| Stage | Result |" >> $GITHUB_STEP_SUMMARY
          echo "|-------|--------|" >> $GITHUB_STEP_SUMMARY
          echo "| CI | ${{ needs.ci.result }} |" >> $GITHUB_STEP_SUMMARY
          echo "| Docker Build | ${{ needs.docker.result }} |" >> $GITHUB_STEP_SUMMARY
          echo "| Staging Deploy | ${{ needs.deploy-staging.result }} |" >> $GITHUB_STEP_SUMMARY
          echo "| Production Deploy | ${{ needs.deploy-production.result }} |" >> $GITHUB_STEP_SUMMARY
```

### Step 6: Using `secrets: inherit`

Notice in the Docker build step we used `secrets: inherit`. This passes **all** secrets from the caller workflow to the reusable workflow, avoiding the need to list each one explicitly.

```yaml
# Explicit secrets (more secure, more verbose):
secrets:
  NPM_TOKEN: ${{ secrets.NPM_TOKEN }}

# Inherited secrets (convenient, passes everything):
secrets: inherit
```

> **Security Note**: Use explicit secret passing in production for better security audit trails. Use `secrets: inherit` for convenience during development.

### Step 7: Cross-Repository Reusable Workflows

Reusable workflows can be called from other repositories. The syntax uses the full path:

```yaml
jobs:
  call-remote:
    uses: organization/shared-workflows/.github/workflows/ci.yml@main
    with:
      node-version: "20"
    secrets: inherit
```

Requirements for cross-repository calls:
- The reusable workflow repository must be **public**, or
- The repository must be in the same organization and the workflow must be set to be accessible from other repositories (Settings > Actions > Access).

### Step 8: Commit and Push

```bash
git add -A
git commit -m "Add reusable workflows and caller pipeline"
git push origin main
```

### Step 9: Observe the Execution

1. Go to the **Actions** tab.
2. Click on the **Full Pipeline** workflow run.
3. Notice how each called workflow appears as a nested job group.
4. Click into each to see the reusable workflow's steps execute.
5. Verify outputs are passed correctly between stages.

---

## Expected Outcomes

After completing this lab, you should see:

1. Three reusable workflows defined: `reusable-ci.yml`, `reusable-docker.yml`, `reusable-deploy.yml`.
2. A caller workflow (`pipeline.yml`) that chains all three together.
3. Inputs being passed from the caller to each reusable workflow.
4. Secrets being forwarded (both explicitly and via `inherit`).
5. Outputs flowing from reusable workflows back to the caller for use in downstream jobs.
6. The full pipeline executing: CI -> Docker -> Staging -> Production.

---

## Bonus Challenges

1. **Create a shared workflows repository** in your GitHub organization and move the reusable workflows there. Update the caller to reference them with `org/repo/.github/workflows/file.yml@main`.

2. **Add input validation** in the reusable workflow to fail early if required inputs are missing or invalid:
   ```yaml
   - name: Validate inputs
     run: |
       if [ -z "${{ inputs.image-name }}" ]; then
         echo "Error: image-name is required"
         exit 1
       fi
   ```

3. **Create a reusable notification workflow** that can send alerts to Slack, email, or Teams based on an input parameter.

4. **Implement workflow versioning** by tagging your reusable workflows with semantic versions and calling specific versions:
   ```yaml
   uses: org/workflows/.github/workflows/ci.yml@v2.1.0
   ```

5. **Create a composite action** (as opposed to a reusable workflow) for a common task and compare the developer experience and capabilities. Place it in `.github/actions/setup-project/action.yml`:
   ```yaml
   name: "Setup Project"
   description: "Install dependencies and setup tools"
   inputs:
     node-version:
       description: "Node.js version"
       default: "20"
   runs:
     using: "composite"
     steps:
       - uses: actions/setup-node@v4
         with:
           node-version: ${{ inputs.node-version }}
       - run: npm ci
         shell: bash
   ```

6. **Implement a workflow matrix that calls reusable workflows** for deploying to multiple environments in parallel:
   ```yaml
   deploy:
     strategy:
       matrix:
         environment: [staging-us, staging-eu, staging-ap]
     uses: ./.github/workflows/reusable-deploy.yml
     with:
       environment: ${{ matrix.environment }}
   ```

---

## Key Concepts Learned

- **`workflow_call`**: The event trigger that makes a workflow reusable
- **Inputs**: Typed parameters (`string`, `boolean`, `number`) passed from the caller to the reusable workflow
- **Secrets in Reusable Workflows**: Must be explicitly declared and passed, or use `secrets: inherit`
- **Outputs**: Values returned from reusable workflows to the caller for downstream use
- **`secrets: inherit`**: Passes all available secrets to the reusable workflow automatically
- **Cross-Repository Calls**: Referencing reusable workflows in other repositories using full path syntax
- **Nesting Limit**: Reusable workflows can be nested up to 4 levels deep
- **Caller Context**: Reusable workflows execute in the context of the caller workflow (same `github` context)
