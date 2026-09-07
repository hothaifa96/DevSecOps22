# Lesson 8: CI/CD Best Practices

## Overview

| Topic | Details |
|-------|---------|
| **Duration** | 75 minutes |
| **Level** | Intermediate |
| **Prerequisites** | Lessons 01–07 |
| **Objectives** | Apply pipeline-as-code; design fast feedback loops; implement idempotent deployments; integrate IaC with CI/CD; monitor deployments; validate post-deployment health |

---

## 1. Pipeline as Code

### The Principle

Your CI/CD pipeline definition should be **treated like application code**: version-controlled, reviewed, tested, and stored alongside the code it builds.

### Why Pipeline as Code?

| Before (Click-Ops Pipelines) | After (Pipeline as Code) |
|---|---|
| Pipeline configured via web UI | Pipeline defined in a YAML/code file |
| No history of changes | Full Git history of pipeline changes |
| No code review for pipeline changes | Pipeline changes go through PR review |
| Hard to replicate across projects | Copy, fork, or template pipelines |
| "Who changed the pipeline and when?" | `git log .github/workflows/` |
| Different pipelines drift apart | Shared templates ensure consistency |

### Pipeline Definition Formats

| CI/CD Platform | File Format | Location |
|---|---|---|
| **GitHub Actions** | YAML | `.github/workflows/*.yml` |
| **GitLab CI** | YAML | `.gitlab-ci.yml` |
| **Jenkins** | Groovy | `Jenkinsfile` |
| **Azure DevOps** | YAML | `azure-pipelines.yml` |
| **CircleCI** | YAML | `.circleci/config.yml` |
| **Tekton** | YAML (K8s CRDs) | `tekton/` directory |
| **Argo Workflows** | YAML (K8s CRDs) | `argo/` directory |
| **Dagger** | Go / Python / TypeScript | Code in your preferred language |

### Example: Well-Structured Pipeline as Code

```yaml
# .github/workflows/ci-cd.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

# Least-privilege permissions
permissions:
  contents: read
  packages: write
  id-token: write       # For OIDC

# Environment variables centralized
env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  # Stage 1: Build and Test
  build-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@b4ffde65    # SHA-pinned
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npm run lint
      - run: npm test -- --coverage
      - uses: actions/upload-artifact@v4
        with:
          name: coverage-report
          path: coverage/

  # Stage 2: Security Scan
  security:
    runs-on: ubuntu-latest
    needs: build-and-test
    steps:
      - uses: actions/checkout@b4ffde65
      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          severity: 'CRITICAL,HIGH'
          exit-code: '1'

  # Stage 3: Build and Push Image (only on main)
  build-image:
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    needs: [build-and-test, security]
    steps:
      - uses: actions/checkout@b4ffde65
      - uses: docker/build-push-action@v5
        with:
          push: true
          tags: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}

  # Stage 4: Deploy to Staging
  deploy-staging:
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    needs: build-image
    environment: staging
    steps:
      - name: Deploy to staging
        run: |
          helm upgrade --install myapp ./chart \
            --set image.tag=${{ github.sha }} \
            --namespace staging

  # Stage 5: Deploy to Production (manual approval)
  deploy-production:
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    needs: deploy-staging
    environment: production     # Requires manual approval
    steps:
      - name: Deploy to production
        run: |
          helm upgrade --install myapp ./chart \
            --set image.tag=${{ github.sha }} \
            --namespace production
```

### Pipeline Templates and Reusability

For organizations with many repositories, create **shared pipeline templates**:

```
Organization Pipeline Templates:
├── templates/
│   ├── node-ci.yml           # Standard Node.js CI pipeline
│   ├── python-ci.yml         # Standard Python CI pipeline
│   ├── docker-build.yml      # Standard Docker build + scan
│   ├── deploy-k8s.yml        # Standard Kubernetes deployment
│   └── security-scan.yml     # Standard security scanning
│
└── Each repo references the template:
    uses: my-org/.github/workflows/node-ci.yml@v1
    with:
      node-version: '20'
```

**Benefits:**
- **Consistency** — All teams follow the same security and quality standards.
- **Maintenance** — Update the template once, all repos benefit.
- **Governance** — Security team can mandate certain pipeline stages.
- **Onboarding** — New projects get a production-ready pipeline immediately.

---

## 2. Fast Feedback Loops

### Why Speed Matters

The value of CI/CD is in the **speed of feedback**. If your pipeline takes an hour, developers context-switch, forget what they were working on, and batch up changes (defeating the purpose of CI).

```
Pipeline Duration vs. Developer Behavior:

  < 5 min:   Developer waits, fixes immediately if broken     ✅
  5-10 min:  Developer grabs coffee, returns to fix            ✅
  10-30 min: Developer starts another task, context-switches   ⚠️
  30-60 min: Developer forgets, batches up changes             ❌
  > 60 min:  Developer ignores pipeline, deploys rarely        ❌
```

### Strategies for Fast Pipelines

#### 1. Parallelize Everything Possible

```
❌ Sequential (25 minutes):
  Lint (3m) → Unit Tests (5m) → Integ Tests (8m) → Security (4m) → Build Image (5m)

✅ Parallel (13 minutes):
  ┌── Lint (3m) ──────────────┐
  ├── Unit Tests (5m) ────────┤
  ├── Integ Tests (8m) ───────┼──▶ Build Image (5m) ──▶ Done
  └── Security (4m) ──────────┘
      (parallel: 8m)              (sequential: 5m)
      Total: 13 minutes
```

#### 2. Cache Aggressively

```yaml
# Cache node_modules between pipeline runs
- uses: actions/cache@v4
  with:
    path: ~/.npm
    key: npm-${{ hashFiles('package-lock.json') }}
    restore-keys: npm-

# Cache Docker layers
- uses: docker/build-push-action@v5
  with:
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

**What to cache:**
| Language | Cache Target | Typical Savings |
|---|---|---|
| Node.js | `node_modules/`, `~/.npm` | 30–60 seconds |
| Python | `~/.cache/pip`, `.venv/` | 20–40 seconds |
| Java | `~/.m2/repository` | 60–120 seconds |
| Go | `~/go/pkg/mod` | 20–40 seconds |
| Docker | Layer cache | 60–300 seconds |

#### 3. Test Splitting and Sharding

Split large test suites across multiple parallel runners:

```
1,000 unit tests on 1 runner:  10 minutes
1,000 unit tests on 4 runners: 2.5 minutes each (parallel)

Runner 1: Tests 1–250    ──┐
Runner 2: Tests 251–500  ──┼── All run simultaneously
Runner 3: Tests 501–750  ──┤
Runner 4: Tests 751–1000 ──┘
                            │
                            ▼ (all must pass)
                          Next stage
```

Tools: **Jest** (`--shard`), **pytest-split**, **CircleCI test splitting**, **Knapsack Pro**

#### 4. Fail Fast

Order pipeline steps so that the **fastest checks run first:**

```
Recommended Order:
  1. Lint / Format check        (seconds — catches obvious issues)
  2. Type checking              (seconds — catches type errors)
  3. Unit tests                 (minutes — catches logic bugs)
  4. Build                      (minutes — catches compilation errors)
  5. Integration tests          (minutes — catches interaction bugs)
  6. Security scan              (minutes — catches vulnerabilities)
  7. E2E tests                  (minutes — catches user-facing bugs)

If step 1 fails, steps 2-7 never run → instant feedback.
```

#### 5. Incremental Builds

Only rebuild what changed:

```
Mono-repo incremental build:
  Changed: services/auth/src/login.js
  
  Build auth-service:  YES (changed)
  Build payment-service: SKIP (unchanged)
  Build frontend:      SKIP (unchanged)
  
  Tools: Nx (affected:build), Turborepo, Bazel
```

---

## 3. Idempotent Deployments

### What Is Idempotency?

A deployment is **idempotent** if running it multiple times produces the same result as running it once. You should be able to re-run a deployment at any time without side effects.

```
Idempotent:
  deploy(v1.2.3) → App running v1.2.3
  deploy(v1.2.3) → App still running v1.2.3 (no changes, no errors)
  deploy(v1.2.3) → App still running v1.2.3 (safe to retry)

NOT Idempotent:
  deploy() → App running
  deploy() → Error: "Port already in use"
  deploy() → Error: "Resource already exists"
```

### Why Idempotency Matters

- **Retry safety** — If a deployment fails halfway, you can re-run it without cleanup.
- **Pipeline reliability** — Flaky networks or transient errors don't require manual intervention.
- **Disaster recovery** — Re-running the deployment restores the desired state.
- **GitOps compatibility** — GitOps controllers continuously reconcile state.

### Making Deployments Idempotent

| Tool / Approach | Idempotent Command | Non-Idempotent Equivalent |
|---|---|---|
| **Kubernetes** | `kubectl apply -f deployment.yaml` | `kubectl create -f deployment.yaml` |
| **Helm** | `helm upgrade --install myapp ./chart` | `helm install myapp ./chart` |
| **Terraform** | `terraform apply` (always plans then applies) | Manual resource creation |
| **Ansible** | Declarative modules (e.g., `state: present`) | Shell commands |
| **Docker Compose** | `docker compose up -d` | Manual `docker run` |

### Declarative vs. Imperative Deployment

```
Imperative (step-by-step instructions):
  1. Create database
  2. Create network
  3. Deploy container A
  4. Deploy container B
  5. Configure load balancer
  Problem: Step 3 fails → Must manually clean up steps 1-2 before retrying.

Declarative (desired state):
  "I want: database, network, container A, container B, load balancer"
  Tool figures out what exists and what needs to change.
  Problem: Step 3 fails → Re-run → Tool skips steps 1-2 (already exist), retries 3.
```

---

## 4. Infrastructure as Code (IaC) Integration

### CI/CD for Infrastructure

Infrastructure changes should go through the same CI/CD process as application code:

```
IaC CI/CD Pipeline:

  Developer changes Terraform/CloudFormation/Pulumi code
      │
      ▼
  ┌─────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
  │   Lint &    │───▶│   Security   │───▶│   Plan /     │───▶│   Apply      │
  │   Validate  │    │   Scan       │    │   Preview    │    │   (Manual    │
  │             │    │   (Checkov,  │    │   (terraform │    │    Approval) │
  │             │    │    tfsec)    │    │    plan)     │    │              │
  └─────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
```

### IaC Security Scanning

| Tool | What It Scans | Example Finding |
|------|-------------|-----------------|
| **Checkov** | Terraform, CloudFormation, K8s, Dockerfile | "S3 bucket is publicly accessible" |
| **tfsec** | Terraform | "Security group allows ingress from 0.0.0.0/0" |
| **KICS** | Terraform, CloudFormation, Docker, K8s, Ansible | "Container running as root" |
| **Terrascan** | Terraform, K8s, Helm, CloudFormation | "RDS instance is not encrypted" |
| **OPA / Conftest** | Any structured data (YAML, JSON, HCL) | Custom policy violations |

### Terraform in CI/CD — Best Practice

```yaml
# Terraform CI/CD Pipeline
jobs:
  terraform:
    steps:
      # 1. Format check
      - run: terraform fmt -check
      
      # 2. Initialize
      - run: terraform init
      
      # 3. Validate syntax
      - run: terraform validate
      
      # 4. Security scan
      - run: checkov -d . --framework terraform
      
      # 5. Plan (show what will change)
      - run: terraform plan -out=tfplan
      
      # 6. Post plan as PR comment (for review)
      - name: Post plan to PR
        # Show reviewers exactly what infrastructure changes will happen
      
      # 7. Apply (only on merge to main, with approval)
      - run: terraform apply tfplan
        if: github.ref == 'refs/heads/main'
```

### GitOps — Git as the Source of Truth for Infrastructure

```
GitOps Workflow:

  Developer ──▶ Git Commit ──▶ Git Repository ◀── GitOps Controller
   (human)      (change)        (desired state)    (ArgoCD / Flux)
                                      │                    │
                                      │              Continuously
                                      │              compares
                                      │                    │
                                      ▼                    ▼
                                  Desired State  ←→  Actual State
                                  (in Git)            (in cluster)
                                      │                    │
                                      └──── Drift? ────────┘
                                              │
                                         Auto-reconcile
                                         (apply changes)
```

**GitOps Principles:**
1. **Declarative** — The entire system is described declaratively.
2. **Versioned and immutable** — The desired state is stored in Git.
3. **Pulled automatically** — Agents pull the desired state and apply it.
4. **Continuously reconciled** — Drift is automatically corrected.

**GitOps Tools:**
| Tool | Maintained By | Approach |
|------|--------------|----------|
| **ArgoCD** | CNCF | Pull-based, UI dashboard, multi-cluster |
| **Flux** | CNCF | Pull-based, lightweight, Kubernetes-native |
| **Jenkins X** | Jenkins community | Opinionated CI/CD + GitOps for K8s |

---

## 5. Monitoring Deployments

### The Three Pillars of Observability

```
                    Observability
                   /      |      \
                  /       |       \
            Metrics    Logs     Traces
            (numbers)  (events)  (requests)
            
  "What's      "What      "Where is the
  happening    happened    request spending
  right now?"  and why?"   its time?"
```

| Pillar | What It Is | Tools | Example |
|--------|-----------|-------|---------|
| **Metrics** | Numerical measurements over time | Prometheus, Datadog, CloudWatch | Request rate: 500/sec, Error rate: 0.1% |
| **Logs** | Discrete events with context | ELK Stack, Loki, CloudWatch Logs | `ERROR: Database connection timeout at 10:15:03` |
| **Traces** | Request path through distributed systems | Jaeger, Zipkin, OpenTelemetry | Request took 450ms: 200ms in API, 250ms in DB |

### Deployment Monitoring Checklist

Immediately after deploying, monitor these metrics:

```
Post-Deployment Monitoring Dashboard:
┌─────────────────────────────────────────────────────────┐
│  Deployment: myapp v1.2.3 (deployed 2 minutes ago)      │
│                                                          │
│  HTTP Request Rate:  ████████████████████  520/sec  ✅   │
│  Error Rate (5xx):   █                     0.12%    ✅   │
│  p50 Latency:        ████████              48ms     ✅   │
│  p99 Latency:        ████████████████      195ms    ✅   │
│  CPU Usage:          ███████████           42%      ✅   │
│  Memory Usage:       ████████████████      65%      ✅   │
│  Pod Restarts:       0                              ✅   │
│  Active Connections: ████████████████████  1,250    ✅   │
│                                                          │
│  Comparison: Metric values are within normal range       │
│  relative to pre-deployment baseline.                    │
└─────────────────────────────────────────────────────────┘
```

### Deployment Events in Monitoring

Annotate your monitoring dashboards with deployment events:

```
Request Latency Over Time:
  ms
  250 │                                    
  200 │              ┌ deploy v1.2.3       ┌ deploy v1.2.4
  150 │──────────────┤────────────────────┤──────────────
  100 │              │                     │
   50 │              │                     │
    0 └──────────────┴─────────────────────┴──────────────▶ time

  The vertical line shows exactly when deployments happened,
  making it easy to correlate changes in metrics with deployments.
```

### Deployment Notifications

Notify the team when deployments happen:

```
Notification Channels:
  ├── Slack: #deployments channel
  │   "🚀 myapp v1.2.3 deployed to production by Alice (commit: abc1234)"
  │
  ├── PagerDuty: Alert on-call if error rate spikes post-deploy
  │
  ├── Monitoring: Deployment annotation on Grafana dashboard
  │
  └── Audit log: Record who deployed what, when, from which pipeline
```

---

## 6. Post-Deployment Validation

### Health Checks

Every application should expose health check endpoints:

| Endpoint | Purpose | What It Checks |
|----------|---------|----------------|
| `/healthz` or `/health` | **Liveness** — Is the process alive? | Application is running and responding |
| `/readyz` or `/ready` | **Readiness** — Can it serve traffic? | Dependencies (DB, cache, APIs) are reachable |
| `/startupz` | **Startup** — Has it finished initializing? | Migrations done, caches warmed |

```json
// GET /readyz
{
  "status": "healthy",
  "checks": {
    "database": { "status": "up", "latency_ms": 5 },
    "redis": { "status": "up", "latency_ms": 2 },
    "external_api": { "status": "up", "latency_ms": 45 }
  },
  "version": "1.2.3",
  "uptime_seconds": 3600
}
```

### Automated Smoke Tests Post-Deploy

```bash
#!/bin/bash
# post-deploy-smoke-test.sh
set -e

BASE_URL="${1:-https://myapp.example.com}"
echo "Running post-deployment smoke tests against $BASE_URL"

# Test 1: Health endpoint
echo -n "Health check... "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/healthz")
[ "$STATUS" -eq 200 ] && echo "PASS" || { echo "FAIL (HTTP $STATUS)"; exit 1; }

# Test 2: Homepage loads
echo -n "Homepage... "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/")
[ "$STATUS" -eq 200 ] && echo "PASS" || { echo "FAIL (HTTP $STATUS)"; exit 1; }

# Test 3: API returns valid JSON
echo -n "API status... "
RESPONSE=$(curl -s "$BASE_URL/api/v1/status")
echo "$RESPONSE" | jq -e '.status == "ok"' > /dev/null && echo "PASS" || { echo "FAIL"; exit 1; }

# Test 4: Verify deployed version
echo -n "Version check... "
VERSION=$(curl -s "$BASE_URL/api/v1/status" | jq -r '.version')
echo "Deployed version: $VERSION"

echo "All smoke tests passed!"
```

### Progressive Delivery Validation

For canary and blue-green deployments, automate the promotion decision:

```
Canary Validation Steps:
  1. Deploy canary (5% traffic)
  2. Wait 5 minutes
  3. Compare canary metrics to baseline:
     ├── Error rate: canary (0.15%) vs baseline (0.12%) → Within threshold ✅
     ├── Latency p99: canary (210ms) vs baseline (200ms) → Within threshold ✅
     └── CPU: canary (45%) vs baseline (42%) → Within threshold ✅
  4. Promote to 25% traffic
  5. Wait 5 minutes
  6. Compare metrics again...
  7. Promote to 100%
  
  At any step, if metrics exceed thresholds → Auto-rollback
```

---

## 7. Environment Management

### Environment Strategy

| Environment | Purpose | Deployed When | Who Uses It |
|-------------|---------|--------------|-------------|
| **Local** | Developer testing | Always (local machine) | Individual developer |
| **Dev** | Integration testing | Every commit to main | Development team |
| **Staging** | Pre-production validation | Every successful dev build | QA team, stakeholders |
| **Pre-prod** | Final validation | Release candidates | Security team, ops |
| **Production** | Live users | After all approvals | Everyone |

### Ephemeral Environments (Preview Environments)

Create a **temporary environment for every Pull Request:**

```
PR #42: Add user profile feature
  │
  ├── CI builds the PR
  ├── CI deploys to: https://pr-42.preview.myapp.com
  ├── PR author tests the feature
  ├── Reviewer reviews code + tests the preview
  ├── PR is merged
  └── Ephemeral environment is automatically destroyed

Benefits:
  - Test changes in a real environment before merging
  - Share with non-technical stakeholders for feedback
  - Run E2E tests against a realistic environment
  - No permanent infrastructure cost (created/destroyed per PR)
```

### Environment Configuration Management

```
Configuration Hierarchy:
  ├── Shared defaults (config/default.yml)
  │   └── applies to all environments
  │
  ├── Environment-specific overrides
  │   ├── config/development.yml
  │   ├── config/staging.yml
  │   └── config/production.yml
  │
  └── Secrets (from secrets manager — NOT in Git)
      ├── vault://secret/myapp/dev/database
      ├── vault://secret/myapp/staging/database
      └── vault://secret/myapp/production/database
```

---

## 8. Pipeline Reliability and Maintenance

### Dealing with Flaky Pipelines

A **flaky pipeline** is one that sometimes passes and sometimes fails for the same code. This is one of the biggest threats to CI/CD effectiveness.

```
Flaky Pipeline Impact:
  Pipeline fails → Developer reruns → Passes → "Must have been flaky"
  Repeated: Developers stop trusting the pipeline
  Result: Developers merge without waiting for CI → Defeats the entire purpose
```

### Flakiness Sources and Fixes

| Source | Example | Fix |
|--------|---------|-----|
| **Flaky tests** | Test depends on timing or external service | Mock external services, use deterministic data |
| **Resource exhaustion** | Runner runs out of memory | Right-size runners, optimize builds |
| **Network issues** | npm install fails due to registry timeout | Use dependency caching, mirror registries |
| **Race conditions** | Parallel jobs accessing shared resource | Isolate test environments |
| **Stale cache** | Cached dependencies don't match lock file | Key cache on lock file hash |
| **Runner state** | Previous job left files on the runner | Use clean/ephemeral runners |

### Pipeline SLO

Define a Service Level Objective for your pipeline:

```
Pipeline SLOs:
  ├── Reliability: > 98% of pipeline runs succeed (excluding code failures)
  ├── Duration: 95% of pipelines complete in < 15 minutes
  ├── Queue time: 95% of jobs start within 2 minutes
  └── Recovery: Broken pipelines are fixed within 30 minutes

Track these metrics and alert when SLOs are breached.
```

---

## 9. CI/CD Governance and Compliance

### Audit Trail

Every deployment should be fully traceable:

```
Audit Trail for Production Deployment:
  ├── Who: alice@company.com
  ├── When: 2024-01-15T14:30:00Z
  ├── What: myapp v1.2.3 (image SHA: sha256:abc123...)
  ├── Where: production cluster (us-east-1)
  ├── Why: PR #142 — "Add payment retry logic"
  ├── How: GitHub Actions workflow run #4521
  ├── Approved by: bob@company.com (manual approval at 14:28:00Z)
  ├── Pipeline: https://github.com/myorg/myapp/actions/runs/4521
  ├── Commit: abc1234 (signed by alice@company.com)
  ├── Security scan: Passed (0 critical, 0 high)
  └── Tests: 342 passed, 0 failed, 0 skipped
```

### Separation of Duties

In regulated environments, the person who writes code should not be the same person who approves deployment:

```
Required Approvals:
  Code Change (PR):
    ├── At least 1 peer developer approval
    └── CI pipeline must pass

  Production Deployment:
    ├── All staging tests must pass
    ├── Security scan must pass
    └── Manual approval from: team lead OR on-call engineer
        (must be different person from the PR author)
```

### Compliance Frameworks and CI/CD

| Framework | CI/CD Requirements |
|-----------|-------------------|
| **SOC 2** | Change management, access control, audit logging |
| **HIPAA** | Access control, audit trail, encryption |
| **PCI DSS** | Code review, vulnerability scanning, change control |
| **FedRAMP** | SBOM, supply chain security, continuous monitoring |
| **ISO 27001** | Change management, risk assessment, access control |

---

## 10. Summary — The CI/CD Best Practices Checklist

### Pipeline Design
- [ ] Pipeline is defined as code (version-controlled YAML/config).
- [ ] Pipeline uses shared templates for consistency across teams.
- [ ] Pipeline runs on every commit and every PR.
- [ ] Pipeline stages are parallelized where possible.
- [ ] Pipeline completes in under 15 minutes (CI) / 30 minutes (full CD).

### Testing
- [ ] Test pyramid is followed (many unit, some integration, few E2E).
- [ ] Tests run in parallel (sharding for large suites).
- [ ] Flaky tests are tracked, quarantined, and fixed promptly.
- [ ] Test coverage is measured and enforced (e.g., 80% minimum).
- [ ] Smoke tests run after every deployment.

### Security
- [ ] SAST runs on every PR.
- [ ] SCA/dependency scanning runs on every build.
- [ ] Container images are scanned before publishing.
- [ ] Secrets are managed via a secrets manager (never in code).
- [ ] SBOM is generated for every release.
- [ ] Images are signed (Cosign/Sigstore).
- [ ] CI/CD actions are pinned to SHA.

### Deployment
- [ ] Build once, deploy many (same artifact across environments).
- [ ] Deployments are idempotent (safe to retry).
- [ ] Zero-downtime deployment strategy is used (rolling, blue-green, or canary).
- [ ] Automated rollback is configured.
- [ ] Feature flags decouple deployment from release.

### Monitoring
- [ ] Deployment events are annotated in monitoring dashboards.
- [ ] Post-deployment health checks are automated.
- [ ] Error rate and latency are monitored after every deployment.
- [ ] Team is notified of deployment status (Slack, email, etc.).

### Governance
- [ ] Full audit trail for every production deployment.
- [ ] Branch protection rules enforce code review and CI.
- [ ] Manual approval gates for production (when required).
- [ ] Pipeline SLOs are defined and tracked.

---

## 11. Review Questions

1. **What does "pipeline as code" mean and why is it important?** How does it compare to configuring pipelines through a web UI?
2. **Your CI pipeline takes 45 minutes. List five specific strategies** you would use to get it under 15 minutes.
3. **What does "idempotent deployment" mean?** Give an example of an idempotent deployment command and a non-idempotent one.
4. **Explain GitOps.** How is it different from traditional CI/CD that pushes changes to a cluster?
5. **Design a post-deployment validation strategy** for a payment processing API. What metrics would you monitor? What would trigger a rollback?
6. **A developer says: "Our pipeline fails randomly about 10% of the time, but it passes when we rerun it."** What would you investigate? How would you fix it?
7. **Your company needs SOC 2 compliance.** What CI/CD practices would you implement to meet the audit requirements?

---

## 12. Further Reading

- **Book:** *Continuous Delivery* by Jez Humble & David Farley
- **Book:** *Accelerate* by Nicole Forsgren, Jez Humble & Gene Kim
- **Book:** *The DevOps Handbook* by Gene Kim et al.
- **Article:** [GitOps Principles](https://opengitops.dev/) — OpenGitOps
- **Tool:** [ArgoCD](https://argo-cd.readthedocs.io/) — GitOps for Kubernetes
- **Article:** [The Twelve-Factor App](https://12factor.net/) — Foundational principles for modern applications
- **Article:** [DORA Metrics](https://dora.dev/guides/dora-metrics-four-keys/) — Measuring DevOps performance

---

*Previous: [07 - CI/CD Security](07-cicd-security.md)*

---

## Course Lessons Complete

You have completed all 8 CI/CD concept lessons! Proceed to the [labs](../labs/) to practice what you've learned:

1. [Lab 01 — Design a Pipeline](../labs/lab01-design-a-pipeline.md)
2. [Lab 02 — Branching Strategy](../labs/lab02-branching-strategy.md)
3. [Lab 03 — Deployment Strategies](../labs/lab03-deployment-strategies.md)
4. [Lab 04 — Secure Pipeline](../labs/lab04-secure-pipeline.md)
