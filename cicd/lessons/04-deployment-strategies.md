# Lesson 4: Deployment Strategies

## Overview

| Topic | Details |
|-------|---------|
| **Duration** | 90 minutes |
| **Level** | Intermediate |
| **Prerequisites** | Lessons 01–03 |
| **Objectives** | Understand and compare deployment strategies; know when to use each; understand rollback mechanisms; implement zero-downtime deployments |

---

## 1. Why Deployment Strategy Matters

Deployment is the riskiest moment in the software delivery lifecycle. The strategy you choose determines:

- **Downtime** — Will users experience an outage?
- **Risk exposure** — How many users are affected if something goes wrong?
- **Rollback speed** — How quickly can you undo a bad deployment?
- **Resource cost** — How much extra infrastructure do you need?
- **Complexity** — How hard is it to implement and maintain?

> **Goal:** Deploy new versions of software to production with zero downtime, minimal risk, and instant rollback capability.

---

## 2. Strategy 1: Recreate (Big Bang)

### How It Works

Stop the old version entirely, then start the new version.

```
Time ──────────────────────────────────────────────▶

v1 running │████████████████│
                             │ DOWNTIME │
v2 running                               │████████████████│

Users:     │  ✅ working     │ ❌ down  │  ✅ working      │
```

### Process

1. Stop all instances of v1.
2. Deploy v2.
3. Start all instances of v2.
4. Verify health.

### Characteristics

| Property | Value |
|----------|-------|
| **Downtime** | Yes — during the switch |
| **Risk** | High — all users hit v2 at once |
| **Rollback** | Slow — must redeploy v1 |
| **Resource cost** | Low — only one version running at a time |
| **Complexity** | Very low |

### When to Use

- **Development and test environments** — Downtime is acceptable.
- **Batch processing systems** — No real-time users.
- **Database-heavy migrations** — When you need exclusive access to the database.
- **Very early-stage products** — Few or no users.

### When NOT to Use

- Production systems with real users.
- Any system with SLA/uptime requirements.
- Customer-facing applications.

---

## 3. Strategy 2: Rolling Update

### How It Works

Replace instances of the old version **one at a time** (or in small batches). At any point during the deployment, both old and new versions are running simultaneously.

```
Time ──────────────────────────────────────────────▶

Instance 1:  │v1 ████│v2 ████████████████████████│
Instance 2:  │v1 ██████████│v2 ████████████████████│
Instance 3:  │v1 ████████████████│v2 ████████████████│
Instance 4:  │v1 ██████████████████████│v2 ████████████│

Traffic:     │ v1 v1 v1 v1 │ v1+v2 │ v2 v2 v2 v2   │
             │              │ mixed │                 │
```

### Process

1. Take one instance out of the load balancer.
2. Deploy v2 to that instance.
3. Health check the new instance.
4. Add it back to the load balancer.
5. Repeat for each instance.

### Kubernetes Rolling Update Configuration

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 4
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1    # At most 1 pod can be down during update
      maxSurge: 1          # At most 1 extra pod can be created
  template:
    spec:
      containers:
      - name: myapp
        image: myapp:v2
        readinessProbe:          # Critical for rolling updates
          httpGet:
            path: /healthz
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10
        livenessProbe:
          httpGet:
            path: /healthz
            port: 8080
          initialDelaySeconds: 15
          periodSeconds: 20
```

### Characteristics

| Property | Value |
|----------|-------|
| **Downtime** | None (if health checks are configured correctly) |
| **Risk** | Medium — gradual rollout limits blast radius |
| **Rollback** | Medium speed — must roll forward or redeploy v1 |
| **Resource cost** | Low — minimal extra resources (maxSurge) |
| **Complexity** | Low — native support in Kubernetes, ECS, etc. |

### Key Considerations

- **Backward compatibility** — During the rollout, v1 and v2 run simultaneously. Both versions must be compatible with the same database schema and API contracts.
- **Session handling** — Users may be routed to different versions between requests. Use sticky sessions or stateless design.
- **Health checks** — Readiness probes are critical. A pod that reports ready before it's actually ready will receive traffic and may fail.

### When to Use

- **Default choice** for most web applications.
- When you need zero-downtime deployment without complex infrastructure.
- When your application is stateless (or handles state externally).

---

## 4. Strategy 3: Blue-Green Deployment

### How It Works

Maintain **two identical production environments** — Blue and Green. Only one is live at any time. Deploy to the idle environment, test it, then switch traffic.

```
                    BEFORE                          AFTER SWITCH
           ┌────────────────────┐          ┌────────────────────┐
           │                    │          │                    │
Users ──▶  │   Load Balancer    │   Users ──▶  Load Balancer    │
           │                    │          │                    │
           └────────┬───────────┘          └───────┬────────────┘
                    │                              │
              ┌─────▼─────┐                  ┌─────┴─────┐
              │           │                  │           │
         ┌────▼────┐ ┌────┴────┐        ┌────┴────┐ ┌────▼────┐
         │  BLUE   │ │  GREEN  │        │  BLUE   │ │  GREEN  │
         │  (v1)   │ │  (v2)   │        │  (v1)   │ │  (v2)   │
         │  LIVE   │ │  IDLE   │        │  IDLE   │ │  LIVE   │
         │  ✅     │ │  Deploy │        │         │ │  ✅     │
         │         │ │  & test │        │         │ │         │
         └─────────┘ └─────────┘        └─────────┘ └─────────┘
```

### Process

1. Identify the idle environment (e.g., Green).
2. Deploy v2 to Green.
3. Run full tests against Green (it's not receiving real traffic yet).
4. Switch the load balancer/DNS to point to Green.
5. Green is now live. Blue is now idle.
6. Monitor for issues.
7. If problems arise, switch back to Blue (instant rollback).

### Characteristics

| Property | Value |
|----------|-------|
| **Downtime** | None (traffic switch is instant) |
| **Risk** | Very Low — full testing before switch |
| **Rollback** | Instant — switch traffic back to the old environment |
| **Resource cost** | High — double the infrastructure |
| **Complexity** | Medium — requires traffic routing management |

### Implementation Approaches

**DNS-based switching:**
```
Before: app.example.com → CNAME → blue.example.com (v1)
After:  app.example.com → CNAME → green.example.com (v2)
```
*Caution:* DNS TTL can cause delays. Some clients cache DNS for longer than the TTL.

**Load balancer-based switching:**
```
Before: ALB target group → Blue instances
After:  ALB target group → Green instances
```
*Better:* Instant switch, no DNS propagation delay.

**Kubernetes with services:**
```yaml
# Switch by updating the Service selector
apiVersion: v1
kind: Service
metadata:
  name: myapp
spec:
  selector:
    app: myapp
    version: green    # Change to "blue" for rollback
  ports:
  - port: 80
    targetPort: 8080
```

### Database Challenges

Blue-Green is straightforward for stateless applications, but databases add complexity:

```
Challenge: Both Blue and Green need to access the same database.

Option 1: Shared database (most common)
  ┌──────┐                    ┌──────┐
  │ Blue │──┐            ┌──▶│Green │
  │ (v1) │  │            │   │ (v2) │
  └──────┘  │  ┌──────┐  │   └──────┘
            └──▶│  DB  │──┘
               └──────┘
  Requirement: DB schema must be backward-compatible

Option 2: Separate databases (complex)
  ┌──────┐    ┌──────┐     ┌──────┐    ┌──────┐
  │ Blue │───▶│DB-B  │     │Green │───▶│DB-G  │
  │ (v1) │    │      │     │ (v2) │    │      │
  └──────┘    └──────┘     └──────┘    └──────┘
  Requirement: Data sync between databases
```

### When to Use

- **Mission-critical applications** where instant rollback is essential.
- **Major version upgrades** that need thorough pre-production testing.
- **Compliance-regulated environments** where you need pre-release validation.
- When you can afford the infrastructure cost.

---

## 5. Strategy 4: Canary Deployment

### How It Works

Deploy the new version to a **small subset** of your infrastructure and route a small percentage of traffic to it. Monitor closely. If everything looks good, gradually increase the traffic percentage.

```
Phase 1: Canary (5% traffic)        Phase 2: Expand (25%)          Phase 3: Full (100%)

  ┌─────────────┐                   ┌─────────────┐               ┌─────────────┐
  │Load Balancer│                   │Load Balancer│               │Load Balancer│
  └──────┬──────┘                   └──────┬──────┘               └──────┬──────┘
    95%  │  5%                        75%  │  25%                    0%  │  100%
   ┌─────┴────┐                      ┌────┴─────┐                 ┌────┴─────┐
   │    │     │                      │    │     │                 │    │     │
┌──▼──┐ ┌──▼──┐                  ┌──▼──┐ ┌──▼──┐             ┌──▼──┐ ┌──▼──┐
│ v1  │ │ v2  │                  │ v1  │ │ v2  │             │ v1  │ │ v2  │
│(9)  │ │(1)  │                  │(6)  │ │(4)  │             │(0)  │ │(10) │
└─────┘ └─────┘                  └─────┘ └─────┘             └─────┘ └─────┘
```

### Process

1. Deploy v2 to a small number of instances (e.g., 1 out of 10).
2. Route a small percentage of traffic (e.g., 5%) to v2.
3. Monitor key metrics: error rate, latency, resource usage.
4. If metrics are healthy, increase traffic to 25%, then 50%, then 100%.
5. If metrics degrade at any point, route all traffic back to v1.

### Canary Metrics to Monitor

```
Canary Health Dashboard:
┌─────────────────────────────────────────────────────────┐
│  Metric            │ v1 (baseline) │ v2 (canary) │ OK? │
│────────────────────┼───────────────┼─────────────┼─────│
│  Error rate        │     0.1%      │    0.12%    │  ✅  │
│  p50 latency       │     45ms      │    48ms     │  ✅  │
│  p99 latency       │    200ms      │   210ms     │  ✅  │
│  CPU usage         │     35%       │    38%      │  ✅  │
│  Memory usage      │     60%       │    62%      │  ✅  │
│  5xx errors/min    │      2        │     1       │  ✅  │
└─────────────────────────────────────────────────────────┘

Auto-promote if ALL metrics are within thresholds for 10 minutes.
Auto-rollback if ANY metric exceeds threshold.
```

### Canary with Kubernetes and Istio

```yaml
# Istio VirtualService for canary traffic splitting
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: myapp
spec:
  hosts:
  - myapp.example.com
  http:
  - route:
    - destination:
        host: myapp
        subset: stable       # v1
      weight: 95
    - destination:
        host: myapp
        subset: canary       # v2
      weight: 5
---
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: myapp
spec:
  host: myapp
  subsets:
  - name: stable
    labels:
      version: v1
  - name: canary
    labels:
      version: v2
```

### Canary Analysis Automation

Tools like **Flagger** (Kubernetes) and **Argo Rollouts** automate canary analysis:

```
Automated Canary Progression:
  1. Deploy canary (1 pod)
  2. Route 5% traffic to canary
  3. Wait 2 minutes, analyze metrics    → Pass? Continue. Fail? Rollback.
  4. Route 25% traffic to canary
  5. Wait 5 minutes, analyze metrics    → Pass? Continue. Fail? Rollback.
  6. Route 50% traffic to canary
  7. Wait 5 minutes, analyze metrics    → Pass? Continue. Fail? Rollback.
  8. Route 100% traffic to canary
  9. Scale down old version
```

### Characteristics

| Property | Value |
|----------|-------|
| **Downtime** | None |
| **Risk** | Very Low — only a small % of users affected |
| **Rollback** | Fast — route all traffic back to v1 |
| **Resource cost** | Medium — slight overhead for canary instances |
| **Complexity** | High — requires traffic splitting + automated metric analysis |

### When to Use

- **High-traffic production systems** where you need data-driven confidence.
- **When you want to test with real production traffic.**
- **Gradual rollouts** of risky or significant changes.
- When you have good observability (metrics, logging, monitoring).

---

## 6. Strategy 5: A/B Testing Deployment

### How It Works

Route different **user segments** to different versions based on specific criteria (not random percentage). This is both a deployment and a product experimentation strategy.

```
                ┌─────────────┐
                │Load Balancer│
                │ + Routing   │
                │   Rules     │
                └──────┬──────┘
                       │
          ┌────────────┼────────────┐
          │            │            │
    US users     EU users     Beta users
          │            │            │
     ┌────▼────┐  ┌────▼────┐  ┌────▼────┐
     │  v1     │  │  v1     │  │  v2     │
     │(current)│  │(current)│  │ (new)   │
     └─────────┘  └─────────┘  └─────────┘
```

### Routing Criteria

| Criteria | Example |
|----------|---------|
| **Geographic** | US users get v1, EU users get v2 |
| **User type** | Free users get v1, premium users get v2 |
| **Percentage** | 10% of all users get v2 |
| **User ID** | Users with IDs ending in 0-1 get v2 |
| **Cookie/header** | Users with beta cookie get v2 |
| **Device** | Mobile users get v2, desktop users get v1 |

### A/B Testing vs. Canary

| Aspect | Canary | A/B Testing |
|--------|--------|-------------|
| **Goal** | Validate technical health | Compare business metrics |
| **Routing** | Random percentage | Specific user segments |
| **Metrics** | Error rate, latency, CPU | Conversion rate, engagement, revenue |
| **Duration** | Minutes to hours | Days to weeks |
| **Decision** | "Is v2 healthy?" | "Does v2 improve the business?" |

---

## 7. Feature Flags

### What They Are

Feature flags (or feature toggles) **decouple deployment from release**. Code is deployed to production but features are hidden behind flags that can be toggled on or off.

```
                    Deployment (code exists in production)
                    ─────────────────────────────────────▶
                    
                              Release (users see feature)
                              ────────────▶
                              
 Code merged    Deployed to     Feature flag    Flag enabled     Flag enabled
 to main        production      enabled for     for 10%          for 100%
    │               │           internal team       │                │
    ▼               ▼               ▼               ▼                ▼
────┼───────────────┼───────────────┼───────────────┼────────────────┼──▶ time
```

### Types of Feature Flags

| Type | Lifespan | Purpose | Example |
|------|----------|---------|---------|
| **Release flag** | Days–weeks | Gate unfinished features | `new-checkout-flow` |
| **Experiment flag** | Days–months | A/B test | `homepage-redesign-v2` |
| **Ops flag** | Permanent | Kill switch for features | `enable-recommendations` |
| **Permission flag** | Permanent | Control access by user tier | `premium-analytics` |

### Implementation Example

```python
# Simple feature flag check
from feature_flags import FeatureFlagClient

flags = FeatureFlagClient()

def get_checkout_page(user):
    if flags.is_enabled("new-checkout-flow", user_id=user.id):
        return render_new_checkout(user)
    else:
        return render_old_checkout(user)
```

### Feature Flag Tools

| Tool | Type | Notes |
|------|------|-------|
| LaunchDarkly | SaaS | Industry leader, enterprise features |
| Unleash | Open source | Self-hosted, good for teams wanting control |
| Flagsmith | Open source + SaaS | Feature flags + remote config |
| Split.io | SaaS | Strong A/B testing integration |
| ConfigCat | SaaS | Simple and affordable |
| Custom (env vars, DB) | DIY | For simple use cases only |

### Feature Flag Best Practices

1. **Name flags clearly** — `enable-new-checkout-flow` not `flag_42`.
2. **Set an expiration date** — Remove release flags after rollout is complete.
3. **Don't nest flags** — Avoid `if flag_A and flag_B and not flag_C` complexity.
4. **Test both paths** — Your test suite should cover flag-on and flag-off behavior.
5. **Clean up old flags** — Technical debt builds up fast with unused flags.

---

## 8. Rollback Strategies

### What Is a Rollback?

A rollback is reverting a deployment to a previous known-good version when the new version causes problems.

### Rollback Approaches

| Approach | How It Works | Speed | Risk |
|----------|-------------|-------|------|
| **Redeploy previous version** | Build and deploy v1 again | Slow (minutes) | Low |
| **Artifact rollback** | Deploy the stored v1 artifact | Medium (seconds-minutes) | Very low |
| **Traffic switch** | Route traffic back to v1 environment (blue-green) | Instant (seconds) | Very low |
| **Feature flag disable** | Turn off the problematic feature | Instant (no deploy) | Very low |
| **Database rollback** | Revert database migrations | Very slow, risky | High |
| **Git revert** | Create a revert commit and deploy | Slow (full pipeline) | Low |

### Rollback Decision Tree

```
Problem detected in production:
│
├── Is it a feature-level issue? (one feature broken)
│   └── YES → Disable feature flag (instant, no deploy)
│
├── Is it an application-level issue? (app is crashing/slow)
│   ├── Blue-Green? → Switch traffic to previous environment
│   ├── Canary? → Route 100% traffic to stable
│   └── Rolling? → Deploy previous artifact version
│
├── Is it a data/database issue?
│   ├── Is the migration reversible? → Run reverse migration
│   └── Is the migration NOT reversible? → Forward-fix (hotfix)
│
└── Is it an infrastructure issue? (config, secrets, networking)
    └── Revert the infrastructure change (IaC rollback)
```

### Automated Rollback

Define rollback triggers that fire automatically:

```yaml
# Argo Rollouts automated rollback example (conceptual)
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: myapp
spec:
  strategy:
    canary:
      steps:
      - setWeight: 5
      - pause: { duration: 2m }
      - analysis:
          templates:
          - templateName: success-rate
            args:
            - name: threshold
              value: "0.99"      # 99% success rate required
      - setWeight: 25
      - pause: { duration: 5m }
      - analysis:
          templates:
          - templateName: success-rate
      - setWeight: 100
```

### Database Rollback Challenges

Database changes are the hardest part of rollback because data changes may not be reversible:

```
Scenario: You added a column and migrated data

Forward migration:
  ALTER TABLE users ADD COLUMN full_name VARCHAR(255);
  UPDATE users SET full_name = first_name || ' ' || last_name;
  ALTER TABLE users DROP COLUMN first_name;
  ALTER TABLE users DROP COLUMN last_name;

Rollback:
  ❌ Can't easily reverse — the original first_name and last_name
     data was derived from full_name but how do you split "Jean-Pierre
     de la Fontaine" back into first and last name?
```

**Best Practice: Expand-Contract Pattern**

```
Step 1 (Deploy v2a): ADD new column, keep old columns
  ALTER TABLE users ADD COLUMN full_name VARCHAR(255);
  -- Write to BOTH old and new columns

Step 2 (Deploy v2b): Migrate data, make new column the source of truth
  UPDATE users SET full_name = first_name || ' ' || last_name WHERE full_name IS NULL;
  -- Read from new column

Step 3 (Deploy v3): DROP old columns (only after v2b is proven stable)
  ALTER TABLE users DROP COLUMN first_name;
  ALTER TABLE users DROP COLUMN last_name;

Rollback: At any step, you can go back because both old and new columns exist.
```

---

## 9. Zero-Downtime Deployment Checklist

Achieving true zero-downtime deployment requires more than just a deployment strategy:

### Application Requirements

- [ ] **Health check endpoints** — `/healthz` (liveness) and `/readyz` (readiness).
- [ ] **Graceful shutdown** — Handle in-flight requests before stopping.
- [ ] **Backward-compatible APIs** — Old clients must work with new servers.
- [ ] **Backward-compatible database schema** — Expand-contract migrations.
- [ ] **Stateless application** — No in-memory sessions (use Redis, DB, etc.).
- [ ] **Externalized configuration** — Environment variables or config service.

### Infrastructure Requirements

- [ ] **Load balancer** — Distributes traffic across instances.
- [ ] **Readiness probes** — Only route traffic to healthy instances.
- [ ] **Multiple instances** — At least 2 replicas for redundancy.
- [ ] **Connection draining** — Allow in-flight requests to complete.
- [ ] **DNS/service discovery** — Route traffic dynamically.

### Graceful Shutdown Example (Node.js)

```javascript
const server = app.listen(3000);

process.on("SIGTERM", () => {
  console.log("SIGTERM received. Starting graceful shutdown...");
  
  // Stop accepting new connections
  server.close(() => {
    console.log("All connections closed. Exiting.");
    process.exit(0);
  });
  
  // Force exit after 30 seconds if connections don't close
  setTimeout(() => {
    console.error("Forced shutdown after timeout.");
    process.exit(1);
  }, 30000);
});
```

---

## 10. Strategy Comparison Summary

| Strategy | Downtime | Risk | Rollback Speed | Cost | Complexity | Best For |
|----------|----------|------|----------------|------|------------|----------|
| **Recreate** | Yes | High | Slow | Low | Very Low | Dev/test environments |
| **Rolling** | No | Medium | Medium | Low | Low | Default for most apps |
| **Blue-Green** | No | Low | Instant | High | Medium | Mission-critical systems |
| **Canary** | No | Very Low | Fast | Medium | High | High-traffic production |
| **A/B Testing** | No | Low | Fast | Medium | High | Product experiments |
| **Feature Flags** | No | Very Low | Instant | Low | Medium | Feature-level control |

### Decision Flowchart

```
What deployment strategy should I use?

Start:
│
├── Can you afford downtime?
│   └── YES → Recreate (simplest)
│   └── NO ─┐
│            │
│   ├── Do you need instant rollback?
│   │   └── YES → Blue-Green
│   │   └── NO ─┐
│   │            │
│   │   ├── Do you want to test with real traffic gradually?
│   │   │   └── YES → Canary
│   │   │   └── NO ─┐
│   │   │            │
│   │   │   └── Rolling Update (default)
```

---

## 11. Review Questions

1. **Explain the difference between blue-green and canary deployments.** When would you choose one over the other?
2. **A rolling update is in progress and one of the new pods fails health checks.** What happens? What should the system do?
3. **Your team uses blue-green deployment but the database needs a schema change.** Describe how you would handle this without downtime.
4. **What is the expand-contract pattern for database migrations?** Why is it important for zero-downtime deployments?
5. **Feature flags add complexity. Why use them instead of just deploying features when they're ready?**
6. **Design a rollback strategy for a payment processing system.** What special considerations apply?
7. **Your canary deployment shows a 0.5% increase in error rate. The baseline is 0.1%.** Should you rollback? What additional information would help you decide?

---

## 12. Further Reading

- **Book:** *Continuous Delivery* by Jez Humble & David Farley — Chapter 10: "Deploying and Releasing Applications"
- **Article:** [BlueGreenDeployment](https://martinfowler.com/bliki/BlueGreenDeployment.html) by Martin Fowler
- **Article:** [CanaryRelease](https://martinfowler.com/bliki/CanaryRelease.html) by Martin Fowler
- **Tool:** [Argo Rollouts](https://argoproj.github.io/rollouts/) — Kubernetes progressive delivery
- **Tool:** [Flagger](https://flagger.app/) — Automated canary analysis for Kubernetes
- **Article:** [Feature Toggles](https://martinfowler.com/articles/feature-toggles.html) by Pete Hodgson

---

*Previous: [03 - Testing Strategies](03-testing-strategies.md) | Next: [05 - Artifact Management](05-artifact-management.md)*
