# Lab 05: Implement the App-of-Apps Pattern

## Objective

Implement the App-of-Apps pattern to manage multiple applications declaratively from a single root Argo CD Application. You will create a root app that bootstraps three child applications, then add and remove applications by simply committing YAML files to Git.

## Prerequisites

- Completed **Lab 01** (Argo CD installed and running).
- `kubectl` and `argocd` CLI configured.
- Port-forward to Argo CD active.
- Your fork of `argocd-example-apps`.

## Estimated Time

30-40 minutes

---

## Step 1: Plan the Repository Structure

We will create the following structure in your fork:

```
argocd-example-apps/
  app-of-apps/
    root-app.yaml                 # Root Application (applied manually once)
    apps/                         # Directory containing child Application manifests
      guestbook-app.yaml          # Child: guestbook
      nginx-app.yaml              # Child: nginx
      redis-app.yaml              # Child: redis
    manifests/                    # Actual workload manifests
      guestbook/
        deployment.yaml
        service.yaml
      nginx/
        deployment.yaml
        service.yaml
      redis/
        deployment.yaml
        service.yaml
```

---

## Step 2: Create the Workload Manifests

Navigate to your fork:

```bash
cd argocd-example-apps
```

Create the directory structure:

```bash
mkdir -p app-of-apps/apps
mkdir -p app-of-apps/manifests/guestbook
mkdir -p app-of-apps/manifests/nginx
mkdir -p app-of-apps/manifests/redis
```

### 2.1 Guestbook manifests

```bash
cat > app-of-apps/manifests/guestbook/deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: guestbook
  labels:
    app: guestbook
spec:
  replicas: 1
  selector:
    matchLabels:
      app: guestbook
  template:
    metadata:
      labels:
        app: guestbook
    spec:
      containers:
        - name: guestbook
          image: gcr.io/heptio-images/ks-guestbook-demo:0.2
          ports:
            - containerPort: 80
          resources:
            requests:
              cpu: 50m
              memory: 64Mi
            limits:
              cpu: 100m
              memory: 128Mi
EOF

cat > app-of-apps/manifests/guestbook/service.yaml << 'EOF'
apiVersion: v1
kind: Service
metadata:
  name: guestbook
spec:
  selector:
    app: guestbook
  ports:
    - port: 80
      targetPort: 80
  type: ClusterIP
EOF
```

### 2.2 NGINX manifests

```bash
cat > app-of-apps/manifests/nginx/deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx
  labels:
    app: nginx
spec:
  replicas: 2
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
        - name: nginx
          image: nginx:1.25-alpine
          ports:
            - containerPort: 80
          resources:
            requests:
              cpu: 50m
              memory: 64Mi
            limits:
              cpu: 100m
              memory: 128Mi
EOF

cat > app-of-apps/manifests/nginx/service.yaml << 'EOF'
apiVersion: v1
kind: Service
metadata:
  name: nginx
spec:
  selector:
    app: nginx
  ports:
    - port: 80
      targetPort: 80
  type: ClusterIP
EOF
```

### 2.3 Redis manifests

```bash
cat > app-of-apps/manifests/redis/deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  labels:
    app: redis
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
        - name: redis
          image: redis:7-alpine
          ports:
            - containerPort: 6379
          resources:
            requests:
              cpu: 50m
              memory: 64Mi
            limits:
              cpu: 100m
              memory: 128Mi
EOF

cat > app-of-apps/manifests/redis/service.yaml << 'EOF'
apiVersion: v1
kind: Service
metadata:
  name: redis
spec:
  selector:
    app: redis
  ports:
    - port: 6379
      targetPort: 6379
  type: ClusterIP
EOF
```

---

## Step 3: Create the Child Application Manifests

These YAML files define Argo CD Applications. They live in the `apps/` directory and are managed by the root app.

> **Important:** Replace `<your-username>` with your actual GitHub username in all files below.

### 3.1 Guestbook Application

```bash
cat > app-of-apps/apps/guestbook-app.yaml << 'EOF'
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: guestbook
  namespace: argocd
  labels:
    app-group: app-of-apps-lab
  finalizers:
    - resources-finalizer.argocd.argoproj.io
spec:
  project: default
  source:
    repoURL: https://github.com/<your-username>/argocd-example-apps.git
    targetRevision: main
    path: app-of-apps/manifests/guestbook
  destination:
    server: https://kubernetes.default.svc
    namespace: guestbook
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
EOF
```

### 3.2 NGINX Application

```bash
cat > app-of-apps/apps/nginx-app.yaml << 'EOF'
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: nginx
  namespace: argocd
  labels:
    app-group: app-of-apps-lab
  finalizers:
    - resources-finalizer.argocd.argoproj.io
spec:
  project: default
  source:
    repoURL: https://github.com/<your-username>/argocd-example-apps.git
    targetRevision: main
    path: app-of-apps/manifests/nginx
  destination:
    server: https://kubernetes.default.svc
    namespace: nginx
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
EOF
```

### 3.3 Redis Application

```bash
cat > app-of-apps/apps/redis-app.yaml << 'EOF'
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: redis
  namespace: argocd
  labels:
    app-group: app-of-apps-lab
  finalizers:
    - resources-finalizer.argocd.argoproj.io
spec:
  project: default
  source:
    repoURL: https://github.com/<your-username>/argocd-example-apps.git
    targetRevision: main
    path: app-of-apps/manifests/redis
  destination:
    server: https://kubernetes.default.svc
    namespace: redis
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
EOF
```

---

## Step 4: Create the Root Application

The root application points to the `apps/` directory. When synced, it creates all the child Application resources.

```bash
cat > app-of-apps/root-app.yaml << 'EOF'
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: root-app
  namespace: argocd
  labels:
    app-group: app-of-apps-lab
  finalizers:
    - resources-finalizer.argocd.argoproj.io
spec:
  project: default
  source:
    repoURL: https://github.com/<your-username>/argocd-example-apps.git
    targetRevision: main
    path: app-of-apps/apps
  destination:
    server: https://kubernetes.default.svc
    namespace: argocd
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
EOF
```

> **Replace** `<your-username>` with your actual GitHub username.

---

## Step 5: Push to Git

```bash
git add app-of-apps/
git commit -m "Add app-of-apps structure with guestbook, nginx, and redis"
git push origin main
```

---

## Step 6: Deploy the Root Application

Apply **only** the root application. It will bootstrap everything else.

```bash
kubectl apply -f app-of-apps/root-app.yaml
```

---

## Step 7: Watch the Cascade

### 7.1 Watch applications appear

```bash
watch argocd app list
```

Or poll manually:

```bash
argocd app list
```

**Expected output (after a minute or two):**

```
NAME        CLUSTER                         NAMESPACE   PROJECT  STATUS  HEALTH   SYNCPOLICY
root-app    https://kubernetes.default.svc  argocd      default  Synced  Healthy  Auto-Prune
guestbook   https://kubernetes.default.svc  guestbook   default  Synced  Healthy  Auto-Prune
nginx       https://kubernetes.default.svc  nginx       default  Synced  Healthy  Auto-Prune
redis       https://kubernetes.default.svc  redis       default  Synced  Healthy  Auto-Prune
```

### 7.2 Verify the chain of events

1. You applied `root-app` → Argo CD synced the `apps/` directory.
2. Argo CD found three Application manifests and created them.
3. Each child Application started its own reconciliation loop.
4. Each child synced its respective manifests and created the workloads.

### 7.3 Verify workloads in the cluster

```bash
echo "=== Guestbook ==="
kubectl get all -n guestbook

echo "=== NGINX ==="
kubectl get all -n nginx

echo "=== Redis ==="
kubectl get all -n redis
```

### 7.4 View in the UI

Open the Argo CD UI. You should see four applications:

- **root-app** — its resource tree shows three Application CRs.
- **guestbook** — shows Deployment, ReplicaSet, Pod, Service.
- **nginx** — shows Deployment (2 replicas), ReplicaSet, Pods, Service.
- **redis** — shows Deployment, ReplicaSet, Pod, Service.

---

## Step 8: Add a New Application via Git

The power of App-of-Apps: adding a new application is just a Git commit.

### 8.1 Create a httpbin application

Create the workload manifests:

```bash
mkdir -p app-of-apps/manifests/httpbin

cat > app-of-apps/manifests/httpbin/deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: httpbin
  labels:
    app: httpbin
spec:
  replicas: 1
  selector:
    matchLabels:
      app: httpbin
  template:
    metadata:
      labels:
        app: httpbin
    spec:
      containers:
        - name: httpbin
          image: kennethreitz/httpbin:latest
          ports:
            - containerPort: 80
          resources:
            requests:
              cpu: 50m
              memory: 64Mi
            limits:
              cpu: 100m
              memory: 128Mi
EOF

cat > app-of-apps/manifests/httpbin/service.yaml << 'EOF'
apiVersion: v1
kind: Service
metadata:
  name: httpbin
spec:
  selector:
    app: httpbin
  ports:
    - port: 80
      targetPort: 80
  type: ClusterIP
EOF
```

Create the child Application manifest:

```bash
cat > app-of-apps/apps/httpbin-app.yaml << 'EOF'
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: httpbin
  namespace: argocd
  labels:
    app-group: app-of-apps-lab
  finalizers:
    - resources-finalizer.argocd.argoproj.io
spec:
  project: default
  source:
    repoURL: https://github.com/<your-username>/argocd-example-apps.git
    targetRevision: main
    path: app-of-apps/manifests/httpbin
  destination:
    server: https://kubernetes.default.svc
    namespace: httpbin
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
EOF
```

> **Replace** `<your-username>`.

### 8.2 Push the change

```bash
git add app-of-apps/
git commit -m "Add httpbin application to app-of-apps"
git push origin main
```

### 8.3 Watch it appear

```bash
argocd app get root-app --refresh
argocd app list
```

Within a few minutes, you should see a new **httpbin** application appear, sync, and become healthy.

```bash
kubectl get all -n httpbin
```

---

## Step 9: Remove an Application via Git

### 9.1 Remove the redis application

Delete the child Application manifest from Git:

```bash
rm app-of-apps/apps/redis-app.yaml
git add -A
git commit -m "Remove redis from app-of-apps"
git push origin main
```

### 9.2 Watch it disappear

```bash
argocd app get root-app --refresh
argocd app list
```

Because the root app has `prune: true`, Argo CD will:

1. Detect that `redis-app.yaml` is no longer in Git.
2. Delete the `redis` Application from Argo CD.
3. The `resources-finalizer` on the `redis` Application will cascade-delete all resources in the `redis` namespace.

Verify:

```bash
kubectl get all -n redis
```

**Expected:** No resources found (or the namespace itself is gone).

### 9.3 Verify the final state

```bash
argocd app list
```

**Expected:**

```
NAME        CLUSTER                         NAMESPACE   PROJECT  STATUS  HEALTH   SYNCPOLICY
root-app    https://kubernetes.default.svc  argocd      default  Synced  Healthy  Auto-Prune
guestbook   https://kubernetes.default.svc  guestbook   default  Synced  Healthy  Auto-Prune
nginx       https://kubernetes.default.svc  nginx       default  Synced  Healthy  Auto-Prune
httpbin     https://kubernetes.default.svc  httpbin     default  Synced  Healthy  Auto-Prune
```

---

## Step 10: Modify a Child Application's Configuration

### 10.1 Scale nginx to 4 replicas

Edit `app-of-apps/manifests/nginx/deployment.yaml`:

Change `replicas: 2` to `replicas: 4`.

```bash
sed -i'' -e 's/replicas: 2/replicas: 4/' app-of-apps/manifests/nginx/deployment.yaml
git add app-of-apps/manifests/nginx/deployment.yaml
git commit -m "Scale nginx to 4 replicas"
git push origin main
```

### 10.2 Verify

```bash
argocd app get nginx --refresh
kubectl get deployment nginx -n nginx
```

**Expected:** 4 replicas.

Note that the root app's status is unchanged — the root app manages Application CRDs, not the workload manifests. The nginx child app detected the change in its own source path.

---

## Cleanup

Delete the root application. The finalizer will cascade-delete all child applications and their resources:

```bash
argocd app delete root-app --yes
```

Wait a moment, then verify everything is cleaned up:

```bash
argocd app list
kubectl get namespaces | grep -E "guestbook|nginx|httpbin|redis"
```

Clean up any remaining namespaces:

```bash
kubectl delete namespace guestbook nginx httpbin redis --ignore-not-found
```

---

## Challenge Exercise (Optional)

If you have extra time, try these challenges:

1. **Add sync waves** to the child applications so that redis deploys before guestbook (hint: add the `argocd.argoproj.io/sync-wave` annotation to the Application manifests in `apps/`).

2. **Add an AppProject** that restricts the child applications to specific namespaces. Modify the child Application specs to use the new project.

3. **Convert to ApplicationSet** — rewrite the child applications as a single ApplicationSet with a Git directory generator pointing at `app-of-apps/manifests/*`.

---

## Summary

In this lab you:

1. Created a repository structure for the App-of-Apps pattern with a root app and child Application manifests.
2. Applied a single root Application that bootstrapped three child applications automatically.
3. Added a new application (httpbin) by committing a YAML file — no manual `kubectl` or CLI needed.
4. Removed an application (redis) by deleting its YAML file — Argo CD pruned it and cascade-deleted all resources.
5. Modified a child application's workload manifests and observed the child app sync independently.

**Key takeaway:** The App-of-Apps pattern turns application lifecycle management into Git operations. Adding, removing, and updating applications is done entirely through commits and pull requests.

---

**Previous lab:** [Lab 04 — Multi-Environment with Kustomize](lab04-multi-environment.md)
