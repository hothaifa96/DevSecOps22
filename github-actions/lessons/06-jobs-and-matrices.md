# Lesson 6: Jobs and Matrices

## Table of Contents

- [Job Fundamentals](#job-fundamentals)
- [Job Dependencies with needs](#job-dependencies-with-needs)
- [Passing Data Between Jobs](#passing-data-between-jobs)
- [Matrix Strategy](#matrix-strategy)
- [Advanced Matrix Configurations](#advanced-matrix-configurations)
- [fail-fast and max-parallel](#fail-fast-and-max-parallel)
- [Dynamic Matrices](#dynamic-matrices)
- [Reusable Workflows (workflow_call)](#reusable-workflows-workflow_call)
- [Container Jobs](#container-jobs)
- [Service Containers](#service-containers)
- [Practical Examples](#practical-examples)
- [Summary](#summary)

---

## Job Fundamentals

Jobs are the main execution units in a workflow. Key characteristics:

| Feature | Behavior |
|---------|----------|
| **Execution** | Each job runs on a **separate runner** (fresh VM) |
| **Parallelism** | Jobs run **in parallel** by default |
| **Dependencies** | Use `needs` to create sequential execution |
| **Isolation** | Jobs don't share filesystem — use artifacts to share data |
| **Limit** | Maximum **256 jobs** per workflow |

### Basic Job Structure

```yaml
jobs:
  build:                          # Job ID (used for references)
    name: Build Application       # Display name (optional)
    runs-on: ubuntu-latest        # Runner type (required)
    timeout-minutes: 30           # Maximum run time
    continue-on-error: false      # Whether failure stops the workflow
    if: github.ref == 'refs/heads/main'  # Conditional execution

    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm run build
```

---

## Job Dependencies with needs

### Linear Pipeline

```yaml
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm run lint

  test:
    needs: lint                    # Waits for lint to succeed
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm test

  build:
    needs: test                    # Waits for test to succeed
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm run build

  deploy:
    needs: build                   # Waits for build to succeed
    runs-on: ubuntu-latest
    steps:
      - run: echo "Deploying..."
```

```
lint ──▶ test ──▶ build ──▶ deploy
```

### Fan-Out / Fan-In (Diamond)

```yaml
jobs:
  setup:
    runs-on: ubuntu-latest
    steps:
      - run: echo "Setting up..."

  lint:
    needs: setup
    runs-on: ubuntu-latest
    steps:
      - run: echo "Linting..."

  test-unit:
    needs: setup
    runs-on: ubuntu-latest
    steps:
      - run: echo "Unit testing..."

  test-integration:
    needs: setup
    runs-on: ubuntu-latest
    steps:
      - run: echo "Integration testing..."

  build:
    needs: [lint, test-unit, test-integration]  # Waits for ALL three
    runs-on: ubuntu-latest
    steps:
      - run: echo "Building..."

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - run: echo "Deploying..."
```

```
        ┌──▶ lint ─────────────┐
        │                      │
setup ──┼──▶ test-unit ────────┼──▶ build ──▶ deploy
        │                      │
        └──▶ test-integration ─┘
```

### Conditional Jobs After Failures

By default, a job is skipped if any of its `needs` jobs fail. Override this:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: npm test

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - run: echo "Deploying..."

  # Always runs — even if test or deploy failed
  notify:
    needs: [test, deploy]
    if: always()                   # Run regardless of dependency status
    runs-on: ubuntu-latest
    steps:
      - name: Send notification
        run: |
          echo "Test result: ${{ needs.test.result }}"
          echo "Deploy result: ${{ needs.deploy.result }}"

  # Only runs if something failed
  rollback:
    needs: deploy
    if: failure()                  # Only if deploy failed
    runs-on: ubuntu-latest
    steps:
      - run: echo "Rolling back deployment..."

  # Runs only if all dependencies succeeded
  cleanup:
    needs: [test, deploy]
    if: success()                  # Default behavior (explicit)
    runs-on: ubuntu-latest
    steps:
      - run: echo "Cleaning up..."
```

### Status Check Functions

| Function | Runs When |
|----------|-----------|
| `success()` | All dependency jobs succeeded (default if no `if`) |
| `failure()` | Any dependency job failed |
| `always()` | Always, regardless of dependency status |
| `cancelled()` | Workflow was cancelled |

### Checking Specific Job Results

```yaml
jobs:
  deploy:
    needs: [build-api, build-frontend]
    if: |
      always() &&
      needs.build-api.result == 'success' &&
      (needs.build-frontend.result == 'success' || needs.build-frontend.result == 'skipped')
    runs-on: ubuntu-latest
    steps:
      - run: echo "Deploying (frontend build was optional)"
```

---

## Passing Data Between Jobs

Since jobs run on separate runners, you need explicit mechanisms to share data.

### Method 1: Job Outputs (Small Values)

Best for passing strings, versions, flags, etc.:

```yaml
jobs:
  prepare:
    runs-on: ubuntu-latest
    outputs:
      version: ${{ steps.version.outputs.version }}
      should-deploy: ${{ steps.check.outputs.deploy }}
      matrix: ${{ steps.matrix.outputs.matrix }}
    steps:
      - uses: actions/checkout@v4

      - id: version
        run: echo "version=$(cat package.json | jq -r .version)" >> "$GITHUB_OUTPUT"

      - id: check
        run: |
          if [[ "${{ github.ref }}" == "refs/heads/main" ]]; then
            echo "deploy=true" >> "$GITHUB_OUTPUT"
          else
            echo "deploy=false" >> "$GITHUB_OUTPUT"
          fi

      - id: matrix
        run: echo 'matrix=["18","20","22"]' >> "$GITHUB_OUTPUT"

  build:
    needs: prepare
    runs-on: ubuntu-latest
    steps:
      - run: |
          echo "Building version: ${{ needs.prepare.outputs.version }}"
          echo "Should deploy: ${{ needs.prepare.outputs.should-deploy }}"

  deploy:
    needs: [prepare, build]
    if: needs.prepare.outputs.should-deploy == 'true'
    runs-on: ubuntu-latest
    steps:
      - run: echo "Deploying version ${{ needs.prepare.outputs.version }}"
```

### Method 2: Artifacts (Files and Directories)

Best for sharing build outputs, test results, or any files:

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm run build

      - uses: actions/upload-artifact@v4
        with:
          name: build-output
          path: dist/
          retention-days: 1

  test:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/download-artifact@v4
        with:
          name: build-output
          path: dist/

      - run: npm run test:e2e

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: build-output
          path: dist/

      - run: echo "Deploying files from dist/"
```

---

## Matrix Strategy

Matrix strategy lets you run a job with **multiple configurations** in parallel. It's perfect for testing across different environments.

### Basic Matrix

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: [18, 20, 22]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
      - run: npm ci
      - run: npm test
```

This creates **3 parallel jobs**: one for each Node.js version.

### Multi-Dimensional Matrix

```yaml
jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        node-version: [18, 20, 22]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
      - run: npm ci
      - run: npm test
```

This creates **9 parallel jobs** (3 OS x 3 Node versions):

| | Node 18 | Node 20 | Node 22 |
|---|---------|---------|---------|
| **Ubuntu** | Job 1 | Job 2 | Job 3 |
| **Windows** | Job 4 | Job 5 | Job 6 |
| **macOS** | Job 7 | Job 8 | Job 9 |

### Including Extra Combinations

Add specific combinations that aren't in the cartesian product:

```yaml
jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest]
        node-version: [18, 20]
        include:
          # Add a specific combination not in the base matrix
          - os: windows-latest
            node-version: 20
            experimental: true

          # Add extra variables to an existing combination
          - os: ubuntu-latest
            node-version: 20
            coverage: true
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
      - run: npm test
      - name: Upload coverage
        if: matrix.coverage
        run: echo "Uploading coverage..."
```

### Excluding Combinations

Remove specific combinations from the cartesian product:

```yaml
jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        node-version: [18, 20, 22]
        exclude:
          # Don't test Node 18 on macOS (not needed)
          - os: macos-latest
            node-version: 18
          # Don't test Node 22 on Windows (known issue)
          - os: windows-latest
            node-version: 22
```

### Matrix with include-Only (No Cartesian Product)

Use `include` without base matrix values to define exact combinations:

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        include:
          - environment: staging
            url: https://staging.example.com
            auto-approve: true
          - environment: production
            url: https://example.com
            auto-approve: false
    steps:
      - name: Deploy to ${{ matrix.environment }}
        run: |
          echo "Deploying to ${{ matrix.url }}"
          echo "Auto-approve: ${{ matrix.auto-approve }}"
```

---

## Advanced Matrix Configurations

### Matrix with Different Step Behavior

```yaml
jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        include:
          - os: ubuntu-latest
            python-version: '3.12'
            install-cmd: 'pip install -r requirements.txt'
            test-cmd: 'pytest --cov'
          - os: ubuntu-latest
            python-version: '3.11'
            install-cmd: 'pip install -r requirements.txt'
            test-cmd: 'pytest'
          - os: windows-latest
            python-version: '3.12'
            install-cmd: 'pip install -r requirements.txt'
            test-cmd: 'pytest'
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: ${{ matrix.install-cmd }}
      - run: ${{ matrix.test-cmd }}
```

### Matrix for Monorepo Services

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service:
          - name: api
            path: ./services/api
            dockerfile: ./services/api/Dockerfile
          - name: web
            path: ./services/web
            dockerfile: ./services/web/Dockerfile
          - name: worker
            path: ./services/worker
            dockerfile: ./services/worker/Dockerfile
    steps:
      - uses: actions/checkout@v4

      - name: Build ${{ matrix.service.name }}
        run: |
          docker build \
            -f ${{ matrix.service.dockerfile }} \
            -t myapp/${{ matrix.service.name }}:${{ github.sha }} \
            ${{ matrix.service.path }}
```

---

## fail-fast and max-parallel

### fail-fast

Controls whether to cancel remaining matrix jobs when one fails:

```yaml
strategy:
  fail-fast: true          # Default: cancel all remaining jobs if one fails
  matrix:
    node-version: [18, 20, 22]

# Set to false to let all jobs complete regardless of failures
strategy:
  fail-fast: false         # All matrix jobs run to completion
  matrix:
    node-version: [18, 20, 22]
```

**When to use `fail-fast: false`:**
- When you need to see which versions pass and which fail
- When matrix jobs are independent (e.g., deployments to different environments)
- When debugging compatibility issues across versions

### max-parallel

Limits the number of matrix jobs running simultaneously:

```yaml
strategy:
  max-parallel: 2           # Only 2 jobs at a time
  matrix:
    node-version: [18, 20, 22]
    os: [ubuntu-latest, windows-latest]
```

**When to use `max-parallel`:**
- Rate-limited APIs or external services
- Self-hosted runners with limited capacity
- Cost control (fewer concurrent runners)
- Database or resource contention

### Combined Example

```yaml
jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false       # Don't cancel other jobs on failure
      max-parallel: 4        # Max 4 concurrent jobs
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ['3.10', '3.11', '3.12']
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -r requirements.txt
      - run: pytest
```

---

## Dynamic Matrices

Generate matrix values dynamically from a previous job's output. Useful for monorepos and conditional builds.

### Example: Detect Changed Services

```yaml
jobs:
  detect-changes:
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.set-matrix.outputs.matrix }}
      has-changes: ${{ steps.set-matrix.outputs.has-changes }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - id: set-matrix
        run: |
          # Find which services changed
          CHANGED=$(git diff --name-only HEAD~1 HEAD | grep '^services/' | cut -d'/' -f2 | sort -u)

          if [ -z "$CHANGED" ]; then
            echo "has-changes=false" >> "$GITHUB_OUTPUT"
            echo 'matrix={"service":[]}' >> "$GITHUB_OUTPUT"
          else
            SERVICES=$(echo "$CHANGED" | jq -R -s -c 'split("\n") | map(select(length > 0))')
            echo "has-changes=true" >> "$GITHUB_OUTPUT"
            echo "matrix={\"service\":$SERVICES}" >> "$GITHUB_OUTPUT"
            echo "Will build: $SERVICES"
          fi

  build:
    needs: detect-changes
    if: needs.detect-changes.outputs.has-changes == 'true'
    runs-on: ubuntu-latest
    strategy:
      matrix: ${{ fromJSON(needs.detect-changes.outputs.matrix) }}
    steps:
      - uses: actions/checkout@v4
      - name: Build ${{ matrix.service }}
        run: |
          cd services/${{ matrix.service }}
          docker build -t myapp/${{ matrix.service }}:${{ github.sha }} .
```

### Example: Matrix from Configuration File

```yaml
# config/test-matrix.json:
# {
#   "include": [
#     { "name": "api", "path": "services/api", "runtime": "node" },
#     { "name": "auth", "path": "services/auth", "runtime": "python" },
#     { "name": "web", "path": "services/web", "runtime": "node" }
#   ]
# }

jobs:
  load-matrix:
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.read.outputs.matrix }}
    steps:
      - uses: actions/checkout@v4
      - id: read
        run: |
          MATRIX=$(cat config/test-matrix.json)
          echo "matrix=$MATRIX" >> "$GITHUB_OUTPUT"

  test:
    needs: load-matrix
    runs-on: ubuntu-latest
    strategy:
      matrix: ${{ fromJSON(needs.load-matrix.outputs.matrix) }}
    steps:
      - uses: actions/checkout@v4
      - name: Test ${{ matrix.name }}
        run: |
          cd ${{ matrix.path }}
          if [ "${{ matrix.runtime }}" = "node" ]; then
            npm ci && npm test
          elif [ "${{ matrix.runtime }}" = "python" ]; then
            pip install -r requirements.txt && pytest
          fi
```

---

## Reusable Workflows (workflow_call)

Reusable workflows let you define a workflow once and call it from multiple places. This is the DRY (Don't Repeat Yourself) pattern for GitHub Actions.

### Defining a Reusable Workflow

```yaml
# .github/workflows/reusable-ci.yml
name: Reusable CI

on:
  workflow_call:
    inputs:
      node-version:
        description: 'Node.js version'
        required: false
        type: string
        default: '20'
      working-directory:
        description: 'Working directory'
        required: false
        type: string
        default: '.'
      run-lint:
        description: 'Whether to run linting'
        required: false
        type: boolean
        default: true
    secrets:
      npm-token:
        description: 'NPM authentication token'
        required: false
    outputs:
      test-result:
        description: 'Test result'
        value: ${{ jobs.test.outputs.result }}

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
      - run: npm ci
      - run: npm run lint

  test:
    runs-on: ubuntu-latest
    outputs:
      result: ${{ steps.test.outputs.result }}
    defaults:
      run:
        working-directory: ${{ inputs.working-directory }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ inputs.node-version }}
      - run: npm ci
      - id: test
        run: |
          npm test
          echo "result=success" >> "$GITHUB_OUTPUT"
```

### Calling the Reusable Workflow

```yaml
# .github/workflows/main.yml
name: Main CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  # Call reusable workflow for frontend
  frontend-ci:
    uses: ./.github/workflows/reusable-ci.yml
    with:
      node-version: '20'
      working-directory: './frontend'
      run-lint: true
    secrets:
      npm-token: ${{ secrets.NPM_TOKEN }}

  # Call reusable workflow for backend
  backend-ci:
    uses: ./.github/workflows/reusable-ci.yml
    with:
      node-version: '20'
      working-directory: './backend'
      run-lint: true
    secrets: inherit     # Pass all secrets

  # Use output from reusable workflow
  deploy:
    needs: [frontend-ci, backend-ci]
    runs-on: ubuntu-latest
    steps:
      - run: |
          echo "Frontend tests: ${{ needs.frontend-ci.outputs.test-result }}"
          echo "Backend tests: ${{ needs.backend-ci.outputs.test-result }}"
```

### Cross-Repository Reusable Workflows

```yaml
jobs:
  ci:
    uses: my-org/shared-workflows/.github/workflows/node-ci.yml@v1
    with:
      node-version: '20'
    secrets: inherit
```

### Nesting Limits

Reusable workflows can call other reusable workflows, up to **4 levels deep**:

```
Caller ──▶ Reusable 1 ──▶ Reusable 2 ──▶ Reusable 3 ──▶ Reusable 4
                                                            (max depth)
```

---

## Container Jobs

Run your entire job inside a Docker container:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    container:
      image: node:20-slim
      env:
        NODE_ENV: test
      ports:
        - 3000
      volumes:
        - my_docker_volume:/volume_mount
      options: --cpus 1 --memory 512m
    steps:
      - uses: actions/checkout@v4
      - run: node --version
      - run: npm ci
      - run: npm test
```

### Why Use Container Jobs?

- **Consistent environment** across all runs
- **Specific OS/tool versions** that aren't on GitHub runners
- **Custom tools** pre-installed in the image
- **Reproducible builds** that match your production environment

---

## Service Containers

Run additional services (databases, caches, etc.) alongside your job:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: testdb
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Run tests with database
        env:
          DATABASE_URL: postgres://test:test@localhost:5432/testdb
          REDIS_URL: redis://localhost:6379
        run: |
          npm ci
          npm run test:integration
```

### Service Container Networking

| Job Type | How to Access Service |
|----------|----------------------|
| **Runner job** (no container) | `localhost:<port>` |
| **Container job** | `<service-name>:<container-port>` |

```yaml
# Runner job: use localhost
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        ports:
          - 5432:5432
    steps:
      - run: psql -h localhost -p 5432 -U test

# Container job: use service name
jobs:
  test:
    runs-on: ubuntu-latest
    container: node:20
    services:
      postgres:
        image: postgres:16
    steps:
      - run: psql -h postgres -p 5432 -U test    # Use service name!
```

---

## Practical Examples

### Full CI/CD with Matrix and Dependencies

```yaml
name: Full CI/CD

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npm run lint

  test:
    needs: lint
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest]
        node-version: [18, 20, 22]
        exclude:
          - os: windows-latest
            node-version: 18
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
          cache: 'npm'
      - run: npm ci
      - run: npm test

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npm run build
      - uses: actions/upload-artifact@v4
        with:
          name: build
          path: dist/

  deploy:
    needs: build
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: build
          path: dist/
      - run: echo "Deploying to production..."
```

### Multi-Service Test with Database

```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  integration:
    runs-on: ubuntu-latest
    services:
      db:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: testpass
          POSTGRES_DB: app_test
        ports:
          - 5432:5432
        options: --health-cmd pg_isready --health-interval 10s --health-timeout 5s --health-retries 5
      cache:
        image: redis:7-alpine
        ports:
          - 6379:6379
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - name: Run migrations
        run: npm run db:migrate
        env:
          DATABASE_URL: postgres://postgres:testpass@localhost:5432/app_test
      - name: Run integration tests
        run: npm run test:integration
        env:
          DATABASE_URL: postgres://postgres:testpass@localhost:5432/app_test
          REDIS_URL: redis://localhost:6379
```

---

## Summary

| Feature | Purpose |
|---------|---------|
| `needs` | Create job dependencies (sequential execution) |
| `outputs` | Pass small values between jobs |
| Artifacts | Pass files/directories between jobs |
| `strategy.matrix` | Run a job with multiple configurations |
| `include` | Add extra matrix combinations |
| `exclude` | Remove specific matrix combinations |
| `fail-fast` | Cancel remaining jobs on first failure (default: true) |
| `max-parallel` | Limit concurrent matrix jobs |
| Dynamic matrix | Generate matrix from job output using `fromJSON()` |
| `workflow_call` | Create reusable workflows |
| `secrets: inherit` | Pass all secrets to reusable workflows |
| `container` | Run entire job in Docker container |
| `services` | Run sidecar containers (databases, caches) |

### Key Takeaways

1. **Jobs run in parallel** by default — use `needs` for sequential execution
2. **Matrix builds** multiply your test coverage across OS, language versions, etc.
3. **Use `fail-fast: false`** when you need to see all results, not just the first failure
4. **Dynamic matrices** are powerful for monorepos — only build what changed
5. **Reusable workflows** eliminate duplication across repositories
6. **Service containers** make integration testing straightforward
7. **Share data** between jobs via outputs (small values) or artifacts (files)

---

**Next Lesson:** [07 - Artifacts and Caching](./07-artifacts-and-caching.md) — Optimizing builds with caching and sharing data between jobs.
