# Lesson 2: ArgoCD Fundamentals

## Learning Objectives

By the end of this lesson you will be able to:

- Explain what Argo CD is and why it is the leading GitOps tool for Kubernetes.
- Describe the Argo CD architecture and the role of each component.
- Install Argo CD on a Kubernetes cluster.
- Access the Argo CD web UI and retrieve the initial admin password.
- Use the Argo CD CLI for basic operations.

---

## 1. What is Argo CD?

Argo CD is an open-source, declarative, GitOps continuous delivery tool for Kubernetes. It is a CNCF graduated project maintained by the Argo community.

Argo CD watches one or more Git repositories and continuously compares the desired state defined in those repositories against the live state running in Kubernetes clusters. When a difference is detected, Argo CD can automatically (or manually, depending on configuration) apply the changes to bring the cluster back in sync.

### 1.1 Why Argo CD?

There are several GitOps tools available (Flux, Rancher Fleet, Jenkins X), but Argo CD has become the most widely adopted because it offers:

- **Rich web UI** with a real-time topology view of all resources.
- **Powerful CLI** for automation and scripting.
- **Multi-cluster support** out of the box.
- **Multiple manifest formats** — plain YAML, Helm, Kustomize, Jsonnet, and custom plugins.
- **Fine-grained RBAC** with SSO/OIDC integration.
- **ApplicationSet controller** for generating applications at scale.
- **Sync waves and hooks** for ordered, phased rollouts.
- **Active community** with regular releases and broad ecosystem integration.

### 1.2 Argo CD in the DevSecOps Context

From a DevSecOps perspective, Argo CD provides:

- **Audit trail** — every deployment is traceable to a Git commit.
- **Policy enforcement** — AppProjects restrict which repos can deploy to which namespaces.
- **Credential isolation** — cluster credentials stay inside the cluster.
- **Drift detection** — unauthorized manual changes are detected and can be auto-reverted.
- **Compliance** — Git history satisfies change-management audit requirements.

---

## 2. Argo CD Architecture

Argo CD is deployed as a set of Kubernetes controllers and services in the `argocd` namespace.

### 2.1 Architecture Diagram

```
                    +---------------------+
                    |    Git Repository    |
                    +----------+----------+
                               |
                         clone / poll
                               |
                    +----------v----------+
                    |   argocd-repo-server |
                    |  (manifest rendering)|
                    +----------+----------+
                               |
                       rendered manifests
                               |
+-------------+     +----------v--------------+     +------------------+
|  argocd-    |<--->| argocd-application-     |<--->|  Kubernetes API   |
|  server     |     | controller              |     |  (target cluster) |
|  (API + UI) |     | (reconciliation engine) |     +------------------+
+------+------+     +-------------------------+
       |
       |  HTTPS / gRPC
       |
+------v------+
|  Users      |
|  (UI / CLI) |
+-------------+
```

### 2.2 Core Components

#### argocd-server (API Server)

- Serves the **web UI** (single-page application).
- Exposes the **gRPC and REST API** used by the CLI and other integrations.
- Handles **authentication** (local accounts, SSO, OIDC via Dex).
- Acts as the gateway for all user interactions.

**Pod:** `argocd-server`  
**Service:** `argocd-server` (ports 80/443)

#### argocd-repo-server

- **Clones Git repositories** (or fetches Helm charts from registries).
- **Renders manifests** — runs `helm template`, `kustomize build`, or returns raw YAML.
- Caches rendered output in Redis to avoid re-rendering on every reconciliation loop.
- Stateless — can be horizontally scaled for large installations.

**Pod:** `argocd-repo-server`

#### argocd-application-controller

- The **heart of Argo CD** — the reconciliation engine.
- Compares rendered manifests (from the repo server) against the live cluster state (from the Kubernetes API).
- Computes **sync status** (Synced / OutOfSync) and **health status** (Healthy / Progressing / Degraded).
- When automated sync is enabled, applies changes to the cluster.
- Runs as a **StatefulSet** in HA mode or a Deployment in non-HA mode.

**Pod:** `argocd-application-controller`

#### argocd-redis

- In-memory cache used by the repo server and application controller.
- Stores rendered manifests, application state, and repository metadata.

**Pod:** `argocd-redis`

#### argocd-dex-server (optional)

- [Dex](https://dexidp.io/) is an OpenID Connect (OIDC) identity provider.
- Enables SSO login with GitHub, GitLab, LDAP, SAML, and other identity providers.
- Optional — you can use Argo CD's built-in local accounts or integrate directly with an external OIDC provider.

**Pod:** `argocd-dex-server`

#### argocd-applicationset-controller

- Watches `ApplicationSet` resources and generates `Application` resources from templates.
- Supports generators: Git directory, Git file, cluster, list, merge, matrix, pull request, and more.

**Pod:** `argocd-applicationset-controller`

### 2.3 How the Components Work Together

1. A user creates an `Application` resource (via UI, CLI, or `kubectl apply`).
2. The **application controller** reads the Application spec and asks the **repo server** to render manifests from the specified Git repository, path, and revision.
3. The **repo server** clones the repo (or uses its cache), runs the appropriate tool (plain YAML, Helm, Kustomize), and returns the rendered manifests.
4. The **application controller** fetches the live state of those resources from the **Kubernetes API**.
5. The controller **compares** desired vs. live state and computes sync/health status.
6. If automated sync is enabled and the application is out of sync, the controller **applies** the rendered manifests to the cluster.
7. The **API server** makes the status available through the UI and API.

---

## 3. Installing Argo CD

### 3.1 Prerequisites

- A running Kubernetes cluster (kind, minikube, k3d, or any managed cluster).
- `kubectl` configured to communicate with the cluster.
- Cluster-admin permissions.

### 3.2 Standard Installation

```bash
# Create the argocd namespace
kubectl create namespace argocd

# Apply the official install manifest (includes CRDs, controllers, and RBAC)
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

This installs all core components, CRDs (`Application`, `AppProject`, `ApplicationSet`), ClusterRoles, and ServiceAccounts.

### 3.3 HA Installation (Production)

For production environments with high availability:

```bash
kubectl create namespace argocd

kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/ha/install.yaml
```

The HA manifest deploys the application controller as a StatefulSet with multiple replicas and uses Redis with Sentinel.

### 3.4 Verify the Installation

```bash
# Wait for all pods to be running
kubectl get pods -n argocd -w

# Expected output (non-HA):
# argocd-application-controller-0     1/1     Running
# argocd-applicationset-controller-*  1/1     Running
# argocd-dex-server-*                 1/1     Running
# argocd-notifications-controller-*   1/1     Running
# argocd-redis-*                      1/1     Running
# argocd-repo-server-*                1/1     Running
# argocd-server-*                     1/1     Running
```

### 3.5 Installation via Helm (Alternative)

Argo CD can also be installed using its official Helm chart:

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update

helm install argocd argo/argo-cd \
  --namespace argocd \
  --create-namespace \
  --set server.service.type=ClusterIP
```

The Helm installation gives more control over configuration values.

---

## 4. Accessing the Argo CD UI

### 4.1 Port-Forward (Development / Local Clusters)

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

Then open **https://localhost:8080** in your browser and accept the self-signed certificate warning.

### 4.2 Retrieve the Initial Admin Password

The initial password for the `admin` user is stored in a Kubernetes secret:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d; echo
```

- **Username:** `admin`
- **Password:** the output from the command above.

> **Security note:** Change the admin password immediately after first login and delete the `argocd-initial-admin-secret` secret.

```bash
# Change password via CLI
argocd account update-password

# Delete the initial secret
kubectl -n argocd delete secret argocd-initial-admin-secret
```

### 4.3 Expose via Ingress (Production)

For production access, create an Ingress resource:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: argocd-server
  namespace: argocd
  annotations:
    nginx.ingress.kubernetes.io/ssl-passthrough: "true"
    nginx.ingress.kubernetes.io/backend-protocol: "HTTPS"
spec:
  ingressClassName: nginx
  rules:
    - host: argocd.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: argocd-server
                port:
                  number: 443
  tls:
    - hosts:
        - argocd.example.com
      secretName: argocd-tls
```

### 4.4 The Web UI Tour

The Argo CD web UI provides:

- **Applications view** — a list or tile view of all applications with sync and health status at a glance.
- **Application detail** — a live topology graph showing every Kubernetes resource, its status, and events.
- **Diff view** — side-by-side comparison of desired vs. live state for out-of-sync resources.
- **History** — a timeline of all sync operations with commit SHAs and outcomes.
- **Settings** — manage repositories, clusters, projects, accounts, and certificates.
- **Logs** — stream container logs directly from the UI.

---

## 5. The Argo CD CLI

The CLI mirrors every feature of the UI and is essential for automation and scripting.

### 5.1 Installation

```bash
# macOS (Homebrew)
brew install argocd

# Linux (download binary)
curl -sSL -o argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
chmod +x argocd
sudo mv argocd /usr/local/bin/

# Windows (via scoop or direct download)
scoop install argocd
```

### 5.2 Login

```bash
# Login (will prompt for username and password)
argocd login localhost:8080

# Login with --insecure to skip TLS verification (local dev)
argocd login localhost:8080 --insecure

# Login non-interactively (CI/CD)
argocd login localhost:8080 --insecure --username admin --password <password>
```

### 5.3 Essential CLI Commands

```bash
# --- Applications ---
argocd app list                          # list all applications
argocd app get <name>                    # detailed status of an application
argocd app create <name> \               # create a new application
  --repo <repo-url> \
  --path <path> \
  --dest-server https://kubernetes.default.svc \
  --dest-namespace <namespace>
argocd app sync <name>                   # manually sync an application
argocd app sync <name> --prune           # sync and prune deleted resources
argocd app diff <name>                   # show diff between desired and live
argocd app delete <name>                 # delete an application
argocd app wait <name> --health          # wait until healthy

# --- Repositories ---
argocd repo list                         # list configured repositories
argocd repo add <url> --username <u> --password <p>  # add a private repo

# --- Clusters ---
argocd cluster list                      # list registered clusters
argocd cluster add <context-name>        # register a new cluster

# --- Projects ---
argocd proj list                         # list AppProjects
argocd proj get <name>                   # project details

# --- Account ---
argocd account update-password           # change your password
argocd account list                      # list accounts
```

### 5.4 CLI Output Formats

```bash
# JSON output for scripting
argocd app get guestbook -o json

# YAML output
argocd app get guestbook -o yaml

# Wide table output
argocd app list -o wide
```

---

## 6. Argo CD Custom Resource Definitions (CRDs)

Argo CD installs several CRDs. The most important ones are:

| CRD | API Group | Purpose |
|-----|-----------|---------|
| `Application` | `argoproj.io/v1alpha1` | Defines a Git-to-cluster mapping |
| `AppProject` | `argoproj.io/v1alpha1` | Groups applications and enforces policies |
| `ApplicationSet` | `argoproj.io/v1alpha1` | Generates multiple Applications from templates |

You can manage these resources with `kubectl` just like any other Kubernetes resource:

```bash
kubectl get applications -n argocd
kubectl get appprojects -n argocd
kubectl get applicationsets -n argocd
kubectl describe application guestbook -n argocd
```

---

## 7. Configuration Overview

Argo CD is configured through two primary ConfigMaps in the `argocd` namespace:

### argocd-cm (main configuration)

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-cm
  namespace: argocd
data:
  # URL for the Argo CD UI
  url: https://argocd.example.com

  # Repositories can also be configured here
  repositories: |
    - url: https://github.com/example/gitops-repo.git
      type: git

  # Resource tracking method
  application.resourceTrackingMethod: annotation
```

### argocd-rbac-cm (RBAC configuration)

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-rbac-cm
  namespace: argocd
data:
  policy.default: role:readonly
  policy.csv: |
    p, role:developer, applications, get, */*, allow
    p, role:developer, applications, sync, */*, allow
    g, dev-team, role:developer
```

---

## 8. Argo CD Notifications (Brief Introduction)

Argo CD Notifications is a built-in sub-project that sends alerts when application state changes. It supports:

- Slack, Microsoft Teams, Email, Webhook, Telegram, GitHub, Grafana.

Configuration is done via the `argocd-notifications-cm` ConfigMap:

```yaml
data:
  trigger.on-sync-succeeded: |
    - when: app.status.operationState.phase in ['Succeeded']
      send: [app-sync-succeeded]
  template.app-sync-succeeded: |
    message: Application {{.app.metadata.name}} synced successfully.
```

This is covered in more depth in later lessons.

---

## 9. Knowledge Check

1. Name the three core Argo CD components and describe the role of each.
2. What does the repo server do when it receives a request to render manifests for a Helm-based Application?
3. How do you retrieve the initial admin password after installing Argo CD?
4. What is the difference between the standard install and the HA install?
5. Which ConfigMap controls Argo CD's RBAC policy?

---

## 10. Summary

- Argo CD is a CNCF-graduated GitOps controller that continuously reconciles Git-defined desired state with live Kubernetes cluster state.
- Its architecture consists of three core components: **API server** (UI + API), **repo server** (manifest rendering), and **application controller** (reconciliation engine), supported by Redis and optionally Dex for SSO.
- Installation is a single `kubectl apply` command; accessing the UI requires a port-forward or Ingress.
- The CLI provides full control over applications, repositories, clusters, and projects.
- Argo CD extends the Kubernetes API with CRDs: `Application`, `AppProject`, and `ApplicationSet`.

---

**Previous lesson:** [Lesson 1 — GitOps Principles](01-gitops-principles.md)  
**Next lesson:** [Lesson 3 — ArgoCD Applications](03-argocd-applications.md)
