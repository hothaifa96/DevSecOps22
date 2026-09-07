# Lesson 2: Workflow Syntax

## Table of Contents

- [Workflow File Basics](#workflow-file-basics)
- [Complete Workflow Structure](#complete-workflow-structure)
- [name](#name)
- [on (Events and Triggers)](#on-events-and-triggers)
- [permissions](#permissions)
- [env (Workflow-Level)](#env-workflow-level)
- [defaults](#defaults)
- [concurrency](#concurrency)
- [jobs](#jobs)
  - [jobs.<job_id>](#jobsjob_id)
  - [runs-on](#runs-on)
  - [needs (Job Dependencies)](#needs-job-dependencies)
  - [if (Conditionals)](#if-conditionals)
  - [environment](#environment)
  - [outputs](#outputs)
- [Steps](#steps)
  - [uses vs run](#uses-vs-run)
  - [with (Action Inputs)](#with-action-inputs)
  - [working-directory](#working-directory)
  - [shell](#shell)
  - [continue-on-error](#continue-on-error)
  - [timeout-minutes](#timeout-minutes)
- [Expressions and Contexts](#expressions-and-contexts)
- [Complete Example](#complete-example)
- [Summary](#summary)

---

## Workflow File Basics

Workflow files must:

- Be placed in the `.github/workflows/` directory
- Use `.yml` or `.yaml` extension
- Be valid YAML syntax
- Not exceed 512 KB in size

```
my-repo/
├── .github/
│   └── workflows/
│       ├── ci.yml
│       ├── deploy.yml
│       └── security-scan.yml
```

> **YAML Refresher:** YAML uses indentation (spaces, NOT tabs) to define structure. Typically 2 spaces per level. Be careful with indentation — it's the most common source of errors.

---

## Complete Workflow Structure

Here's the full skeleton of a workflow file with all top-level keys:

```yaml
# Top-level keys (all optional except 'on' and 'jobs')
name: My Workflow                    # Display name
run-name: Deploy by @${{ github.actor }}  # Dynamic run name

on:                                  # REQUIRED: Trigger events
  push:
    branches: [main]

permissions:                         # Token permissions
  contents: read

env:                                 # Workflow-level environment variables
  NODE_ENV: production

defaults:                            # Default settings for all jobs
  run:
    shell: bash
    working-directory: ./src

concurrency:                         # Concurrency control
  group: ${{ github.ref }}
  cancel-in-progress: true

jobs:                                # REQUIRED: Jobs to run
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: echo "Hello!"
```

---

## name

The `name` key sets the display name of the workflow in the GitHub Actions UI.

```yaml
name: CI Pipeline
```

- If omitted, GitHub uses the workflow file name
- Shows in the **Actions** tab and in status checks on PRs

### run-name

The `run-name` key sets the name for each individual run of the workflow. Supports expressions:

```yaml
name: Deploy
run-name: Deploy to ${{ inputs.environment }} by @${{ github.actor }}
```

---

## on (Events and Triggers)

The `on` key defines **when** the workflow runs. This is **required**.

### Single Event

```yaml
on: push
```

### Multiple Events

```yaml
on: [push, pull_request]
```

### Events with Configuration

```yaml
on:
  push:
    branches: [main, develop]
    paths:
      - 'src/**'
      - 'package.json'
    tags:
      - 'v*'

  pull_request:
    branches: [main]
    types: [opened, synchronize, reopened]

  schedule:
    - cron: '0 6 * * 1'    # Every Monday at 6:00 AM UTC

  workflow_dispatch:         # Manual trigger with inputs
    inputs:
      environment:
        description: 'Target environment'
        required: true
        default: 'staging'
        type: choice
        options:
          - staging
          - production
```

> **Detailed coverage of events is in [Lesson 03 - Events and Triggers](./03-events-and-triggers.md).**

---

## permissions

Controls the permissions of the `GITHUB_TOKEN` for the workflow. Follow the **principle of least privilege**:

```yaml
# Set all permissions to read-only, then grant specific write access
permissions:
  contents: read
  pull-requests: write
  issues: write
  packages: read
  security-events: write
```

### Available Permission Scopes

| Permission | Description |
|-----------|-------------|
| `actions` | Manage GitHub Actions |
| `checks` | Create/update check runs |
| `contents` | Read/write repository contents |
| `deployments` | Manage deployments |
| `id-token` | Request OIDC tokens |
| `issues` | Manage issues |
| `packages` | Manage packages |
| `pages` | Manage GitHub Pages |
| `pull-requests` | Manage pull requests |
| `security-events` | Upload SARIF results |
| `statuses` | Update commit statuses |

### Permission Values

- `read` — Read access
- `write` — Read and write access
- `none` — No access (not available for all scopes)

### Shorthand: Read-All or Write-All

```yaml
permissions: read-all    # All scopes get read access
# or
permissions: write-all   # All scopes get write access (avoid in production!)
```

### Job-Level Permissions

You can also set permissions per job (overrides workflow-level):

```yaml
jobs:
  build:
    permissions:
      contents: read
    runs-on: ubuntu-latest
    steps: [...]

  deploy:
    permissions:
      contents: read
      id-token: write    # Needed for OIDC
    runs-on: ubuntu-latest
    steps: [...]
```

---

## env (Workflow-Level)

Define environment variables available to **all jobs and steps** in the workflow:

```yaml
env:
  NODE_ENV: production
  APP_NAME: my-app
  REGISTRY: ghcr.io
```

Environment variables can also be set at the **job** and **step** level:

```yaml
env:                              # Workflow-level
  GLOBAL_VAR: available-everywhere

jobs:
  build:
    env:                          # Job-level (overrides workflow-level)
      JOB_VAR: available-in-this-job
    runs-on: ubuntu-latest
    steps:
      - name: My step
        env:                      # Step-level (overrides job-level)
          STEP_VAR: available-in-this-step
        run: |
          echo "$GLOBAL_VAR"
          echo "$JOB_VAR"
          echo "$STEP_VAR"
```

**Precedence:** Step env > Job env > Workflow env

---

## defaults

Set default settings for all `run` steps in the workflow:

```yaml
defaults:
  run:
    shell: bash
    working-directory: ./app
```

### Per-Job Defaults

Override workflow defaults at the job level:

```yaml
defaults:
  run:
    shell: bash

jobs:
  frontend:
    defaults:
      run:
        working-directory: ./frontend    # All steps in this job run from ./frontend
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm install                 # Runs in ./frontend
      - run: npm run build               # Runs in ./frontend

  backend:
    defaults:
      run:
        working-directory: ./backend     # All steps in this job run from ./backend
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r requirements.txt   # Runs in ./backend
      - run: python -m pytest                  # Runs in ./backend
```

---

## concurrency

Control concurrent workflow runs. Useful for preventing duplicate deployments or wasted resources:

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

### How It Works

- `group`: A string identifying the concurrency group. Runs in the same group are serialized.
- `cancel-in-progress`: If `true`, cancels any currently running job in the same group when a new run starts.

### Common Patterns

```yaml
# Cancel duplicate PR builds (most common)
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

# Serialize deployments per environment (never cancel in-progress deploys)
concurrency:
  group: deploy-${{ github.ref }}
  cancel-in-progress: false

# One deployment at a time to production
concurrency:
  group: production-deploy
  cancel-in-progress: false
```

### Job-Level Concurrency

```yaml
jobs:
  deploy:
    concurrency:
      group: deploy-prod
      cancel-in-progress: false
    runs-on: ubuntu-latest
    steps: [...]
```

---

## jobs

The `jobs` key is **required** and defines the work your workflow performs. Each job runs on a separate runner.

### jobs.\<job_id\>

Each job needs a unique identifier (the key). The ID must start with a letter or `_` and contain only alphanumeric characters, `-`, or `_`.

```yaml
jobs:
  build:              # job_id = "build"
    name: Build App   # Display name (optional)
    runs-on: ubuntu-latest
    steps: [...]

  run-tests:          # job_id = "run-tests"
    name: Run Tests
    runs-on: ubuntu-latest
    steps: [...]
```

### runs-on

Specifies the type of runner for the job. **Required for every job.**

```yaml
# GitHub-hosted runners
runs-on: ubuntu-latest        # Most common
runs-on: ubuntu-22.04         # Specific version
runs-on: ubuntu-24.04         # Newest Ubuntu
runs-on: windows-latest       # Windows Server 2022
runs-on: windows-2019         # Older Windows
runs-on: macos-latest         # macOS 14 (Sonoma)
runs-on: macos-13             # macOS 13 (Ventura)

# Self-hosted runners (using labels)
runs-on: self-hosted
runs-on: [self-hosted, linux, x64]
runs-on: [self-hosted, gpu]
```

### needs (Job Dependencies)

By default, jobs run **in parallel**. Use `needs` to create dependencies:

```yaml
jobs:
  lint:
    runs-on: ubuntu-latest
    steps: [...]

  test:
    runs-on: ubuntu-latest
    steps: [...]

  build:
    needs: [lint, test]         # Waits for BOTH lint and test
    runs-on: ubuntu-latest
    steps: [...]

  deploy:
    needs: build                # Waits for build (which waits for lint + test)
    runs-on: ubuntu-latest
    steps: [...]
```

This creates a dependency graph:

```
lint ──┐
       ├──▶ build ──▶ deploy
test ──┘
```

### if (Conditionals)

Control whether a job runs based on conditions:

```yaml
jobs:
  deploy-staging:
    if: github.ref == 'refs/heads/develop'
    runs-on: ubuntu-latest
    steps: [...]

  deploy-production:
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps: [...]

  notify-on-failure:
    needs: [deploy-staging, deploy-production]
    if: failure()              # Only runs if a previous job failed
    runs-on: ubuntu-latest
    steps: [...]
```

### Common Conditional Functions

| Function | Description |
|----------|-------------|
| `success()` | All previous jobs succeeded (default) |
| `failure()` | Any previous job failed |
| `always()` | Always run, even if previous jobs failed or were cancelled |
| `cancelled()` | Workflow was cancelled |

### environment

Link a job to a GitHub Environment (for deployments):

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://myapp.example.com
    steps: [...]
```

### outputs

Define outputs from a job that other jobs can consume:

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      version: ${{ steps.get-version.outputs.version }}
      image-tag: ${{ steps.get-version.outputs.tag }}
    steps:
      - id: get-version
        run: |
          echo "version=1.2.3" >> "$GITHUB_OUTPUT"
          echo "tag=myapp:1.2.3" >> "$GITHUB_OUTPUT"

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - run: |
          echo "Deploying version: ${{ needs.build.outputs.version }}"
          echo "Image tag: ${{ needs.build.outputs.image-tag }}"
```

---

## Steps

Steps are the individual tasks within a job. They run **sequentially**.

### uses vs run

The two most important step properties — they're mutually exclusive:

#### `uses` — Run a Pre-Built Action

```yaml
steps:
  # Reference a specific version (recommended for security)
  - uses: actions/checkout@v4

  # Use a specific commit SHA (most secure)
  - uses: actions/checkout@8ade135a41bc03ea155e62e844d188df1ea18608

  # Use a Docker Hub action
  - uses: docker://alpine:3.18

  # Use a local action from your repo
  - uses: ./.github/actions/my-custom-action
```

#### `run` — Execute Shell Commands

```yaml
steps:
  # Single-line command
  - run: echo "Hello World"

  # Multi-line commands (using pipe |)
  - run: |
      echo "Step 1: Install"
      npm install
      echo "Step 2: Build"
      npm run build

  # Multi-line with line continuation (using >)
  - run: >
      curl -X POST
      -H "Content-Type: application/json"
      -d '{"status": "success"}'
      https://api.example.com/webhook
```

### with (Action Inputs)

Pass inputs to actions using `with`:

```yaml
steps:
  - uses: actions/checkout@v4
    with:
      fetch-depth: 0           # Fetch all history
      token: ${{ secrets.PAT }}

  - uses: actions/setup-node@v4
    with:
      node-version: '20'
      cache: 'npm'

  - uses: actions/upload-artifact@v4
    with:
      name: build-output
      path: dist/
      retention-days: 5
```

### working-directory

Set the working directory for a `run` step:

```yaml
steps:
  - uses: actions/checkout@v4

  - name: Install frontend deps
    run: npm install
    working-directory: ./frontend

  - name: Install backend deps
    run: pip install -r requirements.txt
    working-directory: ./backend
```

### shell

Specify the shell for a `run` step:

```yaml
steps:
  - name: Bash (default on Linux/macOS)
    run: echo "Hello from bash"
    shell: bash

  - name: PowerShell (default on Windows)
    run: Write-Output "Hello from PowerShell"
    shell: pwsh

  - name: Python
    run: |
      import os
      print(f"Repository: {os.environ['GITHUB_REPOSITORY']}")
    shell: python

  - name: Custom shell
    run: echo "Hello"
    shell: sh
```

**Available shells:**

| Shell | Platforms | Description |
|-------|-----------|-------------|
| `bash` | Linux, macOS, Windows | Default for Linux/macOS |
| `pwsh` | All | PowerShell Core |
| `python` | All | Runs as Python script |
| `sh` | Linux, macOS | Bourne shell |
| `cmd` | Windows | Windows Command Prompt |
| `powershell` | Windows | Windows PowerShell (legacy) |

### continue-on-error

Allow a step to fail without failing the job:

```yaml
steps:
  - name: Run optional linter
    run: npm run lint
    continue-on-error: true       # Job continues even if this fails

  - name: This still runs
    run: echo "Previous step might have failed, but we continue"
```

You can also use `continue-on-error` at the **job level**:

```yaml
jobs:
  experimental:
    continue-on-error: true       # Workflow continues even if this job fails
    runs-on: ubuntu-latest
    steps: [...]
```

### timeout-minutes

Set a maximum execution time for a step or job:

```yaml
jobs:
  build:
    timeout-minutes: 30           # Job-level timeout (default: 360 = 6 hours)
    runs-on: ubuntu-latest
    steps:
      - name: Long-running test
        timeout-minutes: 10       # Step-level timeout
        run: npm run test:e2e
```

---

## Expressions and Contexts

GitHub Actions uses `${{ }}` syntax for expressions. Expressions let you access context data, perform comparisons, and call functions.

### Common Contexts

| Context | Description | Example |
|---------|-------------|---------|
| `github` | Workflow run info | `${{ github.ref }}`, `${{ github.actor }}` |
| `env` | Environment variables | `${{ env.NODE_ENV }}` |
| `secrets` | Encrypted secrets | `${{ secrets.API_KEY }}` |
| `inputs` | Workflow dispatch inputs | `${{ inputs.environment }}` |
| `job` | Current job info | `${{ job.status }}` |
| `steps` | Step outputs/status | `${{ steps.build.outputs.version }}` |
| `runner` | Runner info | `${{ runner.os }}`, `${{ runner.arch }}` |
| `needs` | Outputs from dependent jobs | `${{ needs.build.outputs.image }}` |
| `matrix` | Current matrix values | `${{ matrix.node-version }}` |
| `vars` | Repository/org variables | `${{ vars.DEPLOY_URL }}` |

### Operators

```yaml
# Comparison
if: github.ref == 'refs/heads/main'
if: github.event_name != 'pull_request'

# Logical
if: github.ref == 'refs/heads/main' && github.event_name == 'push'
if: github.ref == 'refs/heads/main' || github.ref == 'refs/heads/develop'
if: "!cancelled()"

# Contains
if: contains(github.event.head_commit.message, '[skip ci]')

# startsWith / endsWith
if: startsWith(github.ref, 'refs/tags/v')
if: endsWith(github.repository, '-demo')
```

### Useful Functions

| Function | Description | Example |
|----------|-------------|---------|
| `contains(search, item)` | Check if string/array contains item | `contains(github.ref, 'release')` |
| `startsWith(string, prefix)` | Check prefix | `startsWith(github.ref, 'refs/tags/')` |
| `endsWith(string, suffix)` | Check suffix | `endsWith(github.repository, '-api')` |
| `format(string, ...)` | Format a string | `format('Hello {0}', github.actor)` |
| `join(array, separator)` | Join array elements | `join(github.event.commits.*.message, '\n')` |
| `toJSON(value)` | Convert to JSON | `toJSON(github.event)` |
| `fromJSON(value)` | Parse JSON | `fromJSON(steps.get-matrix.outputs.matrix)` |
| `hashFiles(path)` | SHA-256 hash of files | `hashFiles('**/package-lock.json')` |

---

## Complete Example

Here's a comprehensive workflow that demonstrates most syntax features:

```yaml
name: Full CI/CD Pipeline
run-name: CI/CD for ${{ github.ref_name }} by @${{ github.actor }}

on:
  push:
    branches: [main, develop]
    paths-ignore:
      - '*.md'
      - 'docs/**'
  pull_request:
    branches: [main]
  workflow_dispatch:
    inputs:
      deploy-env:
        description: 'Deployment target'
        required: true
        default: 'staging'
        type: choice
        options:
          - staging
          - production

permissions:
  contents: read
  packages: write

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

defaults:
  run:
    shell: bash

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}

jobs:
  # ──────────────── Job 1: Lint ────────────────
  lint:
    name: Lint Code
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - run: npm ci
      - run: npm run lint

  # ──────────────── Job 2: Test ────────────────
  test:
    name: Test (Node ${{ matrix.node-version }})
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: [18, 20, 22]
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
          cache: 'npm'

      - run: npm ci
      - run: npm test

  # ──────────────── Job 3: Build ────────────────
  build:
    name: Build Application
    needs: [lint, test]
    runs-on: ubuntu-latest
    outputs:
      version: ${{ steps.meta.outputs.version }}
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - run: npm ci
      - run: npm run build

      - id: meta
        run: echo "version=$(node -p 'require(\"./package.json\").version')" >> "$GITHUB_OUTPUT"

      - uses: actions/upload-artifact@v4
        with:
          name: build-output
          path: dist/
          retention-days: 7

  # ──────────────── Job 4: Deploy ────────────────
  deploy:
    name: Deploy to ${{ inputs.deploy-env || 'staging' }}
    needs: build
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    runs-on: ubuntu-latest
    environment:
      name: ${{ inputs.deploy-env || 'staging' }}
      url: https://${{ inputs.deploy-env || 'staging' }}.example.com
    timeout-minutes: 15
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: build-output
          path: dist/

      - name: Deploy
        env:
          VERSION: ${{ needs.build.outputs.version }}
        run: |
          echo "Deploying version $VERSION"
          echo "Environment: ${{ inputs.deploy-env || 'staging' }}"

  # ──────────────── Job 5: Notify ────────────────
  notify:
    name: Send Notification
    needs: [build, deploy]
    if: always()
    runs-on: ubuntu-latest
    steps:
      - name: Report status
        run: |
          echo "Build: ${{ needs.build.result }}"
          echo "Deploy: ${{ needs.deploy.result }}"
```

---

## Summary

| Key | Level | Purpose |
|-----|-------|---------|
| `name` | Workflow | Display name for the workflow |
| `run-name` | Workflow | Dynamic name for each run |
| `on` | Workflow | **Required.** Events that trigger the workflow |
| `permissions` | Workflow/Job | GITHUB_TOKEN permissions |
| `env` | Workflow/Job/Step | Environment variables (step > job > workflow) |
| `defaults` | Workflow/Job | Default `shell` and `working-directory` for `run` steps |
| `concurrency` | Workflow/Job | Prevent duplicate/concurrent runs |
| `jobs` | Workflow | **Required.** Define jobs to execute |
| `runs-on` | Job | **Required.** Runner type for the job |
| `needs` | Job | Job dependencies |
| `if` | Job/Step | Conditional execution |
| `strategy.matrix` | Job | Run job with multiple configurations |
| `environment` | Job | Link to a GitHub Environment |
| `outputs` | Job | Values to pass to dependent jobs |
| `uses` | Step | Run a pre-built action |
| `run` | Step | Execute shell commands |
| `with` | Step | Inputs for an action |
| `working-directory` | Step | Set working directory for `run` |
| `shell` | Step | Set shell type for `run` |
| `continue-on-error` | Job/Step | Allow failure without failing the workflow |
| `timeout-minutes` | Job/Step | Maximum execution time |

---

**Next Lesson:** [03 - Events and Triggers](./03-events-and-triggers.md) — Deep dive into all available events and trigger configurations.
