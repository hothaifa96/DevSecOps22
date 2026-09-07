# Lesson 5: Artifact Management

## Overview

| Topic | Details |
|-------|---------|
| **Duration** | 75 minutes |
| **Level** | Foundational to Intermediate |
| **Prerequisites** | Lessons 01–02 |
| **Objectives** | Understand what artifacts are, use container and package registries, apply versioning strategies (SemVer), implement artifact scanning, manage the artifact lifecycle |

---

## 1. What Is an Artifact?

An **artifact** is any output produced by a CI/CD pipeline that is needed for deployment or distribution. It is the **deployable unit** — the thing you actually run in production.

### Common Artifact Types

| Artifact Type | Format | Example |
|---|---|---|
| **Container image** | OCI / Docker image | `myapp:v1.2.3` |
| **JAR / WAR file** | Java archive | `myapp-1.2.3.jar` |
| **Binary executable** | Compiled binary | `myapp-linux-amd64` |
| **npm package** | Tarball | `@myorg/myapp-1.2.3.tgz` |
| **Python wheel** | Wheel archive | `myapp-1.2.3-py3-none-any.whl` |
| **Helm chart** | Chart archive | `myapp-chart-1.2.3.tgz` |
| **Terraform module** | HCL files (versioned) | `modules/vpc/v1.2.3` |
| **Static site bundle** | HTML/CSS/JS files | `dist/` directory |
| **Mobile app package** | APK / IPA | `myapp-1.2.3.apk` |
| **Machine learning model** | Serialized model file | `model-v3.pkl` |

### Artifact Lifecycle

```
┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐    ┌──────────┐
│ Build  │───▶│ Test   │───▶│ Scan   │───▶│ Store  │───▶│ Deploy │───▶│ Archive  │
│        │    │        │    │        │    │        │    │        │    │ / Delete │
└────────┘    └────────┘    └────────┘    └────────┘    └────────┘    └──────────┘
  Create       Validate      Security      Registry     Promote to     Retention
  artifact     artifact       check        / storage    environments    policy
```

---

## 2. The "Build Once, Deploy Many" Principle

This is the single most important principle in artifact management:

> **Build the artifact ONCE, then promote the exact same artifact through all environments.**

### Why This Matters

```
❌ WRONG: Rebuild for each environment

  Source → Build (dev artifact)     → Deploy to dev
  Source → Build (staging artifact) → Deploy to staging
  Source → Build (prod artifact)    → Deploy to production
  
  Problem: Each build may produce a slightly different artifact!
  - Different timestamp
  - Different dependency resolution
  - Different build environment
  - "Works in staging but not in production"

✅ RIGHT: Build once, promote everywhere

  Source → Build → Artifact (v1.2.3) → Deploy to dev
                        │              → Deploy to staging (same artifact!)
                        │              → Deploy to production (same artifact!)
                        │
                   Stored in registry
                   with unique version
```

### Environment-Specific Configuration

If the artifact is the same everywhere, how do you handle environment differences?

**Externalize configuration:**

| What Changes Per Environment | Where to Put It |
|---|---|
| Database connection strings | Environment variables or secrets manager |
| API endpoints | Environment variables or config service |
| Feature flags | Feature flag service |
| Logging level | Environment variables |
| Secrets (passwords, API keys) | Secrets manager (Vault, AWS Secrets Manager) |

```
Same Docker image everywhere:
  myapp:v1.2.3

Different config per environment:
  Dev:     DATABASE_URL=postgres://dev-db:5432/myapp
  Staging: DATABASE_URL=postgres://staging-db:5432/myapp
  Prod:    DATABASE_URL=postgres://prod-db:5432/myapp
```

---

## 3. Container Registries

Container registries store and distribute **Docker/OCI container images**. They are the most common artifact registry in modern CI/CD.

### Major Container Registries

| Registry | Provider | Type | Key Features |
|----------|----------|------|-------------|
| **Docker Hub** | Docker Inc. | Public + Private | Largest public registry, official images |
| **Amazon ECR** | AWS | Private (+ Public) | Deep AWS integration, lifecycle policies |
| **Google Artifact Registry** | GCP | Private (+ Public) | Replaces GCR, supports multiple formats |
| **Azure Container Registry** | Azure | Private | Geo-replication, Azure DevOps integration |
| **GitHub Container Registry** | GitHub | Private + Public | Integrated with GitHub Actions, GHCR |
| **Harbor** | CNCF | Self-hosted | Open source, enterprise features, vulnerability scanning |
| **GitLab Container Registry** | GitLab | Private | Built into GitLab, tight CI integration |
| **JFrog Artifactory** | JFrog | Universal | Supports all artifact types, enterprise-grade |
| **Quay.io** | Red Hat | Public + Private | Security scanning, organization support |

### Container Image Naming Convention

```
Full image reference:
  registry.example.com/namespace/repository:tag@sha256:digest

Examples:
  docker.io/library/nginx:1.25              (Docker Hub official)
  docker.io/myorg/myapp:v1.2.3              (Docker Hub user)
  123456789.dkr.ecr.us-east-1.amazonaws.com/myapp:v1.2.3   (ECR)
  ghcr.io/myorg/myapp:v1.2.3               (GitHub)
  gcr.io/my-project/myapp:v1.2.3           (Google)
  myregistry.azurecr.io/myapp:v1.2.3       (Azure)
```

### Image Tagging Strategy

| Tag Type | Example | Use Case | Mutable? |
|----------|---------|----------|----------|
| **Semantic version** | `v1.2.3` | Release tracking | Immutable |
| **Git SHA** | `abc1234` | Traceability to exact commit | Immutable |
| **Combined** | `v1.2.3-abc1234` | Version + traceability | Immutable |
| **Latest** | `latest` | "Most recent build" | Mutable (overwritten) |
| **Branch name** | `main`, `develop` | Development builds | Mutable |
| **PR number** | `pr-42` | Review environments | Mutable |
| **Date** | `20240115` | Nightly builds | Immutable |

> **Best Practice:** Always use immutable tags for production. Never deploy `latest` to production — you can't tell which version is running.

### Working with Container Registries

```bash
# Build and tag an image
docker build -t myapp:v1.2.3 .

# Tag for a remote registry
docker tag myapp:v1.2.3 ghcr.io/myorg/myapp:v1.2.3

# Authenticate with the registry
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Push to the registry
docker push ghcr.io/myorg/myapp:v1.2.3

# Pull from the registry
docker pull ghcr.io/myorg/myapp:v1.2.3

# Inspect image without pulling
docker manifest inspect ghcr.io/myorg/myapp:v1.2.3
```

### Image Lifecycle Policies

Container registries accumulate images over time. Implement lifecycle policies to manage storage:

```
Lifecycle Policy Example (AWS ECR):
  Rule 1: Keep the last 10 tagged images                → Always available
  Rule 2: Delete untagged images older than 7 days      → Clean up build artifacts
  Rule 3: Delete images tagged "pr-*" older than 30 days → Clean up PR images
  Rule 4: Keep images tagged "v*" for 1 year            → Retain releases

Result:
  Before policy: 2,847 images, 150 GB
  After policy:  120 images, 8 GB
```

---

## 4. Package Registries

Package registries store **language-specific packages** (libraries, modules) that are either published by your team or consumed as dependencies.

### Major Package Registries by Ecosystem

| Ecosystem | Public Registry | Private Options | Package Format |
|-----------|----------------|-----------------|----------------|
| **Node.js** | npmjs.com | npm Enterprise, GitHub Packages, Artifactory | `.tgz` |
| **Python** | pypi.org | Artifactory, private PyPI (devpi), CodeArtifact | `.whl`, `.tar.gz` |
| **Java** | Maven Central | Nexus, Artifactory, GitHub Packages | `.jar`, `.pom` |
| **Go** | proxy.golang.org | Athens (self-hosted), Artifactory | Module (git-based) |
| **Ruby** | rubygems.org | Gemfury, Artifactory | `.gem` |
| **.NET** | nuget.org | Azure Artifacts, Artifactory | `.nupkg` |
| **Rust** | crates.io | Artifactory | `.crate` |
| **PHP** | packagist.org | Private Packagist, Satis | Composer packages |

### Publishing Internal Packages

For internal libraries shared between teams:

```bash
# npm — Publish to a private registry
npm publish --registry https://npm.mycompany.com

# Python — Upload to a private PyPI
twine upload --repository-url https://pypi.mycompany.com/simple/ dist/*

# Maven — Deploy to Nexus
mvn deploy -DaltDeploymentRepository=nexus::default::https://nexus.mycompany.com/repository/maven-releases/
```

### Dependency Proxying / Caching

A **proxy registry** caches public packages locally, providing:
- **Speed** — Packages served from local cache, not the internet.
- **Availability** — Builds don't break if the public registry goes down.
- **Security** — Scan cached packages for vulnerabilities; block banned packages.

```
Without proxy:                       With proxy:
  Build → npmjs.com (internet)        Build → Internal Nexus → (cache miss) → npmjs.com
                                                             → (cache hit)  → Local cache
```

---

## 5. Versioning Strategies

### Semantic Versioning (SemVer)

The most widely used versioning scheme. Format: **MAJOR.MINOR.PATCH**

```
v1.2.3
│ │ │
│ │ └── PATCH: Bug fixes, security patches (backward-compatible)
│ └──── MINOR: New features (backward-compatible)
└────── MAJOR: Breaking changes (NOT backward-compatible)
```

### SemVer Rules

| Change Type | Version Bump | Example | Consumer Impact |
|---|---|---|---|
| Bug fix, security patch | PATCH | `1.2.3 → 1.2.4` | Safe to upgrade |
| New feature (backward-compatible) | MINOR | `1.2.3 → 1.3.0` | Safe to upgrade |
| Breaking change (API change) | MAJOR | `1.2.3 → 2.0.0` | May require code changes |
| Pre-release | Suffix | `1.3.0-beta.1` | Not for production |
| Build metadata | Suffix | `1.3.0+build.123` | Informational only |

### SemVer Examples

```
v1.0.0   — First stable release
v1.0.1   — Fixed a bug in the login form
v1.1.0   — Added user profile feature
v1.1.1   — Fixed profile image upload
v1.2.0   — Added API endpoint for bulk operations
v2.0.0   — Changed authentication from API keys to OAuth (breaking!)
v2.0.0-rc.1 — Release candidate for v2.0.0
v2.0.0-rc.2 — Second release candidate
v2.0.0   — Stable release of v2.0.0
```

### Other Versioning Schemes

| Scheme | Format | Example | Used By |
|--------|--------|---------|---------|
| **CalVer** | YYYY.MM.DD | `2024.01.15` | Ubuntu, pip, Terraform |
| **Git SHA** | Short hash | `abc1234` | Internal builds |
| **Build number** | Incrementing integer | `build-4521` | CI systems |
| **Date + build** | YYYYMMDD.N | `20240115.3` | Nightly builds |
| **Marketing version** | Custom | `Windows 11`, `macOS Sonoma` | Consumer products |

### Automating Version Bumps

Use **Conventional Commits** to automate version bumps:

```
Commit message format:
  type(scope): description

  feat: add user profile page           → MINOR bump (1.2.0 → 1.3.0)
  fix: correct login validation         → PATCH bump (1.2.0 → 1.2.1)
  feat!: change auth to OAuth           → MAJOR bump (1.2.0 → 2.0.0)
  fix(api): handle null response        → PATCH bump
  docs: update README                   → No version bump
  chore: update dependencies            → No version bump

Tools that automate this:
  - semantic-release (Node.js)
  - python-semantic-release (Python)
  - release-please (Google, multi-language)
  - conventional-changelog
```

---

## 6. Artifact Scanning

Before deploying an artifact, scan it for vulnerabilities.

### What to Scan

| Scan Target | What You're Looking For | Tools |
|---|---|---|
| **Container images** | Vulnerable OS packages, libraries | Trivy, Grype, Snyk Container, Clair |
| **Application dependencies** | Known CVEs in npm/pip/maven packages | npm audit, pip-audit, OWASP Dependency-Check |
| **Binaries** | Embedded vulnerabilities, malware | VirusTotal, binary analysis tools |
| **IaC templates** | Misconfigurations | Checkov, tfsec, KICS |
| **License compliance** | Restricted/copyleft licenses | FOSSA, WhiteSource, Trivy |

### Container Image Scanning Example

```bash
# Scan with Trivy
$ trivy image myapp:v1.2.3

myapp:v1.2.3 (debian 12.1)
============================
Total: 14 (UNKNOWN: 0, LOW: 4, MEDIUM: 6, HIGH: 3, CRITICAL: 1)

┌──────────────────┬────────────────┬──────────┬────────────────────────┐
│     Library      │ Vulnerability  │ Severity │    Fixed Version       │
├──────────────────┼────────────────┼──────────┼────────────────────────┤
│ openssl          │ CVE-2024-0001  │ CRITICAL │ 3.0.13-1~deb12u1       │
│ curl             │ CVE-2024-0002  │ HIGH     │ 7.88.1-10+deb12u5      │
│ libxml2          │ CVE-2024-0003  │ HIGH     │ 2.9.14+dfsg-1.3~deb12u1│
│ zlib             │ CVE-2024-0004  │ HIGH     │ 1:1.2.13.dfsg-1+deb12u1│
│ ...              │ ...            │ MEDIUM   │ ...                    │
└──────────────────┴────────────────┴──────────┴────────────────────────┘
```

### Scan Policy Integration in CI/CD

```
Pipeline Configuration:

  Build Image → Scan Image → Evaluate Policy → Publish or Block

  Policy Rules:
    CRITICAL CVEs with fix available  → BLOCK (fail pipeline)
    CRITICAL CVEs without fix         → WARN + create ticket
    HIGH CVEs with fix available      → BLOCK (fail pipeline)
    HIGH CVEs without fix             → WARN + create ticket
    MEDIUM CVEs                       → LOG + track trend
    LOW CVEs                          → LOG only
    Restricted licenses (GPL)         → BLOCK
```

---

## 7. Software Bill of Materials (SBOM)

### What Is an SBOM?

An **SBOM** is a comprehensive list of all components, libraries, and dependencies that make up a software artifact. Think of it as a "nutritional label" for software.

### Why SBOMs Matter

- **Vulnerability response** — When a new CVE is announced (like Log4Shell), you can instantly check if any of your artifacts are affected.
- **License compliance** — Verify all components use approved licenses.
- **Supply chain security** — Know exactly what's in your software.
- **Regulatory requirements** — US Executive Order 14028 mandates SBOMs for software sold to the federal government.

### SBOM Formats

| Format | Full Name | Maintained By | Notes |
|--------|-----------|---------------|-------|
| **SPDX** | Software Package Data Exchange | Linux Foundation | ISO standard (ISO/IEC 5962:2021) |
| **CycloneDX** | CycloneDX | OWASP | Designed for security use cases |
| **SWID** | Software Identification | NIST/ISO | Older format, used in enterprise |

### Generating an SBOM

```bash
# Generate SBOM with Syft (CycloneDX format)
$ syft myapp:v1.2.3 -o cyclonedx-json > sbom.json

# Generate SBOM with Trivy (SPDX format)
$ trivy image --format spdx-json --output sbom.spdx.json myapp:v1.2.3

# Attach SBOM to a container image (using cosign)
$ cosign attach sbom --sbom sbom.json myapp:v1.2.3
```

### SBOM in the Pipeline

```
Build Image → Generate SBOM → Scan SBOM → Store SBOM alongside artifact
                                              │
                                              ├── Attach to container image
                                              ├── Store in artifact registry
                                              └── Publish to SBOM management platform
```

---

## 8. Artifact Storage and Promotion

### Promotion Model

Artifacts move through environments via promotion:

```
┌──────────────┐    ┌───────────────┐    ┌────────────────┐    ┌─────────────┐
│   Dev        │───▶│   Staging     │───▶│   Pre-Prod     │───▶│  Production │
│   Registry   │    │   Registry    │    │   Registry     │    │  Registry   │
│              │    │               │    │                │    │             │
│  All builds  │    │  Passed unit  │    │  Passed full   │    │  Approved   │
│              │    │  + integ tests│    │  test suite    │    │  for release│
└──────────────┘    └───────────────┘    └────────────────┘    └─────────────┘
```

Alternatively, use a **single registry with tags** to track promotion:

```
Single Registry Approach:
  myapp:v1.2.3              ← Built
  myapp:v1.2.3-tested       ← Passed all tests
  myapp:v1.2.3-staging      ← Deployed to staging
  myapp:v1.2.3-production   ← Promoted to production

OR use metadata/labels instead of tag suffixes.
```

### Artifact Retention Policy

| Category | Retention | Rationale |
|----------|-----------|-----------|
| Production releases | 1 year minimum | Rollback capability, audit trail |
| Staging / Pre-prod | 90 days | Debug recent issues |
| Development builds | 30 days | Recent development reference |
| PR / Feature branch builds | 14 days | Review and testing |
| Untagged / dangling images | 7 days | Build cache cleanup |

---

## 9. Universal Artifact Managers

Some tools manage **all artifact types** in a single platform:

| Tool | Type | Supports |
|------|------|----------|
| **JFrog Artifactory** | SaaS / Self-hosted | Docker, Maven, npm, PyPI, Go, Helm, Generic, and 30+ formats |
| **Sonatype Nexus** | Self-hosted / SaaS | Docker, Maven, npm, PyPI, Go, Helm, and more |
| **GitHub Packages** | SaaS | Docker, npm, Maven, NuGet, RubyGems |
| **AWS CodeArtifact** | SaaS | npm, PyPI, Maven, NuGet |
| **Azure Artifacts** | SaaS | npm, Maven, NuGet, Python, Universal |
| **Google Artifact Registry** | SaaS | Docker, Maven, npm, Python, Go, Helm |

### Benefits of a Universal Artifact Manager

1. **Single source of truth** — All artifacts in one place.
2. **Unified security scanning** — Scan all artifact types with one tool.
3. **Consistent access control** — One permission model for all artifacts.
4. **Dependency proxying** — Cache external packages locally.
5. **Traceability** — Link artifacts to builds, commits, and deployments.

---

## 10. Artifact Signing and Verification

### Why Sign Artifacts?

Signing ensures that an artifact:
1. **Came from your CI/CD pipeline** (authenticity).
2. **Has not been tampered with** (integrity).
3. **Was built from a specific commit** (provenance).

### Signing Container Images with Cosign

```bash
# Generate a key pair (one-time setup)
cosign generate-key-pair

# Sign an image after building
cosign sign --key cosign.key ghcr.io/myorg/myapp:v1.2.3

# Verify an image before deploying
cosign verify --key cosign.pub ghcr.io/myorg/myapp:v1.2.3
```

### Keyless Signing with Sigstore

Sigstore enables signing without managing long-lived keys:

```bash
# Keyless signing (uses OIDC identity — e.g., GitHub Actions identity)
cosign sign ghcr.io/myorg/myapp:v1.2.3

# Verify with identity-based policy
cosign verify \
  --certificate-identity "https://github.com/myorg/myapp/.github/workflows/build.yml@refs/heads/main" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  ghcr.io/myorg/myapp:v1.2.3
```

### Enforcing Signed Images in Kubernetes

```yaml
# Kyverno policy — only allow signed images
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: verify-image-signature
spec:
  validationFailureAction: Enforce
  rules:
  - name: check-signature
    match:
      resources:
        kinds:
        - Pod
    verifyImages:
    - imageReferences:
      - "ghcr.io/myorg/*"
      attestors:
      - entries:
        - keyless:
            subject: "https://github.com/myorg/*"
            issuer: "https://token.actions.githubusercontent.com"
```

---

## 11. Review Questions

1. **Explain the "build once, deploy many" principle.** Why is rebuilding for each environment risky?
2. **What is the difference between a container registry and a package registry?** Give two examples of each.
3. **You tag a production image as `myapp:latest` and deploy it.** Three months later, you need to rollback. What problem will you encounter?
4. **Explain Semantic Versioning.** When do you bump MAJOR, MINOR, and PATCH?
5. **Your container scan found a CRITICAL vulnerability in a base image.** Describe the steps you would take.
6. **What is an SBOM and why is it important?** How would you use it to respond to a zero-day vulnerability announcement?
7. **Why should artifacts be signed?** What attack does signing protect against?

---

## 12. Further Reading

- **Specification:** [Semantic Versioning 2.0.0](https://semver.org/)
- **Specification:** [OCI Image Spec](https://github.com/opencontainers/image-spec) — Container image standard
- **Tool:** [Trivy](https://trivy.dev/) — Vulnerability scanner for containers and more
- **Tool:** [Cosign / Sigstore](https://sigstore.dev/) — Artifact signing and verification
- **Tool:** [Syft](https://github.com/anchore/syft) — SBOM generation
- **Article:** [SLSA Framework](https://slsa.dev/) — Supply chain Levels for Software Artifacts
- **Specification:** [CycloneDX](https://cyclonedx.org/) — SBOM standard

---

*Previous: [04 - Deployment Strategies](04-deployment-strategies.md) | Next: [06 - Branching Strategies](06-branching-strategies.md)*
