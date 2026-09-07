# Lesson 2: CI/CD Pipeline Stages

## Overview

| Topic | Details |
|-------|---------|
| **Duration** | 75 minutes |
| **Level** | Foundational |
| **Prerequisites** | Lesson 01 — What Is CI/CD? |
| **Objectives** | Understand each stage of a CI/CD pipeline, how stages connect, what happens at each gate, and how to design an effective pipeline end-to-end |

---

## 1. What Is a Pipeline?

A **CI/CD pipeline** is an automated workflow that takes code from a developer's commit all the way to production. Think of it as an assembly line for software — each station (stage) performs a specific task, and the product only moves forward if it passes quality checks.

### Pipeline Mental Model

```
 COMMIT ──▶ SOURCE ──▶ BUILD ──▶ TEST ──▶ SECURITY ──▶ ARTIFACT ──▶ DEPLOY ──▶ VERIFY ──▶ RELEASE
   │          │          │         │          │            │           │           │          │
   │          │          │         │          │            │           │           │          │
   ▼          ▼          ▼         ▼          ▼            ▼           ▼           ▼          ▼
 Trigger   Checkout   Compile  Automated   Scan for    Store the   Push to    Smoke test  Users
 event     code &     & package  tests     vulns &     versioned   target     & monitor   see the
           resolve              (unit,     secrets     artifact    environ-              change
           deps                 integ,                             ment
                                e2e)
```

### Key Pipeline Concepts

| Concept | Definition |
|---------|-----------|
| **Stage** | A logical phase (build, test, deploy). Stages run sequentially. |
| **Job** | A unit of work within a stage. Jobs within the same stage can run in parallel. |
| **Step** | An individual command or action within a job. |
| **Gate** | A condition (automated or manual) that must pass before the next stage begins. |
| **Trigger** | The event that starts the pipeline (push, PR, tag, schedule, manual). |
| **Runner** | The compute environment that executes jobs (container, VM, bare metal). |

### Pipeline Example Structure

```
Pipeline: "Deploy to Production"
│
├── Stage 1: Source
│   └── Job: Checkout code
│
├── Stage 2: Build
│   ├── Job: Install dependencies
│   ├── Job: Compile application
│   └── Job: Build Docker image
│
├── Stage 3: Test (parallel)
│   ├── Job: Unit tests
│   ├── Job: Integration tests
│   └── Job: Linting & code quality
│
├── Stage 4: Security Scan (parallel)
│   ├── Job: SAST (static analysis)
│   ├── Job: Dependency vulnerability scan
│   └── Job: Container image scan
│
├── Stage 5: Publish Artifact
│   └── Job: Push Docker image to registry
│
├── Stage 6: Deploy to Staging
│   └── Job: Deploy to staging environment
│
├── Stage 7: Staging Validation
│   ├── Job: Smoke tests
│   ├── Job: Integration tests (staging)
│   └── Job: Performance tests
│
├── 🚪 Manual Approval Gate
│
├── Stage 8: Deploy to Production
│   └── Job: Canary deployment → rolling update
│
└── Stage 9: Post-Deploy Verification
    ├── Job: Health checks
    ├── Job: Smoke tests (production)
    └── Job: Monitor error rates
```

---

## 2. Stage 1: Source

The **Source stage** is triggered when code changes are detected. This is the entry point to the pipeline.

### Trigger Types

| Trigger | When It Fires | Use Case |
|---------|--------------|----------|
| **Push** | Code pushed to a branch | CI on every commit |
| **Pull Request / Merge Request** | PR is opened or updated | Validate before merging |
| **Tag** | A Git tag is created (e.g., `v1.2.0`) | Release builds |
| **Schedule (Cron)** | At defined intervals | Nightly builds, security scans |
| **Manual** | User clicks "Run Pipeline" | On-demand deploys, hotfixes |
| **Webhook** | External event (API call) | Cross-system triggers |
| **Dependency Update** | Upstream artifact changes | Rebuild when base image is updated |

### What Happens in the Source Stage

1. **Repository checkout** — Clone the repository or fetch the latest changes.
2. **Branch determination** — Identify which branch triggered the build.
3. **Commit metadata** — Capture commit SHA, author, message for traceability.
4. **Dependency resolution** — Download or cache external dependencies.
5. **Environment setup** — Configure the build environment (language version, tools).

### Caching Strategy

Downloading dependencies on every build is slow. Smart pipelines cache dependencies:

```
First Run:                          Subsequent Runs:
┌──────────────┐                    ┌──────────────┐
│ npm install   │ ← 45 seconds      │ Restore cache│ ← 3 seconds
│ (fresh)       │                    │ npm install  │ ← 2 seconds (only new deps)
└──────────────┘                    └──────────────┘
```

**What to cache:**
- `node_modules/` (Node.js)
- `~/.m2/repository/` (Maven/Java)
- `~/.cache/pip/` (Python)
- Docker layer cache

---

## 3. Stage 2: Build

The **Build stage** compiles source code and produces a deployable artifact.

### Build Activities by Language

| Language/Platform | Build Tool | Output Artifact |
|---|---|---|
| Java | Maven, Gradle | JAR / WAR file |
| Go | `go build` | Static binary |
| Node.js | npm / yarn / pnpm | Bundled JavaScript (webpack, esbuild) |
| Python | setuptools, poetry | Wheel / sdist package |
| .NET | `dotnet build` | DLL assembly |
| Container | Docker / Podman / Buildah | Container image |

### Build Principles

1. **Reproducible builds** — The same source code and dependencies should produce the same artifact every time. Pin dependency versions and use lock files.
2. **Hermetic builds** — Builds should not depend on the host machine's state. Use containers or clean build environments.
3. **Fast builds** — Optimize with caching, incremental compilation, and parallel jobs. Target under 5 minutes for the build stage.
4. **Build once, deploy many** — Build the artifact once, then promote the same artifact through staging, QA, and production. Never rebuild for each environment.

### Build Once, Deploy Many

```
❌ Wrong: Rebuild for each environment
   Source ──▶ Build (dev) ──▶ Build (staging) ──▶ Build (prod)
   (Each build might produce a slightly different artifact!)

✅ Right: Build once, promote the artifact
   Source ──▶ Build ──▶ Artifact ──▶ Deploy (dev) ──▶ Deploy (staging) ──▶ Deploy (prod)
                          │
                          └── Same artifact, different config (env vars, secrets)
```

### Containerized Builds

Modern pipelines build container images as the primary artifact:

```dockerfile
# Multi-stage Dockerfile — separates build from runtime
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci                     # Deterministic install
COPY . .
RUN npm run build              # Compile TypeScript, bundle

FROM node:20-alpine AS runtime
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
EXPOSE 3000
CMD ["node", "dist/server.js"]
```

**Benefits of multi-stage builds:**
- Build tools are not in the production image (smaller, more secure).
- Clear separation between build-time and run-time dependencies.

---

## 4. Stage 3: Test

The **Test stage** validates that the code works correctly. This is often the most complex and time-consuming stage.

### The Test Pyramid

```
                    /\
                   /  \
                  / E2E \          ← Few, slow, expensive
                 /  Tests \           (minutes)
                /──────────\
               / Integration \      ← Some, moderate speed
              /    Tests      \        (seconds to minutes)
             /────────────────\
            /    Unit Tests     \    ← Many, fast, cheap
           /____________________\      (milliseconds)
```

> The test pyramid is covered in depth in Lesson 03. Here we focus on how tests fit into pipeline stages.

### Test Types in the Pipeline

| Test Type | When in Pipeline | Duration | What It Validates |
|-----------|-----------------|----------|-------------------|
| **Linting / Static Analysis** | Build or early Test | Seconds | Code style, common errors |
| **Unit Tests** | Test stage (parallel) | Seconds–minutes | Individual functions/classes |
| **Integration Tests** | Test stage (after unit) | Minutes | Component interactions, API contracts |
| **End-to-End Tests** | After staging deploy | Minutes–hours | Full user workflows |
| **Smoke Tests** | After any deployment | Seconds | Critical paths still work |
| **Performance Tests** | Staging (scheduled or per-release) | Minutes–hours | Response times, throughput |
| **Security Tests** | Dedicated Security stage | Minutes | Vulnerabilities, misconfigurations |

### Parallelizing Tests

Slow test suites should be parallelized:

```
Stage: Test
├── Job 1: Unit Tests (shard 1/3)      ──┐
├── Job 2: Unit Tests (shard 2/3)      ──┼── Run simultaneously
├── Job 3: Unit Tests (shard 3/3)      ──┘
├── Job 4: Integration Tests           ──┐
├── Job 5: Lint + Code Quality         ──┼── Run simultaneously
└── Job 6: Type Checking               ──┘
     │
     ▼ (all must pass)
   Next Stage
```

### Test Reports and Artifacts

Pipeline test stages should produce structured reports:

- **JUnit XML** — Standard format for test results (supported by all CI systems).
- **Code coverage reports** — Show which lines of code are tested (e.g., Istanbul/nyc, JaCoCo).
- **Test trend dashboards** — Track test pass rates, flakiness, and duration over time.

---

## 5. Stage 4: Security Scanning

Security scanning is increasingly treated as its own dedicated pipeline stage — a core DevSecOps practice.

### Security Scan Types

| Scan Type | Full Name | What It Does | When |
|-----------|-----------|-------------|------|
| **SAST** | Static Application Security Testing | Analyzes source code for vulnerabilities | Build / Test stage |
| **SCA** | Software Composition Analysis | Checks dependencies for known CVEs | Build stage |
| **DAST** | Dynamic Application Security Testing | Tests running application for vulnerabilities | After staging deploy |
| **Container Scan** | Container Image Scanning | Scans Docker images for vulnerable packages | After image build |
| **Secret Detection** | Secret / Credential Scanning | Finds hardcoded passwords, API keys, tokens | Source / Build stage |
| **IaC Scan** | Infrastructure as Code Scanning | Checks Terraform/CloudFormation for misconfigs | Build stage |
| **License Compliance** | License Scanning | Ensures dependencies use approved licenses | Build stage |

### Security Gate Policies

Not all vulnerabilities should block the pipeline. Define a policy:

```
Security Gate Policy:
  ┌─────────────────────────────────────────────────┐
  │  Critical vulnerabilities  → BLOCK pipeline     │
  │  High vulnerabilities      → BLOCK pipeline     │
  │  Medium vulnerabilities    → WARN, create ticket │
  │  Low vulnerabilities       → LOG, track trend    │
  └─────────────────────────────────────────────────┘
```

> Security scanning is covered in depth in Lesson 07 — CI/CD Security.

---

## 6. Stage 5: Artifact Management

After a successful build and test, the pipeline produces an **artifact** — the deployable unit.

### What Gets Published

| Artifact Type | Registry / Storage | Example |
|---|---|---|
| Container image | Docker Hub, ECR, GCR, ACR, Harbor | `myapp:v1.2.3` |
| JAR / WAR | Maven Central, Nexus, Artifactory | `myapp-1.2.3.jar` |
| npm package | npm registry, GitHub Packages | `@myorg/myapp@1.2.3` |
| Python wheel | PyPI, private PyPI | `myapp-1.2.3-py3-none-any.whl` |
| Helm chart | Helm repository, OCI registry | `myapp-chart-1.2.3.tgz` |
| Binary / executable | S3, GCS, Artifactory | `myapp-linux-amd64-v1.2.3` |

### Versioning the Artifact

Every artifact should be uniquely versioned. Common strategies:

```
Semantic Versioning:    v1.2.3          (MAJOR.MINOR.PATCH)
Git SHA:                abc1234         (short commit hash)
Timestamp:              20240115-143022 (date-time)
Combined:               v1.2.3-abc1234  (SemVer + SHA for traceability)
```

### Artifact Immutability

> **Rule:** Once an artifact is published with a version tag, it must never be overwritten. If you need to change something, create a new version.

```
❌  Push myapp:v1.2.3 → find bug → push DIFFERENT image as myapp:v1.2.3
✅  Push myapp:v1.2.3 → find bug → fix → push myapp:v1.2.4
```

> Artifact management is covered in depth in Lesson 05.

---

## 7. Stage 6: Deployment

The **Deployment stage** pushes the artifact to a target environment.

### Deployment Environments

Most organizations use multiple environments:

```
┌───────────┐    ┌───────────┐    ┌───────────┐    ┌───────────────┐
│    Dev     │───▶│  Staging   │───▶│    QA     │───▶│  Production   │
│            │    │ (Pre-prod) │    │ (optional)│    │               │
│ Auto-deploy│    │ Auto-deploy│    │ Manual    │    │ Manual or     │
│ on commit  │    │ on merge   │    │ approval  │    │ Auto (canary) │
└───────────┘    └───────────┘    └───────────┘    └───────────────┘
```

### Environment Parity

Environments should be as similar as possible to production:

| Aspect | Dev | Staging | Production |
|--------|-----|---------|------------|
| **Infrastructure** | Smaller scale | Same architecture | Full scale |
| **Data** | Synthetic/seed data | Anonymized prod data | Real data |
| **Config** | Dev settings | Prod-like settings | Production settings |
| **Secrets** | Dev credentials | Staging credentials | Production credentials |
| **Network** | Simplified | Mirrors prod | Production network |

### Deployment Strategies Overview

| Strategy | Description | Risk | Rollback Speed |
|----------|-------------|------|----------------|
| **Recreate** | Stop old, start new | High (downtime) | Slow |
| **Rolling Update** | Replace instances gradually | Low | Medium |
| **Blue-Green** | Run two identical environments, switch traffic | Very Low | Instant (switch back) |
| **Canary** | Route small % of traffic to new version | Very Low | Fast (route back) |
| **A/B Testing** | Route traffic by user segments | Low | Fast |

> Deployment strategies are covered in depth in Lesson 04.

---

## 8. Stage 7: Post-Deployment Verification

Deploying is not the end — you must **verify** that the deployment is healthy.

### Verification Activities

1. **Health Checks** — Confirm the application responds on its health endpoint.
   ```
   GET /healthz  → 200 OK  ✅
   GET /readyz   → 200 OK  ✅
   ```

2. **Smoke Tests** — Run a small set of critical-path tests against the live environment.
   ```
   Test: Can a user log in?            ✅
   Test: Can a user view the dashboard? ✅
   Test: Can a user make a purchase?    ✅
   ```

3. **Synthetic Monitoring** — Automated scripts that simulate user actions continuously.

4. **Error Rate Monitoring** — Compare error rates before and after deployment.
   ```
   Pre-deploy error rate:  0.1%
   Post-deploy error rate: 0.15%  (within threshold ✅)
   ```

5. **Performance Monitoring** — Check that response times haven't degraded.
   ```
   Pre-deploy p99 latency:  200ms
   Post-deploy p99 latency: 210ms  (within threshold ✅)
   ```

### Automated Rollback Triggers

Define conditions that automatically trigger a rollback:

```
Rollback if ANY of the following occur within 10 minutes of deployment:
  ├── Error rate increases by more than 5%
  ├── p99 latency exceeds 500ms
  ├── Health check fails 3 consecutive times
  └── Crash loop detected (pod restarts > 3)
```

---

## 9. Stage 8: Release

**Deployment** and **Release** are not the same thing:

| Term | Meaning |
|------|---------|
| **Deployment** | Pushing code to an environment (technical act) |
| **Release** | Making a feature available to users (business decision) |

### Decoupling Deployment from Release

Using **feature flags**, you can deploy code to production without releasing it:

```
Code deployed to production:

if (featureFlags.isEnabled("new-checkout-flow", user)) {
    showNewCheckoutFlow();    // Only visible to flagged users
} else {
    showOldCheckoutFlow();    // Everyone else sees this
}
```

**Benefits:**
- Deploy anytime without risk — features are hidden behind flags.
- Gradually roll out to 1% → 10% → 50% → 100% of users.
- Instantly disable a problematic feature without a redeploy.
- A/B test different experiences.

---

## 10. Pipeline Design Patterns

### Pattern 1: Fan-Out / Fan-In

Run independent jobs in parallel, then converge:

```
                    ┌── Unit Tests ──────┐
                    │                     │
Build ──────────────┼── Integration Tests─┼──── Deploy
                    │                     │
                    └── Security Scans ──┘
                    
        (fan-out: parallel)     (fan-in: all must pass)
```

### Pattern 2: Pipeline of Pipelines

Complex systems trigger downstream pipelines:

```
Frontend Pipeline ──────┐
                         ├──▶  Integration Test Pipeline ──▶ Deploy Pipeline
Backend Pipeline ───────┘
```

### Pattern 3: Environment Promotion

The same artifact is promoted through environments:

```
Build ──▶ Artifact ──▶ Dev ──▶ Staging ──▶ Prod
                        │        │          │
                        ▼        ▼          ▼
                      Auto     Auto      Manual Gate
                      Deploy   Deploy    + Canary
```

### Pattern 4: Monorepo Pipeline

Different paths trigger different pipelines:

```
Monorepo:
├── services/
│   ├── auth/       ← Change here triggers Auth Pipeline only
│   ├── payments/   ← Change here triggers Payments Pipeline only
│   └── frontend/   ← Change here triggers Frontend Pipeline only
└── shared/
    └── libs/       ← Change here triggers ALL pipelines
```

---

## 11. Pipeline Metrics — Measuring Effectiveness

### Key Metrics to Track

| Metric | What It Measures | Target |
|--------|-----------------|--------|
| **Pipeline duration** | Total time from commit to production | < 15 minutes (CI), < 1 hour (full CD) |
| **Build time** | Time for the build stage | < 5 minutes |
| **Test time** | Time for all test stages | < 10 minutes |
| **Success rate** | % of pipeline runs that succeed | > 95% |
| **Flaky test rate** | % of tests that intermittently fail | < 1% |
| **Queue time** | Time a job waits for a runner | < 2 minutes |
| **Recovery time** | Time to fix a broken pipeline | < 30 minutes |
| **Deployment frequency** | How often you deploy to production | Daily+ |

### Pipeline Duration Budget

Allocate a time budget for each stage:

```
Total Pipeline Budget: 15 minutes
├── Source + Checkout:   30 seconds
├── Build:               2 minutes
├── Unit Tests:          3 minutes
├── Integration Tests:   4 minutes
├── Security Scans:      3 minutes
├── Artifact Publish:    1 minute
└── Deploy + Verify:     1.5 minutes
```

> If a stage exceeds its budget, optimize it (parallelize, cache, split tests).

---

## 12. Real-World Pipeline Examples

### Example: E-Commerce Application

```
Trigger: Push to main branch

Stage 1 — Build (2 min)
  ├── Install dependencies (npm ci)
  ├── Compile TypeScript
  ├── Build Docker image
  └── Tag image: myapp:${COMMIT_SHA}

Stage 2 — Test (5 min, parallel)
  ├── Unit tests (Jest, 3 shards)
  ├── Integration tests (API + DB)
  ├── Lint (ESLint + Prettier)
  └── Type check (tsc --noEmit)

Stage 3 — Security (3 min, parallel)
  ├── npm audit (dependency scan)
  ├── Trivy (container scan)
  └── Gitleaks (secret detection)

Stage 4 — Publish (1 min)
  └── Push Docker image to ECR

Stage 5 — Deploy to Staging (2 min)
  └── Helm upgrade --install staging

Stage 6 — Staging Tests (5 min)
  ├── Smoke tests
  ├── E2E tests (Playwright)
  └── Performance baseline (k6)

Gate — Manual Approval (for production)

Stage 7 — Deploy to Production (5 min)
  ├── Canary (10% traffic)
  ├── Monitor for 5 minutes
  └── Full rollout (100%)

Stage 8 — Verify (2 min)
  ├── Production smoke tests
  └── Monitor error rates
```

---

## 13. Review Questions

1. **What is the difference between a stage, a job, and a step?** Give an example of each.
2. **Why should you "build once, deploy many" instead of rebuilding for each environment?**
3. **A pipeline takes 45 minutes to complete. Where would you start optimizing?** List three strategies.
4. **What is the difference between deployment and release?** How do feature flags help decouple them?
5. **Design a pipeline (stages only) for a mobile application** that needs to support iOS and Android builds.
6. **Your security scan found a critical vulnerability but it's Friday at 5 PM.** Should the pipeline block the deployment? What factors influence your decision?

---

## 14. Further Reading

- **Book:** *Continuous Delivery* by Jez Humble & David Farley — Chapter 5: "Anatomy of the Deployment Pipeline"
- **Article:** [Pipeline Design Patterns](https://docs.gitlab.com/ee/ci/pipelines/pipeline_architectures.html) — GitLab Documentation
- **Article:** [Build Once, Deploy Many](https://12factor.net/build-release-run) — The Twelve-Factor App

---

*Previous: [01 - What Is CI/CD?](01-what-is-cicd.md) | Next: [03 - Testing Strategies](03-testing-strategies.md)*
