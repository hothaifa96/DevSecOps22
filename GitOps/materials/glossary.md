# Glossary

| Term | Definition |
|------|------------|
| **GitOps** | A continuous delivery model that uses Git as the single source of truth for declarative infrastructure and applications. |
| **Argo CD** | A declarative, GitOps continuous delivery tool for Kubernetes. |
| **Application** | Argo CD custom resource that defines the relationship between a Git source and a destination cluster/namespace. |
| **AppProject** | Argo CD custom resource that groups applications and controls allowed sources, destinations, and RBAC. |
| **Reconciliation** | The process of continuously comparing the desired state with the live state and applying changes. |
| **Drift** | Any difference between the state defined in Git and the actual state in the cluster. |
| **Sync** | The act of applying the desired state from Git to the cluster. |
| **Self-healing** | Argo CD's ability to revert manual changes in the cluster back to the Git-defined state. |
| **Pruning** | Removing resources from the cluster that are no longer defined in Git. |
| **App of Apps** | A pattern where one Argo CD Application manages a collection of other Argo CD Applications. |
| **ApplicationSet** | Argo CD controller that generates multiple Applications from a template and one or more generators. |
| **Sync wave** | A numeric annotation that orders the deployment of resources during a sync. |
| **Resource hook** | A Kubernetes Job annotated to run at a specific stage of the sync process. |
| **Sealed Secrets** | A Bitnami project that encrypts Secrets into CRDs that only the cluster can decrypt. |
| **External Secrets Operator** | A Kubernetes operator that syncs secrets from external secret managers into the cluster. |
| **SOPS** | Mozilla's encryption tool for files, often used with GitOps to encrypt secrets at rest. |
