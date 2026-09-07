# Lesson 10: Advanced Patterns

## Table of Contents

- [Monorepo Workflows](#monorepo-workflows)
- [Path Filtering and Conditional Jobs](#path-filtering-and-conditional-jobs)
- [Reusable Workflows at Scale](#reusable-workflows-at-scale)
- [Composite Actions for Shared Logic](#composite-actions-for-shared-logic)
- [Workflow Chaining](#workflow-chaining)
- [Docker Build and Push Patterns](#docker-build-and-push-patterns)
- [Security Scanning in CI](#security-scanning-in-ci)
- [GitOps with GitHub Actions](#gitops-with-github-actions)
- [Performance Optimization](#performance-optimization)
- [Error Handling and Notifications](#error-handling-and-notifications)
- [Summary](#summary)

---

## Monorepo Workflows

Managing multiple services/packages in a single repository requires smart workflow design.

### Pattern 1: Path-Based Triggers

Each service has its own workflow file:

```yaml
# .github/workflows/api-ci.yml
name: API CI

on:
  push:
    branches: [main]
    paths:
      - 'services/api/**'
      - 'shared/**'              # Shared libraries trigger all services
      - '.github/workflows/api-ci.yml'
  pull_request:
    branches: [main]
    paths:
      - 'services/api/**'
      - 'shared/**'
      - '.github/workflows/api-ci.yml'

defaults:
  run:
    working-directory: services/api

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: services/api/package-lock.json
      - run: npm ci
      - run: npm test

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker build -t myapp-api:${{ github.sha }} .
```

### Pattern 2: Dynamic Change Detection

A single workflow detects changes and runs jobs conditionally:

```yaml
name: Monorepo CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  detect-changes:
    runs-on: ubuntu-latest
    outputs:
      api: ${{ steps.changes.outputs.api }}
      web: ${{ steps.changes.outputs.web }}
      worker: ${{ steps.changes.outputs.worker }}
      shared: ${{ steps.changes.outputs.shared }}
    steps:
      - uses: actions/checkout@v4

      - uses: dorny/paths-filter@v3
        id: changes
        with:
          filters: |
            api:
              - 'services/api/**'
              - 'shared/**'
            web:
              - 'services/web/**'
              - 'shared/**'
            worker:
              - 'services/worker/**'
              - 'shared/**'
            shared:
              - 'shared/**'

  api-ci:
    needs: detect-changes
    if: needs.detect-changes.outputs.api == 'true'
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: services/api
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm test
      - run: npm run build

  web-ci:
    needs: detect-changes
    if: needs.detect-changes.outputs.web == 'true'
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: services/web
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm test
      - run: npm run build

  worker-ci:
    needs: detect-changes
    if: needs.detect-changes.outputs.worker == 'true'
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: services/worker
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm test
      - run: npm run build
```

### Pattern 3: Matrix-Based Monorepo

```yaml
name: Monorepo CI (Matrix)

on:
  push:
    branches: [main]

jobs:
  detect-services:
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.detect.outputs.matrix }}
      has-changes: ${{ steps.detect.outputs.has-changes }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 2

      - id: detect
        run: |
          # Get changed files
          CHANGED_FILES=$(git diff --name-only HEAD~1 HEAD)

          # Map changed paths to services
          SERVICES=()
          if echo "$CHANGED_FILES" | grep -q '^services/api/'; then
            SERVICES+=('{"name":"api","path":"services/api"}')
          fi
          if echo "$CHANGED_FILES" | grep -q '^services/web/'; then
            SERVICES+=('{"name":"web","path":"services/web"}')
          fi
          if echo "$CHANGED_FILES" | grep -q '^services/worker/'; then
            SERVICES+=('{"name":"worker","path":"services/worker"}')
          fi
          # Shared changes rebuild everything
          if echo "$CHANGED_FILES" | grep -q '^shared/'; then
            SERVICES=('{"name":"api","path":"services/api"}' '{"name":"web","path":"services/web"}' '{"name":"worker","path":"services/worker"}')
          fi

          if [ ${#SERVICES[@]} -eq 0 ]; then
            echo "has-changes=false" >> "$GITHUB_OUTPUT"
            echo 'matrix={"include":[]}' >> "$GITHUB_OUTPUT"
          else
            MATRIX=$(printf '%s,' "${SERVICES[@]}" | sed 's/,$//')
            echo "has-changes=true" >> "$GITHUB_OUTPUT"
            echo "matrix={\"include\":[$MATRIX]}" >> "$GITHUB_OUTPUT"
          fi

  build:
    needs: detect-services
    if: needs.detect-services.outputs.has-changes == 'true'
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix: ${{ fromJSON(needs.detect-services.outputs.matrix) }}
    steps:
      - uses: actions/checkout@v4
      - name: Build ${{ matrix.name }}
        working-directory: ${{ matrix.path }}
        run: |
          echo "Building service: ${{ matrix.name }}"
          npm ci
          npm run build
```

---

## Path Filtering and Conditional Jobs

### Skip CI Based on Commit Message

```yaml
jobs:
  build:
    if: "!contains(github.event.head_commit.message, '[skip ci]')"
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm test
```

### Run Based on Changed File Types

```yaml
jobs:
  detect:
    runs-on: ubuntu-latest
    outputs:
      docs-only: ${{ steps.check.outputs.docs-only }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 2
      - id: check
        run: |
          CHANGED=$(git diff --name-only HEAD~1 HEAD)
          NON_DOC=$(echo "$CHANGED" | grep -v '\.md$' | grep -v '^docs/' || true)
          if [ -z "$NON_DOC" ]; then
            echo "docs-only=true" >> "$GITHUB_OUTPUT"
          else
            echo "docs-only=false" >> "$GITHUB_OUTPUT"
          fi

  build:
    needs: detect
    if: needs.detect.outputs.docs-only == 'false'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm run build

  deploy-docs:
    needs: detect
    if: needs.detect.outputs.docs-only == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: echo "Only deploying docs..."
```

### Conditional Steps Using Labels

```yaml
on:
  pull_request:
    types: [opened, synchronize, labeled]

jobs:
  deploy-preview:
    if: contains(github.event.pull_request.labels.*.name, 'deploy-preview')
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: echo "Deploying preview environment for this PR"

  full-test:
    if: contains(github.event.pull_request.labels.*.name, 'full-test')
    runs-on: ubuntu-latest
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
    steps:
      - uses: actions/checkout@v4
      - run: npm test
```

---

## Reusable Workflows at Scale

### Shared Workflow Repository

Create an organization-wide repository of shared workflows:

```
my-org/shared-workflows/
├── .github/
│   └── workflows/
│       ├── node-ci.yml
│       ├── python-ci.yml
│       ├── docker-build.yml
│       ├── deploy-aws.yml
│       └── security-scan.yml
```

### Node.js CI Reusable Workflow

```yaml
# shared-workflows/.github/workflows/node-ci.yml
name: Node.js CI (Reusable)

on:
  workflow_call:
    inputs:
      node-version:
        type: string
        default: '20'
      working-directory:
        type: string
        default: '.'
      run-lint:
        type: boolean
        default: true
      run-e2e:
        type: boolean
        default: false
      upload-coverage:
        type: boolean
        default: false
    secrets:
      codecov-token:
        required: false

jobs:
  lint:
    if: inputs.run-lint
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: ${{ inputs.working-directory }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ inputs.node-version }}
          cache: 'npm'
          cache-dependency-path: ${{ inputs.working-directory }}/package-lock.json
      - run: npm ci
      - run: npm run lint

  test:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: ${{ inputs.working-directory }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ inputs.node-version }}
          cache: 'npm'
          cache-dependency-path: ${{ inputs.working-directory }}/package-lock.json
      - run: npm ci
      - run: npm test -- --coverage
      - name: Upload coverage
        if: inputs.upload-coverage
        uses: codecov/codecov-action@v4
        with:
          token: ${{ secrets.codecov-token }}

  e2e:
    if: inputs.run-e2e
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: ${{ inputs.working-directory }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ inputs.node-version }}
          cache: 'npm'
          cache-dependency-path: ${{ inputs.working-directory }}/package-lock.json
      - run: npm ci
      - run: npx playwright install --with-deps
      - run: npm run test:e2e
```

### Calling from Consumer Repos

```yaml
# any-repo/.github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  ci:
    uses: my-org/shared-workflows/.github/workflows/node-ci.yml@v1
    with:
      node-version: '20'
      run-e2e: true
      upload-coverage: true
    secrets:
      codecov-token: ${{ secrets.CODECOV_TOKEN }}
```

---

## Composite Actions for Shared Logic

When you need to share step-level logic (not entire workflows), use composite actions.

### Example: Setup, Build, and Test Action

```yaml
# .github/actions/node-setup/action.yml
name: 'Node.js Setup and Build'
description: 'Sets up Node.js, installs deps, builds, and optionally tests'

inputs:
  node-version:
    description: 'Node.js version'
    default: '20'
  working-directory:
    description: 'Working directory'
    default: '.'
  build-command:
    description: 'Build command'
    default: 'npm run build'
  run-tests:
    description: 'Run tests after build'
    default: 'true'

outputs:
  cache-hit:
    description: 'Whether the cache was hit'
    value: ${{ steps.cache.outputs.cache-hit }}

runs:
  using: 'composite'
  steps:
    - uses: actions/setup-node@v4
      with:
        node-version: ${{ inputs.node-version }}

    - name: Cache node_modules
      id: cache
      uses: actions/cache@v4
      with:
        path: ${{ inputs.working-directory }}/node_modules
        key: ${{ runner.os }}-modules-${{ hashFiles(format('{0}/package-lock.json', inputs.working-directory)) }}

    - name: Install dependencies
      if: steps.cache.outputs.cache-hit != 'true'
      shell: bash
      working-directory: ${{ inputs.working-directory }}
      run: npm ci

    - name: Build
      shell: bash
      working-directory: ${{ inputs.working-directory }}
      run: ${{ inputs.build-command }}

    - name: Test
      if: inputs.run-tests == 'true'
      shell: bash
      working-directory: ${{ inputs.working-directory }}
      run: npm test
```

### Using the Composite Action

```yaml
jobs:
  api:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: ./.github/actions/node-setup
        with:
          working-directory: services/api
          node-version: '20'

  web:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: ./.github/actions/node-setup
        with:
          working-directory: services/web
          build-command: 'npm run build:production'
```

### Example: Docker Build Composite Action

```yaml
# .github/actions/docker-build/action.yml
name: 'Docker Build and Push'
description: 'Builds and pushes a Docker image with caching'

inputs:
  image-name:
    description: 'Full image name (e.g., ghcr.io/owner/repo)'
    required: true
  dockerfile:
    description: 'Path to Dockerfile'
    default: 'Dockerfile'
  context:
    description: 'Build context'
    default: '.'
  push:
    description: 'Push the image'
    default: 'true'
  tags:
    description: 'Image tags (newline-separated)'
    required: true

outputs:
  image-digest:
    description: 'Image digest'
    value: ${{ steps.build.outputs.digest }}
  image-metadata:
    description: 'Image metadata'
    value: ${{ steps.build.outputs.metadata }}

runs:
  using: 'composite'
  steps:
    - uses: docker/setup-buildx-action@v3

    - uses: docker/build-push-action@v5
      id: build
      with:
        context: ${{ inputs.context }}
        file: ${{ inputs.dockerfile }}
        push: ${{ inputs.push }}
        tags: ${{ inputs.tags }}
        cache-from: type=gha
        cache-to: type=gha,mode=max
        labels: |
          org.opencontainers.image.source=${{ github.server_url }}/${{ github.repository }}
          org.opencontainers.image.revision=${{ github.sha }}
```

---

## Workflow Chaining

### Using workflow_run to Chain Workflows

```yaml
# .github/workflows/ci.yml
name: CI
on:
  push:
    branches: [main]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm test

---

# .github/workflows/deploy.yml
name: Deploy
on:
  workflow_run:
    workflows: ["CI"]
    types: [completed]
    branches: [main]

jobs:
  deploy:
    if: github.event.workflow_run.conclusion == 'success'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Download artifact from CI
        uses: actions/download-artifact@v4
        with:
          name: build
          github-token: ${{ secrets.GITHUB_TOKEN }}
          run-id: ${{ github.event.workflow_run.id }}
      - run: echo "Deploying after successful CI"

  notify-failure:
    if: github.event.workflow_run.conclusion == 'failure'
    runs-on: ubuntu-latest
    steps:
      - run: echo "CI failed! Not deploying."
```

### Triggering Workflows Across Repositories

```yaml
# Repo A: Trigger deployment in Repo B
jobs:
  trigger-deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger deployment in another repo
        run: |
          curl -X POST \
            -H "Authorization: token ${{ secrets.PAT }}" \
            -H "Accept: application/vnd.github.v3+json" \
            https://api.github.com/repos/my-org/deploy-repo/dispatches \
            -d '{
              "event_type": "deploy",
              "client_payload": {
                "version": "${{ github.sha }}",
                "service": "api",
                "triggered_by": "${{ github.repository }}"
              }
            }'
```

---

## Docker Build and Push Patterns

### Multi-Platform Build

```yaml
name: Docker Multi-Platform

on:
  push:
    branches: [main]
    tags: ['v*']

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v4

      - uses: docker/setup-qemu-action@v3

      - uses: docker/setup-buildx-action@v3

      - uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - uses: docker/metadata-action@v5
        id: meta
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha

      - uses: docker/build-push-action@v5
        with:
          context: .
          platforms: linux/amd64,linux/arm64
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

### Build, Scan, and Push

```yaml
name: Secure Docker Build

on:
  push:
    branches: [main]

jobs:
  build-and-scan:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
      security-events: write

    steps:
      - uses: actions/checkout@v4

      - uses: docker/setup-buildx-action@v3

      # Build (don't push yet)
      - uses: docker/build-push-action@v5
        with:
          context: .
          load: true                           # Load into local Docker
          tags: myapp:scan
          cache-from: type=gha
          cache-to: type=gha,mode=max

      # Scan for vulnerabilities
      - uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'myapp:scan'
          format: 'sarif'
          output: 'trivy-results.sarif'
          severity: 'CRITICAL,HIGH'
          exit-code: '1'                       # Fail on critical/high

      - uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: 'trivy-results.sarif'

      # Push only if scan passed
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ghcr.io/${{ github.repository }}:${{ github.sha }}
          cache-from: type=gha
```

---

## Security Scanning in CI

### Comprehensive DevSecOps Pipeline

```yaml
name: DevSecOps Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 6 * * 1'            # Weekly full scan

permissions:
  contents: read
  security-events: write
  pull-requests: write

jobs:
  # ──────────── Secret Detection ────────────
  secret-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: TruffleHog Secret Scan
        uses: trufflesecurity/trufflehog@main
        with:
          extra_args: --only-verified

  # ──────────── SAST (Static Analysis) ────────────
  sast:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Initialize CodeQL
        uses: github/codeql-action/init@v3
        with:
          languages: javascript

      - name: Autobuild
        uses: github/codeql-action/autobuild@v3

      - name: Run CodeQL Analysis
        uses: github/codeql-action/analyze@v3

  # ──────────── SCA (Dependency Scanning) ────────────
  dependency-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-fs-results.sarif'
          severity: 'CRITICAL,HIGH'

      - uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: 'trivy-fs-results.sarif'
          category: 'dependency-scan'

  # ──────────── License Compliance ────────────
  license-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Check licenses
        run: |
          npm ci
          npx license-checker --failOn "GPL-3.0;AGPL-3.0" --summary

  # ──────────── Container Scanning ────────────
  container-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build Docker image
        run: docker build -t myapp:scan .

      - name: Scan container image
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'myapp:scan'
          format: 'sarif'
          output: 'trivy-image-results.sarif'
          severity: 'CRITICAL,HIGH'

      - uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: 'trivy-image-results.sarif'
          category: 'container-scan'

  # ──────────── SBOM Generation ────────────
  sbom:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Generate SBOM
        uses: anchore/sbom-action@v0
        with:
          path: .
          format: spdx-json
          output-file: sbom.spdx.json

      - uses: actions/upload-artifact@v4
        with:
          name: sbom
          path: sbom.spdx.json

  # ──────────── IaC Scanning ────────────
  iac-scan:
    runs-on: ubuntu-latest
    if: hashFiles('**/*.tf') != '' || hashFiles('**/Dockerfile') != ''
    steps:
      - uses: actions/checkout@v4

      - name: Run Checkov IaC scanner
        uses: bridgecrewio/checkov-action@v12
        with:
          directory: .
          framework: terraform,dockerfile
          output_format: sarif
          output_file_path: checkov-results.sarif
          soft_fail: true

      - uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: checkov-results.sarif
          category: 'iac-scan'

  # ──────────── Gate: All Scans Must Pass ────────────
  security-gate:
    needs: [secret-scan, sast, dependency-scan, license-check, container-scan]
    runs-on: ubuntu-latest
    steps:
      - name: All security checks passed
        run: echo "All security scans passed successfully!"
```

### PR Comment with Scan Results

```yaml
  comment-results:
    needs: [dependency-scan, container-scan]
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
    steps:
      - uses: actions/github-script@v7
        with:
          script: |
            await github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              body: `## Security Scan Results

              | Scan | Status |
              |------|--------|
              | Secret Detection | ${{ needs.secret-scan.result == 'success' && 'Passed' || 'Failed' }} |
              | SAST (CodeQL) | ${{ needs.sast.result == 'success' && 'Passed' || 'Failed' }} |
              | Dependency Scan | ${{ needs.dependency-scan.result == 'success' && 'Passed' || 'Failed' }} |
              | Container Scan | ${{ needs.container-scan.result == 'success' && 'Passed' || 'Failed' }} |

              [View full results](https://github.com/${context.repo.owner}/${context.repo.repo}/security/code-scanning)`
            });
```

---

## GitOps with GitHub Actions

### Auto-Update Deployment Manifests

```yaml
name: GitOps Deploy

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      image-tag: ${{ steps.build.outputs.tag }}
    steps:
      - uses: actions/checkout@v4

      - name: Build and push image
        id: build
        run: |
          TAG="${{ github.sha }}"
          docker build -t ghcr.io/myorg/myapp:$TAG .
          docker push ghcr.io/myorg/myapp:$TAG
          echo "tag=$TAG" >> "$GITHUB_OUTPUT"

  update-manifests:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Checkout GitOps repo
        uses: actions/checkout@v4
        with:
          repository: myorg/gitops-config
          token: ${{ secrets.PAT }}
          path: gitops

      - name: Update image tag
        working-directory: gitops
        run: |
          # Update the Kubernetes manifest
          sed -i "s|image: ghcr.io/myorg/myapp:.*|image: ghcr.io/myorg/myapp:${{ needs.build.outputs.image-tag }}|" \
            environments/production/deployment.yaml

      - name: Commit and push
        working-directory: gitops
        run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add .
          git commit -m "Deploy myapp:${{ needs.build.outputs.image-tag }}"
          git push
```

---

## Performance Optimization

### Technique 1: Cancel Redundant Runs

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

### Technique 2: Skip Unnecessary Work

```yaml
jobs:
  check:
    runs-on: ubuntu-latest
    outputs:
      should-build: ${{ steps.check.outputs.should-build }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 2
      - id: check
        run: |
          CHANGED=$(git diff --name-only HEAD~1 HEAD)
          if echo "$CHANGED" | grep -qvE '\.(md|txt|yml)$'; then
            echo "should-build=true" >> "$GITHUB_OUTPUT"
          else
            echo "should-build=false" >> "$GITHUB_OUTPUT"
            echo "Only docs/config changed, skipping build"
          fi

  build:
    needs: check
    if: needs.check.outputs.should-build == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm run build
```

### Technique 3: Aggressive Caching

```yaml
steps:
  # Cache multiple things
  - uses: actions/cache@v4
    with:
      path: |
        node_modules
        ~/.npm
        .next/cache
      key: ${{ runner.os }}-full-${{ hashFiles('**/package-lock.json') }}-${{ hashFiles('**/*.ts', '**/*.tsx') }}
      restore-keys: |
        ${{ runner.os }}-full-${{ hashFiles('**/package-lock.json') }}-
        ${{ runner.os }}-full-
```

### Technique 4: Parallel Everything

```yaml
jobs:
  # These all run in parallel (no 'needs')
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm run lint

  test-unit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm test

  test-e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm run test:e2e

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: aquasecurity/trivy-action@master
        with:
          scan-type: fs

  # Only this waits for everything
  deploy:
    needs: [lint, test-unit, test-e2e, security]
    runs-on: ubuntu-latest
    steps:
      - run: echo "All checks passed, deploying..."
```

### Technique 5: Use Job Summaries Instead of Artifacts

```yaml
steps:
  - name: Write summary (faster than uploading artifacts)
    run: |
      echo "## Test Results" >> $GITHUB_STEP_SUMMARY
      echo "" >> $GITHUB_STEP_SUMMARY
      echo "| Suite | Tests | Passed | Failed |" >> $GITHUB_STEP_SUMMARY
      echo "|-------|-------|--------|--------|" >> $GITHUB_STEP_SUMMARY
      echo "| Unit | 150 | 148 | 2 |" >> $GITHUB_STEP_SUMMARY
      echo "| Integration | 45 | 45 | 0 |" >> $GITHUB_STEP_SUMMARY
```

---

## Error Handling and Notifications

### Comprehensive Error Handling

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4

      - name: Pre-deploy checks
        id: pre-check
        run: |
          # Verify the deployment target is healthy
          STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://example.com/health || echo "000")
          if [ "$STATUS" != "200" ]; then
            echo "Pre-deploy check failed: target returned $STATUS"
            echo "status=unhealthy" >> "$GITHUB_OUTPUT"
          else
            echo "status=healthy" >> "$GITHUB_OUTPUT"
          fi

      - name: Deploy
        id: deploy
        if: steps.pre-check.outputs.status == 'healthy'
        run: ./deploy.sh
        continue-on-error: true

      - name: Post-deploy verification
        id: verify
        if: steps.deploy.outcome == 'success'
        run: |
          sleep 30
          for i in {1..5}; do
            STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://example.com/health)
            if [ "$STATUS" = "200" ]; then
              echo "Deployment verified!"
              exit 0
            fi
            echo "Attempt $i: got $STATUS, retrying..."
            sleep 10
          done
          echo "Verification failed!"
          exit 1
        continue-on-error: true

      - name: Rollback if needed
        if: steps.deploy.outcome == 'failure' || steps.verify.outcome == 'failure'
        run: |
          echo "Initiating rollback..."
          ./rollback.sh

      - name: Notify Slack
        if: always()
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*Deployment Report*\n*Repo:* ${{ github.repository }}\n*Deploy:* ${{ steps.deploy.outcome }}\n*Verify:* ${{ steps.verify.outcome }}\n*Actor:* ${{ github.actor }}"
                  }
                }
              ]
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}

      - name: Fail workflow if deployment failed
        if: steps.deploy.outcome == 'failure' || steps.verify.outcome == 'failure'
        run: exit 1
```

---

## Summary

| Pattern | Description | When to Use |
|---------|-------------|-------------|
| **Monorepo path filtering** | Trigger builds only for changed services | Multi-service repos |
| **Dynamic change detection** | Use `dorny/paths-filter` or git diff | Complex monorepo logic |
| **Dynamic matrices** | Generate matrix from job outputs | Variable number of services |
| **Shared workflows** | Organization-wide reusable workflows | DRY across repos |
| **Composite actions** | Reusable step sequences | Shared step logic |
| **Workflow chaining** | `workflow_run` to chain workflows | Separate CI and CD |
| **Multi-platform Docker** | `docker/build-push-action` with QEMU | Cross-architecture images |
| **Security scanning** | CodeQL, Trivy, TruffleHog, Checkov | DevSecOps pipeline |
| **GitOps** | Auto-update manifests on build | Kubernetes deployments |
| **Concurrency groups** | Cancel redundant runs | PR workflows |

### Key Takeaways

1. **Monorepo workflows** need path filtering to avoid unnecessary builds — use `dorny/paths-filter` or native `paths`
2. **Reusable workflows and composite actions** keep your CI/CD DRY across repositories
3. **Security scanning** should be integrated at every stage: secrets, SAST, SCA, containers, IaC
4. **Docker builds** should use BuildKit caching (`type=gha`) and multi-platform support
5. **Performance** matters — use concurrency groups, caching, parallelism, and skip checks
6. **Error handling** with `continue-on-error`, rollbacks, and notifications makes pipelines production-ready
7. **GitOps patterns** automate the last mile from CI to Kubernetes deployment

---

**Congratulations!** You've completed the GitHub Actions lesson series. Review the [Cheatsheet](../cheatsheet/github-actions-cheatsheet.md) for a quick reference of everything covered.
