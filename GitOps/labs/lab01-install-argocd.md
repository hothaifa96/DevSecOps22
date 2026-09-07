# Lab 01: Install Argo CD on Kubernetes

## Objective

Install Argo CD on a local Kubernetes cluster, access the web UI, set up the CLI, and log in. By the end of this lab you will have a fully functional Argo CD instance ready for the remaining labs.

## Prerequisites

- Docker Desktop running.
- `kubectl` installed and configured.
- `kind` or `minikube` installed.
- Internet access to pull images and manifests.

## Estimated Time

20-30 minutes

---

## Step 1: Create a Local Kubernetes Cluster

If you do not already have a running cluster, create one with kind:

```bash
kind create cluster --name gitops-lab
```

Or with minikube:

```bash
minikube start --driver=docker --cpus=4 --memory=4096 --kubernetes-version=stable
```

Verify the cluster is running:

```bash
kubectl cluster-info
kubectl get nodes
```

**Expected output:**

```
NAME                      STATUS   ROLES           AGE   VERSION
gitops-lab-control-plane  Ready    control-plane   1m    v1.28.x
```

---

## Step 2: Install Argo CD

### 2.1 Create the argocd namespace

```bash
kubectl create namespace argocd
```

### 2.2 Apply the installation manifest

```bash
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

This installs:

- Custom Resource Definitions (Application, AppProject, ApplicationSet)
- argocd-server (API + UI)
- argocd-repo-server (manifest rendering)
- argocd-application-controller (reconciliation)
- argocd-redis (caching)
- argocd-dex-server (SSO)
- argocd-applicationset-controller
- argocd-notifications-controller
- ServiceAccounts, ClusterRoles, and ClusterRoleBindings

### 2.3 Wait for all pods to be ready

```bash
kubectl wait --for=condition=Ready pods --all -n argocd --timeout=300s
```

Or watch them come up:

```bash
kubectl get pods -n argocd -w
```

**Expected output (all pods Running and Ready):**

```
NAME                                                READY   STATUS    RESTARTS   AGE
argocd-application-controller-0                     1/1     Running   0          2m
argocd-applicationset-controller-xxxxxxxxxx-xxxxx   1/1     Running   0          2m
argocd-dex-server-xxxxxxxxxx-xxxxx                  1/1     Running   0          2m
argocd-notifications-controller-xxxxxxxxxx-xxxxx    1/1     Running   0          2m
argocd-redis-xxxxxxxxxx-xxxxx                       1/1     Running   0          2m
argocd-repo-server-xxxxxxxxxx-xxxxx                 1/1     Running   0          2m
argocd-server-xxxxxxxxxx-xxxxx                      1/1     Running   0          2m
```

### 2.4 Verify the CRDs were installed

```bash
kubectl get crd | grep argo
```

**Expected output:**

```
applications.argoproj.io          ...
applicationsets.argoproj.io       ...
appprojects.argoproj.io           ...
```

---

## Step 3: Access the Argo CD Web UI

### 3.1 Port-forward the argocd-server service

Open a **new terminal window** (this command runs in the foreground):

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

### 3.2 Retrieve the initial admin password

In your original terminal:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d; echo
```

Copy the output — this is your password.

### 3.3 Open the UI

1. Open your browser and navigate to **https://localhost:8080**.
2. You will see a certificate warning (self-signed cert). Click **Advanced** and **Proceed** (or accept the risk).
3. Log in with:
   - **Username:** `admin`
   - **Password:** the password from Step 3.2.

### 3.4 Explore the UI

After logging in, you should see an empty Applications dashboard. Take a moment to explore:

- **Applications** — where all your apps will appear.
- **Settings** (gear icon) — Repositories, Clusters, Projects, Accounts.
- **User Info** (person icon) — your current user and permissions.

---

## Step 4: Install and Configure the Argo CD CLI

### 4.1 Install the CLI

**macOS (Homebrew):**

```bash
brew install argocd
```

**Linux:**

```bash
curl -sSL -o argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
chmod +x argocd
sudo mv argocd /usr/local/bin/
```

**Windows (scoop):**

```bash
scoop install argocd
```

### 4.2 Verify the installation

```bash
argocd version --client
```

**Expected output:**

```
argocd: v2.x.x+xxxxxxx
  ...
```

### 4.3 Log in to Argo CD from the CLI

Make sure the port-forward from Step 3.1 is still running.

```bash
argocd login localhost:8080 --insecure
```

When prompted:

- **Username:** `admin`
- **Password:** the password from Step 3.2.

**Expected output:**

```
'admin:login' logged in successfully
Context 'localhost:8080' updated
```

### 4.4 Test the CLI

```bash
# List applications (should be empty)
argocd app list

# List clusters (should show the in-cluster)
argocd cluster list

# List projects (should show 'default')
argocd proj list
```

---

## Step 5: Change the Admin Password (Recommended)

```bash
argocd account update-password
```

When prompted, enter the current password and then your new password.

After changing the password, delete the initial secret:

```bash
kubectl -n argocd delete secret argocd-initial-admin-secret
```

---

## Step 6: Verify Everything Works

Run these commands to confirm your installation is complete:

```bash
# Check Argo CD server version
argocd version

# Confirm you are logged in
argocd account get-user-info

# List the default project
argocd proj get default
```

---

## Cleanup (Optional)

If you want to remove everything after the lab:

```bash
# Delete the cluster (kind)
kind delete cluster --name gitops-lab

# Or delete the cluster (minikube)
minikube delete
```

> **Note:** Do NOT clean up if you plan to continue with Lab 02 and beyond.

---

## Troubleshooting

### Pods stuck in Pending or CrashLoopBackOff

Check resource availability:

```bash
kubectl describe pod <pod-name> -n argocd
kubectl logs <pod-name> -n argocd
```

If using minikube with limited resources, increase CPU/memory:

```bash
minikube delete
minikube start --cpus=4 --memory=4096
```

### Port-forward connection refused

Ensure the argocd-server pod is Running:

```bash
kubectl get pods -n argocd -l app.kubernetes.io/name=argocd-server
```

### Cannot retrieve the initial password

If the secret was already deleted, reset the admin password by patching the `argocd-secret`:

```bash
# Generate a bcrypt hash of your new password
BCRYPT_HASH=$(htpasswd -nbBC 10 "" "newpassword" | tr -d ':\n' | sed 's/$2y/$2a/')

# Patch the secret
kubectl -n argocd patch secret argocd-secret \
  -p "{\"stringData\": {\"admin.password\": \"$BCRYPT_HASH\", \"admin.passwordMtime\": \"$(date +%FT%T%Z)\"}}"

# Restart the server
kubectl -n argocd rollout restart deployment argocd-server
```

---

## Summary

In this lab you:

1. Created a local Kubernetes cluster.
2. Installed Argo CD using the official manifest.
3. Accessed the web UI via port-forward.
4. Installed and configured the Argo CD CLI.
5. Logged in and verified the installation.

You are now ready to deploy your first application with Argo CD in **Lab 02**.

---

**Next lab:** [Lab 02 — Deploy an Application with ArgoCD](lab02-deploy-app-with-argocd.md)
