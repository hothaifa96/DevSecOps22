# Lesson 4: ArgoCD with Helm

## Learning Objectives

By the end of this lesson you will be able to:

- Explain how Argo CD integrates with Helm and why `helm template` is used instead of `helm install`.
- Configure an Application that deploys a Helm chart from a repository, a Git repo, or an OCI registry.
- Override Helm values at the Application level.
- Understand the differences between Helm hooks and Argo CD hooks.
- Use ApplicationSet to generate applications for multiple clusters or environments.

---

## 1. How Argo CD Uses Helm

Argo CD does **not** run `helm install` or `helm upgrade`. Instead, it runs **`helm template`** to render the chart into plain Kubernetes manifests and then applies those manifests using its own sync engine.

### 1.1 Why `helm template`?

- **Consistency:** Argo CD tracks every resource individually. Using `helm template` gives Argo CD full visibility into each resource, its sync status, and its health.
- **No Helm state:** There is no Helm release secret (`sh.helm.release.v1.*`) in the cluster. Argo CD is the single source of truth, not Helm's release history.
- **Unified diff:** The diff view in the UI shows the exact rendered output, regardless of whether the source is Helm, Kustomize, or plain YAML.

### 1.2 Implications

| Helm Feature | Supported in Argo CD? | Notes |
|-------------|----------------------|-------|
| `helm template` | Yes | Core rendering mechanism |
| `values.yaml` / `--set` | Yes | Via Application spec |
| Helm hooks | Partial | See Section 4 |
| `helm test` | No | Use Argo CD PostSync hooks instead |
| `helm rollback` | No | Rollback via Git revert |
| Helm release history | No | Use Argo CD sync history instead |
| Helm dependencies (`Chart.yaml`) | Yes | Resolved during rendering |

---

## 2. Configuring Helm Applications

### 2.1 Chart from a Helm Repository

Deploy a chart published to a Helm repository (e.g., Bitnami, Prometheus Community):

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: nginx
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://charts.bitnami.com/bitnami    # Helm repo URL
    chart: nginx                                     # chart name
    targetRevision: 15.4.0                           # chart version
    helm:
      values: |
        replicaCount: 3
        service:
          type: ClusterIP
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 250m
            memory: 256Mi
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

> **Note:** When using a Helm repo, you specify `chart` and `targetRevision` (the chart version). There is no `path` field.

#### Adding a Helm Repository to Argo CD

If the Helm repo is not already configured:

```bash
# Public repo
argocd repo add https://charts.bitnami.com/bitnami --type helm --name bitnami

# Private repo with credentials
argocd repo add https://charts.example.com --type helm --name internal \
  --username admin --password secret
```

Or declaratively via a Secret:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: bitnami-helm-repo
  namespace: argocd
  labels:
    argocd.argoproj.io/secret-type: repository
stringData:
  type: helm
  name: bitnami
  url: https://charts.bitnami.com/bitnami
```

### 2.2 Chart from a Git Repository

If the Helm chart lives in a Git repo alongside your application code:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: my-api
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/example/gitops-repo.git
    targetRevision: main
    path: charts/my-api             # directory containing Chart.yaml
    helm:
      valueFiles:
        - values.yaml               # default values
        - values-production.yaml    # environment-specific overrides
  destination:
    server: https://kubernetes.default.svc
    namespace: my-api
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

> **Note:** When using a Git repo, you specify `path` (the directory with `Chart.yaml`). There is no `chart` field.

### 2.3 Chart from an OCI Registry

Helm 3 supports OCI registries for chart storage:

```yaml
spec:
  source:
    repoURL: oci://ghcr.io/example          # OCI registry base URL
    chart: my-chart                           # chart name
    targetRevision: 1.0.0                     # chart version
```

---

## 3. Overriding Helm Values

Argo CD provides multiple ways to override Helm values, evaluated in order of precedence (lowest to highest):

### 3.1 values (inline)

Embed values directly in the Application manifest:

```yaml
helm:
  values: |
    replicaCount: 5
    image:
      repository: myapp
      tag: v2.0.0
    ingress:
      enabled: true
      hosts:
        - host: myapp.example.com
          paths:
            - path: /
              pathType: Prefix
```

### 3.2 valueFiles

Reference one or more values files relative to the chart directory:

```yaml
helm:
  valueFiles:
    - values.yaml
    - values-staging.yaml
```

Files are merged in order — later files override earlier ones.

### 3.3 parameters (--set equivalents)

Override individual values, equivalent to `helm install --set`:

```yaml
helm:
  parameters:
    - name: replicaCount
      value: "3"
    - name: image.tag
      value: v2.1.0
    - name: service.type
      value: LoadBalancer
```

### 3.4 fileParameters

Inject file contents as values, equivalent to `helm install --set-file`:

```yaml
helm:
  fileParameters:
    - name: config
      path: configs/app-config.json
```

### 3.5 Precedence Order

```
values.yaml (from chart) < valueFiles < values (inline) < parameters
```

`parameters` has the highest precedence and always wins.

### 3.6 Values from External Git Repos (Multi-Source)

Argo CD 2.6+ supports multi-source Applications. You can pull the chart from one source and values from another:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: my-app
  namespace: argocd
spec:
  project: default
  sources:
    - repoURL: https://charts.bitnami.com/bitnami
      chart: nginx
      targetRevision: 15.4.0
      helm:
        valueFiles:
          - $values/envs/production/values.yaml    # reference to the other source
    - repoURL: https://github.com/example/config-repo.git
      targetRevision: main
      ref: values                                   # named reference
  destination:
    server: https://kubernetes.default.svc
    namespace: nginx
```

This pattern keeps the chart in a Helm repo and environment-specific values in a separate Git repo.

---

## 4. Helm Hooks vs Argo CD Hooks

Helm and Argo CD both have the concept of hooks, but they work differently and can conflict.

### 4.1 Helm Hooks

Helm hooks use the `helm.sh/hook` annotation:

```yaml
metadata:
  annotations:
    "helm.sh/hook": pre-install,pre-upgrade
    "helm.sh/hook-weight": "-5"
    "helm.sh/hook-delete-policy": before-hook-creation
```

### 4.2 How Argo CD Handles Helm Hooks

Because Argo CD uses `helm template` (not `helm install`), Helm hooks are rendered as regular resources. By default, Argo CD maps Helm hooks to Argo CD hooks:

| Helm Hook | Argo CD Mapping |
|-----------|----------------|
| `pre-install`, `pre-upgrade` | `PreSync` |
| `post-install`, `post-upgrade` | `PostSync` |
| `pre-delete` | `PreSync` (on delete) |
| `crd-install` | `PreSync` |
| `test` | Skipped |

### 4.3 Disabling Helm Hook Mapping

If the automatic mapping causes problems, disable it:

```yaml
helm:
  skipCrds: false
  values: |
    ...
```

Or set the resource to be treated as a regular resource:

```yaml
metadata:
  annotations:
    argocd.argoproj.io/hook: Skip    # Argo CD will ignore this during sync
```

### 4.4 Recommendation

For applications managed by Argo CD, prefer **Argo CD hook annotations** over Helm hook annotations. This gives you consistent behavior regardless of the manifest source (Helm, Kustomize, or plain YAML).

```yaml
metadata:
  annotations:
    argocd.argoproj.io/hook: PreSync
    argocd.argoproj.io/hook-delete-policy: BeforeHookCreation
```

---

## 5. ApplicationSet for Multiple Clusters and Environments

`ApplicationSet` is an Argo CD controller that generates multiple `Application` resources from a single template using **generators**.

### 5.1 Why ApplicationSet?

Instead of writing one Application YAML per environment or cluster, you write a single `ApplicationSet` that generates all of them. This is especially useful for:

- Deploying the same application to **multiple clusters** (dev, staging, prod).
- Deploying the same chart with **different values per environment**.
- Generating applications from a **Git directory structure**.
- Creating applications from an **external list** or **pull request**.

### 5.2 List Generator

Generate applications from an explicit list:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: nginx-multi-env
  namespace: argocd
spec:
  generators:
    - list:
        elements:
          - env: dev
            namespace: nginx-dev
            values_file: values-dev.yaml
            replicas: "1"
          - env: staging
            namespace: nginx-staging
            values_file: values-staging.yaml
            replicas: "2"
          - env: prod
            namespace: nginx-prod
            values_file: values-prod.yaml
            replicas: "5"
  template:
    metadata:
      name: 'nginx-{{env}}'
    spec:
      project: default
      source:
        repoURL: https://github.com/example/gitops-repo.git
        targetRevision: main
        path: charts/nginx
        helm:
          valueFiles:
            - '{{values_file}}'
          parameters:
            - name: replicaCount
              value: '{{replicas}}'
      destination:
        server: https://kubernetes.default.svc
        namespace: '{{namespace}}'
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
        syncOptions:
          - CreateNamespace=true
```

This generates three Applications: `nginx-dev`, `nginx-staging`, and `nginx-prod`.

### 5.3 Git Directory Generator

Generate one application per directory in a Git repo:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: cluster-addons
  namespace: argocd
spec:
  generators:
    - git:
        repoURL: https://github.com/example/gitops-repo.git
        revision: main
        directories:
          - path: addons/*       # one app per directory under addons/
  template:
    metadata:
      name: '{{path.basename}}'
    spec:
      project: default
      source:
        repoURL: https://github.com/example/gitops-repo.git
        targetRevision: main
        path: '{{path}}'
      destination:
        server: https://kubernetes.default.svc
        namespace: '{{path.basename}}'
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
        syncOptions:
          - CreateNamespace=true
```

If the repo has `addons/prometheus/`, `addons/grafana/`, and `addons/cert-manager/`, this generates three Applications automatically.

### 5.4 Cluster Generator

Generate one application per registered Argo CD cluster:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: monitoring
  namespace: argocd
spec:
  generators:
    - clusters: {}       # all registered clusters
  template:
    metadata:
      name: 'monitoring-{{name}}'
    spec:
      project: default
      source:
        repoURL: https://github.com/example/gitops-repo.git
        targetRevision: main
        path: monitoring
      destination:
        server: '{{server}}'
        namespace: monitoring
```

### 5.5 Matrix and Merge Generators

Combine multiple generators:

```yaml
generators:
  - matrix:
      generators:
        - git:
            repoURL: https://github.com/example/gitops-repo.git
            revision: main
            directories:
              - path: apps/*
        - clusters: {}
```

This creates one application per directory per cluster.

### 5.6 Pull Request Generator

Generate preview applications from open pull requests:

```yaml
generators:
  - pullRequest:
      github:
        owner: example
        repo: my-app
        labels:
          - preview
      requeueAfterSeconds: 60
template:
  metadata:
    name: 'preview-{{number}}'
  spec:
    source:
      targetRevision: '{{head_sha}}'
      path: k8s
    destination:
      namespace: 'preview-{{number}}'
```

---

## 6. Helm Chart Dependencies

When a chart has dependencies defined in `Chart.yaml`, Argo CD resolves them automatically:

```yaml
# Chart.yaml
apiVersion: v2
name: my-app
version: 1.0.0
dependencies:
  - name: postgresql
    version: 12.1.0
    repository: https://charts.bitnami.com/bitnami
  - name: redis
    version: 17.0.0
    repository: https://charts.bitnami.com/bitnami
```

Argo CD runs `helm dependency build` before `helm template`, so sub-charts are included in the rendered output.

---

## 7. Practical Tips

### Pin chart versions

Always specify a `targetRevision` (chart version) rather than using a range or `*`. This ensures reproducible deployments.

### Use `values` for small overrides, `valueFiles` for large configs

Inline `values` is easy to read for a few settings. For full environment configurations, use separate values files in Git.

### Avoid mixing Helm hooks and Argo CD hooks

Pick one approach. If the chart is managed exclusively by Argo CD, convert Helm hooks to Argo CD hooks.

### Use ApplicationSet for scale

Once you have more than three environments or clusters, switch from individual Application manifests to ApplicationSet.

### Test chart rendering locally

Before committing, verify the rendered output:

```bash
helm template my-release ./charts/my-app \
  -f values.yaml \
  -f values-production.yaml \
  --namespace my-app
```

---

## 8. Knowledge Check

1. Why does Argo CD use `helm template` instead of `helm install`?
2. What is the difference between specifying a chart from a Helm repo vs. a Git repo?
3. You want to deploy nginx with `replicaCount=5` but the chart's default `values.yaml` says `1`. Show two ways to override this in the Application spec.
4. A Helm chart has a `pre-install` hook Job. How does Argo CD treat this resource?
5. Write an ApplicationSet that deploys the same Helm chart to three environments (dev, staging, prod) with different replica counts.

---

## 9. Summary

- Argo CD renders Helm charts with `helm template`, giving it full control over every resource and eliminating Helm release state.
- Charts can be sourced from Helm repositories, Git repositories, or OCI registries.
- Values can be overridden via inline `values`, `valueFiles`, `parameters`, or multi-source Applications.
- Helm hooks are mapped to Argo CD hooks automatically, but Argo CD-native hooks are preferred for consistency.
- `ApplicationSet` is the recommended way to deploy Helm charts across multiple clusters or environments using generators (list, Git directory, cluster, matrix, pull request).

---

**Previous lesson:** [Lesson 3 — ArgoCD Applications](03-argocd-applications.md)  
**Next lesson:** [Lesson 5 — ArgoCD with Kustomize](05-argocd-with-kustomize.md)
