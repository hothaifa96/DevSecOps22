# Lab 02: Deploy an Application with Argo CD

## Objective

Create an Argo CD Application that points to a Git repository containing Kubernetes manifests. Observe the sync process, make changes to the manifests in Git, and watch Argo CD auto-sync the changes to the cluster.

## Prerequisites

- Completed **Lab 01** (Argo CD installed and running).
- `kubectl` and `argocd` CLI configured.
- Port-forward to Argo CD still active (`kubectl port-forward svc/argocd-server -n argocd 8080:443`).
- A GitHub account (for forking the example repo).

## Estimated Time

30-40 minutes

---

## Step 1: Fork the Example Repository

We will use the official Argo CD example apps repository.

### 1.1 Fork the repo

1. Go to **https://github.com/argoproj/argocd-example-apps** in your browser.
2. Click **Fork** to create a copy under your GitHub account.
3. Note your fork URL: `https://github.com/<your-username>/argocd-example-apps.git`

### 1.2 Clone your fork locally

```bash
git clone https://github.com/<your-username>/argocd-example-apps.git
cd argocd-example-apps
```

### 1.3 Examine the guestbook application

```bash
ls guestbook/
```

**Expected output:**

```
guestbook-ui-deployment.yaml
guestbook-ui-svc.yaml
```

Inspect the manifests:

```bash
cat guestbook/guestbook-ui-deployment.yaml
cat guestbook/guestbook-ui-svc.yaml
```

The guestbook app is a simple Deployment with one replica and a Service.

---

## Step 2: Create the Application (CLI Method)

### 2.1 Create the guestbook namespace

```bash
kubectl create namespace guestbook
```

### 2.2 Create the Argo CD Application

```bash
argocd app create guestbook \
  --repo https://github.com/<your-username>/argocd-example-apps.git \
  --path guestbook \
  --dest-server https://kubernetes.default.svc \
  --dest-namespace guestbook \
  --sync-policy manual
```

> **Replace** `<your-username>` with your actual GitHub username.

### 2.3 Verify the application was created

```bash
argocd app list
```

**Expected output:**

```
NAME        CLUSTER                         NAMESPACE   PROJECT  STATUS     HEALTH   SYNCPOLICY  CONDITIONS
guestbook   https://kubernetes.default.svc  guestbook   default  OutOfSync  Missing  Manual      <none>
```

The application is **OutOfSync** because it has not been synced yet. Health is **Missing** because no resources exist in the cluster.

---

## Step 3: Explore the Application in the UI

1. Open **https://localhost:8080** in your browser.
2. You should see the **guestbook** application tile.
3. Click on it to see the detailed view.

Notice:

- The sync status is **OutOfSync** (yellow).
- The health status is **Missing**.
- The resource tree shows the expected Deployment and Service, but they have not been created yet.
- Click **Diff** to see what will be applied.

---

## Step 4: Perform a Manual Sync

### 4.1 Sync via CLI

```bash
argocd app sync guestbook
```

**Expected output:**

```
TIMESTAMP  GROUP  KIND        NAMESPACE  NAME          STATUS   HEALTH   HOOK  MESSAGE
...        apps   Deployment  guestbook  guestbook-ui  Synced   Healthy        deployment.apps/guestbook-ui created
...               Service     guestbook  guestbook-ui  Synced   Healthy        service/guestbook-ui created
```

### 4.2 Verify the sync

```bash
argocd app get guestbook
```

**Expected output (key fields):**

```
Name:               guestbook
Project:            default
Server:             https://kubernetes.default.svc
Namespace:          guestbook
Sync Status:        Synced
Health Status:      Healthy
```

### 4.3 Verify resources in the cluster

```bash
kubectl get all -n guestbook
```

**Expected output:**

```
NAME                                READY   STATUS    RESTARTS   AGE
pod/guestbook-ui-xxxxxxxxxx-xxxxx  1/1     Running   0          30s

NAME                   TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)   AGE
service/guestbook-ui   ClusterIP   10.96.xxx.xxx   <none>        80/TCP    30s

NAME                           READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/guestbook-ui   1/1     1            1           30s
```

### 4.4 Check the UI

Go back to the Argo CD UI. The guestbook tile should now show:

- Sync status: **Synced** (green checkmark)
- Health status: **Healthy** (green heart)

Click on the application to see the resource tree with the Deployment, ReplicaSet, Pod, and Service.

---

## Step 5: Enable Automated Sync

Now let us enable auto-sync so Argo CD applies changes from Git automatically.

### 5.1 Enable auto-sync with self-heal and prune

```bash
argocd app set guestbook \
  --sync-policy automated \
  --auto-prune \
  --self-heal
```

### 5.2 Verify the sync policy

```bash
argocd app get guestbook | grep -i sync
```

You should see `Sync Policy: Automated (Prune, Self-Heal)`.

---

## Step 6: Make a Change in Git and Watch Auto-Sync

### 6.1 Edit the deployment in your fork

In your local clone of `argocd-example-apps`, edit the replica count:

```bash
cd argocd-example-apps
```

Open `guestbook/guestbook-ui-deployment.yaml` in your editor and change the replica count from `1` to `3`:

```yaml
spec:
  replicas: 3       # changed from 1
```

### 6.2 Commit and push

```bash
git add guestbook/guestbook-ui-deployment.yaml
git commit -m "Scale guestbook to 3 replicas"
git push origin main
```

### 6.3 Wait for Argo CD to detect the change

Argo CD polls Git every 3 minutes by default. To see the change faster, you can trigger a manual refresh:

```bash
argocd app get guestbook --refresh
```

### 6.4 Verify the change was applied

Wait a few moments, then check:

```bash
kubectl get deployment guestbook-ui -n guestbook
```

**Expected output:**

```
NAME           READY   UP-TO-DATE   AVAILABLE   AGE
guestbook-ui   3/3     3            3           5m
```

The replica count has been updated to 3 automatically.

### 6.5 Check the UI

In the Argo CD UI, click on the guestbook application. You should see:

- 3 Pods in the resource tree.
- The sync history shows the new commit SHA.

---

## Step 7: Test Self-Healing

### 7.1 Make a manual change to the cluster

Simulate someone making a manual change:

```bash
kubectl scale deployment/guestbook-ui --replicas=10 -n guestbook
```

### 7.2 Verify the manual change

```bash
kubectl get deployment guestbook-ui -n guestbook
```

You should briefly see `10/10` replicas.

### 7.3 Wait for self-heal

Within a few minutes (or trigger a refresh), Argo CD will detect the drift and restore the Git-defined state:

```bash
argocd app get guestbook --refresh
```

```bash
kubectl get deployment guestbook-ui -n guestbook
```

**Expected output (after self-heal):**

```
NAME           READY   UP-TO-DATE   AVAILABLE   AGE
guestbook-ui   3/3     3            3           10m
```

The replica count is back to **3** — the value defined in Git.

---

## Step 8: Test Pruning

### 8.1 Add a new resource in Git

Create a new ConfigMap in your fork:

```bash
cat > guestbook/configmap.yaml << 'EOF'
apiVersion: v1
kind: ConfigMap
metadata:
  name: guestbook-config
data:
  APP_COLOR: blue
  APP_MODE: production
EOF
```

```bash
git add guestbook/configmap.yaml
git commit -m "Add guestbook ConfigMap"
git push origin main
```

### 8.2 Verify it was created

```bash
argocd app get guestbook --refresh
# Wait a moment...
kubectl get configmap guestbook-config -n guestbook
```

### 8.3 Remove the resource from Git

```bash
rm guestbook/configmap.yaml
git add -A
git commit -m "Remove guestbook ConfigMap"
git push origin main
```

### 8.4 Verify it was pruned

```bash
argocd app get guestbook --refresh
# Wait a moment...
kubectl get configmap guestbook-config -n guestbook
```

**Expected output:**

```
Error from server (NotFound): configmaps "guestbook-config" not found
```

The ConfigMap was automatically deleted from the cluster because prune is enabled.

---

## Step 9: Create an Application Declaratively (YAML Method)

Instead of using the CLI, you can define the Application as a YAML manifest.

### 9.1 Create the Application manifest

```bash
cat > guestbook-app.yaml << 'EOF'
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: guestbook-declarative
  namespace: argocd
  finalizers:
    - resources-finalizer.argocd.argoproj.io
spec:
  project: default
  source:
    repoURL: https://github.com/<your-username>/argocd-example-apps.git
    targetRevision: main
    path: guestbook
  destination:
    server: https://kubernetes.default.svc
    namespace: guestbook-v2
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
EOF
```

> **Replace** `<your-username>` with your actual GitHub username.

### 9.2 Apply it

```bash
kubectl apply -f guestbook-app.yaml
```

### 9.3 Verify

```bash
argocd app list
kubectl get all -n guestbook-v2
```

You should see two guestbook applications: one in the `guestbook` namespace and one in `guestbook-v2`.

---

## Step 10: View Sync History

### 10.1 CLI

```bash
argocd app history guestbook
```

This shows every sync operation with the commit SHA, date, and status.

### 10.2 UI

In the Argo CD UI, click on the guestbook application, then click the **History and Rollback** tab (clock icon). You will see a timeline of all sync operations.

---

## Cleanup

Remove the applications and namespaces created in this lab:

```bash
argocd app delete guestbook --yes
argocd app delete guestbook-declarative --yes

# The finalizer will delete cluster resources automatically
# If namespaces remain, delete them manually:
kubectl delete namespace guestbook --ignore-not-found
kubectl delete namespace guestbook-v2 --ignore-not-found
```

> **Note:** Keep the Argo CD installation for the next labs.

---

## Summary

In this lab you:

1. Forked the example apps repository and examined the guestbook manifests.
2. Created an Argo CD Application using the CLI (manual sync).
3. Performed a manual sync and verified resources in the cluster.
4. Enabled automated sync with self-heal and prune.
5. Made a change in Git (scaled replicas) and watched auto-sync apply it.
6. Tested self-healing by making a manual cluster change that Argo CD reverted.
7. Tested pruning by adding and removing a resource in Git.
8. Created an Application declaratively using a YAML manifest.
9. Viewed sync history via CLI and UI.

---

**Previous lab:** [Lab 01 — Install ArgoCD](lab01-install-argocd.md)  
**Next lab:** [Lab 03 — Helm with ArgoCD](lab03-helm-with-argocd.md)
