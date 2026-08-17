# GitOps & Argo CD — Full Tutorial

## 1. What is GitOps?

GitOps is a way to do continuous delivery for cloud-native applications. The desired state of the system is declared in a Git repository, and an automated agent continuously reconciles the live state with the desired state defined in Git.

Git = single source of truth  
Automated controllers = enforcement layer

## 2. The four GitOps principles

1. **Declarative configuration**  
   Every part of the system is described declaratively (usually YAML). The desired state is explicit and versioned.

2. **Versioned and immutable source of truth**  
   Git is the canonical record. Changes to infrastructure or applications go through Git, giving you full history, audit, and rollback.

3. **Automatic pull-based delivery**  
   An operator running in the cluster pulls the desired state from Git and applies it. There is no external actor pushing changes into the cluster with raw `kubectl`.

4. **Continuous reconciliation**  
   The operator continuously compares the live cluster state to the desired state in Git and self-heals drift.

## 3. GitOps vs traditional CI/CD

| Traditional CI/CD | GitOps |
|-------------------|--------|
| Push-based: CI system runs `kubectl apply` or `helm upgrade` | Pull-based: cluster operator pulls and reconciles |
| CI has cluster credentials | Cluster only reads Git; credentials stay in cluster |
| State is split across CI logs, scripts, and runtime | Single source of truth in Git |
| Rollback often requires re-running pipelines | Revert a commit and the cluster follows |
| Drift from manual changes may go unnoticed | Drift is detected and corrected automatically |

## 4. Why Argo CD?

Argo CD is the most widely adopted open-source GitOps controller for Kubernetes. It reads application definitions from Git, compares them to the live cluster, and keeps them in sync. It also provides:

- A web UI and a CLI
- Multi-tenancy through AppProjects
- Support for plain manifests, Helm, Kustomize, Jsonnet, and custom plugins
- Automated sync, pruning, and self-healing
- ApplicationSets for generating many applications from a single definition
- Sync waves and resource hooks for ordered rollouts
- RBAC, SSO, and OIDC integration

## 5. Argo CD architecture

Core components installed in the `argocd` namespace:

- **argocd-server** — serves the API and web UI.
- **argocd-repo-server** — clones repositories and generates manifests.
- **argocd-application-controller** — reconciles live state with desired state.
- **argocd-dex-server** (optional) — handles SSO/OIDC.
- **argocd-redis** — caching layer for generated manifests and state.

Workflow:

1. Administrator creates an Argo CD `Application` resource.
2. Argo CD clones the Git repo at the configured path/revision.
3. The repo server renders manifests (YAML, Helm, Kustomize, etc.).
4. The application controller compares rendered manifests against the cluster.
5. Argo CD reports health and sync status, and optionally applies changes.

## 6. Installing Argo CD

### 6.1 Create the namespace and apply the install manifest

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

### 6.2 Access the API server

Port-forward for local access:

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

Then open `https://localhost:8080` and accept the self-signed certificate.

### 6.3 Login credentials

The initial password for the `admin` account is the name of the `argocd-initial-admin-secret` secret:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

Username: `admin`

### 6.4 Install the Argo CD CLI

On macOS with Homebrew:

```bash
brew install argocd
```

Other platforms and direct downloads are documented on the Argo CD release page.

### 6.5 Login from the CLI

```bash
argocd login localhost:8080
# or with insecure TLS
argocd login localhost:8080 --insecure
```

## 7. Core concepts

### 7.1 Application

An `Application` is the most important custom resource. It ties a Git source to a target cluster/namespace.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: guestbook
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/argoproj/argocd-example-apps.git
    targetRevision: HEAD
    path: guestbook
  destination:
    server: https://kubernetes.default.svc
    namespace: guestbook
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

### 7.2 AppProject

AppProjects group applications, define allowed sources and destinations, and enforce RBAC.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AppProject
metadata:
  name: production
  namespace: argocd
spec:
  description: Production workloads
  sourceRepos:
    - https://github.com/example/prod-apps.git
  destinations:
    - namespace: prod-*
      server: https://kubernetes.default.svc
  clusterResourceWhitelist:
    - group: ''
      kind: Namespace
```

### 7.3 Repository credentials

For private repositories, create a `Secret` with the `argocd.argoproj.io/secret-type: repository` label:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: private-repo
  namespace: argocd
  labels:
    argocd.argoproj.io/secret-type: repository
stringData:
  type: git
  url: https://github.com/example/private.git
  username: example
  password: <token>
```

## 8. Application definitions by tool

### 8.1 Plain manifests

Argo CD reads any `.yaml` or `.json` files in the specified directory and applies them with `kubectl`.

### 8.2 Helm

Helm applications can use a chart from a Git repo, a packaged chart, or a Helm repository.

```yaml
spec:
  source:
    repoURL: https://charts.bitnami.com/bitnami
    chart: nginx
    targetRevision: 15.0.0
    helm:
      values: |
        replicaCount: 2
        service:
          type: ClusterIP
```

### 8.3 Kustomize

Kustomize overlays are applied when the source path contains a `kustomization.yaml`.

```yaml
spec:
  source:
    repoURL: https://github.com/example/kustomize-demo.git
    targetRevision: main
    path: overlays/production
```

No extra configuration is required; Argo CD detects the `kustomization.yaml` and runs `kustomize build`.

## 9. Sync strategies

### 9.1 Manual sync

By default, Argo CD reports drift but does not apply changes. An operator clicks **Sync** in the UI or runs:

```bash
argocd app sync <app-name>
```

### 9.2 Automated sync

```yaml
syncPolicy:
  automated:
    prune: true       # remove resources no longer in Git
    selfHeal: true    # overwrite manual cluster changes
    allowEmpty: false
```

### 9.3 Sync options

```yaml
syncPolicy:
  syncOptions:
    - CreateNamespace=true
    - PrunePropagationPolicy=foreground
    - PruneLast=true
    - ApplyOutOfSyncOnly=true
    - ServerSideApply=true
```

### 9.4 Replace vs apply

For resources where `kubectl apply` is not appropriate, add an annotation:

```yaml
metadata:
  annotations:
    argocd.argoproj.io/sync-options: Replace=true
```

## 10. Health, sync, and operation states

Argo CD reports several states in the UI and through `kubectl`:

- **Sync status**: `Synced`, `OutOfSync`
- **Health status**: `Healthy`, `Progressing`, `Degraded`, `Missing`, `Suspended`, `Unknown`
- **Operation**: `Running`, `Succeeded`, `Failed`, `Error`

You can also query from the CLI:

```bash
argocd app get <app-name>
argocd app wait <app-name> --health
```

## 11. App of Apps

The App of Apps pattern uses one Argo CD Application whose manifests are other Argo CD Applications. This is a simple way to manage many applications from a single root.

```yaml
# bootstrap-app.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: bootstrap
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/example/gitops-config.git
    targetRevision: main
    path: apps
  destination:
    server: https://kubernetes.default.svc
    namespace: argocd
```

The `apps/` directory contains other `Application` resources, e.g. `nginx.yaml`, `redis.yaml`.

## 12. ApplicationSet

`ApplicationSet` is the preferred way to generate multiple Applications from a single template. It supports generators for clusters, Git files/directories, lists, and more.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: cluster-addons
  namespace: argocd
spec:
  generators:
    - list:
        elements:
          - cluster: prod
            url: https://prod.example.com
          - cluster: staging
            url: https://staging.example.com
  template:
    metadata:
      name: '{{cluster}}-prometheus'
    spec:
      project: default
      source:
        repoURL: https://github.com/example/monitoring.git
        targetRevision: main
        path: prometheus
      destination:
        server: '{{url}}'
        namespace: monitoring
```

## 13. Sync waves and hooks

### 13.1 Sync waves

Assign a wave number to a resource with the `argocd.argoproj.io/sync-wave` annotation. Lower numbers sync first.

```yaml
metadata:
  annotations:
    argocd.argoproj.io/sync-wave: "-5"
```

Use this to order CRDs, namespaces, or prerequisites before application workloads.

### 13.2 Resource hooks

Hooks run at specific points in the sync lifecycle:

- `PreSync` — before the main sync
- `Sync` — during the main sync
- `PostSync` — after the main sync
- `SyncFail` — if the sync fails

Mark a Job with a hook annotation:

```yaml
metadata:
  annotations:
    argocd.argoproj.io/hook: PostSync
    argocd.argoproj.io/hook-delete-policy: HookSucceeded
```

## 14. Secrets in GitOps

Storing plain Kubernetes Secrets in Git is dangerous. Common patterns:

### 14.1 Sealed Secrets

Bitnami Sealed Secrets encrypt a Secret into a `SealedSecret` CRD that only the cluster controller can decrypt.

```bash
kubeseal --controller-namespace=sealed-secrets \
  --controller-name=sealed-secrets \
  < mysecret.yaml > mysealedsecret.yaml
```

### 14.2 External Secrets Operator (ESO)

ESO pulls secrets from an external secret manager (AWS Secrets Manager, Vault, Azure Key Vault, GCP Secret Manager) and writes them to Kubernetes.

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: db-creds
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: secret-store
    kind: SecretStore
  target:
    name: db-creds
  dataFrom:
    - extract:
        key: prod/db/creds
```

### 14.3 SOPS + Mozilla SOPS

Encrypt YAML files with SOPS and let Argo CD decrypt them using the SOPS-age extension or a custom config management plugin.

## 15. Multi-cluster deployments

Argo CD can deploy to multiple clusters by adding them as `Cluster` secrets.

```bash
argocd cluster add <context-name>
```

Then reference the cluster's API server URL in `destination.server`:

```yaml
destination:
  server: https://prod-api.example.com
  namespace: app
```

Use AppProjects to scope which applications can target which clusters and namespaces.

## 16. Rollbacks

Because Git is the source of truth, a rollback is a Git operation:

1. Find the last good commit.
2. Revert the offending commit or reset the branch.
3. Argo CD detects the change and resyncs.

For an immediate rollback:

```bash
git revert <bad-commit>
git push
```

You can also use Argo CD to roll back to a previously synced state from the UI history tab, but the permanent fix belongs in Git.

## 17. Monitoring and observability

Argo CD exposes Prometheus metrics on `/metrics`. Useful metrics include:

- `argocd_app_info`
- `argocd_app_sync_total`
- `argocd_app_reconcile`
- `argocd_redis_request_duration_seconds`

The built-in UI gives a real-time graph of sync status, resource health, and operation history.

## 18. Best practices

1. **One repo or many?** Use a repo per team or environment, or a mono-repo with clear directory structure.
2. **Branch per environment?** Use `main` as production and deploy to other environments with branches, tags, or overlays.
3. **Use ApplicationSets** instead of hand-written Application lists when scaling past a few apps.
4. **Keep secrets out of Git** — use Sealed Secrets, ESO, or SOPS.
5. **Limit cluster-wide resources** with AppProjects and RBAC.
6. **Enable self-heal and prune** only after you trust your Git state.
7. **Use sync waves** for ordered rollouts, especially CRDs and namespaces.
8. **Monitor sync metrics** and alert on degraded or out-of-sync applications.
9. **Back up the Argo CD state**; the `argocd-cm`, `argocd-rbac-cm`, and AppProject/Application resources can be stored in Git too.
10. **Test changes in a lower environment** before merging to the branch that Argo CD watches.

## 19. Common troubleshooting

### Application stuck OutOfSync

```bash
argocd app diff <app-name>
```

Check for fields managed by webhooks or controllers that mutate the desired state.

### Permission denied

Verify that the Application's project allows the destination namespace and that the repo credentials are valid.

### Resource hook not running

Ensure the hook Job is in the same Application and the annotation value is spelled exactly: `PreSync`, `Sync`, `PostSync`, `SyncFail`.

### Argo CD UI unreachable

```bash
kubectl -n argocd get pods
kubectl -n argocd logs deployment/argocd-server
```

### Sync fails with a CRD

Make sure the CRD is defined in a negative sync wave so it exists before the custom resource is applied.

## 20. Summary

GitOps turns Git into the control plane for Kubernetes. Argo CD implements GitOps with a pull-based, declarative, continuously reconciling controller. By the end of this tutorial you should be able to install Argo CD, define Applications, automate deployments, manage secrets safely, and operate across multiple clusters.
