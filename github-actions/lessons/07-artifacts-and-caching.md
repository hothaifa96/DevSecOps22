# Lesson 7: Artifacts and Caching

## Table of Contents

- [Overview: Artifacts vs Caching](#overview-artifacts-vs-caching)
- [Artifacts](#artifacts)
  - [Uploading Artifacts](#uploading-artifacts)
  - [Downloading Artifacts](#downloading-artifacts)
  - [Artifacts Between Jobs](#artifacts-between-jobs)
  - [Artifacts Across Workflow Runs](#artifacts-across-workflow-runs)
  - [Artifact Retention and Limits](#artifact-retention-and-limits)
- [Caching](#caching)
  - [How Caching Works](#how-caching-works)
  - [Using actions/cache](#using-actionscache)
  - [Cache Keys and Restore Keys](#cache-keys-and-restore-keys)
  - [Cache Strategies Per Language](#cache-strategies-per-language)
  - [Built-in Caching in Setup Actions](#built-in-caching-in-setup-actions)
  - [Cache Limits and Eviction](#cache-limits-and-eviction)
- [Advanced Patterns](#advanced-patterns)
- [Troubleshooting](#troubleshooting)
- [Summary](#summary)

---

## Overview: Artifacts vs Caching

Both artifacts and caching store files between steps/jobs, but they serve different purposes:

| Feature | Artifacts | Cache |
|---------|-----------|-------|
| **Purpose** | Share build outputs between jobs or download results | Speed up workflows by reusing dependencies |
| **Lifetime** | Persists after workflow completes (default 90 days) | Available across workflow runs (evicted by LRU) |
| **Scope** | Available to other jobs in the same run (or downloaded later) | Available to all workflow runs on the same branch |
| **Size limit** | No strict limit per artifact (repo storage limit applies) | 10 GB per repository |
| **Typical use** | Build outputs, test reports, binaries, logs | `node_modules`, pip packages, Maven `.m2`, Go modules |
| **Downloadable** | Yes (from Actions UI or API) | No (internal only) |

### When to Use Which

```
Need to share files between JOBS in the same workflow?
  → Use ARTIFACTS

Need to speed up dependency installation across RUNS?
  → Use CACHE

Need to download build results from the GitHub UI?
  → Use ARTIFACTS

Need to store node_modules/pip packages between pushes?
  → Use CACHE
```

---

## Artifacts

### Uploading Artifacts

Use `actions/upload-artifact@v4` to save files from a job:

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm run build

      # Upload a single directory
      - uses: actions/upload-artifact@v4
        with:
          name: build-output
          path: dist/

      # Upload multiple paths
      - uses: actions/upload-artifact@v4
        with:
          name: reports
          path: |
            coverage/
            test-results/
            *.log

      # Upload with options
      - uses: actions/upload-artifact@v4
        with:
          name: production-build
          path: dist/
          retention-days: 5                    # Override default retention
          if-no-files-found: error             # error, warn, or ignore
          compression-level: 6                 # 0 (none) to 9 (best)
          overwrite: true                      # Overwrite existing artifact
```

### Downloading Artifacts

Use `actions/download-artifact@v4` to retrieve files:

```yaml
jobs:
  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      # Download a specific artifact
      - uses: actions/download-artifact@v4
        with:
          name: build-output
          path: dist/                          # Where to extract

      # Download ALL artifacts from the workflow run
      - uses: actions/download-artifact@v4
        # No 'name' = download everything
        # Each artifact goes to a subdirectory matching its name

      - run: ls -la
      # build-output/
      # reports/
      # production-build/
```

### Artifacts Between Jobs

The most common use case — passing build output from a build job to a deploy job:

```yaml
name: Build and Deploy

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - run: npm ci
      - run: npm run build
      - run: npm test

      # Upload build output
      - uses: actions/upload-artifact@v4
        with:
          name: webapp
          path: dist/
          retention-days: 1

      # Upload test results
      - uses: actions/upload-artifact@v4
        if: always()                           # Upload even on failure
        with:
          name: test-results
          path: test-results/
          retention-days: 7

  deploy-staging:
    needs: build
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: webapp
          path: dist/

      - name: Deploy to staging
        run: |
          echo "Deploying $(ls dist/ | wc -l) files to staging"

  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: webapp
          path: dist/

      - name: Deploy to production
        run: |
          echo "Deploying to production"
```

### Artifacts Across Workflow Runs

Download artifacts from a previous workflow run using the GitHub API or `actions/download-artifact`:

```yaml
jobs:
  compare:
    runs-on: ubuntu-latest
    steps:
      # Download artifact from a specific workflow run
      - uses: actions/download-artifact@v4
        with:
          name: build-output
          path: previous-build/
          github-token: ${{ secrets.GITHUB_TOKEN }}
          repository: ${{ github.repository }}
          run-id: 1234567890                   # Specific run ID

      # Or use the GitHub CLI
      - name: Download from previous run
        run: |
          gh run download $RUN_ID -n build-output -D previous-build/
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          RUN_ID: 1234567890
```

### Artifact Retention and Limits

| Setting | Default | Range |
|---------|---------|-------|
| **Retention period** | 90 days | 1-400 days |
| **Storage limit (Free)** | 500 MB | — |
| **Storage limit (Pro)** | 1 GB | — |
| **Storage limit (Team)** | 2 GB | — |
| **Storage limit (Enterprise)** | 50 GB | — |

**Configure retention:**

```yaml
# Per-artifact retention
- uses: actions/upload-artifact@v4
  with:
    name: my-artifact
    path: dist/
    retention-days: 5              # Keep for 5 days only
```

**Repository-level setting:** Go to Settings > Actions > General > Artifact and log retention.

### Merging Multiple Artifacts

When matrix jobs produce artifacts:

```yaml
jobs:
  build:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
    steps:
      - uses: actions/checkout@v4
      - run: npm run build

      # Each matrix job uploads its own artifact
      - uses: actions/upload-artifact@v4
        with:
          name: build-${{ matrix.os }}
          path: dist/

  release:
    needs: build
    runs-on: ubuntu-latest
    steps:
      # Download all build artifacts
      - uses: actions/download-artifact@v4
        with:
          pattern: build-*                     # Download all matching artifacts
          merge-multiple: true                 # Merge into single directory
          path: all-builds/
```

---

## Caching

### How Caching Works

```
┌─────────────────────────────────────────────────────┐
│ Workflow Run #1 (no cache exists)                    │
│                                                      │
│  1. Check cache key: npm-linux-abc123                │
│  2. Cache miss → install dependencies from scratch   │
│  3. Save to cache: npm-linux-abc123                  │
│     ⏱️ npm ci took 45 seconds                        │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ Workflow Run #2 (cache exists, same lockfile)        │
│                                                      │
│  1. Check cache key: npm-linux-abc123                │
│  2. Cache hit! → restore from cache                  │
│  3. Skip full install (already cached)               │
│     ⏱️ Restore took 5 seconds (90% faster!)          │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ Workflow Run #3 (lockfile changed)                   │
│                                                      │
│  1. Check cache key: npm-linux-def456                │
│  2. Cache miss on exact key                          │
│  3. Check restore keys: npm-linux-                   │
│  4. Partial hit → restore closest match              │
│  5. npm ci updates the differences                   │
│  6. Save new cache: npm-linux-def456                 │
│     ⏱️ Partial restore + update took 15 seconds      │
└─────────────────────────────────────────────────────┘
```

### Using actions/cache

```yaml
- uses: actions/cache@v4
  with:
    path: ~/.npm                                       # What to cache
    key: ${{ runner.os }}-npm-${{ hashFiles('**/package-lock.json') }}
    restore-keys: |                                    # Fallback keys
      ${{ runner.os }}-npm-
```

### Cache Keys and Restore Keys

The cache system uses a key-based lookup strategy:

#### Primary Key (Exact Match)

```yaml
key: ${{ runner.os }}-npm-${{ hashFiles('**/package-lock.json') }}
# Example: Linux-npm-a1b2c3d4e5f6
```

- If an exact match is found → **cache hit** (dependencies restored)
- If no exact match → check **restore keys**

#### Restore Keys (Prefix Match)

```yaml
restore-keys: |
  ${{ runner.os }}-npm-
  ${{ runner.os }}-
```

- Restore keys are checked in order
- The most recent cache matching the prefix is restored
- After the job, a **new cache is saved** with the primary key

#### Key Design Strategies

```yaml
# Strategy 1: Lock file hash (most common)
key: ${{ runner.os }}-npm-${{ hashFiles('**/package-lock.json') }}

# Strategy 2: Include branch for branch-specific caches
key: ${{ runner.os }}-npm-${{ github.ref_name }}-${{ hashFiles('**/package-lock.json') }}
restore-keys: |
  ${{ runner.os }}-npm-${{ github.ref_name }}-
  ${{ runner.os }}-npm-main-
  ${{ runner.os }}-npm-

# Strategy 3: Include workflow for workflow-specific caches
key: ${{ runner.os }}-${{ github.workflow }}-npm-${{ hashFiles('**/package-lock.json') }}

# Strategy 4: Weekly cache refresh
key: ${{ runner.os }}-npm-week${{ github.run_number / 100 }}-${{ hashFiles('**/package-lock.json') }}
```

### Cache Strategies Per Language

#### Node.js (npm)

```yaml
- uses: actions/cache@v4
  with:
    path: ~/.npm
    key: ${{ runner.os }}-npm-${{ hashFiles('**/package-lock.json') }}
    restore-keys: |
      ${{ runner.os }}-npm-

- run: npm ci
```

#### Node.js (yarn)

```yaml
- name: Get yarn cache directory
  id: yarn-cache
  run: echo "dir=$(yarn cache dir)" >> "$GITHUB_OUTPUT"

- uses: actions/cache@v4
  with:
    path: ${{ steps.yarn-cache.outputs.dir }}
    key: ${{ runner.os }}-yarn-${{ hashFiles('**/yarn.lock') }}
    restore-keys: |
      ${{ runner.os }}-yarn-

- run: yarn install --frozen-lockfile
```

#### Node.js (pnpm)

```yaml
- uses: pnpm/action-setup@v3
  with:
    version: 9

- name: Get pnpm store directory
  id: pnpm-cache
  run: echo "dir=$(pnpm store path)" >> "$GITHUB_OUTPUT"

- uses: actions/cache@v4
  with:
    path: ${{ steps.pnpm-cache.outputs.dir }}
    key: ${{ runner.os }}-pnpm-${{ hashFiles('**/pnpm-lock.yaml') }}
    restore-keys: |
      ${{ runner.os }}-pnpm-

- run: pnpm install --frozen-lockfile
```

#### Python (pip)

```yaml
- uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
    restore-keys: |
      ${{ runner.os }}-pip-

- run: pip install -r requirements.txt
```

#### Python (pipenv)

```yaml
- uses: actions/cache@v4
  with:
    path: ~/.local/share/virtualenvs
    key: ${{ runner.os }}-pipenv-${{ hashFiles('**/Pipfile.lock') }}
    restore-keys: |
      ${{ runner.os }}-pipenv-

- run: pipenv install --deploy
```

#### Java (Maven)

```yaml
- uses: actions/cache@v4
  with:
    path: ~/.m2/repository
    key: ${{ runner.os }}-maven-${{ hashFiles('**/pom.xml') }}
    restore-keys: |
      ${{ runner.os }}-maven-

- run: mvn install -DskipTests
```

#### Java (Gradle)

```yaml
- uses: actions/cache@v4
  with:
    path: |
      ~/.gradle/caches
      ~/.gradle/wrapper
    key: ${{ runner.os }}-gradle-${{ hashFiles('**/*.gradle*', '**/gradle-wrapper.properties') }}
    restore-keys: |
      ${{ runner.os }}-gradle-

- run: ./gradlew build
```

#### Go

```yaml
- uses: actions/cache@v4
  with:
    path: |
      ~/go/pkg/mod
      ~/.cache/go-build
    key: ${{ runner.os }}-go-${{ hashFiles('**/go.sum') }}
    restore-keys: |
      ${{ runner.os }}-go-

- run: go build ./...
```

#### Rust (Cargo)

```yaml
- uses: actions/cache@v4
  with:
    path: |
      ~/.cargo/bin/
      ~/.cargo/registry/index/
      ~/.cargo/registry/cache/
      ~/.cargo/git/db/
      target/
    key: ${{ runner.os }}-cargo-${{ hashFiles('**/Cargo.lock') }}
    restore-keys: |
      ${{ runner.os }}-cargo-

- run: cargo build --release
```

#### Docker Layer Caching

```yaml
- uses: docker/build-push-action@v5
  with:
    context: .
    push: true
    tags: myapp:latest
    cache-from: type=gha                       # GitHub Actions cache backend
    cache-to: type=gha,mode=max
```

### Built-in Caching in Setup Actions

Many setup actions have built-in caching — simpler than using `actions/cache` directly:

```yaml
# Node.js — built-in cache
- uses: actions/setup-node@v4
  with:
    node-version: '20'
    cache: 'npm'                               # or 'yarn' or 'pnpm'

# Python — built-in cache
- uses: actions/setup-python@v5
  with:
    python-version: '3.12'
    cache: 'pip'                               # or 'pipenv' or 'poetry'

# Java — built-in cache
- uses: actions/setup-java@v4
  with:
    distribution: 'temurin'
    java-version: '21'
    cache: 'maven'                             # or 'gradle'

# Go — built-in cache
- uses: actions/setup-go@v5
  with:
    go-version: '1.22'
    cache: true                                # Caches Go modules

# .NET — built-in cache
- uses: actions/setup-dotnet@v4
  with:
    dotnet-version: '8.0'
    cache: true
```

### Cache Limits and Eviction

| Limit | Value |
|-------|-------|
| **Total cache per repo** | 10 GB |
| **Single cache entry max** | 10 GB |
| **Eviction policy** | Least Recently Used (LRU) |
| **Cache lifetime** | 7 days without access |
| **Branch scope** | Feature branches can access caches from default branch |

#### Cache Scoping Rules

```
main branch ──────────────────── Can only use main's caches
  │
  ├── feature/login ──────────── Can use its own caches + main's caches
  │
  └── feature/signup ─────────── Can use its own caches + main's caches
       │
       └── PR #42 ───────────── Can use PR's caches + feature/signup's + main's
```

Key rules:
1. A workflow run can **restore** caches from the current branch, the base branch, and the default branch
2. Caches created on a feature branch are **not accessible** to other feature branches
3. Caches created on the default branch are accessible to **all branches**
4. Pull request workflows can access caches from the base branch

---

## Advanced Patterns

### Conditional Caching

```yaml
- uses: actions/cache@v4
  id: cache
  with:
    path: node_modules
    key: ${{ runner.os }}-modules-${{ hashFiles('**/package-lock.json') }}

- name: Install dependencies
  if: steps.cache.outputs.cache-hit != 'true'    # Only install on cache miss
  run: npm ci
```

### Cache and Artifact Combo

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # Cache for dependencies (reused across runs)
      - uses: actions/cache@v4
        with:
          path: node_modules
          key: ${{ runner.os }}-modules-${{ hashFiles('**/package-lock.json') }}

      - run: npm ci
      - run: npm run build

      # Artifact for build output (shared between jobs in this run)
      - uses: actions/upload-artifact@v4
        with:
          name: build
          path: dist/

  test:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # Same cache key → reuses cached node_modules
      - uses: actions/cache@v4
        with:
          path: node_modules
          key: ${{ runner.os }}-modules-${{ hashFiles('**/package-lock.json') }}

      # Download the build artifact
      - uses: actions/download-artifact@v4
        with:
          name: build
          path: dist/

      - run: npm test
```

### Saving Cache on Failure

By default, cache is only saved on successful jobs. Use `actions/cache/save` and `actions/cache/restore` for more control:

```yaml
steps:
  - uses: actions/checkout@v4

  # Restore cache (always attempt)
  - uses: actions/cache/restore@v4
    id: cache
    with:
      path: node_modules
      key: ${{ runner.os }}-modules-${{ hashFiles('**/package-lock.json') }}

  - run: npm ci
  - run: npm test

  # Save cache even if tests fail
  - uses: actions/cache/save@v4
    if: always() && steps.cache.outputs.cache-hit != 'true'
    with:
      path: node_modules
      key: ${{ runner.os }}-modules-${{ hashFiles('**/package-lock.json') }}
```

### Multiple Caches in One Job

```yaml
steps:
  - uses: actions/checkout@v4

  # Cache 1: npm dependencies
  - uses: actions/cache@v4
    with:
      path: ~/.npm
      key: ${{ runner.os }}-npm-${{ hashFiles('**/package-lock.json') }}
      restore-keys: ${{ runner.os }}-npm-

  # Cache 2: Next.js build cache
  - uses: actions/cache@v4
    with:
      path: .next/cache
      key: ${{ runner.os }}-nextjs-${{ hashFiles('**/package-lock.json') }}-${{ hashFiles('**/*.js', '**/*.jsx', '**/*.ts', '**/*.tsx') }}
      restore-keys: |
        ${{ runner.os }}-nextjs-${{ hashFiles('**/package-lock.json') }}-
        ${{ runner.os }}-nextjs-

  # Cache 3: Playwright browsers
  - uses: actions/cache@v4
    with:
      path: ~/.cache/ms-playwright
      key: ${{ runner.os }}-playwright-${{ hashFiles('**/package-lock.json') }}

  - run: npm ci
  - run: npm run build
  - run: npx playwright test
```

---

## Troubleshooting

### Common Issues and Solutions

| Issue | Cause | Solution |
|-------|-------|---------|
| Cache miss every run | Lock file changes frequently | Use broader restore keys |
| Cache too large | Caching build artifacts + deps | Cache only dependencies |
| Artifact not found | Job dependency missing | Ensure `needs` is set correctly |
| Slow cache restore | Cache entry too large | Split into multiple smaller caches |
| Cache not shared between branches | Branch scoping rules | Build cache on default branch first |
| Artifact expired | Retention period exceeded | Increase `retention-days` |

### Debugging Cache

```yaml
steps:
  - uses: actions/cache@v4
    id: cache
    with:
      path: node_modules
      key: ${{ runner.os }}-modules-${{ hashFiles('**/package-lock.json') }}

  - name: Cache debug info
    run: |
      echo "Cache hit: ${{ steps.cache.outputs.cache-hit }}"
      echo "Cache key: ${{ runner.os }}-modules-${{ hashFiles('**/package-lock.json') }}"
      echo "Lock file hash: ${{ hashFiles('**/package-lock.json') }}"
```

### Clearing Cache

```bash
# List caches via GitHub CLI
gh cache list

# Delete a specific cache
gh cache delete <cache-key>

# Delete all caches
gh cache list --json key -q '.[].key' | xargs -I {} gh cache delete {}
```

---

## Summary

| Feature | Action | Purpose |
|---------|--------|---------|
| **Upload artifact** | `actions/upload-artifact@v4` | Save files from a job |
| **Download artifact** | `actions/download-artifact@v4` | Retrieve files in another job |
| **Cache** | `actions/cache@v4` | Cache dependencies across runs |
| **Cache restore** | `actions/cache/restore@v4` | Restore-only (no auto-save) |
| **Cache save** | `actions/cache/save@v4` | Save-only (manual control) |
| **Built-in cache** | `setup-node`, `setup-python`, etc. | Simplest caching approach |

### Key Takeaways

1. **Use artifacts** to share build outputs between jobs in the same workflow run
2. **Use caching** to speed up dependency installation across workflow runs
3. **Built-in caching** in setup actions is the simplest approach — use it first
4. **Design cache keys carefully** — include the lock file hash for automatic invalidation
5. **Use restore keys** for graceful fallback when exact cache misses
6. **Cache scoping** allows feature branches to use the default branch's cache
7. **Monitor cache usage** — the 10 GB limit is per repository, and old caches are evicted via LRU
8. **Set artifact retention** to minimize storage costs (use short retention for CI builds)

---

**Next Lesson:** [08 - Environments and Deployments](./08-environments-and-deployments.md) — Controlled deployments with approval gates and environment protection.
