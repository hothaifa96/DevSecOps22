# Lesson 6: Branching Strategies

## Overview

| Topic | Details |
|-------|---------|
| **Duration** | 75 minutes |
| **Level** | Foundational to Intermediate |
| **Prerequisites** | Git basics, Lesson 01 (CI/CD concepts) |
| **Objectives** | Understand and compare branching strategies; choose the right strategy for your team; understand the relationship between branching and CI/CD; evaluate mono-repo vs. multi-repo |

---

## 1. Why Branching Strategy Matters for CI/CD

Your branching strategy directly affects your CI/CD pipeline's effectiveness. The wrong strategy can undermine everything you've built:

| Branching Decision | CI/CD Impact |
|---|---|
| Long-lived feature branches | Delayed integration, merge conflicts, defeats CI |
| Too many active branches | Complex pipeline configuration, resource waste |
| No branch protection | Untested code reaches production |
| No clear release process | Confusion about what's deployed where |

> **The Fundamental Tension:** Branches enable parallel development, but CI is about integrating frequently. Every branching strategy is a trade-off between isolation and integration.

---

## 2. Strategy 1: Git Flow

### Origin

Created by Vincent Driessen in 2010. Designed for projects with **scheduled releases** and **multiple supported versions**.

### Branch Structure

```
main (production)
  │
  ├── hotfix/fix-login-crash ──────────────────────────▶ merge to main + develop
  │
  │         develop (integration)
  │           │
  │           ├── feature/user-profile ──▶ merge to develop
  │           │
  │           ├── feature/search ──────▶ merge to develop
  │           │
  │           ├── release/v1.2.0 ─────────────────────▶ merge to main + develop
  │           │     │
  │           │     └── bugfix on release branch
  │           │
  │           └── feature/notifications ──▶ merge to develop
  │
  └──── Tags: v1.0.0, v1.1.0, v1.2.0
```

### Branch Types

| Branch | Purpose | Created From | Merges Into | Lifetime |
|--------|---------|-------------|-------------|----------|
| **main** | Production-ready code | — | — | Permanent |
| **develop** | Integration branch | main | — | Permanent |
| **feature/*** | New features | develop | develop | Days–weeks |
| **release/*** | Release preparation | develop | main + develop | Days |
| **hotfix/*** | Emergency production fixes | main | main + develop | Hours–days |

### Git Flow Workflow

```
1. Developer creates feature/user-profile from develop
2. Developer works on the feature (commits to feature branch)
3. Developer opens PR: feature/user-profile → develop
4. CI runs on feature branch (tests, lint, security scan)
5. Code review + approval
6. Merge to develop
7. When ready for release, create release/v1.2.0 from develop
8. Final testing, bug fixes on release branch
9. Merge release/v1.2.0 → main (tag v1.2.0) AND → develop
10. Deploy from main
```

### CI/CD Pipeline Configuration for Git Flow

```
Pipeline triggers:
  feature/* branches:  Build → Unit Tests → Lint → Security Scan
  develop branch:      Build → Full Tests → Security → Deploy to Dev
  release/* branches:  Build → Full Tests → Security → Deploy to Staging
  main branch:         Build → Full Tests → Security → Deploy to Production
  hotfix/* branches:   Build → Full Tests → Security → Deploy to Staging (expedited)
```

### Pros and Cons

| Pros | Cons |
|------|------|
| Clear structure for releases | Complex — many branch types to manage |
| Supports multiple versions in production | Feature branches can live too long (anti-CI) |
| Hotfix process is well-defined | Merge conflicts between develop and release |
| Good for scheduled release cycles | Overhead for small teams |
| Well-documented, widely understood | Not ideal for continuous deployment |

### When to Use Git Flow

- **Packaged software** with version numbers (libraries, frameworks, mobile apps).
- **Multiple versions in production** (customers on v1.x and v2.x).
- **Scheduled release cycles** (monthly or quarterly releases).
- **Regulated environments** where release branches need formal QA.

### When NOT to Use Git Flow

- Web applications with continuous deployment.
- Small teams (< 5 developers).
- Projects that deploy daily or more frequently.

---

## 3. Strategy 2: GitHub Flow

### Origin

Simplified branching model created by GitHub. Designed for **continuous deployment** of web applications.

### Branch Structure

```
main (always deployable)
  │
  ├── feature/user-profile ──────▶ PR ──▶ merge to main ──▶ deploy
  │
  ├── fix/login-bug ─────────────▶ PR ──▶ merge to main ──▶ deploy
  │
  ├── feature/search ────────────▶ PR ──▶ merge to main ──▶ deploy
  │
  └── feature/notifications ─────▶ PR ──▶ merge to main ──▶ deploy
```

**That's it.** Only `main` and short-lived feature branches.

### GitHub Flow Rules

1. **`main` is always deployable.** Everything in `main` has been tested and can be deployed at any time.
2. **Create a branch from `main` for any change.** Name it descriptively (e.g., `feature/add-search`, `fix/login-timeout`).
3. **Keep branches short-lived.** Ideally merge within 1–2 days. Maximum: 1 week.
4. **Open a Pull Request early.** PRs are for discussion and review, not just final approval.
5. **CI runs on every push to the PR branch.** Tests must pass before merging.
6. **Merge to `main` after review + passing CI.** Use squash merge or merge commit.
7. **Deploy from `main` after every merge.** Either automatically or with a manual trigger.

### GitHub Flow Workflow

```
1. git checkout -b feature/user-profile main
2. Write code, commit frequently
3. Push to origin/feature/user-profile
4. Open Pull Request → CI runs automatically
5. Team reviews code, CI passes ✅
6. Merge PR to main (squash or merge commit)
7. CI/CD deploys main to production automatically
8. Delete feature branch
```

### CI/CD Pipeline for GitHub Flow

```
On push to any branch (except main):
  Build → Unit Tests → Integration Tests → Lint → Security Scan
  → Status reported on PR

On merge to main:
  Build → Full Tests → Security → Build Artifact → Deploy to Staging
  → Smoke Tests → Deploy to Production → Post-deploy Verification
```

### Branch Protection Rules

```
Branch Protection for main:
  ✅ Require pull request before merging
  ✅ Require at least 1 approval
  ✅ Require status checks to pass (CI pipeline)
  ✅ Require branches to be up to date before merging
  ✅ Require signed commits (optional but recommended)
  ✅ Do not allow force pushes
  ✅ Do not allow deletions
  ❌ Allow bypassing (no one should bypass)
```

### Pros and Cons

| Pros | Cons |
|------|------|
| Simple — only two branch types | No explicit release process |
| Fast feedback — short-lived branches | Harder to manage multiple versions |
| Perfect for continuous deployment | Requires strong CI/CD and test coverage |
| Low overhead — less process | No staging-specific branch |
| Easy to understand and teach | Hotfixes go through same process as features |

### When to Use GitHub Flow

- **Web applications** deployed continuously.
- **Small to medium teams** (2–20 developers).
- **SaaS products** with a single version in production.
- Teams practicing **continuous deployment**.

---

## 4. Strategy 3: Trunk-Based Development

### Origin

The most CI-aligned branching strategy. Popularized by Google, Facebook, and described in *Accelerate* as a practice of high-performing teams.

### Core Idea

Everyone commits to a single branch (`main` / `trunk`) directly or via very short-lived branches (less than 1 day).

### Branch Structure

```
main / trunk (single source of truth)
  │
  │  ← Alice commits directly
  │  ← Bob commits directly
  │  ← Carol creates a branch, merges within hours
  │
  │──── short-lived/alice-fix ──▶ merged within 4 hours
  │──── short-lived/bob-feature ──▶ merged within 8 hours
  │
  │  ← Feature flags control what users see
  │  ← Release branches (optional, for release stabilization)
  │
  └── release/v1.2 ← created from main when ready to release
                      (only receives cherry-picked fixes)
```

### Trunk-Based Development Rules

1. **Everyone integrates to `main` at least once per day.** This is the definition of continuous integration.
2. **Branches live for hours, not days.** If you use branches at all, they merge within 24 hours.
3. **Use feature flags** to hide incomplete features. Code goes to `main` even if the feature isn't done.
4. **No long-lived branches.** No `develop`, no `release/*` branches (or very short-lived release branches).
5. **Build and tests run on every commit to `main`.** The pipeline must be fast (< 10 minutes).
6. **Broken builds are fixed within 10 minutes** or the commit is reverted.

### How Incomplete Features Work

```
Traditional approach (feature branch):
  Day 1: Create feature/checkout-v2
  Day 2-10: Work on the feature (branch diverges from main)
  Day 11: Merge to main (painful merge, big PR)
  Day 12: Deploy

Trunk-based approach (feature flags):
  Day 1: Commit to main behind flag: checkout_v2_enabled=false
  Day 2: Commit more code to main behind the same flag
  Day 3-10: Continue committing small pieces to main
  Day 10: Enable flag for internal team → test in production
  Day 11: Enable flag for 10% of users → canary
  Day 12: Enable flag for 100% → full release
  
  All along, main is always deployable. The feature is just hidden.
```

### Pair Programming and Trunk-Based Development

At Google and similar companies, trunk-based development is often paired with:
- **Code review on every commit** (pre-commit review).
- **Pair programming** — Two developers write code together, reducing review overhead.
- **Automated checks** — Extensive CI catches issues immediately.

### Pros and Cons

| Pros | Cons |
|------|------|
| True continuous integration | Requires mature testing and CI infrastructure |
| No merge conflicts (small, frequent merges) | Feature flags add complexity |
| Fastest feedback loops | Requires team discipline |
| Supported by research (DORA/Accelerate) | Harder for junior teams to adopt |
| Simplest branch model | Incomplete features in production (behind flags) |

### When to Use Trunk-Based Development

- **Teams that truly practice CI/CD** and continuous deployment.
- **Large engineering organizations** (Google, Facebook, LinkedIn).
- Teams with **strong automated testing** and feature flag infrastructure.
- **Senior/experienced teams** with high trust.

---

## 5. Strategy 4: GitLab Flow

### Origin

Created by GitLab as a middle ground between Git Flow (too complex) and GitHub Flow (too simple for some teams).

### Core Idea

Like GitHub Flow, but with **environment branches** that map to deployment targets.

```
main (development)
  │
  ├── feature/user-profile ──▶ merge to main
  │
  ├── main ──────────────────────▶ auto-deploy to development
  │
  ├── pre-production ────────────▶ auto-deploy to staging
  │     (merged from main)
  │
  └── production ────────────────▶ auto-deploy to production
        (merged from pre-production)
```

### Promotion Model

```
feature → main → pre-production → production

Code is promoted by merging between environment branches:
  1. Feature merges into main → deployed to dev
  2. main merges into pre-production → deployed to staging
  3. pre-production merges into production → deployed to production
```

---

## 6. Comparison of All Strategies

| Aspect | Git Flow | GitHub Flow | Trunk-Based | GitLab Flow |
|--------|----------|-------------|-------------|-------------|
| **Complexity** | High | Low | Very Low | Medium |
| **Branches** | main, develop, feature, release, hotfix | main, feature | main (+ short-lived) | main, environment branches |
| **CI-friendliness** | Medium | High | Highest | High |
| **Release model** | Scheduled releases | Continuous | Continuous | Environment promotion |
| **Feature isolation** | Feature branches | Feature branches | Feature flags | Feature branches |
| **Multiple versions** | Yes (release branches) | No | No (or release branches) | No |
| **Team size** | Any | Small–medium | Any (with maturity) | Any |
| **Deploy frequency** | Weekly–monthly | Daily–hourly | Hourly–continuous | Daily–weekly |
| **Best for** | Packaged software | Web SaaS | Mature CI/CD teams | Teams needing env control |

### Decision Flowchart

```
Which branching strategy should you use?

Start:
│
├── Do you ship packaged software with version numbers?
│   └── YES → Git Flow
│   └── NO ─┐
│            │
├── Do you need environment-specific branches (staging, prod)?
│   └── YES → GitLab Flow
│   └── NO ─┐
│            │
├── Is your team mature with strong CI/CD and feature flags?
│   └── YES → Trunk-Based Development
│   └── NO ─┐
│            │
└── GitHub Flow (best default choice for most teams)
```

---

## 7. Feature Flags vs. Feature Branches

These are two approaches to the same problem: how to develop a feature without disrupting the main codebase.

| Aspect | Feature Branches | Feature Flags |
|--------|-----------------|---------------|
| **Isolation mechanism** | Code is on a separate branch | Code is in main, hidden behind a flag |
| **Integration timing** | At merge time (potentially late) | At commit time (continuous) |
| **Merge conflicts** | Likely (especially with long branches) | Unlikely (small, frequent commits) |
| **Testing** | Tested on the branch, then again after merge | Tested on main continuously |
| **Rollback** | Revert merge commit or redeploy | Toggle flag off (instant) |
| **Overhead** | Git operations, PR process | Flag management, test both paths |
| **Visibility** | Branch exists in Git | Flag exists in code and flag service |
| **CI/CD alignment** | Medium — depends on branch lifetime | High — true continuous integration |

### When to Use Each

**Use Feature Branches when:**
- The change is small and can be merged in 1–2 days.
- The feature can be completed in a single PR.
- Your team is comfortable with branch-based workflows.

**Use Feature Flags when:**
- The feature takes more than a few days to build.
- You want to deploy incomplete work to production safely.
- You need gradual rollout (canary, percentage-based).
- You want instant rollback without redeploying.
- You practice trunk-based development.

### Combining Both

Many teams use **both** strategies:

```
Short tasks (< 2 days):
  → Short-lived feature branch → PR → Merge to main → Deploy

Long tasks (> 2 days):
  → Short-lived branches → PR → Merge to main (behind feature flag)
  → Flag off by default
  → Gradually enable flag: internal → beta → 10% → 100%
```

---

## 8. Mono-Repo vs. Multi-Repo

### What They Are

| Approach | Description | Example |
|----------|-------------|---------|
| **Mono-repo** | All projects/services in a single repository | Google, Facebook, Uber |
| **Multi-repo** | Each project/service has its own repository | Most startups, microservice teams |
| **Hybrid** | Related services grouped into a few repositories | Medium-sized organizations |

### Mono-Repo Structure

```
my-company/
├── services/
│   ├── auth-service/
│   │   ├── src/
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── package.json
│   ├── payment-service/
│   │   ├── src/
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── pom.xml
│   └── frontend/
│       ├── src/
│       ├── tests/
│       └── package.json
├── shared/
│   ├── common-lib/
│   └── proto-definitions/
├── infrastructure/
│   ├── terraform/
│   └── kubernetes/
└── .github/
    └── workflows/
```

### Multi-Repo Structure

```
GitHub Organization: my-company
├── auth-service          (separate repo)
├── payment-service       (separate repo)
├── frontend              (separate repo)
├── common-lib            (separate repo)
├── proto-definitions     (separate repo)
└── infrastructure        (separate repo)
```

### Comparison

| Aspect | Mono-Repo | Multi-Repo |
|--------|-----------|------------|
| **Code sharing** | Easy — import from shared/ | Harder — publish as packages |
| **Atomic changes** | One commit changes multiple services | Need coordinated PRs across repos |
| **CI/CD** | Must detect what changed and build only that | Each repo has its own pipeline |
| **Code ownership** | CODEOWNERS file per directory | Per-repo permissions |
| **Dependency management** | All services use same dependency versions | Each service manages its own deps |
| **Repository size** | Can become very large | Each repo stays small |
| **Tooling** | Needs special tools (Bazel, Nx, Turborepo) | Standard Git tools work fine |
| **Onboarding** | Clone one repo, see everything | Must discover and clone many repos |
| **Refactoring** | Easy — change API and all consumers in one PR | Hard — must update each consumer repo |

### CI/CD for Mono-Repos

The key challenge: **only build and test what changed.**

```
Change Detection:
  1. Developer changes services/auth-service/src/login.js
  2. CI detects: only auth-service changed
  3. CI runs: auth-service tests + auth-service build
  4. CI skips: payment-service, frontend (unchanged)

  Exception: Changes to shared/ trigger builds for ALL services

Tools for mono-repo CI:
  - Nx (JavaScript/TypeScript) — affected:test, affected:build
  - Turborepo (JavaScript) — smart caching and task scheduling
  - Bazel (multi-language) — Google's build system
  - Pants (Python/Go/Java) — scalable build system
  - Path filters in GitHub Actions / GitLab CI
```

```yaml
# GitHub Actions path filter example
name: Auth Service CI
on:
  push:
    paths:
      - 'services/auth-service/**'
      - 'shared/**'
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: cd services/auth-service && npm ci && npm test
```

---

## 9. Merge Strategies

How you merge branches also matters:

### Merge Commit

```
Feature branch:  A ── B ── C
                              \
Main branch:     1 ── 2 ── 3 ── M (merge commit)

Preserves full branch history. Good for traceability.
```

### Squash Merge

```
Feature branch:  A ── B ── C
                              
Main branch:     1 ── 2 ── 3 ── S (single squashed commit)

Combines all branch commits into one. Cleaner history.
```

### Rebase and Merge

```
Feature branch:  A ── B ── C  →  (rebased) A' ── B' ── C'
                              
Main branch:     1 ── 2 ── 3 ── A' ── B' ── C'

Replays commits on top of main. Linear history.
```

### Which to Use

| Strategy | Pros | Cons | Best For |
|----------|------|------|----------|
| **Merge commit** | Full history, clear branch points | Noisy log with merge commits | Git Flow, auditing |
| **Squash merge** | Clean history, one commit per feature | Loses granular commit history | GitHub Flow, most teams |
| **Rebase** | Linear history, no merge commits | Rewrites history, can confuse | Advanced teams, OSS |

---

## 10. Review Questions

1. **Compare GitHub Flow and Git Flow.** Which would you recommend for a 6-person SaaS startup? Why?
2. **What is trunk-based development and why does the DORA research support it?** What prerequisites does a team need?
3. **A developer's feature branch has been open for 3 weeks.** What problems might this cause? How would you prevent this?
4. **Explain the trade-off between feature branches and feature flags.** When would you use each?
5. **Your company has 50 microservices. Should you use mono-repo or multi-repo?** List three arguments for each.
6. **Design branch protection rules for a `main` branch** that ensures code quality without slowing down the team.
7. **You're migrating from Git Flow to GitHub Flow.** What challenges would you expect, and how would you address them?

---

## 11. Further Reading

- **Article:** [A Successful Git Branching Model](https://nvie.com/posts/a-successful-git-branching-model/) by Vincent Driessen (Git Flow original)
- **Article:** [GitHub Flow](https://docs.github.com/en/get-started/using-github/github-flow) — Official documentation
- **Article:** [Trunk-Based Development](https://trunkbaseddevelopment.com/) — Comprehensive guide
- **Book:** *Accelerate* by Nicole Forsgren — Chapter on trunk-based development
- **Article:** [Monorepo vs Multi-Repo](https://earthly.dev/blog/monorepo-vs-polyrepo/) — Detailed comparison
- **Tool:** [Nx](https://nx.dev/) — Smart mono-repo tooling
- **Tool:** [Turborepo](https://turbo.build/) — High-performance build system for mono-repos

---

*Previous: [05 - Artifact Management](05-artifact-management.md) | Next: [07 - CI/CD Security](07-cicd-security.md)*
