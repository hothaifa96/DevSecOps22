# Lesson 3: Events and Triggers

## Table of Contents

- [Overview](#overview)
- [Push Event](#push-event)
- [Pull Request Event](#pull-request-event)
- [Schedule (Cron)](#schedule-cron)
- [workflow_dispatch (Manual Trigger)](#workflow_dispatch-manual-trigger)
- [repository_dispatch (External Trigger)](#repository_dispatch-external-trigger)
- [workflow_call (Reusable Workflows)](#workflow_call-reusable-workflows)
- [Release Event](#release-event)
- [Other Useful Events](#other-useful-events)
- [Filtering: Branches, Paths, and Tags](#filtering-branches-paths-and-tags)
- [Activity Types](#activity-types)
- [Multiple Events Combined](#multiple-events-combined)
- [Event Payloads and Context](#event-payloads-and-context)
- [Summary](#summary)

---

## Overview

Events are the foundation of GitHub Actions — they determine **when** your workflows run. GitHub provides over 35 different event types.

### Event Categories

| Category | Events | Description |
|----------|--------|-------------|
| **Code** | `push`, `pull_request`, `pull_request_target` | Triggered by code changes |
| **Scheduled** | `schedule` | Triggered by cron schedule |
| **Manual** | `workflow_dispatch`, `repository_dispatch` | Triggered by user or API |
| **Reuse** | `workflow_call` | Triggered by another workflow |
| **Release** | `release` | Triggered by release activity |
| **Issue/PR** | `issues`, `issue_comment`, `pull_request_review` | Triggered by issue/PR activity |
| **Registry** | `registry_package` | Triggered by package events |
| **Other** | `create`, `delete`, `fork`, `star`, `watch` | Triggered by repo events |

---

## Push Event

Triggers when commits are pushed to the repository.

### Basic Push

```yaml
on: push
```

### Push with Branch Filtering

```yaml
on:
  push:
    branches:
      - main
      - develop
      - 'release/**'       # Matches release/1.0, release/2.0, etc.
      - '!release/**-beta'  # Excludes release branches ending in -beta
```

### Push with Tag Filtering

```yaml
on:
  push:
    tags:
      - 'v*'              # Matches v1.0, v2.0.1, v3.0-beta
      - 'v[0-9]+.[0-9]+.[0-9]+'  # Semantic versioning pattern
```

### Push with Path Filtering

```yaml
on:
  push:
    branches: [main]
    paths:
      - 'src/**'
      - 'package.json'
      - 'package-lock.json'
      - '.github/workflows/ci.yml'
```

### Push with Path Ignore

```yaml
on:
  push:
    branches: [main]
    paths-ignore:
      - '**.md'
      - 'docs/**'
      - '.gitignore'
      - 'LICENSE'
```

> **Important:** You cannot use both `paths` and `paths-ignore` for the same event. Choose one.

### Push Event Context

```yaml
steps:
  - run: |
      echo "Pushed to: ${{ github.ref }}"
      echo "Commit SHA: ${{ github.sha }}"
      echo "Pushed by: ${{ github.actor }}"
      echo "Commit message: ${{ github.event.head_commit.message }}"
      echo "Before SHA: ${{ github.event.before }}"
      echo "After SHA: ${{ github.event.after }}"
```

---

## Pull Request Event

Triggers when a pull request is opened, updated, or undergoes other PR activities.

### Basic Pull Request

```yaml
on: pull_request
```

By default, `pull_request` triggers on these activity types: `opened`, `synchronize`, `reopened`.

### PR with Branch Filtering

```yaml
on:
  pull_request:
    branches:
      - main               # PRs targeting main
      - 'release/**'       # PRs targeting release branches
```

### PR with Activity Types

```yaml
on:
  pull_request:
    types:
      - opened              # PR is created
      - synchronize         # New commits pushed to PR
      - reopened            # PR is reopened
      - closed              # PR is closed or merged
      - ready_for_review    # PR marked as ready for review
      - labeled             # Label added to PR
      - unlabeled           # Label removed from PR
```

### PR with Path Filtering

```yaml
on:
  pull_request:
    branches: [main]
    paths:
      - 'src/**'
      - 'tests/**'
```

### pull_request vs pull_request_target

This distinction is **critical for security**:

| Feature | `pull_request` | `pull_request_target` |
|---------|---------------|----------------------|
| **Code context** | PR head (fork's code) | Base branch code |
| **Secrets access** | No (from forks) | Yes |
| **GITHUB_TOKEN** | Read-only (from forks) | Read-write |
| **Use case** | CI for PRs | Labeling, commenting on PRs |

```yaml
# SAFE: Runs PR author's code without secrets
on:
  pull_request:
    branches: [main]

# DANGEROUS if misconfigured: Runs with secrets access
# Only use this for operations that DON'T execute PR code
on:
  pull_request_target:
    types: [opened, labeled]
```

> **Security Warning:** Never use `pull_request_target` with `actions/checkout` to check out the PR head and then run untrusted code. This gives fork PRs access to your secrets.

### PR Event Context

```yaml
steps:
  - run: |
      echo "PR Number: ${{ github.event.pull_request.number }}"
      echo "PR Title: ${{ github.event.pull_request.title }}"
      echo "PR Author: ${{ github.event.pull_request.user.login }}"
      echo "Base Branch: ${{ github.event.pull_request.base.ref }}"
      echo "Head Branch: ${{ github.event.pull_request.head.ref }}"
      echo "Is Draft: ${{ github.event.pull_request.draft }}"
      echo "Merged: ${{ github.event.pull_request.merged }}"
```

---

## Schedule (Cron)

Triggers workflows on a recurring schedule using POSIX cron syntax.

### Cron Syntax

```
┌───────────── minute (0 - 59)
│ ┌───────────── hour (0 - 23)
│ │ ┌───────────── day of the month (1 - 31)
│ │ │ ┌───────────── month (1 - 12)
│ │ │ │ ┌───────────── day of the week (0 - 6, Sunday = 0)
│ │ │ │ │
│ │ │ │ │
* * * * *
```

### Common Schedule Patterns

```yaml
on:
  schedule:
    # Every day at midnight UTC
    - cron: '0 0 * * *'

    # Every Monday at 9:00 AM UTC
    - cron: '0 9 * * 1'

    # Every 6 hours
    - cron: '0 */6 * * *'

    # Every weekday at 8:00 AM UTC (Mon-Fri)
    - cron: '0 8 * * 1-5'

    # First day of every month at 6:00 AM UTC
    - cron: '0 6 1 * *'

    # Every 15 minutes (be careful with minute usage!)
    - cron: '*/15 * * * *'
```

### Multiple Schedules

```yaml
on:
  schedule:
    - cron: '0 6 * * 1'    # Monday at 6 AM
    - cron: '0 6 * * 4'    # Thursday at 6 AM
```

### Important Notes About Scheduled Workflows

1. **Runs on the default branch only** — scheduled workflows always run on the default branch (usually `main`)
2. **Minimum interval** — the shortest interval is every 5 minutes (`*/5 * * * *`)
3. **May be delayed** — during peak times, scheduled runs may be delayed up to 15+ minutes
4. **Auto-disabled** — GitHub disables scheduled workflows after 60 days of no repository activity
5. **Times are UTC** — all cron times are in UTC timezone

### Practical Example: Nightly Security Scan

```yaml
name: Nightly Security Scan

on:
  schedule:
    - cron: '0 2 * * *'    # Every day at 2:00 AM UTC

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          severity: 'CRITICAL,HIGH'

      - name: Check for outdated dependencies
        run: npm audit --audit-level=high
```

---

## workflow_dispatch (Manual Trigger)

Allows you to **manually trigger** a workflow from the GitHub UI, GitHub CLI, or REST API. Perfect for deployments and ad-hoc tasks.

### Basic Manual Trigger

```yaml
on:
  workflow_dispatch:
```

This adds a "Run workflow" button in the Actions tab.

### With Inputs

```yaml
on:
  workflow_dispatch:
    inputs:
      environment:
        description: 'Target deployment environment'
        required: true
        default: 'staging'
        type: choice
        options:
          - development
          - staging
          - production

      version:
        description: 'Version to deploy (e.g., 1.2.3)'
        required: true
        type: string

      dry-run:
        description: 'Perform a dry run without deploying'
        required: false
        default: false
        type: boolean

      log-level:
        description: 'Log verbosity level'
        required: false
        default: 'info'
        type: choice
        options:
          - debug
          - info
          - warning
          - error

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Deploy
        run: |
          echo "Environment: ${{ inputs.environment }}"
          echo "Version: ${{ inputs.version }}"
          echo "Dry Run: ${{ inputs.dry-run }}"
          echo "Log Level: ${{ inputs.log-level }}"

      - name: Skip deploy if dry run
        if: inputs.dry-run == false
        run: echo "Deploying for real..."
```

### Input Types

| Type | Description | Example |
|------|-------------|---------|
| `string` | Free text input | Version number, branch name |
| `boolean` | True/false checkbox | Dry run toggle |
| `choice` | Dropdown selection | Environment picker |
| `environment` | GitHub environment selector | Picks from configured environments |

### Triggering via GitHub CLI

```bash
# Basic trigger
gh workflow run deploy.yml

# With inputs
gh workflow run deploy.yml \
  -f environment=production \
  -f version=1.2.3 \
  -f dry-run=false

# On a specific branch
gh workflow run deploy.yml --ref release/2.0
```

### Triggering via REST API

```bash
curl -X POST \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/OWNER/REPO/actions/workflows/deploy.yml/dispatches \
  -d '{"ref":"main","inputs":{"environment":"production","version":"1.2.3"}}'
```

---

## repository_dispatch (External Trigger)

Triggers a workflow from an **external system** via the GitHub REST API. Useful for integrating with external CI/CD systems, webhooks, or custom tooling.

### Workflow Configuration

```yaml
on:
  repository_dispatch:
    types:
      - deploy-request
      - run-tests
      - notify

jobs:
  handle-event:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Handle deploy request
        if: github.event.action == 'deploy-request'
        run: |
          echo "Deploy version: ${{ github.event.client_payload.version }}"
          echo "Target: ${{ github.event.client_payload.environment }}"

      - name: Handle test request
        if: github.event.action == 'run-tests'
        run: |
          echo "Test suite: ${{ github.event.client_payload.suite }}"
```

### Triggering via API

```bash
curl -X POST \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/OWNER/REPO/dispatches \
  -d '{
    "event_type": "deploy-request",
    "client_payload": {
      "version": "1.2.3",
      "environment": "production",
      "triggered_by": "external-system"
    }
  }'
```

### Use Cases

- Triggering deployments from Slack bots
- Running workflows after an external build system completes
- Integration with monitoring systems (e.g., rollback on alert)
- Cross-repository workflow triggers

---

## workflow_call (Reusable Workflows)

Allows a workflow to be **called by another workflow**, enabling code reuse.

### Defining a Reusable Workflow (Callee)

```yaml
# .github/workflows/reusable-deploy.yml
name: Reusable Deploy

on:
  workflow_call:
    inputs:
      environment:
        description: 'Target environment'
        required: true
        type: string
      version:
        description: 'Version to deploy'
        required: true
        type: string
    secrets:
      deploy-token:
        description: 'Deployment authentication token'
        required: true
    outputs:
      deploy-url:
        description: 'URL of the deployment'
        value: ${{ jobs.deploy.outputs.url }}

jobs:
  deploy:
    runs-on: ubuntu-latest
    outputs:
      url: ${{ steps.deploy.outputs.url }}
    steps:
      - uses: actions/checkout@v4

      - id: deploy
        name: Deploy to ${{ inputs.environment }}
        env:
          TOKEN: ${{ secrets.deploy-token }}
        run: |
          echo "Deploying version ${{ inputs.version }} to ${{ inputs.environment }}"
          echo "url=https://${{ inputs.environment }}.example.com" >> "$GITHUB_OUTPUT"
```

### Calling a Reusable Workflow (Caller)

```yaml
# .github/workflows/main.yml
name: Main Pipeline

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      version: ${{ steps.version.outputs.version }}
    steps:
      - uses: actions/checkout@v4
      - id: version
        run: echo "version=1.2.3" >> "$GITHUB_OUTPUT"

  deploy-staging:
    needs: build
    uses: ./.github/workflows/reusable-deploy.yml
    with:
      environment: staging
      version: ${{ needs.build.outputs.version }}
    secrets:
      deploy-token: ${{ secrets.STAGING_TOKEN }}

  deploy-production:
    needs: deploy-staging
    uses: ./.github/workflows/reusable-deploy.yml
    with:
      environment: production
      version: ${{ needs.build.outputs.version }}
    secrets:
      deploy-token: ${{ secrets.PRODUCTION_TOKEN }}
```

### Cross-Repository Reusable Workflows

```yaml
jobs:
  deploy:
    uses: my-org/shared-workflows/.github/workflows/deploy.yml@main
    with:
      environment: production
    secrets: inherit    # Pass all secrets from the caller
```

> **Note:** `secrets: inherit` passes all the caller's secrets to the reusable workflow. Use it when you trust the reusable workflow.

---

## Release Event

Triggers when a GitHub Release is created, published, edited, or deleted.

### Basic Release Trigger

```yaml
on:
  release:
    types: [published]
```

### Release Activity Types

| Type | Description |
|------|-------------|
| `published` | Release is published (most common) |
| `created` | Release is created |
| `edited` | Release is edited |
| `deleted` | Release is deleted |
| `prereleased` | Pre-release is published |
| `released` | Release is published (not pre-release) |

### Practical Example: Publish Package on Release

```yaml
name: Publish on Release

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          registry-url: 'https://npm.pkg.github.com'

      - run: npm ci
      - run: npm run build

      - name: Publish package
        run: npm publish
        env:
          NODE_AUTH_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Release info
        run: |
          echo "Release Tag: ${{ github.event.release.tag_name }}"
          echo "Release Name: ${{ github.event.release.name }}"
          echo "Pre-release: ${{ github.event.release.prerelease }}"
          echo "Release URL: ${{ github.event.release.html_url }}"
```

---

## Other Useful Events

### issues

```yaml
on:
  issues:
    types: [opened, labeled]

jobs:
  auto-label:
    if: github.event.action == 'opened'
    runs-on: ubuntu-latest
    permissions:
      issues: write
    steps:
      - name: Add triage label
        run: gh issue edit ${{ github.event.issue.number }} --add-label "triage"
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### issue_comment

```yaml
on:
  issue_comment:
    types: [created]

jobs:
  slash-command:
    if: github.event.issue.pull_request && contains(github.event.comment.body, '/deploy')
    runs-on: ubuntu-latest
    steps:
      - name: Deploy from PR comment
        run: echo "Deploying as requested by ${{ github.event.comment.user.login }}"
```

### create and delete (Branch/Tag)

```yaml
on:
  create:    # Branch or tag created
  delete:    # Branch or tag deleted

jobs:
  cleanup:
    if: github.event_name == 'delete' && github.event.ref_type == 'branch'
    runs-on: ubuntu-latest
    steps:
      - name: Clean up preview environment
        run: echo "Cleaning up environment for branch ${{ github.event.ref }}"
```

### workflow_run

Triggers after another workflow completes. Useful for chaining workflows:

```yaml
on:
  workflow_run:
    workflows: ["CI Pipeline"]
    types: [completed]
    branches: [main]

jobs:
  deploy:
    if: github.event.workflow_run.conclusion == 'success'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy after successful CI
        run: echo "CI passed, deploying..."
```

---

## Filtering: Branches, Paths, and Tags

### Branch Filters

```yaml
on:
  push:
    # Include specific branches
    branches:
      - main
      - develop
      - 'release/**'       # Glob: release/1.0, release/2.0
      - 'feature/*'        # Glob: feature/login (NOT feature/auth/login)
      - 'feature/**'       # Glob: feature/login AND feature/auth/login

    # Or exclude specific branches
    branches-ignore:
      - 'dependabot/**'
      - 'temp-*'
```

### Path Filters

```yaml
on:
  push:
    # Only trigger when these paths change
    paths:
      - 'src/**'
      - '*.js'
      - 'package.json'

    # Or ignore changes to these paths
    paths-ignore:
      - '**.md'
      - 'docs/**'
      - '.github/**'
      - '!.github/workflows/**'   # Negate: DO include workflow changes
```

### Tag Filters

```yaml
on:
  push:
    tags:
      - 'v*'                      # v1.0, v2.0.1
      - 'v[0-9]+.[0-9]+.[0-9]+'  # Strict semver: v1.2.3
    tags-ignore:
      - 'v*-beta'                  # Ignore beta tags
```

### Glob Pattern Reference

| Pattern | Matches | Doesn't Match |
|---------|---------|---------------|
| `*` | Any characters (single level) | Path separators (`/`) |
| `**` | Any characters (multiple levels) | — |
| `?` | Any single character | — |
| `[abc]` | a, b, or c | — |
| `[0-9]` | Any digit | — |
| `!pattern` | Negation (exclude) | — |

### Important: branches + paths Behavior

When using both `branches` and `paths` filters, **both must match** for the workflow to trigger:

```yaml
on:
  push:
    branches: [main]      # AND
    paths: ['src/**']      # BOTH must be true
```

This means: "Trigger when pushing to `main` AND files in `src/` were changed."

---

## Activity Types

Many events support `types` to filter on specific activities:

```yaml
on:
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review]

  issues:
    types: [opened, labeled, assigned]

  release:
    types: [published]

  workflow_run:
    workflows: ["Build"]
    types: [completed]
```

### Common Activity Types by Event

| Event | Common Types |
|-------|-------------|
| `pull_request` | `opened`, `synchronize`, `reopened`, `closed`, `ready_for_review`, `labeled` |
| `issues` | `opened`, `closed`, `labeled`, `assigned`, `milestoned` |
| `issue_comment` | `created`, `edited`, `deleted` |
| `release` | `published`, `created`, `edited`, `deleted`, `prereleased` |
| `workflow_run` | `completed`, `requested`, `in_progress` |
| `check_run` | `created`, `completed`, `rerequested` |

---

## Multiple Events Combined

A single workflow can respond to multiple events:

```yaml
name: Comprehensive CI

on:
  # Trigger on push to main
  push:
    branches: [main]
    paths-ignore: ['**.md']

  # Trigger on PRs to main
  pull_request:
    branches: [main]
    paths-ignore: ['**.md']

  # Trigger on manual dispatch
  workflow_dispatch:
    inputs:
      debug:
        description: 'Enable debug mode'
        type: boolean
        default: false

  # Trigger weekly on Monday
  schedule:
    - cron: '0 9 * * 1'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Show trigger info
        run: |
          echo "Event: ${{ github.event_name }}"

          # Conditional logic based on trigger
          if [ "${{ github.event_name }}" = "schedule" ]; then
            echo "This is a scheduled run"
          elif [ "${{ github.event_name }}" = "workflow_dispatch" ]; then
            echo "This is a manual run (debug=${{ inputs.debug }})"
          else
            echo "This is a code change trigger"
          fi
```

### Conditional Jobs Based on Event Type

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm test

  deploy:
    needs: test
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - run: echo "Only deploys on push to main, not on PRs or schedule"

  full-scan:
    if: github.event_name == 'schedule'
    runs-on: ubuntu-latest
    steps:
      - run: echo "Only runs on schedule — full security scan"
```

---

## Event Payloads and Context

Every event provides a payload accessible via `github.event`. You can debug this by printing the entire payload:

```yaml
steps:
  - name: Dump full event payload
    run: echo '${{ toJSON(github.event) }}'

  - name: Dump GitHub context
    run: echo '${{ toJSON(github) }}'
```

### Most Useful Context Properties

```yaml
# Always available
${{ github.event_name }}        # "push", "pull_request", "schedule", etc.
${{ github.ref }}               # "refs/heads/main", "refs/tags/v1.0"
${{ github.ref_name }}          # "main", "v1.0" (short form)
${{ github.sha }}               # Full commit SHA
${{ github.actor }}             # User who triggered the workflow
${{ github.repository }}        # "owner/repo"
${{ github.repository_owner }} # "owner"
${{ github.workspace }}         # Runner workspace path
${{ github.run_id }}            # Unique workflow run ID
${{ github.run_number }}        # Sequential run number
${{ github.run_attempt }}       # Retry attempt number

# Push-specific
${{ github.event.head_commit.message }}
${{ github.event.before }}      # Previous commit SHA
${{ github.event.after }}       # New commit SHA
${{ github.event.commits }}     # Array of commits

# PR-specific
${{ github.event.pull_request.number }}
${{ github.event.pull_request.title }}
${{ github.event.pull_request.head.ref }}
${{ github.event.pull_request.base.ref }}
${{ github.event.pull_request.draft }}
${{ github.event.pull_request.merged }}
${{ github.event.pull_request.labels.*.name }}
```

---

## Summary

| Event | Trigger | Key Use Cases |
|-------|---------|---------------|
| `push` | Code pushed to branches/tags | CI builds, deployments |
| `pull_request` | PR opened/updated | PR checks, code review automation |
| `pull_request_target` | PR activity (base branch context) | Labeling, commenting (not for running PR code) |
| `schedule` | Cron schedule | Nightly builds, security scans, cleanup |
| `workflow_dispatch` | Manual UI/CLI/API trigger | On-demand deployments, manual testing |
| `repository_dispatch` | External API trigger | External system integration |
| `workflow_call` | Called by another workflow | Reusable workflow patterns |
| `workflow_run` | After another workflow completes | Workflow chaining |
| `release` | Release published/created | Package publishing, deployment |
| `issues` | Issue activity | Auto-labeling, triage |
| `issue_comment` | Comment on issue/PR | Slash commands, bot responses |
| `create`/`delete` | Branch/tag created/deleted | Environment provisioning/cleanup |

### Key Takeaways

1. **Use path and branch filters** to avoid running workflows unnecessarily (saves minutes!)
2. **`pull_request` is safe for forks** — `pull_request_target` requires extra caution
3. **Scheduled workflows only run on the default branch** and may be delayed
4. **`workflow_dispatch`** is essential for manual deployment triggers
5. **`workflow_call`** enables DRY workflows through reuse
6. **Always check `github.event_name`** when a workflow has multiple triggers

---

**Next Lesson:** [04 - Actions and Marketplace](./04-actions-and-marketplace.md) — Using pre-built actions and creating your own.
