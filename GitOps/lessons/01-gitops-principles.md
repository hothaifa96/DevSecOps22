# Lesson 1: GitOps Principles

## Learning Objectives

By the end of this lesson you will be able to:

- Define GitOps and explain why it matters for cloud-native operations.
- List and describe the four GitOps principles.
- Compare GitOps to traditional CI/CD pipelines.
- Distinguish between push-based and pull-based deployment models.

---

## 1. What is GitOps?

GitOps is an operational framework that applies DevOps best practices used for application development — version control, collaboration, compliance, and CI/CD — to infrastructure automation. In a GitOps workflow, the entire desired state of a system is stored declaratively in a Git repository, and an automated agent running inside the target environment continuously reconciles the live state with that desired state.

**In one sentence:** GitOps uses Git as the single source of truth and an automated controller as the enforcement layer.

### 1.1 Origin of the Term

The term "GitOps" was coined by Weaveworks in 2017. It emerged from their experience running Kubernetes in production and realising that Git already provided the versioning, auditing, and collaboration primitives needed to manage infrastructure safely. The CNCF later formalised the definition through the [OpenGitOps](https://opengitops.dev/) working group.

### 1.2 Why GitOps?

Traditional operations rely on imperative scripts, manual SSH sessions, or CI pipelines that push changes into production environments. These approaches suffer from:

- **Configuration drift** — live systems silently diverge from what was intended.
- **Poor auditability** — it is hard to answer "who changed what, when, and why?"
- **Fragile rollbacks** — undoing a bad change often means re-running a pipeline or writing a new fix-forward script.
- **Credential sprawl** — CI systems need privileged access to every target cluster.

GitOps addresses all of these problems by making Git the authoritative record and letting an in-cluster agent handle enforcement.

---

## 2. The Four GitOps Principles

The OpenGitOps project defines four principles that a workflow must satisfy to be considered GitOps:

### Principle 1: Declarative

> The entire desired state of the system must be expressed declaratively.

Instead of writing scripts that say *"run these ten commands,"* you write manifests that say *"this is what the system should look like."* Kubernetes YAML, Helm charts, Kustomize overlays, and Terraform HCL are all declarative formats.

**Why it matters:** A declarative description can be diffed, reviewed in a pull request, stored in version control, and applied idempotently.

```yaml
# Declarative: "I want 3 replicas of nginx"
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx
spec:
  replicas: 3
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
          image: nginx:1.25
```

### Principle 2: Versioned and Immutable

> The desired state is stored in a way that enforces immutability, versioning, and a complete audit trail.

Git provides this naturally. Every commit is an immutable snapshot with a SHA, an author, a timestamp, and an optional GPG signature. You can trace every change back to a specific person and pull request.

**Why it matters:** You get a complete audit log for free. Rollback is as simple as reverting a commit. Compliance teams can review the history without needing access to the live cluster.

### Principle 3: Pulled Automatically

> Approved changes are automatically pulled and applied by agents in the target environment.

Software agents (such as Argo CD or Flux) run inside the cluster, watch the Git repository, and pull new desired state whenever it changes. The cluster reaches out to Git — Git never reaches into the cluster.

**Why it matters:** The cluster only needs read access to Git. No external system needs cluster-admin credentials, dramatically reducing the attack surface.

### Principle 4: Continuously Reconciled

> Agents continuously compare the actual state with the desired state and take action to correct drift.

This is the self-healing property. If someone manually edits a Deployment in the cluster, the agent detects the difference and restores the Git-defined state. Reconciliation typically runs on a polling interval (e.g., every 3 minutes) or is triggered by a webhook.

**Why it matters:** The system converges to the desired state even when unexpected changes happen. Drift is eliminated rather than merely reported.

---

## 3. GitOps vs Traditional CI/CD

Understanding the differences between GitOps and traditional CI/CD helps clarify what GitOps adds.

| Aspect | Traditional CI/CD | GitOps |
|--------|-------------------|--------|
| **Deployment trigger** | CI pipeline runs `kubectl apply` or `helm upgrade` | In-cluster agent detects a Git change and reconciles |
| **Direction** | Push: external system pushes into the cluster | Pull: cluster agent pulls from Git |
| **Cluster credentials** | CI system stores and uses cluster-admin tokens | Credentials stay inside the cluster; only Git read access needed |
| **Source of truth** | Scattered across CI scripts, Dockerfiles, pipeline configs | Single Git repository |
| **Drift detection** | None or manual checks | Continuous and automatic |
| **Drift correction** | Manual intervention required | Automatic self-healing |
| **Rollback** | Re-run an older pipeline or write a new commit | `git revert` and the agent reconciles |
| **Audit trail** | CI logs (often ephemeral) | Git history (permanent, immutable) |
| **Security posture** | Larger attack surface (CI has cluster creds) | Smaller attack surface (no external cluster access) |

### Key takeaway

GitOps does not replace CI. You still need CI to build, test, and publish container images. GitOps replaces the **CD** portion — the step where changes are delivered to the running environment.

A typical end-to-end workflow looks like this:

```
Developer pushes code
       |
       v
  CI pipeline
  - lint, test, build image
  - push image to registry
  - update image tag in GitOps repo (e.g., via automated PR)
       |
       v
  GitOps repo updated
       |
       v
  GitOps agent (Argo CD / Flux) detects change
       |
       v
  Agent applies new desired state to the cluster
       |
       v
  Cluster converges to new state
```

---

## 4. Push Model vs Pull Model

This distinction is central to understanding GitOps.

### 4.1 Push Model

In the push model, an external actor (a CI server, a script, or a human) connects to the cluster and applies changes directly.

```
CI Server  ---kubectl apply--->  Kubernetes Cluster
```

**Characteristics:**

- The CI system needs cluster credentials (kubeconfig, service account token).
- Deployments happen only when the pipeline runs; there is no ongoing reconciliation.
- If someone manually changes the cluster, nobody notices until something breaks.
- Scaling to multiple clusters means distributing credentials to many CI jobs.

**Examples:** Jenkins pipelines that run `kubectl apply`, GitHub Actions that call `helm upgrade`, Ansible playbooks that target a cluster.

### 4.2 Pull Model

In the pull model, an agent inside the cluster watches Git and pulls changes when the desired state is updated.

```
Git Repo  <---polls/webhook---  Agent inside Cluster  --->  Kubernetes API
```

**Characteristics:**

- The agent runs as a Kubernetes controller with in-cluster RBAC.
- The agent only needs read access to Git (HTTPS clone or SSH).
- No external system requires cluster-admin credentials.
- Continuous reconciliation corrects drift automatically.
- Adding a new cluster means deploying another agent, not distributing more secrets.

**Examples:** Argo CD, Flux, Rancher Fleet.

### 4.3 Comparison

| Factor | Push | Pull |
|--------|------|------|
| Who initiates? | External CI | In-cluster agent |
| Credential exposure | High | Low |
| Drift correction | None | Continuous |
| Complexity at scale | Grows (more creds, more pipelines) | Flat (agent per cluster) |
| Fits GitOps principles? | Partially | Fully |

> **Note:** Some teams use a hybrid approach — CI builds images and updates the GitOps repo, while a pull-based agent handles delivery. This is the recommended pattern.

---

## 5. Real-World GitOps Workflow

Let us walk through a concrete example to see how all the pieces fit together.

### Scenario

A team maintains a web application. The application code lives in `app-repo` and the Kubernetes manifests live in `gitops-repo`.

### Step-by-step

1. **Developer** opens a pull request in `app-repo` with a bug fix.
2. **CI pipeline** runs unit tests, lints the code, builds a new container image (`myapp:v1.2.3`), and pushes it to the container registry.
3. **CI pipeline** (or an automated bot) opens a pull request in `gitops-repo` that updates the image tag from `v1.2.2` to `v1.2.3`.
4. **Reviewer** approves and merges the PR in `gitops-repo`.
5. **Argo CD** (running inside the cluster) detects the new commit on `main`.
6. **Argo CD** renders the manifests with the updated image tag.
7. **Argo CD** compares the rendered manifests to the live cluster state.
8. **Argo CD** applies the difference — in this case, updating the Deployment to use `myapp:v1.2.3`.
9. **Kubernetes** performs a rolling update to the new image.
10. **Argo CD** reports the Application as `Synced` and `Healthy`.

### Rollback

If `v1.2.3` introduces a regression:

1. **Developer** runs `git revert <commit>` in `gitops-repo`, restoring the image tag to `v1.2.2`.
2. **Argo CD** detects the new commit and resyncs, rolling back the Deployment.

No pipeline re-run, no emergency SSH session, no manual `kubectl set image`. The entire operation is auditable in Git.

---

## 6. Benefits and Challenges

### Benefits

- **Faster recovery** — rollback is a `git revert` away.
- **Improved security** — cluster credentials never leave the cluster.
- **Auditability** — every change is a Git commit with author, timestamp, and review trail.
- **Consistency** — what is in Git is what is in the cluster; drift is eliminated.
- **Developer experience** — developers already know Git; no new tools for deploying.

### Challenges

- **Secrets management** — plain secrets must not be stored in Git; additional tooling (Sealed Secrets, External Secrets Operator, SOPS) is required.
- **Learning curve** — teams unfamiliar with declarative infrastructure need time to adapt.
- **Repo strategy** — deciding on mono-repo vs. multi-repo, branch strategies, and directory structures requires upfront planning.
- **Debugging** — when a sync fails, you need to understand both Git and Kubernetes to diagnose the issue.

---

## 7. Key Terminology

| Term | Meaning |
|------|---------|
| **Desired state** | The configuration declared in Git that describes what the system should look like. |
| **Live state** | The actual current state of the resources in the cluster. |
| **Reconciliation** | The process of comparing desired state to live state and applying corrections. |
| **Drift** | Any discrepancy between desired state and live state. |
| **Self-healing** | Automatic correction of drift by the GitOps agent. |
| **Source of truth** | The authoritative record of the system's desired state — in GitOps, this is Git. |

---

## 8. Knowledge Check

1. What are the four GitOps principles defined by OpenGitOps?
2. Explain the difference between the push model and the pull model. Which one aligns with GitOps?
3. Why is it a security advantage that the GitOps agent only needs read access to Git?
4. A team member runs `kubectl scale deployment/nginx --replicas=5` directly on the cluster, but the Git manifest specifies 3 replicas. What happens under GitOps with self-healing enabled?
5. How does GitOps improve rollback compared to traditional CI/CD?

---

## 9. Summary

- GitOps is a set of practices that use Git as the single source of truth for declarative infrastructure and applications.
- The four principles are: **declarative**, **versioned and immutable**, **pulled automatically**, and **continuously reconciled**.
- GitOps replaces the CD (delivery) stage of a pipeline, not the CI (integration) stage.
- The pull model is preferred over the push model because it keeps cluster credentials inside the cluster and enables continuous drift correction.
- GitOps improves security, auditability, and recovery speed, but requires careful planning for secrets management and repository structure.

---

**Next lesson:** [Lesson 2 — ArgoCD Fundamentals](02-argocd-fundamentals.md)
