# Kubernetes Quiz - 50 Questions (Easy to Extreme)

> **Instructions:** Answer each question to the best of your ability. Questions progress from easy to extreme difficulty. No answers are provided - use this as a self-assessment tool.

---

## Easy (Questions 1-10)

### Question 1
What is the smallest deployable unit in Kubernetes?

A) Container  
B) Pod  
C) Node  
D) Deployment  

---

### Question 2
Which `kubectl` command is used to list all running Pods in the current namespace?

A) `kubectl list pods`  
B) `kubectl show pods`  
C) `kubectl get pods`  
D) `kubectl describe pods`  

---

### Question 3
What is the default Service type in Kubernetes?

A) NodePort  
B) LoadBalancer  
C) ExternalName  
D) ClusterIP  

---

### Question 4
Which restart policy is the default for Pods?

A) Never  
B) OnFailure  
C) Always  
D) Unless-Stopped  

---

### Question 5
What command do you use to enter a running container interactively?

A) `kubectl ssh my-pod`  
B) `kubectl exec -it my-pod -- /bin/bash`  
C) `kubectl connect my-pod`  
D) `kubectl attach my-pod --shell`  

---

### Question 6
Which Kubernetes object is used to store non-sensitive configuration data as key-value pairs?

A) Secret  
B) ConfigMap  
C) PersistentVolume  
D) Annotation  

---

### Question 7
What does the `kubectl apply -f deployment.yaml` command do?

A) Deletes the resource defined in the file  
B) Only validates the YAML syntax  
C) Creates or updates the resource defined in the file  
D) Displays the resource without creating it  

---

### Question 8
What is the purpose of a Namespace in Kubernetes?

A) To encrypt network traffic between Pods  
B) To provide virtual clusters for resource isolation and organization  
C) To store container images  
D) To manage node hardware  

---

### Question 9
Which of the following is NOT one of the default namespaces in a Kubernetes cluster?

A) default  
B) kube-system  
C) kube-public  
D) kube-apps  

---

### Question 10
How do containers within the same Pod communicate with each other?

A) Through a Service  
B) Through an Ingress  
C) Via `localhost` (they share the same network namespace)  
D) Through a ConfigMap  

---

## Intermediate (Questions 11-25)

### Question 11
What is the valid NodePort range in Kubernetes?

A) 1-65535  
B) 8000-9000  
C) 30000-32767  
D) 80-443  

---

### Question 12
Which update strategy kills all existing Pods before creating new ones?

A) RollingUpdate  
B) Recreate  
C) BlueGreen  
D) Canary  

---

### Question 13
In a Deployment's RollingUpdate strategy, what does `maxSurge` control?

A) The maximum number of Pods that can be unavailable during an update  
B) The maximum number of Pods that can exist above the desired replica count during an update  
C) The maximum time allowed for the update  
D) The maximum number of failed Pods before rolling back  

---

### Question 14
What is the purpose of a ReplicaSet?

A) To manage database replication  
B) To ensure a specified number of Pod replicas are running at all times  
C) To manage storage replication across nodes  
D) To replicate ConfigMaps across namespaces  

---

### Question 15
Why should you typically NOT create ReplicaSets directly?

A) ReplicaSets are deprecated  
B) ReplicaSets do not support rolling updates or rollbacks; use Deployments instead  
C) ReplicaSets cannot manage more than 3 Pods  
D) ReplicaSets require root access  

---

### Question 16
What does a Kubernetes Secret encode its data with by default?

A) AES-256 encryption  
B) SHA-256 hashing  
C) Base64 encoding  
D) RSA encryption  

---

### Question 17
What is the default Secret type in Kubernetes?

A) kubernetes.io/tls  
B) kubernetes.io/basic-auth  
C) Opaque  
D) kubernetes.io/dockerconfigjson  

---

### Question 18
What command can you use to roll back a Deployment to the previous revision?

A) `kubectl rollback deployment/my-deployment`  
B) `kubectl rollout undo deployment/my-deployment`  
C) `kubectl revert deployment/my-deployment`  
D) `kubectl restore deployment/my-deployment`  

---

### Question 19
What is the maximum size limit for a ConfigMap or Secret in Kubernetes?

A) 256 KB  
B) 512 KB  
C) 1 MB  
D) 10 MB  

---

### Question 20
Which Kubernetes resource ensures that a copy of a Pod runs on every (or selected) node in the cluster?

A) Deployment  
B) StatefulSet  
C) DaemonSet  
D) ReplicaSet  

---

### Question 21
What Kubernetes object is required for an Ingress to function?

A) LoadBalancer Service  
B) Ingress Controller  
C) External DNS  
D) Network Policy  

---

### Question 22
At which OSI layer does an Ingress operate?

A) Layer 3 (Network)  
B) Layer 4 (Transport)  
C) Layer 7 (Application)  
D) Layer 2 (Data Link)  

---

### Question 23
What is the DNS format for accessing a Service across namespaces?

A) `<service-name>.<namespace>`  
B) `<service-name>.<namespace>.svc.cluster.local`  
C) `<namespace>/<service-name>`  
D) `<service-name>.cluster.<namespace>`  

---

### Question 24
Which Pod lifecycle phase indicates that all containers have terminated and at least one failed?

A) Pending  
B) Unknown  
C) Failed  
D) CrashLoopBackOff  

---

### Question 25
What does a `livenessProbe` determine?

A) Whether the Pod is ready to receive traffic  
B) Whether the container is still running and healthy  
C) Whether the Pod should be scaled up  
D) Whether the container has started successfully  

---

## Advanced (Questions 26-40)

### Question 26
What is required for a StatefulSet to provide stable network identities to its Pods?

A) A LoadBalancer Service  
B) A Headless Service (clusterIP: None)  
C) A NodePort Service  
D) An ExternalName Service  

---

### Question 27
In a StatefulSet, what is the DNS name format for individual Pods?

A) `<pod-name>.<namespace>.svc.cluster.local`  
B) `<pod-name>.<headless-service>.<namespace>.svc.cluster.local`  
C) `<statefulset-name>-<index>.<namespace>.pods.cluster.local`  
D) `<headless-service>.<pod-name>.<namespace>.svc.cluster.local`  

---

### Question 28
What happens to network traffic when a NetworkPolicy targets a Pod?

A) All traffic is allowed by default, and only explicitly denied traffic is blocked  
B) All non-matching traffic is denied; only explicitly allowed traffic gets through  
C) Nothing changes; NetworkPolicies are advisory only  
D) Only egress traffic is affected  

---

### Question 29
Which component must be installed for the Horizontal Pod Autoscaler (HPA) to function?

A) Cluster Autoscaler  
B) Metrics Server  
C) Prometheus  
D) kube-state-metrics  

---

### Question 30
For an HPA to calculate CPU utilization percentage, what must be defined in the Pod spec?

A) CPU limits only  
B) Resource requests  
C) Resource annotations  
D) Node affinity rules  

---

### Question 31
What is the `apiVersion` for a Kubernetes Ingress resource?

A) `v1`  
B) `extensions/v1beta1`  
C) `networking.k8s.io/v1`  
D) `apps/v1`  

---

### Question 32
In a Job, what is the difference between `completions` and `parallelism`?

A) They are the same thing  
B) `completions` is the total successful completions needed; `parallelism` is how many Pods run simultaneously  
C) `completions` is how many Pods run simultaneously; `parallelism` is total successful completions needed  
D) `completions` sets the retry count; `parallelism` sets the timeout  

---

### Question 33
What is the default `concurrencyPolicy` for a CronJob?

A) Forbid  
B) Replace  
C) Allow  
D) Queue  

---

### Question 34
Which PersistentVolume reclaim policy is deprecated?

A) Retain  
B) Delete  
C) Recycle  
D) Archive  

---

### Question 35
What are the three PersistentVolume access modes?

A) ReadOnly, WriteOnly, ReadWrite  
B) ReadWriteOnce (RWO), ReadOnlyMany (ROX), ReadWriteMany (RWX)  
C) SingleRead, SingleWrite, MultiReadWrite  
D) Exclusive, Shared, ReadOnly  

---

### Question 36
What does the `WaitForFirstConsumer` volume binding mode do in a StorageClass?

A) Waits for an admin to approve the PV before binding  
B) Delays PV provisioning until a Pod using the PVC is scheduled  
C) Waits for the PV to be fully replicated before binding  
D) Delays binding until the PVC is 24 hours old  

---

### Question 37
In RBAC, what is the difference between a `Role` and a `ClusterRole`?

A) Roles are for users; ClusterRoles are for service accounts  
B) Roles are namespace-scoped; ClusterRoles are cluster-wide  
C) Roles are read-only; ClusterRoles support writes  
D) There is no difference; they are aliases  

---

### Question 38
What does `apiGroups: [""]` mean in an RBAC Role rule?

A) It matches all API groups  
B) It refers to the core API group (Pods, Services, Secrets, ConfigMaps, etc.)  
C) It means no API group is specified and the rule is invalid  
D) It refers to the apps API group  

---

### Question 39
What command checks if a specific user has permission to perform an action?

A) `kubectl auth check-permission create pods --user developer1`  
B) `kubectl auth can-i create pods --as developer1`  
C) `kubectl rbac verify developer1 --action create --resource pods`  
D) `kubectl get permissions --user developer1`  

---

### Question 40
What is the `pathType` option that matches a URL path and all its sub-paths in an Ingress rule?

A) Exact  
B) Prefix  
C) Wildcard  
D) ImplementationSpecific  

---

## Expert (Questions 41-45)

### Question 41
How does a `RoleBinding` differ from a `ClusterRoleBinding` when both reference a `ClusterRole`?

A) There is no difference; they behave identically  
B) A `RoleBinding` referencing a `ClusterRole` grants those permissions only within the RoleBinding's namespace; a `ClusterRoleBinding` grants them cluster-wide  
C) A `RoleBinding` cannot reference a `ClusterRole`  
D) A `ClusterRoleBinding` can only be used with ServiceAccounts  

---

### Question 42
In a StatefulSet with 5 replicas, you scale down to 3. Which Pods are terminated first, and what happens to their PersistentVolumeClaims?

A) Random Pods are terminated; their PVCs are deleted  
B) Pods with the highest ordinal index are terminated first (pod-4, pod-3); their PVCs are retained  
C) Pods with the lowest ordinal index are terminated first (pod-0, pod-1); their PVCs are retained  
D) All Pods are terminated and recreated; all PVCs are recycled  

---

### Question 43
A CronJob has `concurrencyPolicy: Forbid` and a scheduled run triggers while the previous Job is still running. What happens?

A) The new Job is queued and runs after the current one finishes  
B) The new Job replaces the running Job  
C) The new scheduled run is skipped entirely  
D) Both Jobs run in parallel  

---

### Question 44
You create a NetworkPolicy that selects Pods with `app: api` and allows ingress only from Pods with `role: frontend`. You also have Pods labeled `role: monitoring` in a different namespace. Can the monitoring Pods reach the API Pods?

A) Yes, because NetworkPolicies do not apply across namespaces  
B) No, because the policy only allows ingress from `role: frontend` and denies all other traffic  
C) Yes, because cross-namespace traffic bypasses NetworkPolicies  
D) It depends on whether the CNI plugin supports cross-namespace policies  

---

### Question 45
What is the `stabilizationWindowSeconds` field in an HPA's `behavior` spec used for?

A) It sets the time between consecutive scaling decisions to prevent rapid scale-up and scale-down (flapping)  
B) It determines how long to wait before deleting terminated Pods  
C) It sets the timeout for the Metrics Server to respond  
D) It controls how long newly created Pods have before they must be ready  

---

## Extreme (Questions 46-50)

### Question 46
You have a Deployment with `replicas: 4`, `maxSurge: 50%`, and `maxUnavailable: 25%` during a rolling update. What is the maximum number of Pods that can exist simultaneously during the update, and what is the minimum number of Pods that must be available?

A) Max 6, Min 3  
B) Max 5, Min 4  
C) Max 8, Min 2  
D) Max 6, Min 2  

---

### Question 47
You have a Pod with both a `readinessProbe` and a `livenessProbe`. The `readinessProbe` fails while the `livenessProbe` succeeds. What is the resulting behavior?

A) The Pod is terminated and restarted  
B) The Pod remains running but is removed from all Service endpoints (no traffic is routed to it)  
C) Both probes must fail for any action to be taken  
D) The Pod is evicted from the node  

---

### Question 48
A PersistentVolume has `persistentVolumeReclaimPolicy: Retain` and is bound to a PVC. The PVC is deleted. What is the state of the PV afterward, and can a new PVC automatically bind to it?

A) The PV is deleted along with the PVC  
B) The PV enters `Released` state; a new PVC cannot automatically bind to it until an administrator manually clears the `claimRef`  
C) The PV returns to `Available` state and can be immediately claimed by a new PVC  
D) The PV enters `Failed` state and must be recreated  

---

### Question 49
You define both a `podSelector` AND a `namespaceSelector` within the same `from` rule of a NetworkPolicy ingress entry. How does Kubernetes evaluate these two selectors?

A) It uses OR logic: traffic is allowed if it matches either the podSelector or the namespaceSelector  
B) It uses AND logic: traffic is allowed only from Pods that match the podSelector AND are in namespaces that match the namespaceSelector  
C) The namespaceSelector is ignored; only podSelector is evaluated  
D) It creates two separate rules, one for each selector  

---

### Question 50
You have an HPA targeting a Deployment with `minReplicas: 2`, `maxReplicas: 10`, and a target CPU utilization of 50%. The Deployment has resource requests of `100m` CPU per Pod. Currently 4 Pods are running, and the total CPU usage across all Pods is `600m`. How many replicas will the HPA scale to, and why?

A) 6 replicas, because the current average utilization is 150% of the target (600m / 4 Pods = 150m per Pod, which is 150% of the 100m request, and 150%/50% target ratio means 4 * 3 = 12, capped at 10)  
B) 10 replicas, because it always scales to max when utilization exceeds the target  
C) 12 replicas, because 600m total / 50m target per Pod = 12  
D) 8 replicas, because ceil(600m / (100m * 0.50)) = ceil(600/50) = 12, but capped at maxReplicas of 10, so 10... wait, the formula is ceil(currentMetricValue / desiredMetricValue) = ceil((600/4)/(100*0.5)) * 4 = ceil(150/50) * ... the HPA formula is: desiredReplicas = ceil(currentReplicas * (currentMetricValue / desiredMetricValue)) = ceil(4 * (150% / 50%)) = ceil(4 * 3) = 12, capped at maxReplicas = 10  

---

## Bonus Challenge

### Question B1 (Architecture)
Explain the complete flow that occurs when you run `kubectl apply -f deployment.yaml`. Which Kubernetes control-plane components are involved, in what order, and what role does each play from the moment the API request is received until the Pods are running on a node?

---

### Question B2 (Troubleshooting)
A Pod is stuck in `Pending` state. List at least 5 possible reasons why this could happen and the `kubectl` commands you would use to diagnose each one.

---

### Question B3 (Design)
Design a Kubernetes architecture for a stateful application (e.g., a PostgreSQL cluster with 3 replicas) that includes: storage, networking, scaling, configuration management, and security. Specify which Kubernetes resources you would use for each concern and explain why.

---

*Good luck! Review the course materials and practice with a real cluster to verify your answers.*
