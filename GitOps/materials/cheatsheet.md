# Argo CD Cheat Sheet

## CLI commands

```bash
# Log in to an Argo CD server
argocd login <host>:<port>
argocd login <host>:<port> --insecure

# List applications
argocd app list

# Create an application
argocd app create <name> \
  --repo <repo-url> \
  --path <path-in-repo> \
  --dest-server <cluster-url> \
  --dest-namespace <namespace>

# Sync an application
argocd app sync <name>
argocd app sync <name> --prune

# Wait until an app is healthy
argocd app wait <name> --health

# Delete an application
argocd app delete <name>

# Get application details
argocd app get <name>
argocd app diff <name>
argocd app logs <name>

# Add a cluster
argocd cluster add <context>

# Add a private Git repository
argocd repo add <repo-url> --username <user> --password <token>
```

## Common annotations

```yaml
metadata:
  annotations:
    argocd.argoproj.io/sync-wave: "-5"
    argocd.argoproj.io/hook: PostSync
    argocd.argoproj.io/hook-delete-policy: HookSucceeded
    argocd.argoproj.io/sync-options: Prune=false,Replace=true
    argocd.argoproj.io/compare-options: IgnoreExtraneous
```

## Sync options

```yaml
spec:
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
      - PruneLast=true
      - ApplyOutOfSyncOnly=true
      - ServerSideApply=true
      - RespectIgnoreDifferences=true
```

## Health status values

- `Healthy`
- `Progressing`
- `Degraded`
- `Missing`
- `Suspended`
- `Unknown`

## Useful `kubectl` shortcuts

```bash
# Get all Argo CD applications
kubectl get applications -n argocd

# Get application status in YAML
kubectl get application <name> -n argocd -o yaml

# Watch Argo CD pods
kubectl get pods -n argocd -w

# Read Argo CD logs
kubectl logs -n argocd deployment/argocd-application-controller
```
