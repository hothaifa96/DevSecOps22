# Lesson 3: ArgoCD Applications

## Learning Objectives

By the end of this lesson you will be able to:

- Define an Argo CD Application resource and explain every field in the spec.
- Configure sync policies: manual sync, automated sync, self-heal, and prune.
- Use sync waves to order resource creation during a sync.
- Use resource hooks (PreSync, PostSync, SyncFail) for migration jobs and notifications.
- Understand health checks and how Argo CD determines resource health.
- Implement the App-of-Apps pattern to manage multiple applications declaratively.

---

## 1. The Application Custom Resource

The `Application` CRD is the central abstraction in Argo CD. It connects a **source** (a Git repository, Helm chart, or OCI artifact) to a **destination** (a Kubernetes cluster and namespace).

### 1.1 Full Application Manifest

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: my-web-app
  namespace: argocd            # Applications must live in the argocd namespace
  labels:
    team: platform
  finalizers:
    - resources-finalizer.argocd.argoproj.io   # cascade-delete cluster resources
spec:
  project: default             # AppProject this application belongs to

  source:
    repoURL: https://github.com/example/gitops-repo.git
    targetRevision: main       # branch, tag, or commit SHA
    path: apps/my-web-app      # directory containing manifests

  destination:
    server: https://kubernetes.default.svc   # target cluster API
    namespace: my-web-app                    # target namespace

  syncPolicy:
    automated:
      prune: true
      selfHeal: true
      allowEmpty: false
    syncOptions:
      - CreateNamespace=true
      - PrunePropagationPolicy=foreground
      - ApplyOutOfSyncOnly=true
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m

  ignoreDifferences:
    - group: apps
      kind: Deployment
      jsonPointers:
        - /spec/replicas       # ignore HPA-managed replica count
```

### 1.2 Key Fields Explained

| Field | Purpose |
|-------|---------|
| `metadata.namespace` | Must be `argocd` (or wherever Argo CD is installed). |
| `metadata.finalizers` | When set, deleting the Application also deletes the cluster resources it manages. |
| `spec.project` | The AppProject that governs allowed sources, destinations, and RBAC. |
| `spec.source.repoURL` | Git repository URL (HTTPS or SSH) or Helm chart repository. |
| `spec.source.targetRevision` | Branch name, tag, or commit SHA to track. |
| `spec.source.path` | Directory in the repo containing manifests. |
| `spec.destination.server` | Kubernetes API server URL of the target cluster. |
| `spec.destination.namespace` | Namespace where resources will be created. |
| `spec.syncPolicy` | Controls how and when syncs happen (see Section 2). |
| `spec.ignoreDifferences` | Fields to exclude from diff comparison (useful for HPA, mutating webhooks). |

### 1.3 Creating an Application

You can create an Application in three ways:

**Via kubectl:**

```bash
kubectl apply -f my-web-app-application.yaml
```

**Via the CLI:**

```bash
argocd app create my-web-app \
  --repo https://github.com/example/gitops-repo.git \
  --path apps/my-web-app \
  --dest-server https://kubernetes.default.svc \
  --dest-namespace my-web-app \
  --sync-policy automated \
  --auto-prune \
  --self-heal \
  --sync-option CreateNamespace=true
```

**Via the UI:**

Click **+ New App** in the top-left of the Applications view and fill in the form.

---

## 2. Sync Policies

Sync policies control when and how Argo CD applies changes from Git to the cluster.

### 2.1 Manual Sync (Default)

When no `syncPolicy.automated` is specified, Argo CD only **detects** drift and reports the application as `OutOfSync`. A human must explicitly trigger a sync.

```bash
# Trigger a manual sync
argocd app sync my-web-app
```

**When to use:** Early adoption, production environments where you want a human gate, or applications managed by change-management processes.

### 2.2 Automated Sync

With automated sync enabled, Argo CD applies changes automatically whenever it detects that the live state differs from Git.

```yaml
syncPolicy:
  automated: {}
```

By default, automated sync does **not** prune deleted resources or self-heal manual changes. You must opt in.

### 2.3 Prune

When `prune: true` is set, Argo CD deletes resources from the cluster that are no longer present in Git.

```yaml
syncPolicy:
  automated:
    prune: true
```

**Example:** You remove a ConfigMap from Git. With prune enabled, Argo CD deletes it from the cluster on the next sync. Without prune, the orphaned ConfigMap remains.

> **Safety tip:** If you want prune globally but need to protect a specific resource, add the annotation `argocd.argoproj.io/sync-options: Prune=false` to that resource.

### 2.4 Self-Heal

When `selfHeal: true` is set, Argo CD reverts any manual changes made directly to the cluster.

```yaml
syncPolicy:
  automated:
    selfHeal: true
```

**Example:** Someone runs `kubectl scale deployment/nginx --replicas=10` but Git says `replicas: 3`. With self-heal, Argo CD overwrites the change and restores 3 replicas.

> **Note:** Self-heal is checked every time the application controller reconciles (default polling interval: 3 minutes, or immediately via webhook).

### 2.5 allowEmpty

```yaml
syncPolicy:
  automated:
    allowEmpty: false    # default
```

When `false`, Argo CD refuses to sync if the rendered manifests produce zero resources. This protects against accidentally deleting everything if the repo server encounters an error.

### 2.6 Sync Options Reference

Sync options are flags applied at the application level or per-resource via annotations.

| Option | Effect |
|--------|--------|
| `CreateNamespace=true` | Create the target namespace if it does not exist. |
| `PrunePropagationPolicy=foreground` | Wait for dependents to be deleted before pruning the parent. |
| `PruneLast=true` | Prune resources after all other sync operations complete. |
| `ApplyOutOfSyncOnly=true` | Only apply resources that are out of sync (faster for large apps). |
| `ServerSideApply=true` | Use server-side apply instead of `kubectl apply`. Avoids "too large" annotation errors. |
| `Replace=true` | Use `kubectl replace` instead of `kubectl apply` (per-resource annotation). |
| `RespectIgnoreDifferences=true` | Respect `ignoreDifferences` during sync (not just during diff). |
| `FailOnSharedResource=true` | Fail sync if a resource is managed by another Application. |

### 2.7 Retry Policy

Configure automatic retries for failed syncs:

```yaml
syncPolicy:
  retry:
    limit: 5
    backoff:
      duration: 5s
      factor: 2
      maxDuration: 3m
```

This retries up to 5 times with exponential backoff: 5s, 10s, 20s, 40s, 80s (capped at 3m).

---

## 3. Sync Waves and Hooks

### 3.1 Sync Waves

Sync waves let you control the **order** in which resources are applied during a sync. Each resource is assigned a wave number via annotation. Resources in lower-numbered waves are applied first.

```yaml
metadata:
  annotations:
    argocd.argoproj.io/sync-wave: "-5"   # applied first
---
metadata:
  annotations:
    argocd.argoproj.io/sync-wave: "0"    # default wave (applied second)
---
metadata:
  annotations:
    argocd.argoproj.io/sync-wave: "5"    # applied last
```

**Typical ordering:**

| Wave | Resources |
|------|-----------|
| -10 | Namespaces |
| -5 | CRDs, RBAC (ClusterRoles, ServiceAccounts) |
| 0 | ConfigMaps, Secrets, Services (default) |
| 5 | Deployments, StatefulSets |
| 10 | Ingress, HPA, monitoring resources |

Argo CD waits for all resources in a wave to be **healthy** before moving to the next wave.

### 3.2 Resource Hooks

Hooks are Kubernetes resources (usually Jobs) that run at specific points in the sync lifecycle. They are annotated with `argocd.argoproj.io/hook`.

| Hook Phase | When It Runs |
|------------|--------------|
| `PreSync` | Before the main sync starts. Use for database migrations, backups, or pre-flight checks. |
| `Sync` | During the main sync, alongside the normal resources. |
| `PostSync` | After all resources have been synced and are healthy. Use for smoke tests, notifications, or cache warming. |
| `SyncFail` | Only if the sync fails. Use for rollback notifications or cleanup. |
| `Skip` | The resource is skipped during sync entirely. |

**Example: Database migration Job (PreSync)**

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: db-migrate
  namespace: my-web-app
  annotations:
    argocd.argoproj.io/hook: PreSync
    argocd.argoproj.io/hook-delete-policy: HookSucceeded
spec:
  template:
    spec:
      containers:
        - name: migrate
          image: my-web-app:latest
          command: ["python", "manage.py", "migrate"]
      restartPolicy: Never
  backoffLimit: 3
```

**Example: Slack notification (PostSync)**

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: notify-slack
  annotations:
    argocd.argoproj.io/hook: PostSync
    argocd.argoproj.io/hook-delete-policy: HookSucceeded
spec:
  template:
    spec:
      containers:
        - name: notify
          image: curlimages/curl:latest
          command:
            - curl
            - -X
            - POST
            - -d
            - '{"text":"Deployment succeeded!"}'
            - https://hooks.slack.com/services/XXXXX
      restartPolicy: Never
```

### 3.3 Hook Delete Policies

Control when hook resources are cleaned up:

| Policy | Behavior |
|--------|----------|
| `HookSucceeded` | Delete the hook resource after it succeeds. |
| `HookFailed` | Delete the hook resource after it fails. |
| `BeforeHookCreation` | Delete any previous instance of the hook before creating a new one. |

You can combine policies:

```yaml
argocd.argoproj.io/hook-delete-policy: HookSucceeded,BeforeHookCreation
```

### 3.4 Combining Waves and Hooks

Hooks also respect sync waves. A `PreSync` hook in wave `-5` runs before a `PreSync` hook in wave `0`.

```yaml
metadata:
  annotations:
    argocd.argoproj.io/hook: PreSync
    argocd.argoproj.io/sync-wave: "-5"    # runs before other PreSync hooks
```

**Full sync execution order:**

1. PreSync hooks (ordered by wave)
2. Sync resources (ordered by wave)
3. PostSync hooks (ordered by wave)
4. *(if sync failed)* SyncFail hooks (ordered by wave)

---

## 4. Health Checks

Argo CD evaluates the **health** of every resource it manages. Health status determines whether the application is considered healthy and whether sync waves can proceed.

### 4.1 Built-in Health Assessments

Argo CD includes health checks for common Kubernetes resources:

| Resource | Healthy When |
|----------|-------------|
| Deployment | All replicas are available and updated. |
| StatefulSet | All replicas are ready. |
| DaemonSet | Desired number of pods are scheduled and ready. |
| Service | Always healthy (no runtime state). |
| Ingress | Has at least one IP or hostname in status. |
| Job | Completed successfully. |
| Pod | Running and all containers ready. |
| PersistentVolumeClaim | Bound to a PV. |

### 4.2 Health Status Values

| Status | Meaning |
|--------|---------|
| `Healthy` | Resource is fully operational. |
| `Progressing` | Resource is updating (e.g., rolling out new pods). |
| `Degraded` | Resource has a problem (e.g., CrashLoopBackOff). |
| `Suspended` | Resource is intentionally paused (e.g., suspended CronJob). |
| `Missing` | Resource does not exist in the cluster. |
| `Unknown` | Health cannot be determined. |

### 4.3 Custom Health Checks

You can define custom health checks in the `argocd-cm` ConfigMap using Lua scripts:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-cm
  namespace: argocd
data:
  resource.customizations.health.mycrd.example.com_MyResource: |
    hs = {}
    if obj.status ~= nil then
      if obj.status.phase == "Ready" then
        hs.status = "Healthy"
        hs.message = "Resource is ready"
      elseif obj.status.phase == "Provisioning" then
        hs.status = "Progressing"
        hs.message = "Resource is being provisioned"
      else
        hs.status = "Degraded"
        hs.message = obj.status.message or "Unknown issue"
      end
    end
    return hs
```

---

## 5. The App-of-Apps Pattern

### 5.1 What is App-of-Apps?

The App-of-Apps pattern uses a single "root" Argo CD Application whose Git source contains other Argo CD Application manifests. When the root application syncs, it creates (and manages) all child applications.

This pattern lets you:

- **Bootstrap an entire cluster** with a single Application.
- **Manage all applications declaratively** in Git.
- **Add or remove applications** by adding or removing YAML files from the root directory.

### 5.2 Repository Structure

```
gitops-repo/
  apps/                          # Root app points here
    nginx.yaml                   # Application manifest for nginx
    redis.yaml                   # Application manifest for redis
    monitoring.yaml              # Application manifest for Prometheus stack
    cert-manager.yaml            # Application manifest for cert-manager
  manifests/
    nginx/
      deployment.yaml
      service.yaml
    redis/
      deployment.yaml
      service.yaml
    monitoring/
      ...
    cert-manager/
      ...
```

### 5.3 Root Application

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: root-app
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/example/gitops-repo.git
    targetRevision: main
    path: apps                   # directory containing Application YAMLs
  destination:
    server: https://kubernetes.default.svc
    namespace: argocd            # child Applications live in argocd namespace
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

### 5.4 Child Application Example

```yaml
# apps/nginx.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: nginx
  namespace: argocd
  finalizers:
    - resources-finalizer.argocd.argoproj.io
spec:
  project: default
  source:
    repoURL: https://github.com/example/gitops-repo.git
    targetRevision: main
    path: manifests/nginx
  destination:
    server: https://kubernetes.default.svc
    namespace: nginx
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

### 5.5 Lifecycle

1. You apply the root Application (`root-app`) to the cluster.
2. Argo CD syncs `root-app`, which reads the `apps/` directory.
3. Argo CD creates the child Application resources (nginx, redis, monitoring, cert-manager).
4. Each child Application begins its own reconciliation loop.
5. To add a new application, commit a new YAML file to `apps/`. To remove one, delete the file.

### 5.6 App-of-Apps vs ApplicationSet

| Feature | App-of-Apps | ApplicationSet |
|---------|-------------|----------------|
| Configuration style | Individual YAML files per app | Template + generator |
| Best for | Heterogeneous apps with different configs | Homogeneous apps across clusters/envs |
| Flexibility | Full control per application | Templated, less per-app customization |
| Scale | Tens of apps | Hundreds of apps |

Both patterns are valid and can even be combined.

---

## 6. Ignore Differences

Some fields are managed by controllers (HPA, VPA, mutating webhooks) and will always differ from the Git manifest. Use `ignoreDifferences` to prevent these from causing perpetual `OutOfSync` status.

```yaml
spec:
  ignoreDifferences:
    # Ignore replica count managed by HPA
    - group: apps
      kind: Deployment
      jsonPointers:
        - /spec/replicas

    # Ignore annotations added by a mutating webhook
    - group: ""
      kind: Service
      jqPathExpressions:
        - .metadata.annotations["webhook.example.com/injected"]

    # Ignore all managedFields
    - group: "*"
      kind: "*"
      managedFieldsManagers:
        - kube-controller-manager
```

---

## 7. Application Status

You can inspect an application's status via CLI, UI, or kubectl:

```bash
# CLI
argocd app get my-web-app

# kubectl
kubectl get application my-web-app -n argocd -o yaml
```

The status includes:

- **Sync status:** `Synced`, `OutOfSync`, `Unknown`
- **Health status:** `Healthy`, `Progressing`, `Degraded`, `Missing`, `Suspended`, `Unknown`
- **Operation state:** `Succeeded`, `Failed`, `Running`, `Error`
- **Resource list:** every managed resource with individual sync and health status
- **Conditions:** warnings and errors (e.g., "ComparisonError", "InvalidSpecError")
- **History:** list of previous sync operations with revision, date, and outcome

---

## 8. Knowledge Check

1. What happens when you set `prune: true` and remove a Deployment from Git?
2. Explain the difference between `selfHeal` and manual sync.
3. You need to run a database migration before deploying new application code. Which hook phase do you use, and what annotation do you add?
4. A Deployment is showing as `OutOfSync` because an HPA is changing the replica count. How do you fix this?
5. Describe the App-of-Apps pattern. What goes in the root application's source path?

---

## 9. Summary

- The `Application` CRD is the core abstraction in Argo CD, mapping a Git source to a cluster destination.
- Sync policies control automation: **manual** for gated environments, **automated** for continuous delivery, with optional **prune** and **self-heal**.
- **Sync waves** order resource creation; **hooks** run Jobs at specific sync phases (PreSync, PostSync, SyncFail).
- Argo CD evaluates **health** for every managed resource using built-in checks or custom Lua scripts.
- The **App-of-Apps** pattern lets you manage an entire platform from a single root Application, with each child application defined as a YAML file in Git.

---

**Previous lesson:** [Lesson 2 — ArgoCD Fundamentals](02-argocd-fundamentals.md)  
**Next lesson:** [Lesson 4 — ArgoCD with Helm](04-argocd-with-helm.md)
