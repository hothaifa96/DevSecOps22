# Lesson 1: Introduction to GitHub Actions

## Table of Contents

- [What is GitHub Actions?](#what-is-github-actions)
- [Why GitHub Actions?](#why-github-actions)
- [Key Concepts](#key-concepts)
  - [Workflows](#1-workflows)
  - [Events](#2-events)
  - [Jobs](#3-jobs)
  - [Steps](#4-steps)
  - [Actions](#5-actions)
  - [Runners](#6-runners)
- [How It All Fits Together](#how-it-all-fits-together)
- [Your First Workflow](#your-first-workflow)
- [Comparison with Other CI/CD Tools](#comparison-with-other-cicd-tools)
- [Pricing and Limits](#pricing-and-limits)
- [GitHub Actions in a DevSecOps Context](#github-actions-in-a-devsecops-context)
- [Summary](#summary)

---

## What is GitHub Actions?

**GitHub Actions** is a CI/CD (Continuous Integration / Continuous Delivery) platform built directly into GitHub. It allows you to automate your software development workflows right from your repository. With GitHub Actions, you can build, test, and deploy your code, as well as automate virtually any other task triggered by events in your repository.

Unlike traditional CI/CD tools that require separate servers and configuration, GitHub Actions is **natively integrated** into the GitHub ecosystem. This means:

- Your CI/CD pipelines live alongside your code (as YAML files in `.github/workflows/`)
- You get seamless access to GitHub events (pushes, pull requests, issues, releases, etc.)
- No separate infrastructure to manage (unless you choose self-hosted runners)
- A rich marketplace of pre-built actions you can reuse

---

## Why GitHub Actions?

| Benefit | Description |
|---------|-------------|
| **Native Integration** | Built into GitHub — no external tool setup required |
| **Configuration as Code** | Workflows defined in YAML files, versioned alongside your source code |
| **Event-Driven** | Trigger workflows on any GitHub event (push, PR, issue, cron, etc.) |
| **Marketplace** | Thousands of pre-built actions available for reuse |
| **Matrix Builds** | Test across multiple OS versions, language versions, etc. in parallel |
| **Free Tier** | Generous free minutes for public repositories (unlimited) and private repos |
| **Scalable** | From simple CI to complex multi-environment deployment pipelines |
| **Community** | Massive community with extensive documentation and examples |

---

## Key Concepts

GitHub Actions has six core concepts you need to understand. Think of them as a hierarchy:

```
Repository
  └── Workflow (YAML file)
        └── Event (trigger)
        └── Job (runs on a runner)
              └── Step
                    └── Action or shell command
```

### 1. Workflows

A **workflow** is an automated process defined in a YAML file. Workflow files live in the `.github/workflows/` directory of your repository.

- A repository can have **multiple workflows**
- Each workflow has a specific purpose (e.g., CI, deployment, code scanning)
- Workflows are triggered by **events**

```
my-repo/
├── .github/
│   └── workflows/
│       ├── ci.yml           # Runs tests on every push
│       ├── deploy.yml       # Deploys to production on release
│       └── security.yml     # Runs security scans weekly
├── src/
├── tests/
└── README.md
```

### 2. Events

An **event** is a specific activity that triggers a workflow. GitHub provides dozens of events:

| Event Type | Examples |
|-----------|----------|
| **Code events** | `push`, `pull_request`, `pull_request_review` |
| **Issue events** | `issues`, `issue_comment` |
| **Schedule** | `schedule` (cron syntax) |
| **Manual** | `workflow_dispatch` (button in UI) |
| **External** | `repository_dispatch` (API call) |
| **Reuse** | `workflow_call` (called by another workflow) |
| **Release** | `release` (published, created, etc.) |

### 3. Jobs

A **job** is a set of steps that execute on the same runner (virtual machine). Key points:

- Jobs within a workflow run **in parallel** by default
- You can configure jobs to run **sequentially** using `needs`
- Each job runs in a **fresh instance** of the runner environment
- Jobs can share data via **artifacts**

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps: [...]

  test:
    runs-on: ubuntu-latest
    needs: build          # Waits for 'build' to complete
    steps: [...]

  deploy:
    runs-on: ubuntu-latest
    needs: test           # Waits for 'test' to complete
    steps: [...]
```

### 4. Steps

A **step** is an individual task within a job. Steps run **sequentially** within a job and can:

- Run a **shell command** (using `run`)
- Use a **pre-built action** (using `uses`)
- Set environment variables
- Use conditionals

```yaml
steps:
  - name: Check out code        # Step 1: Use an action
    uses: actions/checkout@v4

  - name: Install dependencies  # Step 2: Run a shell command
    run: npm install

  - name: Run tests             # Step 3: Run a shell command
    run: npm test
```

### 5. Actions

An **action** is a reusable unit of code that performs a specific task. Actions are the building blocks of workflows:

- **Official actions** by GitHub: `actions/checkout`, `actions/setup-node`, `actions/cache`
- **Community actions** from the Marketplace: thousands available
- **Custom actions** you create: composite, JavaScript, or Docker-based

```yaml
# Using actions from different sources
steps:
  - uses: actions/checkout@v4              # Official GitHub action
  - uses: docker/build-push-action@v5      # Community action
  - uses: ./.github/actions/my-action      # Local custom action
```

### 6. Runners

A **runner** is the machine that executes your workflow jobs. GitHub provides two types:

| Type | Description | Use Case |
|------|-------------|----------|
| **GitHub-hosted** | Virtual machines managed by GitHub | Most workflows; no setup required |
| **Self-hosted** | Your own machines registered with GitHub | Special hardware, compliance, cost control |

**GitHub-hosted runner options:**

| Runner Label | OS | Specs |
|-------------|-----|-------|
| `ubuntu-latest` | Ubuntu 22.04 | 2-core CPU, 7 GB RAM, 14 GB SSD |
| `ubuntu-24.04` | Ubuntu 24.04 | 2-core CPU, 7 GB RAM, 14 GB SSD |
| `windows-latest` | Windows Server 2022 | 2-core CPU, 7 GB RAM, 14 GB SSD |
| `macos-latest` | macOS 14 (Sonoma) | 3-core CPU, 7 GB RAM, 14 GB SSD |

---

## How It All Fits Together

Here is the complete picture showing how all concepts relate:

```
┌─────────────────────────────────────────────────────────┐
│  GitHub Repository                                       │
│                                                          │
│   EVENT (e.g., push to main)                             │
│     │                                                    │
│     ▼                                                    │
│   WORKFLOW (.github/workflows/ci.yml)                    │
│     │                                                    │
│     ├── JOB: build (runs on ubuntu-latest RUNNER)        │
│     │     ├── STEP 1: actions/checkout@v4    (ACTION)    │
│     │     ├── STEP 2: actions/setup-node@v4  (ACTION)    │
│     │     ├── STEP 3: npm install            (COMMAND)   │
│     │     └── STEP 4: npm run build          (COMMAND)   │
│     │                                                    │
│     └── JOB: test (needs: build)                         │
│           ├── STEP 1: actions/checkout@v4    (ACTION)    │
│           ├── STEP 2: npm install            (COMMAND)   │
│           └── STEP 3: npm test               (COMMAND)   │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## Your First Workflow

Let's create a simple workflow that runs on every push. Create a file at `.github/workflows/hello.yml`:

```yaml
name: Hello World CI

# When to run this workflow
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

# What to run
jobs:
  greet:
    name: Say Hello
    runs-on: ubuntu-latest

    steps:
      - name: Check out the repository
        uses: actions/checkout@v4

      - name: Print a greeting
        run: echo "Hello, GitHub Actions!"

      - name: Show environment info
        run: |
          echo "Repository: ${{ github.repository }}"
          echo "Branch: ${{ github.ref }}"
          echo "Actor: ${{ github.actor }}"
          echo "Event: ${{ github.event_name }}"
          echo "Runner OS: ${{ runner.os }}"
```

### What this workflow does:

1. **Triggers** on pushes and pull requests to the `main` branch
2. **Runs a single job** called `greet` on an Ubuntu runner
3. **Checks out** the repository code
4. **Prints** a greeting and shows environment information

### How to see it run:

1. Push this file to your repository's `main` branch
2. Go to the **Actions** tab in your GitHub repository
3. You'll see the workflow run, and can click into it to see logs for each step

---

## Comparison with Other CI/CD Tools

| Feature | GitHub Actions | Jenkins | GitLab CI | CircleCI | Azure DevOps |
|---------|---------------|---------|-----------|----------|---------------|
| **Hosting** | Cloud (+ self-hosted) | Self-hosted | Cloud (+ self-hosted) | Cloud (+ self-hosted) | Cloud (+ self-hosted) |
| **Config Format** | YAML | Groovy (Jenkinsfile) | YAML | YAML | YAML |
| **Config Location** | `.github/workflows/` | `Jenkinsfile` | `.gitlab-ci.yml` | `.circleci/config.yml` | `azure-pipelines.yml` |
| **Marketplace** | 20,000+ actions | 1,800+ plugins | Limited | Orbs | Extensions |
| **Free Tier** | 2,000 min/month (private) | Free (self-host) | 400 min/month | 6,000 min/month | 1,800 min/month |
| **Setup Effort** | Minimal | High | Minimal | Low | Low |
| **Git Integration** | Native (GitHub) | Plugin-based | Native (GitLab) | API-based | Native (Azure Repos) |
| **Container Support** | Excellent | Good | Excellent | Excellent | Good |
| **Security Features** | Built-in (Dependabot, CodeQL) | Plugins | Built-in (SAST, DAST) | Plugins/Orbs | Built-in |

### When to Choose GitHub Actions:

- Your source code is already on GitHub
- You want minimal setup and maintenance overhead
- You need tight integration with GitHub features (PRs, issues, releases)
- You want access to a large marketplace of reusable actions
- You need matrix builds across multiple OS/language versions

### When Another Tool Might Be Better:

- **Jenkins**: Complex on-premises requirements, existing Jenkins investment, need for extensive plugin ecosystem
- **GitLab CI**: Your code is on GitLab, need integrated container registry and security scanning
- **CircleCI**: Need advanced caching, resource classes, or specific performance optimizations
- **Azure DevOps**: Deep Microsoft/Azure ecosystem integration, complex release pipelines

---

## Pricing and Limits

### Free Tier (GitHub Free)

| Resource | Public Repos | Private Repos |
|----------|-------------|---------------|
| **Minutes/month** | Unlimited | 2,000 |
| **Storage (artifacts/caches)** | 500 MB | 500 MB |
| **Concurrent jobs** | 20 | 20 |

### Paid Plans

| Plan | Private Repo Minutes | Storage |
|------|---------------------|---------|
| **GitHub Free** | 2,000 min/month | 500 MB |
| **GitHub Pro** | 3,000 min/month | 1 GB |
| **GitHub Team** | 3,000 min/month | 2 GB |
| **GitHub Enterprise** | 50,000 min/month | 50 GB |

### Minute Multipliers by OS

GitHub-hosted runners consume minutes at different rates depending on the operating system:

| Runner OS | Minute Multiplier |
|-----------|------------------|
| **Linux** | 1x |
| **Windows** | 2x |
| **macOS** | 10x |

> **Example:** A 10-minute job on macOS consumes 100 minutes from your quota.

### Key Limits

| Limit | Value |
|-------|-------|
| Workflow run time (max) | 35 days |
| Job execution time (max) | 6 hours |
| Concurrent jobs (Free) | 20 |
| Concurrent jobs (Enterprise) | 500 |
| API requests per hour | 1,000 |
| Workflow file size (max) | 512 KB |
| Jobs per workflow | 256 |
| Steps per job | No strict limit (practical limit ~1,000) |
| Nested reusable workflow depth | 4 levels |
| Artifact retention (default) | 90 days |
| Cache size per repo | 10 GB |

### Cost Optimization Tips

1. **Use Linux runners** whenever possible (cheapest)
2. **Cache dependencies** aggressively to reduce build times
3. **Use path filters** to skip unnecessary workflow runs
4. **Cancel in-progress runs** when a new push arrives (concurrency groups)
5. **Use self-hosted runners** for high-volume private repos
6. **Optimize matrix builds** — only test combinations that matter

---

## GitHub Actions in a DevSecOps Context

GitHub Actions is a key enabler for **DevSecOps** — integrating security into every phase of the development lifecycle:

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│   CODE   │───▶│  BUILD   │───▶│   TEST   │───▶│  DEPLOY  │
│          │    │          │    │          │    │          │
│ - Lint   │    │ - Compile│    │ - Unit   │    │ - Staging│
│ - SAST   │    │ - Docker │    │ - Integ. │    │ - Prod   │
│ - Secrets│    │ - SBOM   │    │ - DAST   │    │ - Monitor│
│   scan   │    │          │    │ - Pen    │    │          │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
     │               │               │               │
     └───────────────┴───────────────┴───────────────┘
                    GitHub Actions Workflows
```

### Security Integrations Available:

| Phase | Tool/Action | Purpose |
|-------|-------------|---------|
| **Code** | `github/codeql-action` | Static Application Security Testing (SAST) |
| **Code** | `trufflesecurity/trufflehog` | Secret detection in code |
| **Code** | `aquasecurity/trivy-action` | Vulnerability scanning |
| **Build** | `docker/build-push-action` | Secure container builds |
| **Build** | `anchore/sbom-action` | Software Bill of Materials (SBOM) |
| **Test** | `OWASP/ZAP` | Dynamic Application Security Testing (DAST) |
| **Deploy** | GitHub Environments | Approval gates, branch protection |
| **Deploy** | OIDC tokens | Secure, secretless cloud authentication |

### Example: Security-First CI Pipeline

```yaml
name: DevSecOps Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Upload scan results to GitHub Security
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'trivy-results.sarif'

  build-and-test:
    needs: security-scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm test
      - run: npm run build
```

---

## Summary

| Concept | What It Is |
|---------|-----------|
| **Workflow** | A YAML file defining an automated process (`.github/workflows/`) |
| **Event** | A trigger that starts a workflow (push, PR, cron, manual, etc.) |
| **Job** | A set of steps running on the same runner; parallel by default |
| **Step** | A single task — either a shell command (`run`) or an action (`uses`) |
| **Action** | A reusable building block (from Marketplace or custom-built) |
| **Runner** | The machine executing your job (GitHub-hosted or self-hosted) |

### Key Takeaways

1. GitHub Actions is a **powerful, native CI/CD platform** built into GitHub
2. Workflows are **YAML files** stored in `.github/workflows/`
3. The platform is **event-driven** — workflows respond to repository events
4. The **Marketplace** provides thousands of reusable actions
5. GitHub Actions is ideal for **DevSecOps** — security scanning, compliance checks, and secure deployments can be automated directly in your pipeline

---

**Next Lesson:** [02 - Workflow Syntax](./02-workflow-syntax.md) — Deep dive into YAML workflow structure and syntax.
