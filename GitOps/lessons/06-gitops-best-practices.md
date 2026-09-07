# Lesson 6: GitOps Best Practices

## Learning Objectives

By the end of this lesson you will be able to:

- Choose an appropriate repository structure (mono-repo vs multi-repo) for your organization.
- Implement secrets management in a GitOps workflow using Sealed Secrets, SOPS, and External Secrets Operator.
- Configure RBAC in Argo CD using AppProjects, roles, and SSO integration.
- Design multi-tenant Argo CD deployments.
- Plan disaster recovery and backup strategies for Argo CD.

---

## 1. Repository Structure

How you organize your Git repositories has a significant impact on team velocity, security boundaries, and operational complexity.

### 1.1 Mono-Repo

All applications and environments are stored in a single repository.

```
gitops-repo/
  apps/
    app-a/
      base/
        deployment.yaml
        service.yaml
        kustomization.yaml
      overlays/
        dev/
          kustomization.yaml
        staging/
          kustomization.yaml
        prod/
          kustomization.yaml
    app-b/
      base/
        ...
      overlays/
        ...
  platform/
    argocd/
      ...
    cert-manager/
      ...
    monitoring/
      ...
  applicationsets/
    apps.yaml
    platform.yaml
```

**Advantages:**

- Single place to search, review, and audit all configurations.
- Easier cross-cutting changes (e.g., updating a label across all apps).
- Simpler CI/CD — one repo to clone, one webhook to configure.
- Atomic commits can update multiple apps together.

**Disadvantages:**

- All teams share the same repository, which can lead to permission complexity.
- A bad merge can break unrelated applications.
- Large repos become slow to clone and hard to navigate.
- CODEOWNERS rules and branch protection become complex.

**Best for:** Small-to-medium organizations, platform teams, or early-stage GitOps adoption.

### 1.2 Multi-Repo

Each application or team has its own repository.

```
# Team A's repo: team-a-gitops
team-a-gitops/
  app-a/
    base/
    overlays/
  app-b/
    base/
    overlays/

# Team B's repo: team-b-gitops
team-b-gitops/
  app-c/
    ...

# Platform repo: platform-gitops
platform-gitops/
  argocd/
  cert-manager/
  monitoring/
  applicationsets/
```

**Advantages:**

- Clear ownership and access control per team.
- Teams can work independently without interfering with each other.
- Smaller repos are faster and easier to manage.
- Security boundaries align with organizational structure.

**Disadvantages:**

- Cross-cutting changes require multiple PRs across repos.
- More repositories to manage, configure, and monitor.
- Harder to get a global view of the entire system state.

**Best for:** Large organizations with multiple teams, strict security requirements, or regulated environments.

### 1.3 Hybrid Approach

A common pattern is:

- **One platform repo** for cluster-level resources (Argo CD, monitoring, networking, RBAC).
- **One repo per team** for application-level resources.
- **A "root" repo** (or ApplicationSet in the platform repo) that ties everything together.

### 1.4 Branch Strategy

| Strategy | Description | Recommendation |
|----------|-------------|----------------|
| **Branch per environment** | `main` = prod, `develop` = staging, `feature/*` = dev | Avoid — leads to long-lived branches and merge drift. |
| **Directory per environment** | Single branch (`main`), overlays directory per env | Recommended — Kustomize overlays or Helm value files. |
| **Tag-based promotion** | Tag commits for promotion: `v1.0.0-dev`, `v1.0.0-prod` | Works for release-based workflows but adds tagging overhead. |

**Recommendation:** Use a single `main` branch with **directory-based environment separation** (overlays or value files). This avoids branch drift, simplifies reviews, and works naturally with Kustomize and Helm.

---

## 2. Secrets Management

Storing plain Kubernetes Secrets in Git is a critical security violation. The following tools integrate with GitOps workflows to manage secrets safely.

### 2.1 Bitnami Sealed Secrets

Sealed Secrets lets you encrypt a Kubernetes Secret into a `SealedSecret` CRD that only the in-cluster controller can decrypt.

#### How it works

1. Install the Sealed Secrets controller in the cluster.
2. Use the `kubeseal` CLI to encrypt a Secret against the controller's public key.
3. Commit the encrypted `SealedSecret` to Git.
4. The controller decrypts it and creates the actual Secret in the cluster.

#### Installation

```bash
# Install the controller
helm repo add sealed-secrets https://bitnami-labs.github.io/sealed-secrets
helm install sealed-secrets sealed-secrets/sealed-secrets \
  --namespace kube-system

# Install the CLI
brew install kubeseal
```

#### Usage

```bash
# Create a regular secret YAML (do NOT commit this)
kubectl create secret generic db-creds \
  --from-literal=username=admin \
  --from-literal=password=supersecret \
  --dry-run=client -o yaml > db-creds-secret.yaml

# Encrypt it into a SealedSecret (safe to commit)
kubeseal --format yaml < db-creds-secret.yaml > db-creds-sealed.yaml

# Delete the unencrypted file
rm db-creds-secret.yaml
```

**db-creds-sealed.yaml** (safe to commit):

```yaml
apiVersion: bitnami.com/v1alpha1
kind: SealedSecret
metadata:
  name: db-creds
  namespace: my-app
spec:
  encryptedData:
    username: AgA3f8...   # encrypted
    password: AgB7k2...   # encrypted
```

#### Pros and Cons

| Pros | Cons |
|------|------|
| Simple, no external dependencies | Secrets are scoped to one cluster (re-encrypt for each) |
| Encrypted at rest in Git | Rotating the sealing key requires re-encrypting |
| Works with any GitOps tool | No centralized secret management |

### 2.2 Mozilla SOPS

SOPS (Secrets OPerationS) encrypts specific values in YAML/JSON files using age, PGP, AWS KMS, GCP KMS, or Azure Key Vault.

#### How it works

1. Create a `.sops.yaml` configuration file defining encryption rules.
2. Use `sops` to encrypt sensitive files.
3. Commit the encrypted files to Git.
4. Argo CD decrypts them at render time using a plugin or the KSOPS Kustomize plugin.

#### Setup

```bash
# Install SOPS
brew install sops

# Generate an age key
age-keygen -o age.key
# Public key: age1abc123...
```

**.sops.yaml** (in the repo root):

```yaml
creation_rules:
  - path_regex: .*secret.*\.yaml$
    age: age1abc123...
```

#### Encrypt a file

```bash
sops --encrypt --in-place secrets/db-creds.yaml
```

The encrypted file keeps the YAML structure but encrypts the values:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-creds
stringData:
  username: ENC[AES256_GCM,data:abc123...,type:str]
  password: ENC[AES256_GCM,data:def456...,type:str]
sops:
  age:
    - recipient: age1abc123...
      enc: |
        -----BEGIN AGE ENCRYPTED FILE-----
        ...
```

#### Integrating with Argo CD

Use the **KSOPS** Kustomize plugin or the **Argo CD Vault Plugin** to decrypt at render time:

```yaml
# kustomization.yaml using KSOPS
generators:
  - secret-generator.yaml

# secret-generator.yaml
apiVersion: viaduct.ai/v1
kind: ksops
metadata:
  name: db-creds
files:
  - secrets/db-creds.yaml
```

#### Pros and Cons

| Pros | Cons |
|------|------|
| Encrypted values visible in context | Requires plugin setup in Argo CD |
| Supports multiple KMS backends | Key management is your responsibility |
| File-level encryption rules | More complex than Sealed Secrets |

### 2.3 External Secrets Operator (ESO)

ESO syncs secrets from external secret managers into Kubernetes Secrets. No encrypted data is stored in Git at all.

#### How it works

1. Install ESO in the cluster.
2. Configure a `SecretStore` or `ClusterSecretStore` pointing to your secret manager.
3. Create `ExternalSecret` resources in Git that reference secret keys.
4. ESO fetches the values and creates Kubernetes Secrets.

#### Supported Backends

- AWS Secrets Manager / SSM Parameter Store
- HashiCorp Vault
- Azure Key Vault
- GCP Secret Manager
- 1Password, Doppler, and more

#### Example

```yaml
# ClusterSecretStore — connects ESO to AWS Secrets Manager
apiVersion: external-secrets.io/v1beta1
kind: ClusterSecretStore
metadata:
  name: aws-secrets
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-east-1
      auth:
        jwt:
          serviceAccountRef:
            name: external-secrets-sa
            namespace: external-secrets
---
# ExternalSecret — declares which secret to fetch (safe to commit)
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: db-creds
  namespace: my-app
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets
    kind: ClusterSecretStore
  target:
    name: db-creds
    creationPolicy: Owner
  dataFrom:
    - extract:
        key: production/db/credentials
```

#### Pros and Cons

| Pros | Cons |
|------|------|
| No secrets in Git at all | Depends on an external secret manager |
| Centralized secret management | Additional infrastructure (ESO + secret store) |
| Automatic rotation via refreshInterval | More moving parts to configure and maintain |
| Works across clusters | Secret manager access must be properly secured |

### 2.4 Comparison Matrix

| Feature | Sealed Secrets | SOPS | External Secrets |
|---------|---------------|------|-----------------|
| Secrets in Git? | Encrypted | Encrypted | No (only references) |
| External dependency | None | KMS (optional) | Secret manager required |
| Secret rotation | Manual re-encrypt | Manual re-encrypt | Automatic |
| Multi-cluster | Re-encrypt per cluster | Same key works | Same store works |
| Complexity | Low | Medium | Medium-High |
| Best for | Small teams, single cluster | Teams with KMS | Enterprise, multi-cluster |

---

## 3. RBAC in Argo CD

Argo CD provides fine-grained Role-Based Access Control through AppProjects and a policy engine.

### 3.1 AppProjects for Isolation

AppProjects define boundaries for applications:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AppProject
metadata:
  name: team-frontend
  namespace: argocd
spec:
  description: Frontend team applications

  # Allowed source repositories
  sourceRepos:
    - https://github.com/example/frontend-*.git
    - https://github.com/example/shared-charts.git

  # Allowed destination clusters and namespaces
  destinations:
    - server: https://kubernetes.default.svc
      namespace: frontend-*
    - server: https://kubernetes.default.svc
      namespace: shared

  # Allowed cluster-scoped resources (empty = none allowed)
  clusterResourceWhitelist: []

  # Blocked namespace-scoped resources
  namespaceResourceBlacklist:
    - group: ""
      kind: ResourceQuota
    - group: ""
      kind: LimitRange

  # Application sync windows (maintenance windows)
  syncWindows:
    - kind: allow
      schedule: "0 8-18 * * 1-5"     # Allow sync Mon-Fri 8am-6pm
      duration: 10h
      applications:
        - "*"
    - kind: deny
      schedule: "0 0 * * 0"           # Deny sync on Sundays
      duration: 24h
      applications:
        - "*"

  # Roles within this project
  roles:
    - name: developer
      description: Can sync and view applications
      policies:
        - p, proj:team-frontend:developer, applications, get, team-frontend/*, allow
        - p, proj:team-frontend:developer, applications, sync, team-frontend/*, allow
      groups:
        - frontend-devs              # SSO group mapping
    - name: viewer
      description: Read-only access
      policies:
        - p, proj:team-frontend:viewer, applications, get, team-frontend/*, allow
      groups:
        - frontend-viewers
```

### 3.2 Global RBAC Policies

Global policies are configured in the `argocd-rbac-cm` ConfigMap:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-rbac-cm
  namespace: argocd
data:
  # Default role for authenticated users
  policy.default: role:readonly

  # Policy rules (Casbin format)
  policy.csv: |
    # Roles
    p, role:admin, applications, *, */*, allow
    p, role:admin, clusters, *, *, allow
    p, role:admin, repositories, *, *, allow
    p, role:admin, projects, *, *, allow

    p, role:developer, applications, get, */*, allow
    p, role:developer, applications, sync, */*, allow
    p, role:developer, applications, action/*, */*, allow
    p, role:developer, logs, get, */*, allow

    p, role:readonly, applications, get, */*, allow
    p, role:readonly, logs, get, */*, allow

    # Group-to-role mappings
    g, platform-team, role:admin
    g, dev-team, role:developer
    g, stakeholders, role:readonly
```

### 3.3 Policy Format

```
p, <role>, <resource>, <action>, <project>/<application>, <allow|deny>
g, <group-or-user>, <role>
```

**Resources:** `applications`, `clusters`, `repositories`, `projects`, `logs`, `exec`

**Actions:** `get`, `create`, `update`, `delete`, `sync`, `override`, `action/<action-name>`, `*`

### 3.4 SSO Integration

Configure SSO in `argocd-cm`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-cm
  namespace: argocd
data:
  url: https://argocd.example.com
  dex.config: |
    connectors:
      - type: github
        id: github
        name: GitHub
        config:
          clientID: $dex.github.clientID
          clientSecret: $dex.github.clientSecret
          orgs:
            - name: my-org
```

The `$dex.github.clientID` syntax references values from the `argocd-secret` Secret.

---

## 4. Multi-Tenancy

Multi-tenancy in Argo CD means safely sharing a single Argo CD instance across multiple teams.

### 4.1 Tenancy Boundaries

| Layer | Mechanism |
|-------|-----------|
| **Repository access** | AppProject `sourceRepos` restricts which repos a team can use. |
| **Namespace access** | AppProject `destinations` restricts which namespaces a team can deploy to. |
| **Resource types** | `clusterResourceWhitelist` and `namespaceResourceBlacklist` control what resource types are allowed. |
| **RBAC** | Project roles + global policies control who can sync, view, or delete. |
| **Sync windows** | Control when syncs are allowed (e.g., block prod deploys outside business hours). |

### 4.2 Example: Two-Team Setup

```yaml
# Team A: Frontend
apiVersion: argoproj.io/v1alpha1
kind: AppProject
metadata:
  name: team-a
  namespace: argocd
spec:
  sourceRepos:
    - https://github.com/example/team-a-*.git
  destinations:
    - server: https://kubernetes.default.svc
      namespace: team-a-*
  clusterResourceWhitelist: []
---
# Team B: Backend
apiVersion: argoproj.io/v1alpha1
kind: AppProject
metadata:
  name: team-b
  namespace: argocd
spec:
  sourceRepos:
    - https://github.com/example/team-b-*.git
  destinations:
    - server: https://kubernetes.default.svc
      namespace: team-b-*
  clusterResourceWhitelist: []
```

### 4.3 Namespace Isolation Pattern

Combine AppProjects with Kubernetes RBAC:

1. Create a dedicated namespace per team.
2. Create an AppProject per team that only allows their namespaces.
3. Apply Kubernetes NetworkPolicies to isolate network traffic.
4. Apply ResourceQuotas and LimitRanges to control resource usage.
5. Map SSO groups to project roles.

---

## 5. Disaster Recovery

### 5.1 What to Back Up

Since Git is the source of truth for applications, the main concern is Argo CD's own configuration:

| Resource | Location | Backup Method |
|----------|----------|---------------|
| Application CRDs | Kubernetes (`argocd` namespace) | `kubectl get applications -n argocd -o yaml` |
| AppProject CRDs | Kubernetes (`argocd` namespace) | `kubectl get appprojects -n argocd -o yaml` |
| ApplicationSet CRDs | Kubernetes (`argocd` namespace) | `kubectl get applicationsets -n argocd -o yaml` |
| Repository credentials | Secrets in `argocd` namespace | `kubectl get secrets -n argocd -l argocd.argoproj.io/secret-type=repository -o yaml` |
| Cluster credentials | Secrets in `argocd` namespace | `kubectl get secrets -n argocd -l argocd.argoproj.io/secret-type=cluster -o yaml` |
| RBAC config | `argocd-rbac-cm` ConfigMap | `kubectl get cm argocd-rbac-cm -n argocd -o yaml` |
| Main config | `argocd-cm` ConfigMap | `kubectl get cm argocd-cm -n argocd -o yaml` |

### 5.2 GitOps for Argo CD Itself

The best practice is to manage Argo CD's own configuration with GitOps:

```
platform-repo/
  argocd/
    install.yaml                # Argo CD installation manifests
    argocd-cm.yaml              # Configuration
    argocd-rbac-cm.yaml         # RBAC policies
    projects/
      team-a.yaml
      team-b.yaml
    repositories/
      github.yaml
      helm-repos.yaml
    applicationsets/
      ...
```

A root Application manages the `argocd/` directory, so Argo CD manages itself.

### 5.3 Backup Script

```bash
#!/bin/bash
# backup-argocd.sh
BACKUP_DIR="argocd-backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

kubectl get applications -n argocd -o yaml > "$BACKUP_DIR/applications.yaml"
kubectl get appprojects -n argocd -o yaml > "$BACKUP_DIR/appprojects.yaml"
kubectl get applicationsets -n argocd -o yaml > "$BACKUP_DIR/applicationsets.yaml"
kubectl get cm argocd-cm -n argocd -o yaml > "$BACKUP_DIR/argocd-cm.yaml"
kubectl get cm argocd-rbac-cm -n argocd -o yaml > "$BACKUP_DIR/argocd-rbac-cm.yaml"
kubectl get secrets -n argocd -l argocd.argoproj.io/secret-type=repository -o yaml \
  > "$BACKUP_DIR/repo-secrets.yaml"
kubectl get secrets -n argocd -l argocd.argoproj.io/secret-type=cluster -o yaml \
  > "$BACKUP_DIR/cluster-secrets.yaml"

echo "Backup saved to $BACKUP_DIR"
```

### 5.4 Recovery Procedure

1. Install Argo CD on the new/recovered cluster.
2. Apply the backed-up ConfigMaps (`argocd-cm`, `argocd-rbac-cm`).
3. Apply the backed-up Secrets (repository and cluster credentials).
4. Apply the backed-up AppProjects.
5. Apply the backed-up Applications and ApplicationSets.
6. Argo CD will reconcile and restore all workloads from Git.

Because the application manifests live in Git, Argo CD re-deploys everything automatically once it has its configuration back.

### 5.5 High Availability Considerations

For production Argo CD:

- Use the **HA installation manifest** (multiple controller replicas, Redis Sentinel).
- Run the Argo CD namespace with **PodDisruptionBudgets**.
- Use **persistent storage** for Redis if caching performance matters.
- Distribute Argo CD pods across **availability zones**.
- Monitor Argo CD with **Prometheus metrics** and alert on degraded applications.

---

## 6. Additional Best Practices

### 6.1 Image Update Automation

Use [Argo CD Image Updater](https://argocd-image-updater.readthedocs.io/) to automatically update image tags in Git when new images are pushed to a registry:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: my-app
  namespace: argocd
  annotations:
    argocd-image-updater.argoproj.io/image-list: myapp=myregistry.io/myapp
    argocd-image-updater.argoproj.io/myapp.update-strategy: semver
    argocd-image-updater.argoproj.io/write-back-method: git
```

### 6.2 Progressive Delivery

Combine Argo CD with [Argo Rollouts](https://argoproj.github.io/argo-rollouts/) for canary and blue-green deployments:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: my-app
spec:
  strategy:
    canary:
      steps:
        - setWeight: 20
        - pause: { duration: 5m }
        - setWeight: 50
        - pause: { duration: 5m }
        - setWeight: 100
```

### 6.3 Notifications and Alerting

Configure Argo CD Notifications to alert on sync failures:

```yaml
# argocd-notifications-cm
data:
  trigger.on-sync-failed: |
    - when: app.status.operationState.phase in ['Error', 'Failed']
      send: [slack-alert]
  template.slack-alert: |
    message: |
      Application {{.app.metadata.name}} sync failed!
      Revision: {{.app.status.sync.revision}}
      Message: {{.app.status.operationState.message}}
  service.slack: |
    token: $slack-token
```

### 6.4 Resource Tracking

Argo CD tracks which resources belong to which Application. Configure the tracking method in `argocd-cm`:

```yaml
data:
  application.resourceTrackingMethod: annotation
```

Options: `label` (default), `annotation` (recommended for large resources), `annotation+label`.

### 6.5 Sync Windows for Change Management

Enforce deployment windows for regulated environments:

```yaml
spec:
  syncWindows:
    - kind: allow
      schedule: "0 9-17 * * 1-5"    # Mon-Fri 9am-5pm
      duration: 8h
      applications:
        - "*"
      manualSync: true               # allow manual syncs outside window
```

---

## 7. Security Checklist

Use this checklist when setting up Argo CD in production:

- [ ] Change the admin password and delete `argocd-initial-admin-secret`.
- [ ] Enable SSO/OIDC and disable local admin if possible.
- [ ] Use AppProjects to restrict sources, destinations, and resource types per team.
- [ ] Configure RBAC with least-privilege roles.
- [ ] Use Sealed Secrets, SOPS, or External Secrets for secret management.
- [ ] Enable TLS for the Argo CD server (Ingress or load balancer).
- [ ] Restrict network access to the Argo CD UI/API.
- [ ] Enable audit logging.
- [ ] Monitor Argo CD with Prometheus and set up alerts for degraded applications.
- [ ] Back up Argo CD configuration and store it in Git.
- [ ] Review and rotate repository and cluster credentials regularly.
- [ ] Use signed commits and branch protection on the GitOps repository.

---

## 8. Knowledge Check

1. What are the pros and cons of a mono-repo vs multi-repo approach?
2. Name three tools for managing secrets in a GitOps workflow and explain when you would choose each one.
3. How do AppProjects enforce multi-tenancy in Argo CD?
4. Write an AppProject that allows a team to deploy only from their Git repo to namespaces prefixed with their team name.
5. What resources should you back up to recover an Argo CD installation?

---

## 9. Summary

- **Repository structure**: Choose mono-repo for simplicity, multi-repo for team isolation, or a hybrid approach. Use directory-based environment separation, not branches.
- **Secrets management**: Never store plain secrets in Git. Use Sealed Secrets for simplicity, SOPS for file-level encryption, or External Secrets Operator for centralized secret management.
- **RBAC**: Use AppProjects to define tenancy boundaries and the `argocd-rbac-cm` ConfigMap for global policies. Integrate SSO for enterprise environments.
- **Multi-tenancy**: Combine AppProjects, Kubernetes RBAC, NetworkPolicies, and ResourceQuotas to safely share a single Argo CD instance.
- **Disaster recovery**: Back up Argo CD configuration and manage it with GitOps. Application state lives in Git and is automatically restored when Argo CD reconciles.

---

**Previous lesson:** [Lesson 5 — ArgoCD with Kustomize](05-argocd-with-kustomize.md)
