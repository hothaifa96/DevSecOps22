# Lesson 5: ArgoCD with Kustomize

## Learning Objectives

By the end of this lesson you will be able to:

- Explain what Kustomize is and how it differs from Helm.
- Describe how Argo CD detects and renders Kustomize-based applications.
- Structure a Kustomize project with a base and overlays for multiple environments.
- Override images, replicas, labels, and configuration per environment.
- Manage configurations across multiple clusters using Kustomize and Argo CD together.

---

## 1. What is Kustomize?

Kustomize is a built-in Kubernetes configuration management tool (shipped with `kubectl` since v1.14). It lets you customize raw YAML manifests without modifying the originals by using **patches** and **overlays**.

### 1.1 Key Concepts

| Concept | Description |
|---------|-------------|
| **Base** | A set of original, reusable Kubernetes manifests. |
| **Overlay** | A layer that modifies the base for a specific purpose (environment, cluster, team). |
| **kustomization.yaml** | The file that declares which resources to include, which patches to apply, and which transformations to run. |
| **Patch** | A partial YAML document that modifies specific fields in a base resource. |
| **Transformer** | A built-in operation like `namePrefix`, `commonLabels`, `images`, or `replicas`. |

### 1.2 Kustomize vs Helm

| Aspect | Kustomize | Helm |
|--------|-----------|------|
| **Approach** | Patch-based overlays on raw YAML | Template engine with Go templates |
| **Learning curve** | Low — plain YAML, no templating language | Higher — Go template syntax |
| **Parameterization** | Limited (images, replicas, patches) | Full (any value can be a template variable) |
| **Reusability** | Bases + overlays | Charts + values files |
| **Ecosystem** | Built into kubectl | Huge chart ecosystem (Artifact Hub) |
| **Best for** | Internal apps with simple variations per env | Third-party apps, complex parameterization |

### 1.3 When to Use Kustomize with Argo CD

- Your team writes its own Kubernetes manifests and needs to vary them per environment.
- You want to avoid a templating language and keep manifests as plain, readable YAML.
- You are deploying to multiple environments (dev, staging, prod) with small differences (image tag, replica count, resource limits).
- You want to combine Kustomize with upstream manifests (e.g., patching a vendor's YAML without forking it).

---

## 2. How Argo CD Uses Kustomize

Argo CD automatically detects a Kustomize project when the source path contains a `kustomization.yaml` (or `kustomization.yml` or `Kustomization`) file.

When detected, Argo CD runs `kustomize build` on the specified path and applies the resulting manifests.

### 2.1 Minimal Application

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: my-app-dev
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/example/gitops-repo.git
    targetRevision: main
    path: overlays/dev            # must contain kustomization.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: my-app-dev
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

No special configuration is needed — Argo CD detects the `kustomization.yaml` and runs Kustomize automatically.

### 2.2 Overriding Kustomize Settings from Argo CD

You can override certain Kustomize parameters directly in the Application spec:

```yaml
spec:
  source:
    path: overlays/dev
    kustomize:
      namePrefix: dev-
      nameSuffix: -v2
      commonLabels:
        environment: dev
        managed-by: argocd
      commonAnnotations:
        team: platform
      images:
        - myapp=myregistry.io/myapp:v2.0.0
      replicas:
        - name: my-deployment
          count: 3
```

These overrides are applied on top of whatever is already in the `kustomization.yaml` file.

---

## 3. Kustomize Project Structure

### 3.1 Base and Overlays

The standard Kustomize directory layout uses a **base** (shared resources) and **overlays** (per-environment customizations):

```
gitops-repo/
  base/
    kustomization.yaml
    deployment.yaml
    service.yaml
    configmap.yaml
  overlays/
    dev/
      kustomization.yaml
      patch-replicas.yaml
    staging/
      kustomization.yaml
      patch-replicas.yaml
      patch-resources.yaml
    prod/
      kustomization.yaml
      patch-replicas.yaml
      patch-resources.yaml
      patch-hpa.yaml
```

### 3.2 The Base

The base contains the canonical Kubernetes manifests with default values.

**base/kustomization.yaml:**

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - deployment.yaml
  - service.yaml
  - configmap.yaml
```

**base/deployment.yaml:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: web-app
  template:
    metadata:
      labels:
        app: web-app
    spec:
      containers:
        - name: web-app
          image: myregistry.io/web-app:latest
          ports:
            - containerPort: 8080
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: 200m
              memory: 256Mi
          envFrom:
            - configMapRef:
                name: web-app-config
```

**base/service.yaml:**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-app
spec:
  selector:
    app: web-app
  ports:
    - port: 80
      targetPort: 8080
  type: ClusterIP
```

**base/configmap.yaml:**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: web-app-config
data:
  LOG_LEVEL: "info"
  DB_HOST: "localhost"
  DB_PORT: "5432"
```

### 3.3 The Dev Overlay

The dev overlay inherits the base and applies minimal changes.

**overlays/dev/kustomization.yaml:**

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../../base

namePrefix: dev-

commonLabels:
  environment: dev

images:
  - name: myregistry.io/web-app
    newTag: dev-latest

patches:
  - path: patch-replicas.yaml
```

**overlays/dev/patch-replicas.yaml:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
spec:
  replicas: 1
```

### 3.4 The Staging Overlay

**overlays/staging/kustomization.yaml:**

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../../base

namePrefix: staging-

commonLabels:
  environment: staging

images:
  - name: myregistry.io/web-app
    newTag: v1.2.0-rc1

patches:
  - path: patch-replicas.yaml
  - path: patch-resources.yaml
```

**overlays/staging/patch-replicas.yaml:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
spec:
  replicas: 2
```

**overlays/staging/patch-resources.yaml:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
spec:
  template:
    spec:
      containers:
        - name: web-app
          resources:
            requests:
              cpu: 200m
              memory: 256Mi
            limits:
              cpu: 500m
              memory: 512Mi
```

### 3.5 The Production Overlay

**overlays/prod/kustomization.yaml:**

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../../base
  - hpa.yaml

namePrefix: prod-

commonLabels:
  environment: prod

images:
  - name: myregistry.io/web-app
    newTag: v1.2.0

patches:
  - path: patch-replicas.yaml
  - path: patch-resources.yaml

configMapGenerator:
  - name: web-app-config
    behavior: merge
    literals:
      - LOG_LEVEL=warn
      - DB_HOST=prod-db.internal
      - DB_PORT=5432
```

**overlays/prod/patch-replicas.yaml:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
spec:
  replicas: 5
```

**overlays/prod/hpa.yaml:**

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: web-app
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: prod-web-app
  minReplicas: 5
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

---

## 4. Kustomize Features Commonly Used with Argo CD

### 4.1 Image Overrides

The `images` transformer in `kustomization.yaml` changes the image name, tag, or digest without modifying the base:

```yaml
images:
  - name: myregistry.io/web-app         # match this image
    newName: myregistry.io/web-app       # optionally change the registry/name
    newTag: v2.0.0                       # set the new tag
    # or use digest:
    # digest: sha256:abc123...
```

Argo CD can also override images from the Application spec:

```yaml
kustomize:
  images:
    - myregistry.io/web-app=myregistry.io/web-app:v2.0.0
```

This is useful when a CI pipeline updates the image tag without modifying the Kustomize files.

### 4.2 Replicas

Override replica count without a patch:

```yaml
# In kustomization.yaml
replicas:
  - name: web-app
    count: 3
```

### 4.3 ConfigMap and Secret Generators

Kustomize can generate ConfigMaps and Secrets with content-based hashes, triggering rolling updates when the content changes:

```yaml
configMapGenerator:
  - name: app-config
    literals:
      - KEY=value
    files:
      - config.json

secretGenerator:
  - name: db-creds
    literals:
      - username=admin
      - password=supersecret
    type: Opaque
```

The generated name will be something like `app-config-abc123`, and all references in Deployments are automatically updated.

### 4.4 Strategic Merge Patches vs JSON Patches

**Strategic Merge Patch** (most common):

```yaml
patches:
  - path: patch-replicas.yaml
```

The patch file is a partial resource that merges into the base.

**JSON 6902 Patch:**

```yaml
patches:
  - target:
      kind: Deployment
      name: web-app
    patch: |
      - op: replace
        path: /spec/replicas
        value: 5
      - op: add
        path: /metadata/annotations/patched-by
        value: kustomize
```

JSON patches are more precise and can add, remove, or replace specific fields.

### 4.5 Components (Reusable Kustomize Modules)

Kustomize components let you share a set of patches across multiple overlays:

```yaml
# components/monitoring/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1alpha1
kind: Component

patches:
  - target:
      kind: Deployment
    patch: |
      - op: add
        path: /spec/template/metadata/annotations/prometheus.io~1scrape
        value: "true"
```

Use in an overlay:

```yaml
# overlays/prod/kustomization.yaml
components:
  - ../../components/monitoring
```

---

## 5. Managing Configurations Across Clusters

### 5.1 One Application Per Overlay

The simplest approach: create one Argo CD Application per environment overlay.

```yaml
# dev-app.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: web-app-dev
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/example/gitops-repo.git
    targetRevision: main
    path: overlays/dev
  destination:
    server: https://kubernetes.default.svc
    namespace: web-app-dev
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
---
# prod-app.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: web-app-prod
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/example/gitops-repo.git
    targetRevision: main
    path: overlays/prod
  destination:
    server: https://prod-cluster-api.example.com
    namespace: web-app-prod
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

### 5.2 ApplicationSet with Kustomize Overlays

Use an ApplicationSet to generate one Application per overlay directory:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: web-app
  namespace: argocd
spec:
  generators:
    - git:
        repoURL: https://github.com/example/gitops-repo.git
        revision: main
        directories:
          - path: overlays/*
  template:
    metadata:
      name: 'web-app-{{path.basename}}'
    spec:
      project: default
      source:
        repoURL: https://github.com/example/gitops-repo.git
        targetRevision: main
        path: '{{path}}'
      destination:
        server: https://kubernetes.default.svc
        namespace: 'web-app-{{path.basename}}'
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
        syncOptions:
          - CreateNamespace=true
```

Adding a new environment is as simple as creating a new overlay directory.

### 5.3 Multi-Cluster with Kustomize

For different clusters, combine the cluster generator with Kustomize overlays:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: web-app-multi-cluster
  namespace: argocd
spec:
  generators:
    - matrix:
        generators:
          - clusters:
              selector:
                matchLabels:
                  tier: production
          - list:
              elements:
                - overlay: prod
  template:
    metadata:
      name: 'web-app-{{name}}'
    spec:
      project: default
      source:
        repoURL: https://github.com/example/gitops-repo.git
        targetRevision: main
        path: 'overlays/{{overlay}}'
      destination:
        server: '{{server}}'
        namespace: web-app
```

---

## 6. Testing Kustomize Locally

Always validate your Kustomize output before pushing to Git:

```bash
# Build and inspect the rendered output
kustomize build overlays/dev

# Or use kubectl
kubectl kustomize overlays/dev

# Dry-run against the cluster
kubectl apply -k overlays/dev --dry-run=server

# Diff against the live cluster
kubectl diff -k overlays/dev
```

---

## 7. Common Pitfalls

### Resource name collisions

If you use `namePrefix` in an overlay, make sure all references (Service selectors, ConfigMap refs) are updated. Kustomize handles most cases automatically, but external references (e.g., in application config) need manual attention.

### Hash suffix on ConfigMaps/Secrets

Kustomize appends a content hash to generated ConfigMaps and Secrets. If you reference them from outside Kustomize-managed resources, the names will not match. Use `generatorOptions: { disableNameSuffixHash: true }` when necessary.

### Overlay dependency on base path

Overlays reference the base with a relative path (`../../base`). If you restructure the repository, update these paths or the build will break.

### Large overlays

If an overlay has extensive patches, it may be clearer to duplicate the base resources. Kustomize is best for small, targeted changes.

---

## 8. Knowledge Check

1. How does Argo CD detect that a source path should be built with Kustomize?
2. What is the difference between a base and an overlay?
3. You need to change the image tag from `latest` to `v3.0.0` for production without modifying the base. How do you do this?
4. Write a `kustomization.yaml` for a production overlay that uses the base, adds a `prod-` prefix, and sets 5 replicas.
5. How can you use an ApplicationSet to generate one Argo CD Application per Kustomize overlay directory?

---

## 9. Summary

- Kustomize customizes Kubernetes manifests through overlays and patches, without templates or a new DSL.
- Argo CD auto-detects Kustomize when a `kustomization.yaml` is present and renders manifests with `kustomize build`.
- The base + overlay pattern is the standard way to manage environment-specific configurations (dev, staging, prod).
- Common transformations include image overrides, replica counts, name prefixes, labels, and ConfigMap/Secret generation.
- ApplicationSet combined with the Git directory generator makes multi-environment Kustomize management scalable and automatic.

---

**Previous lesson:** [Lesson 4 — ArgoCD with Helm](04-argocd-with-helm.md)  
**Next lesson:** [Lesson 6 — GitOps Best Practices](06-gitops-best-practices.md)
