# Lab 03: Deploy a Helm Chart with Argo CD

## Objective

Deploy a Helm chart through Argo CD, override values, update the chart version, and observe how Argo CD manages the lifecycle. You will work with both a public Helm repository chart and a chart stored in a Git repository.

## Prerequisites

- Completed **Lab 01** (Argo CD installed and running).
- `kubectl` and `argocd` CLI configured.
- Port-forward to Argo CD active.
- `helm` CLI installed (for local testing).
- Your fork of `argocd-example-apps` from Lab 02 (or fork it now).

## Estimated Time

30-40 minutes

---

## Part A: Deploy a Chart from a Helm Repository

### Step 1: Add the Helm Repository to Argo CD

```bash
argocd repo add https://charts.bitnami.com/bitnami --type helm --name bitnami
```

Verify:

```bash
argocd repo list
```

You should see the Bitnami Helm repo in the list.

---

### Step 2: Create an Application for the NGINX Chart

#### 2.1 Create the Application manifest

Create a file called `nginx-helm-app.yaml`:

```bash
cat > nginx-helm-app.yaml << 'EOF'
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: nginx-helm
  namespace: argocd
  finalizers:
    - resources-finalizer.argocd.argoproj.io
spec:
  project: default
  source:
    repoURL: https://charts.bitnami.com/bitnami
    chart: nginx
    targetRevision: 15.14.0
    helm:
      values: |
        replicaCount: 2
        service:
          type: ClusterIP
        resources:
          requests:
            cpu: 50m
            memory: 64Mi
          limits:
            cpu: 100m
            memory: 128Mi
  destination:
    server: https://kubernetes.default.svc
    namespace: nginx-helm
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
EOF
```

> **Note:** If version `15.14.0` is not available, check available versions with:
> ```bash
> helm search repo bitnami/nginx --versions | head -10
> ```
> And use any recent version.

#### 2.2 Apply the Application

```bash
kubectl apply -f nginx-helm-app.yaml
```

#### 2.3 Watch the sync

```bash
argocd app get nginx-helm --refresh
```

Wait for the sync to complete:

```bash
argocd app wait nginx-helm --health --timeout 120
```

#### 2.4 Verify resources in the cluster

```bash
kubectl get all -n nginx-helm
```

**Expected output:** You should see 2 nginx pods (matching `replicaCount: 2`), a Deployment, a ReplicaSet, and a ClusterIP Service.

#### 2.5 Explore in the UI

Open the Argo CD UI and click on the **nginx-helm** application. Notice:

- The resource tree shows all Helm-rendered resources.
- The source is shown as a Helm chart (not a Git path).
- Click **Parameters** to see the Helm values.

---

### Step 3: Override Values

#### 3.1 Scale up via parameters

```bash
argocd app set nginx-helm --helm-set replicaCount=4
```

#### 3.2 Verify the change

```bash
argocd app sync nginx-helm
argocd app wait nginx-helm --health

kubectl get deployment -n nginx-helm
```

**Expected:** 4 replicas.

#### 3.3 Override via the Application manifest

Edit `nginx-helm-app.yaml` to change the values:

```yaml
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
            cpu: 200m
            memory: 256Mi
```

Apply the updated manifest:

```bash
kubectl apply -f nginx-helm-app.yaml
```

Verify:

```bash
argocd app get nginx-helm --refresh
kubectl get deployment -n nginx-helm
```

**Expected:** 3 replicas with updated resource limits.

---

### Step 4: Update the Chart Version

#### 4.1 Check available versions

```bash
helm search repo bitnami/nginx --versions | head -5
```

#### 4.2 Update the targetRevision

Edit `nginx-helm-app.yaml` and change `targetRevision` to a different version:

```yaml
    targetRevision: 15.14.1    # or any other available version
```

Apply:

```bash
kubectl apply -f nginx-helm-app.yaml
```

#### 4.3 Watch the rolling update

```bash
argocd app get nginx-helm --refresh
kubectl rollout status deployment -n nginx-helm -l app.kubernetes.io/name=nginx
```

Argo CD will render the new chart version and apply any differences.

---

## Part B: Deploy a Chart from a Git Repository

### Step 5: Create a Helm Chart in Your Fork

#### 5.1 Navigate to your fork

```bash
cd argocd-example-apps    # your fork from Lab 02
```

#### 5.2 Create a simple Helm chart

```bash
mkdir -p helm-webapp/templates
```

**helm-webapp/Chart.yaml:**

```bash
cat > helm-webapp/Chart.yaml << 'EOF'
apiVersion: v2
name: webapp
description: A simple web application Helm chart for ArgoCD lab
version: 0.1.0
appVersion: "1.0.0"
EOF
```

**helm-webapp/values.yaml:**

```bash
cat > helm-webapp/values.yaml << 'EOF'
replicaCount: 1

image:
  repository: nginx
  tag: "1.25"
  pullPolicy: IfNotPresent

service:
  type: ClusterIP
  port: 80

resources:
  requests:
    cpu: 50m
    memory: 64Mi
  limits:
    cpu: 100m
    memory: 128Mi

config:
  appName: "My Web App"
  environment: "default"
EOF
```

**helm-webapp/templates/deployment.yaml:**

```bash
cat > helm-webapp/templates/deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Release.Name }}-webapp
  labels:
    app: {{ .Release.Name }}-webapp
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      app: {{ .Release.Name }}-webapp
  template:
    metadata:
      labels:
        app: {{ .Release.Name }}-webapp
    spec:
      containers:
        - name: webapp
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          ports:
            - containerPort: 80
          resources:
            requests:
              cpu: {{ .Values.resources.requests.cpu }}
              memory: {{ .Values.resources.requests.memory }}
            limits:
              cpu: {{ .Values.resources.limits.cpu }}
              memory: {{ .Values.resources.limits.memory }}
          env:
            - name: APP_NAME
              value: {{ .Values.config.appName | quote }}
            - name: ENVIRONMENT
              value: {{ .Values.config.environment | quote }}
EOF
```

**helm-webapp/templates/service.yaml:**

```bash
cat > helm-webapp/templates/service.yaml << 'EOF'
apiVersion: v1
kind: Service
metadata:
  name: {{ .Release.Name }}-webapp
spec:
  selector:
    app: {{ .Release.Name }}-webapp
  ports:
    - port: {{ .Values.service.port }}
      targetPort: 80
  type: {{ .Values.service.type }}
EOF
```

**helm-webapp/templates/configmap.yaml:**

```bash
cat > helm-webapp/templates/configmap.yaml << 'EOF'
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ .Release.Name }}-webapp-config
data:
  APP_NAME: {{ .Values.config.appName | quote }}
  ENVIRONMENT: {{ .Values.config.environment | quote }}
EOF
```

#### 5.3 Test the chart locally

```bash
helm template my-release helm-webapp/
```

You should see rendered Deployment, Service, and ConfigMap manifests.

#### 5.4 Push to Git

```bash
git add helm-webapp/
git commit -m "Add Helm chart for webapp lab"
git push origin main
```

---

### Step 6: Create an Argo CD Application for the Git-Based Chart

```bash
argocd app create webapp-helm \
  --repo https://github.com/<your-username>/argocd-example-apps.git \
  --path helm-webapp \
  --dest-server https://kubernetes.default.svc \
  --dest-namespace webapp \
  --sync-policy automated \
  --auto-prune \
  --self-heal \
  --sync-option CreateNamespace=true \
  --helm-set replicaCount=2 \
  --helm-set config.environment=dev
```

> **Replace** `<your-username>` with your actual GitHub username.

### Step 7: Verify the deployment

```bash
argocd app get webapp-helm
kubectl get all -n webapp
kubectl get configmap -n webapp
```

**Expected:** 2 replicas, a Service, and a ConfigMap with `ENVIRONMENT: dev`.

---

### Step 8: Update Values via Git

#### 8.1 Create a values override file

```bash
cat > helm-webapp/values-production.yaml << 'EOF'
replicaCount: 5

image:
  tag: "1.25-alpine"

resources:
  requests:
    cpu: 200m
    memory: 256Mi
  limits:
    cpu: 500m
    memory: 512Mi

config:
  appName: "My Web App (Production)"
  environment: "production"
EOF
```

```bash
git add helm-webapp/values-production.yaml
git commit -m "Add production values for webapp"
git push origin main
```

#### 8.2 Update the Application to use the values file

```bash
argocd app set webapp-helm --values values-production.yaml
argocd app sync webapp-helm
```

#### 8.3 Verify

```bash
kubectl get deployment -n webapp -o wide
kubectl get configmap -n webapp -o yaml
```

**Expected:** 5 replicas, alpine image, production config values.

---

## Cleanup

```bash
argocd app delete nginx-helm --yes
argocd app delete webapp-helm --yes

kubectl delete namespace nginx-helm --ignore-not-found
kubectl delete namespace webapp --ignore-not-found

rm -f nginx-helm-app.yaml
```

> **Note:** Keep the Argo CD installation and your fork for the next labs.

---

## Summary

In this lab you:

1. Added a public Helm repository (Bitnami) to Argo CD.
2. Deployed an NGINX chart from the Helm repo with custom values.
3. Overrode values using `--helm-set` and inline `values`.
4. Updated the chart version and watched the rolling update.
5. Created a custom Helm chart in your Git repository.
6. Deployed the Git-based chart through Argo CD.
7. Used multiple values files (default + production) for environment-specific configuration.

---

**Previous lab:** [Lab 02 — Deploy an Application with ArgoCD](lab02-deploy-app-with-argocd.md)  
**Next lab:** [Lab 04 — Multi-Environment with Kustomize](lab04-multi-environment.md)
