# GitOps & Argo CD Tutorial

Welcome to a hands-on, end-to-end tutorial on **GitOps** and **Argo CD**.
This repository is split into two parts:

- `materials/` — theory, diagrams, cheat sheets, and reference docs.
- `practice/` — hands-on labs with step-by-step instructions and ready-to-apply manifests.

## How to use this tutorial

1. Read `tutorial.md` from start to end to understand the core concepts.
2. Keep `cheatsheet.md` and `glossary.md` open while you work.
3. Work through the `practice/exercise-*` folders in order.
4. Each exercise has its own `instructions.md` and supporting YAML manifests.

## What you will learn

- The four GitOps principles
- How GitOps differs from traditional CI/CD
- Argo CD architecture and core components
- Installing Argo CD on Kubernetes
- Defining Argo CD Applications for plain YAML, Helm, and Kustomize
- Automated sync, self-healing, and pruning
- App of Apps and ApplicationSet patterns
- Sync waves and resource hooks
- Managing secrets in a GitOps workflow
- Multi-cluster and multi-tenant deployment strategies
- Rollbacks and disaster recovery

## Prerequisites

- A local Kubernetes cluster: `kind`, `minikube`, or `k3d`.
- `kubectl` installed and configured.
- `git` and a GitHub/GitLab/Bitbucket account.
- Basic knowledge of Kubernetes resources (Deployment, Service, ConfigMap).
- Optional: `helm`, `kustomize`, and `argocd` CLI.

## Suggested cluster setup

```bash
kind create cluster --name gitops
```

or

```bash
minikube start --driver=docker --kubernetes-version=stable
```

## Table of contents

- `tutorial.md` — full written course
- `cheatsheet.md` — quick command and annotation reference
- `glossary.md` — terminology
- `extra-resources.md` — links to official docs and further reading
