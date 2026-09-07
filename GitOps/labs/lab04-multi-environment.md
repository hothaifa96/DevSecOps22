# Lab 04: Multi-Environment Deployment with Kustomize and Argo CD

## Objective

Set up dev, staging, and production environments for a web application using Kustomize overlays, each managed by its own Argo CD Application. You will see how the same base manifests produce different configurations per environment.

## Prerequisites

- Completed **Lab 01** (Argo CD installed and running).
- `kubectl` and `argocd` CLI configured.
- Port-forward to Argo CD active.
- Your fork of `argocd-example-apps` from Lab 02.

## Estimated Time

30-40 minutes

---

## Step 1: Create the Kustomize Directory Structure

Navigate to your fork of `argocd-example-apps`:

```bash
cd argocd-example-apps
```

Create the full directory structure:

```bash
mkdir -p kustomize-app/base
mkdir -p kustomize-app/overlays/dev
mkdir -p kustomize-app/overlays/staging
mkdir -p kustomize-app/overlays/prod
```

---

## Step 2: Create the Base Manifests

### 2.1 Deployment

```bash
cat > kustomize-app/base/deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
  labels:
    app: web-app
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
          image: nginx:1.25
          ports:
            - containerPort: 80
          resources:
            requests:
              cpu: 50m
              memory: 64Mi
            limits:
              cpu: 100m
              memory: 128Mi
          envFrom:
            - configMapRef:
                name: web-app-config
          readinessProbe:
            httpGet:
              path: /
              port: 80
            initialDelaySeconds: 5
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /
              port: 80
            initialDelaySeconds: 10
            periodSeconds: 30
EOF
```

### 2.2 Service

```bash
cat > kustomize-app/base/service.yaml << 'EOF'
apiVersion: v1
kind: Service
metadata:
  name: web-app
  labels:
    app: web-app
spec:
  selector:
    app: web-app
  ports:
    - port: 80
      targetPort: 80
      protocol: TCP
  type: ClusterIP
EOF
```

### 2.3 ConfigMap

```bash
cat > kustomize-app/base/configmap.yaml << 'EOF'
apiVersion: v1
kind: ConfigMap
metadata:
  name: web-app-config
data:
  APP_NAME: "Web App"
  LOG_LEVEL: "info"
  ENVIRONMENT: "default"
EOF
```

### 2.4 Base kustomization.yaml

```bash
cat > kustomize-app/base/kustomization.yaml << 'EOF'
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - deployment.yaml
  - service.yaml
  - configmap.yaml

commonLabels:
  managed-by: argocd
EOF
```

### 2.5 Verify the base renders correctly

```bash
kubectl kustomize kustomize-app/base/
```

You should see the Deployment, Service, and ConfigMap with the `managed-by: argocd` label added.

---

## Step 3: Create the Dev Overlay

### 3.1 Dev kustomization.yaml

```bash
cat > kustomize-app/overlays/dev/kustomization.yaml << 'EOF'
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../../base

namePrefix: dev-

commonLabels:
  environment: dev

commonAnnotations:
  team: development

images:
  - name: nginx
    newTag: "1.25-alpine"

replicas:
  - name: web-app
    count: 1

patches:
  - target:
      kind: ConfigMap
      name: web-app-config
    patch: |
      - op: replace
        path: /data/ENVIRONMENT
        value: "development"
      - op: replace
        path: /data/LOG_LEVEL
        value: "debug"
      - op: replace
        path: /data/APP_NAME
        value: "Web App (Dev)"
EOF
```

### 3.2 Verify

```bash
kubectl kustomize kustomize-app/overlays/dev/
```

**Check that:**

- All resource names are prefixed with `dev-`.
- The `environment: dev` label is present.
- The image is `nginx:1.25-alpine`.
- The ConfigMap has `ENVIRONMENT: development` and `LOG_LEVEL: debug`.

---

## Step 4: Create the Staging Overlay

```bash
cat > kustomize-app/overlays/staging/kustomization.yaml << 'EOF'
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../../base

namePrefix: staging-

commonLabels:
  environment: staging

commonAnnotations:
  team: qa

images:
  - name: nginx
    newTag: "1.25"

replicas:
  - name: web-app
    count: 2

patches:
  - target:
      kind: ConfigMap
      name: web-app-config
    patch: |
      - op: replace
        path: /data/ENVIRONMENT
        value: "staging"
      - op: replace
        path: /data/LOG_LEVEL
        value: "info"
      - op: replace
        path: /data/APP_NAME
        value: "Web App (Staging)"
  - target:
      kind: Deployment
      name: web-app
    patch: |
      - op: replace
        path: /spec/template/spec/containers/0/resources/requests/cpu
        value: "100m"
      - op: replace
        path: /spec/template/spec/containers/0/resources/requests/memory
        value: "128Mi"
      - op: replace
        path: /spec/template/spec/containers/0/resources/limits/cpu
        value: "250m"
      - op: replace
        path: /spec/template/spec/containers/0/resources/limits/memory
        value: "256Mi"
EOF
```

Verify:

```bash
kubectl kustomize kustomize-app/overlays/staging/
```

**Check that:**

- Names prefixed with `staging-`.
- 2 replicas.
- Increased resource limits.

---

## Step 5: Create the Production Overlay

### 5.1 Production kustomization.yaml

```bash
cat > kustomize-app/overlays/prod/kustomization.yaml << 'EOF'
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../../base
  - hpa.yaml

namePrefix: prod-

commonLabels:
  environment: prod

commonAnnotations:
  team: platform

images:
  - name: nginx
    newTag: "1.25"

replicas:
  - name: web-app
    count: 3

patches:
  - target:
      kind: ConfigMap
      name: web-app-config
    patch: |
      - op: replace
        path: /data/ENVIRONMENT
        value: "production"
      - op: replace
        path: /data/LOG_LEVEL
        value: "warn"
      - op: replace
        path: /data/APP_NAME
        value: "Web App (Production)"
  - target:
      kind: Deployment
      name: web-app
    patch: |
      - op: replace
        path: /spec/template/spec/containers/0/resources/requests/cpu
        value: "200m"
      - op: replace
        path: /spec/template/spec/containers/0/resources/requests/memory
        value: "256Mi"
      - op: replace
        path: /spec/template/spec/containers/0/resources/limits/cpu
        value: "500m"
      - op: replace
        path: /spec/template/spec/containers/0/resources/limits/memory
        value: "512Mi"
EOF
```

### 5.2 Production HPA

```bash
cat > kustomize-app/overlays/prod/hpa.yaml << 'EOF'
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: prod-web-app
  labels:
    app: web-app
    environment: prod
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: prod-web-app
  minReplicas: 3
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
EOF
```

Verify:

```bash
kubectl kustomize kustomize-app/overlays/prod/
```

**Check that:**

- Names prefixed with `prod-`.
- 3 replicas.
- HPA is included.
- Higher resource limits.

---

## Step 6: Push Everything to Git

```bash
git add kustomize-app/
git commit -m "Add Kustomize base and overlays for dev/staging/prod"
git push origin main
```

---

## Step 7: Create Argo CD Applications for Each Environment

### 7.1 Dev Application

```bash
argocd app create web-app-dev \
  --repo https://github.com/<your-username>/argocd-example-apps.git \
  --path kustomize-app/overlays/dev \
  --dest-server https://kubernetes.default.svc \
  --dest-namespace web-app-dev \
  --sync-policy automated \
  --auto-prune \
  --self-heal \
  --sync-option CreateNamespace=true
```

### 7.2 Staging Application

```bash
argocd app create web-app-staging \
  --repo https://github.com/<your-username>/argocd-example-apps.git \
  --path kustomize-app/overlays/staging \
  --dest-server https://kubernetes.default.svc \
  --dest-namespace web-app-staging \
  --sync-policy automated \
  --auto-prune \
  --self-heal \
  --sync-option CreateNamespace=true
```

### 7.3 Production Application

```bash
argocd app create web-app-prod \
  --repo https://github.com/<your-username>/argocd-example-apps.git \
  --path kustomize-app/overlays/prod \
  --dest-server https://kubernetes.default.svc \
  --dest-namespace web-app-prod \
  --sync-policy automated \
  --auto-prune \
  --self-heal \
  --sync-option CreateNamespace=true
```

> **Replace** `<your-username>` with your actual GitHub username in all three commands.

### 7.4 Wait for all applications to sync

```bash
argocd app wait web-app-dev --health --timeout 120
argocd app wait web-app-staging --health --timeout 120
argocd app wait web-app-prod --health --timeout 120
```

---

## Step 8: Verify All Environments

### 8.1 List all applications

```bash
argocd app list
```

**Expected output:**

```
NAME              CLUSTER                         NAMESPACE        STATUS  HEALTH   SYNCPOLICY
web-app-dev       https://kubernetes.default.svc  web-app-dev      Synced  Healthy  Auto-Prune
web-app-staging   https://kubernetes.default.svc  web-app-staging  Synced  Healthy  Auto-Prune
web-app-prod      https://kubernetes.default.svc  web-app-prod     Synced  Healthy  Auto-Prune
```

### 8.2 Compare environments

**Dev:**

```bash
kubectl get deployment -n web-app-dev
kubectl get configmap dev-web-app-config -n web-app-dev -o jsonpath='{.data}' | python3 -m json.tool
```

Expected: 1 replica, LOG_LEVEL=debug, ENVIRONMENT=development

**Staging:**

```bash
kubectl get deployment -n web-app-staging
kubectl get configmap staging-web-app-config -n web-app-staging -o jsonpath='{.data}' | python3 -m json.tool
```

Expected: 2 replicas, LOG_LEVEL=info, ENVIRONMENT=staging

**Production:**

```bash
kubectl get deployment -n web-app-prod
kubectl get hpa -n web-app-prod
kubectl get configmap prod-web-app-config -n web-app-prod -o jsonpath='{.data}' | python3 -m json.tool
```

Expected: 3 replicas, HPA present, LOG_LEVEL=warn, ENVIRONMENT=production

### 8.3 View in the UI

Open the Argo CD UI. You should see three application tiles, each with a green **Synced** and **Healthy** status. Click on each to compare the resource trees.

---

## Step 9: Simulate a Promotion Workflow

### 9.1 Update the image tag for dev

Edit `kustomize-app/overlays/dev/kustomization.yaml` and change the image tag:

```yaml
images:
  - name: nginx
    newTag: "1.25.3-alpine"
```

```bash
git add kustomize-app/overlays/dev/kustomization.yaml
git commit -m "Update dev image to 1.25.3-alpine"
git push origin main
```

### 9.2 Verify dev updated

```bash
argocd app get web-app-dev --refresh
kubectl get deployment dev-web-app -n web-app-dev -o jsonpath='{.spec.template.spec.containers[0].image}'; echo
```

**Expected:** `nginx:1.25.3-alpine`

### 9.3 Promote to staging

After validating in dev, update the staging overlay with the same tag:

Edit `kustomize-app/overlays/staging/kustomization.yaml`:

```yaml
images:
  - name: nginx
    newTag: "1.25.3"
```

```bash
git add kustomize-app/overlays/staging/kustomization.yaml
git commit -m "Promote image 1.25.3 to staging"
git push origin main
```

### 9.4 Promote to production

After validating in staging, update the production overlay:

Edit `kustomize-app/overlays/prod/kustomization.yaml`:

```yaml
images:
  - name: nginx
    newTag: "1.25.3"
```

```bash
git add kustomize-app/overlays/prod/kustomization.yaml
git commit -m "Promote image 1.25.3 to production"
git push origin main
```

### 9.5 Verify all environments

```bash
for env in dev staging prod; do
  echo "=== web-app-$env ==="
  kubectl get deployment -n "web-app-$env" -o jsonpath='{.items[0].spec.template.spec.containers[0].image}'
  echo
done
```

---

## Step 10: Test a Base Change (Cross-Environment)

### 10.1 Add a label to the base

Edit `kustomize-app/base/kustomization.yaml` to add a common annotation:

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - deployment.yaml
  - service.yaml
  - configmap.yaml

commonLabels:
  managed-by: argocd
  app-version: "2.0"
```

```bash
git add kustomize-app/base/kustomization.yaml
git commit -m "Add app-version label to base"
git push origin main
```

### 10.2 Verify all environments updated

```bash
for env in dev staging prod; do
  echo "=== web-app-$env ==="
  argocd app get "web-app-$env" --refresh | grep -i sync
  echo
done
```

All three environments should show the new label after Argo CD syncs.

---

## Cleanup

```bash
argocd app delete web-app-dev --yes
argocd app delete web-app-staging --yes
argocd app delete web-app-prod --yes

kubectl delete namespace web-app-dev --ignore-not-found
kubectl delete namespace web-app-staging --ignore-not-found
kubectl delete namespace web-app-prod --ignore-not-found
```

> **Note:** Keep the Argo CD installation and your fork for Lab 05.

---

## Summary

In this lab you:

1. Created a Kustomize project with a shared base and three overlays (dev, staging, prod).
2. Each overlay customized replicas, resources, image tags, labels, and configuration.
3. Production included an additional HPA resource.
4. Created three Argo CD Applications, one per environment.
5. Simulated a promotion workflow: dev -> staging -> prod.
6. Made a base change and observed it propagate to all environments.

**Key takeaway:** Kustomize overlays combined with Argo CD provide a clean, template-free way to manage multiple environments from a single set of base manifests.

---

**Previous lab:** [Lab 03 — Helm with ArgoCD](lab03-helm-with-argocd.md)  
**Next lab:** [Lab 05 — App-of-Apps Pattern](lab05-app-of-apps.md)
