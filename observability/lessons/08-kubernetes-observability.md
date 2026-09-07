# Lesson 08: Kubernetes Observability

## Table of Contents

- [Overview of Kubernetes Monitoring](#overview-of-kubernetes-monitoring)
- [Metrics Server](#metrics-server)
- [kube-state-metrics](#kube-state-metrics)
- [Node Exporter](#node-exporter)
- [cAdvisor](#cadvisor)
- [Prometheus Operator](#prometheus-operator)
- [Grafana Dashboards for Kubernetes](#grafana-dashboards-for-kubernetes)
- [Logging in Kubernetes](#logging-in-kubernetes)
- [Kubernetes Events](#kubernetes-events)
- [Key Takeaways](#key-takeaways)

---

## Overview of Kubernetes Monitoring

Monitoring Kubernetes requires visibility at multiple layers:

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 4: Application Metrics                                │
│   Custom business metrics, SLIs, request rates              │
│   Tool: Application instrumentation (Prometheus client)     │
├─────────────────────────────────────────────────────────────┤
│ Layer 3: Container Metrics                                  │
│   CPU, memory, network, disk per container                  │
│   Tool: cAdvisor (built into kubelet)                       │
├─────────────────────────────────────────────────────────────┤
│ Layer 2: Kubernetes Object State                            │
│   Pod status, deployment replicas, node conditions          │
│   Tool: kube-state-metrics                                  │
├─────────────────────────────────────────────────────────────┤
│ Layer 1: Infrastructure Metrics                             │
│   Node CPU, memory, disk, network                           │
│   Tool: node-exporter                                       │
└─────────────────────────────────────────────────────────────┘
```

### The Monitoring Stack for Kubernetes

```
┌──────────────────────────────────────────────────────────────┐
│                     Grafana (Visualization)                   │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  Dashboards: Cluster, Node, Pod, Namespace, App      │    │
│  └──────────────────────────────────────────────────────┘    │
└───────────────────────────┬──────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────┐
│                   Prometheus (Storage & Query)                │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐   │
│  │ Alerting    │  │ Recording    │  │ Service Discovery │   │
│  │ Rules       │  │ Rules        │  │ (K8s SD)          │   │
│  └─────────────┘  └──────────────┘  └───────────────────┘   │
└───────────────────────────┬──────────────────────────────────┘
                            │ Scrapes
            ┌───────────────┼───────────────────┐
            │               │                   │
  ┌─────────▼────┐  ┌──────▼───────┐  ┌───────▼──────────┐
  │ kube-state   │  │ node         │  │ kubelet/cAdvisor  │
  │ -metrics     │  │ -exporter    │  │ (per node)        │
  │ (K8s state)  │  │ (host HW)   │  │ (containers)      │
  └──────────────┘  └──────────────┘  └──────────────────┘
```

---

## Metrics Server

The **Metrics Server** is a cluster-wide aggregator of resource usage data. It's required for `kubectl top` and Horizontal Pod Autoscaler (HPA).

### What It Provides

```bash
# After installing metrics-server:
$ kubectl top nodes
NAME     CPU(cores)   CPU%   MEMORY(bytes)   MEMORY%
node-1   245m         12%    1842Mi          48%
node-2   189m         9%     1563Mi          41%

$ kubectl top pods -n production
NAME                        CPU(cores)   MEMORY(bytes)
api-6d4f5b7c8-abc12         45m          128Mi
api-6d4f5b7c8-def34         38m          115Mi
worker-7f8g9h0-xyz56        120m         256Mi
```

### Installation

```bash
# Install via kubectl
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# For local development (minikube/kind), add insecure TLS flag:
kubectl patch deployment metrics-server -n kube-system \
  --type='json' \
  -p='[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]'
```

### Metrics Server vs Prometheus

| Feature | Metrics Server | Prometheus |
|---------|---------------|------------|
| **Purpose** | HPA, `kubectl top` | Full monitoring and alerting |
| **Retention** | Last value only (no history) | Configurable (days to years) |
| **Metrics** | CPU and memory only | Thousands of metrics |
| **Querying** | API only | PromQL (powerful) |
| **Use Case** | Autoscaling | Dashboards, alerts, debugging |

---

## kube-state-metrics

**kube-state-metrics** (KSM) generates metrics about the state of Kubernetes objects. It queries the Kubernetes API server and converts object state into Prometheus metrics.

### What It Monitors

```
Deployments:  kube_deployment_status_replicas
              kube_deployment_spec_replicas
              kube_deployment_status_replicas_available

Pods:         kube_pod_status_phase
              kube_pod_container_status_restarts_total
              kube_pod_container_status_waiting_reason
              kube_pod_container_resource_requests
              kube_pod_container_resource_limits

Nodes:        kube_node_status_condition
              kube_node_status_allocatable
              kube_node_info

StatefulSets: kube_statefulset_status_replicas
              kube_statefulset_replicas

Jobs:         kube_job_status_succeeded
              kube_job_status_failed
              kube_job_complete

CronJobs:     kube_cronjob_next_schedule_time
              kube_cronjob_status_last_schedule_time

PVCs:         kube_persistentvolumeclaim_status_phase
              kube_persistentvolumeclaim_resource_requests_storage_bytes

HPA:          kube_horizontalpodautoscaler_status_current_replicas
              kube_horizontalpodautoscaler_spec_max_replicas
```

### Installation

```bash
# Helm
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install kube-state-metrics prometheus-community/kube-state-metrics \
  --namespace monitoring

# Or as part of kube-prometheus-stack (recommended)
```

### Useful kube-state-metrics Queries

```promql
# Pods not in Running state
kube_pod_status_phase{phase!="Running", phase!="Succeeded"} == 1

# Pods in CrashLoopBackOff
kube_pod_container_status_waiting_reason{reason="CrashLoopBackOff"} > 0

# Container restart count in the last hour
increase(kube_pod_container_status_restarts_total[1h]) > 3

# Deployments with unavailable replicas
kube_deployment_status_replicas_unavailable > 0

# Deployment rollout stuck
kube_deployment_status_observed_generation != kube_deployment_metadata_generation

# Pods exceeding memory requests
container_memory_working_set_bytes
/
on (namespace, pod, container) kube_pod_container_resource_requests{resource="memory"}
> 1.5

# Node not ready
kube_node_status_condition{condition="Ready", status="true"} == 0

# PVC pending
kube_persistentvolumeclaim_status_phase{phase="Pending"} == 1

# Jobs failed
kube_job_status_failed > 0

# HPA at max replicas
kube_horizontalpodautoscaler_status_current_replicas
==
kube_horizontalpodautoscaler_spec_max_replicas
```

---

## Node Exporter

The **Node Exporter** provides hardware and OS-level metrics for Linux hosts.

### Deployment as DaemonSet

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: node-exporter
  namespace: monitoring
  labels:
    app: node-exporter
spec:
  selector:
    matchLabels:
      app: node-exporter
  template:
    metadata:
      labels:
        app: node-exporter
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "9100"
    spec:
      hostNetwork: true
      hostPID: true
      tolerations:
        - effect: NoSchedule
          operator: Exists
      containers:
      - name: node-exporter
        image: quay.io/prometheus/node-exporter:v1.7.0
        args:
          - '--path.rootfs=/host'
          - '--path.procfs=/host/proc'
          - '--path.sysfs=/host/sys'
          - '--collector.filesystem.mount-points-exclude=^/(dev|proc|sys|var/lib/docker/.+|var/lib/kubelet/.+)($|/)'
        ports:
        - containerPort: 9100
          hostPort: 9100
        resources:
          requests:
            cpu: 100m
            memory: 64Mi
          limits:
            cpu: 250m
            memory: 128Mi
        volumeMounts:
        - name: host
          mountPath: /host
          readOnly: true
          mountPropagation: HostToContainer
      volumes:
      - name: host
        hostPath:
          path: /
```

### Key Node Exporter Metrics

```promql
# CPU usage by node
100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Memory usage by node
(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100

# Disk usage
(node_filesystem_size_bytes{mountpoint="/"} - node_filesystem_avail_bytes{mountpoint="/"})
/ node_filesystem_size_bytes{mountpoint="/"} * 100

# Disk I/O utilization
rate(node_disk_io_time_seconds_total[5m])

# Network received bytes per second
rate(node_network_receive_bytes_total{device!~"lo|veth.*|docker.*|br.*"}[5m])

# Network transmitted bytes per second
rate(node_network_transmit_bytes_total{device!~"lo|veth.*|docker.*|br.*"}[5m])

# System load (1-minute)
node_load1

# Filesystem free space prediction (will run out in 4 hours?)
predict_linear(node_filesystem_avail_bytes{mountpoint="/"}[6h], 4*3600) < 0
```

---

## cAdvisor

**cAdvisor** (Container Advisor) is built into the kubelet and provides container-level resource metrics.

### Key cAdvisor Metrics

```promql
# Container CPU usage
rate(container_cpu_usage_seconds_total{container!="POD", container!=""}[5m])

# Container memory usage (working set)
container_memory_working_set_bytes{container!="POD", container!=""}

# Container memory vs limit
container_memory_working_set_bytes{container!="POD"}
/ on (namespace, pod, container)
kube_pod_container_resource_limits{resource="memory"}

# Container CPU throttling
rate(container_cpu_cfs_throttled_seconds_total[5m])
/ rate(container_cpu_cfs_periods_total[5m])

# Container network I/O
rate(container_network_receive_bytes_total[5m])
rate(container_network_transmit_bytes_total[5m])

# Container filesystem usage
container_fs_usage_bytes

# OOM killed containers
kube_pod_container_status_last_terminated_reason{reason="OOMKilled"}
```

---

## Prometheus Operator

The **Prometheus Operator** makes it easy to run Prometheus on Kubernetes using Custom Resource Definitions (CRDs).

### CRDs Provided

| CRD | Purpose |
|-----|---------|
| **Prometheus** | Defines a Prometheus instance |
| **ServiceMonitor** | Defines how to scrape services |
| **PodMonitor** | Defines how to scrape pods directly |
| **PrometheusRule** | Defines recording and alerting rules |
| **AlertmanagerConfig** | Defines Alertmanager configuration |

### kube-prometheus-stack (Recommended)

The `kube-prometheus-stack` Helm chart deploys the complete monitoring stack:

```bash
# Add the Helm repository
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install with custom values
helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --values values.yaml
```

```yaml
# values.yaml
prometheus:
  prometheusSpec:
    retention: 30d
    storageSpec:
      volumeClaimTemplate:
        spec:
          accessModes: ["ReadWriteOnce"]
          resources:
            requests:
              storage: 50Gi
    resources:
      requests:
        cpu: 500m
        memory: 2Gi
      limits:
        cpu: 2
        memory: 4Gi

grafana:
  adminPassword: "supersecret"
  persistence:
    enabled: true
    size: 10Gi
  dashboardProviders:
    dashboardproviders.yaml:
      apiVersion: 1
      providers:
        - name: 'custom'
          folder: 'Custom'
          type: file
          options:
            path: /var/lib/grafana/dashboards/custom

alertmanager:
  alertmanagerSpec:
    storage:
      volumeClaimTemplate:
        spec:
          accessModes: ["ReadWriteOnce"]
          resources:
            requests:
              storage: 5Gi

# Enable all default rules
defaultRules:
  create: true
  rules:
    alertmanager: true
    etcd: true
    configReloaders: true
    general: true
    k8s: true
    kubeApiserver: true
    kubeApiserverBurnrate: true
    kubeApiserverHistogram: true
    kubeApiserverSlos: true
    kubeControllerManager: true
    kubelet: true
    kubeProxy: true
    kubeScheduler: true
    kubeStateMetrics: true
    network: true
    node: true
    nodeExporterAlerting: true
    nodeExporterRecording: true
    prometheus: true
    prometheusOperator: true
```

### ServiceMonitor Example

A ServiceMonitor tells Prometheus how to scrape a Kubernetes service:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: my-app
  namespace: monitoring
  labels:
    release: monitoring  # Must match Prometheus Operator's serviceMonitorSelector
spec:
  namespaceSelector:
    matchNames:
      - production
  selector:
    matchLabels:
      app: my-app
  endpoints:
    - port: http-metrics    # Name of the service port
      path: /metrics
      interval: 15s
      scrapeTimeout: 10s
      honorLabels: true
      metricRelabelings:
        - sourceLabels: [__name__]
          regex: 'go_gc_.*'
          action: drop
```

### PodMonitor Example

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PodMonitor
metadata:
  name: my-app-pods
  namespace: monitoring
spec:
  namespaceSelector:
    matchNames:
      - production
  selector:
    matchLabels:
      app: my-app
  podMetricsEndpoints:
    - port: metrics
      path: /metrics
      interval: 30s
```

### PrometheusRule Example

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: my-app-alerts
  namespace: monitoring
  labels:
    release: monitoring
spec:
  groups:
    - name: my-app.rules
      rules:
        - alert: MyAppHighErrorRate
          expr: |
            sum(rate(http_requests_total{job="my-app", status=~"5.."}[5m]))
            / sum(rate(http_requests_total{job="my-app"}[5m])) > 0.05
          for: 5m
          labels:
            severity: critical
            team: backend
          annotations:
            summary: "High error rate on my-app"
            description: "Error rate is {{ $value | humanizePercentage }}"
            runbook_url: "https://wiki.example.com/runbooks/my-app-errors"

        - alert: MyAppPodCrashLooping
          expr: |
            increase(kube_pod_container_status_restarts_total{namespace="production", pod=~"my-app.*"}[1h]) > 5
          for: 5m
          labels:
            severity: critical
          annotations:
            summary: "Pod {{ $labels.pod }} is crash looping"
            description: "Pod has restarted {{ $value }} times in the last hour"

        - alert: MyAppHighMemoryUsage
          expr: |
            container_memory_working_set_bytes{namespace="production", container="my-app"}
            / on (namespace, pod, container)
            kube_pod_container_resource_limits{resource="memory"}
            > 0.9
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "High memory usage on {{ $labels.pod }}"
            description: "Memory usage is at {{ $value | humanizePercentage }} of limit"
```

---

## Grafana Dashboards for Kubernetes

### Essential Dashboards

Install these community dashboards from [grafana.com/dashboards](https://grafana.com/dashboards):

| Dashboard | ID | Description |
|-----------|-----|------------|
| **Kubernetes Cluster Overview** | 7249 | Cluster-wide resource usage |
| **Node Exporter Full** | 1860 | Detailed node metrics |
| **Kubernetes Pod Resources** | 6879 | Pod CPU/memory details |
| **Kubernetes Namespace Resources** | 12117 | Resources by namespace |
| **CoreDNS** | 5926 | DNS performance |
| **ETCD** | 3070 | etcd cluster health |

### Custom K8s Dashboard Queries

**Cluster Overview:**
```promql
# Total cluster CPU usage
sum(rate(container_cpu_usage_seconds_total{container!="POD", container!=""}[5m]))

# Total cluster memory usage
sum(container_memory_working_set_bytes{container!="POD", container!=""})

# Total running pods
count(kube_pod_status_phase{phase="Running"} == 1)

# Cluster CPU utilization percentage
sum(rate(container_cpu_usage_seconds_total{container!="POD", container!=""}[5m]))
/ sum(kube_node_status_allocatable{resource="cpu"}) * 100
```

**Namespace Overview:**
```promql
# CPU usage by namespace
sum by (namespace) (rate(container_cpu_usage_seconds_total{container!="POD", container!=""}[5m]))

# Memory usage by namespace
sum by (namespace) (container_memory_working_set_bytes{container!="POD", container!=""})

# Pod count by namespace
count by (namespace) (kube_pod_status_phase{phase="Running"} == 1)
```

**Pod Health:**
```promql
# Pod restart rate
sum by (namespace, pod) (increase(kube_pod_container_status_restarts_total[1h]))

# Pods not ready
kube_pod_status_ready{condition="true"} == 0

# Container CPU throttling
sum by (namespace, pod) (rate(container_cpu_cfs_throttled_seconds_total[5m]))
```

---

## Logging in Kubernetes

### Kubernetes Logging Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Kubernetes Node                    │
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │ Pod A    │  │ Pod B    │  │ Pod C    │          │
│  │ stdout → │  │ stdout → │  │ stdout → │          │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘          │
│       │              │              │                │
│       ▼              ▼              ▼                │
│  /var/log/containers/*.log                           │
│       │                                              │
│       ▼                                              │
│  ┌──────────────────────────────────────────┐       │
│  │  Fluent Bit (DaemonSet)                  │       │
│  │  - Reads container logs                   │       │
│  │  - Enriches with K8s metadata            │       │
│  │  - Forwards to backend                    │       │
│  └─────────────────────┬────────────────────┘       │
│                        │                             │
└────────────────────────┼─────────────────────────────┘
                         │
              ┌──────────▼──────────┐
              │  Loki / Elasticsearch│
              └─────────────────────┘
```

### Fluent Bit DaemonSet for Kubernetes

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluent-bit
  namespace: logging
spec:
  selector:
    matchLabels:
      app: fluent-bit
  template:
    metadata:
      labels:
        app: fluent-bit
    spec:
      serviceAccountName: fluent-bit
      tolerations:
        - key: node-role.kubernetes.io/master
          effect: NoSchedule
      containers:
      - name: fluent-bit
        image: fluent/fluent-bit:2.2
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 256Mi
        volumeMounts:
        - name: varlog
          mountPath: /var/log
        - name: varlibdockercontainers
          mountPath: /var/lib/docker/containers
          readOnly: true
        - name: config
          mountPath: /fluent-bit/etc/
      volumes:
      - name: varlog
        hostPath:
          path: /var/log
      - name: varlibdockercontainers
        hostPath:
          path: /var/lib/docker/containers
      - name: config
        configMap:
          name: fluent-bit-config
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluent-bit-config
  namespace: logging
data:
  fluent-bit.conf: |
    [SERVICE]
        Flush         5
        Log_Level     info
        Parsers_File  parsers.conf

    [INPUT]
        Name              tail
        Tag               kube.*
        Path              /var/log/containers/*.log
        Parser            cri
        DB                /var/log/fluent-bit-kube.db
        Mem_Buf_Limit     50MB
        Skip_Long_Lines   On
        Refresh_Interval  10

    [FILTER]
        Name                kubernetes
        Match               kube.*
        Kube_URL            https://kubernetes.default.svc:443
        Kube_CA_File        /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
        Kube_Token_File     /var/run/secrets/kubernetes.io/serviceaccount/token
        Merge_Log           On
        K8S-Logging.Parser  On
        K8S-Logging.Exclude On
        Labels              On
        Annotations         Off

    [OUTPUT]
        Name            loki
        Match           *
        Host            loki.logging.svc.cluster.local
        Port            3100
        Labels          job=fluent-bit, namespace=$kubernetes['namespace_name'], pod=$kubernetes['pod_name'], container=$kubernetes['container_name']
        Auto_Kubernetes_Labels On

  parsers.conf: |
    [PARSER]
        Name        cri
        Format      regex
        Regex       ^(?<time>[^ ]+) (?<stream>stdout|stderr) (?<logtag>[^ ]*) (?<message>.*)$
        Time_Key    time
        Time_Format %Y-%m-%dT%H:%M:%S.%L%z
```

### Loki for Kubernetes

```bash
# Install Loki stack via Helm
helm repo add grafana https://grafana.github.io/helm-charts

helm install loki grafana/loki-stack \
  --namespace logging \
  --create-namespace \
  --set promtail.enabled=true \
  --set grafana.enabled=false  # Use existing Grafana
```

### Useful LogQL Queries for Kubernetes

```logql
# All logs from a specific namespace
{namespace="production"}

# Error logs from a specific pod
{namespace="production", pod="api-6d4f5b7c8-abc12"} |= "error"

# All logs from a deployment (using label)
{namespace="production", app="checkout-service"}

# Parse JSON logs and filter
{namespace="production", app="checkout-service"} | json | level="ERROR"

# Count error logs per service in the last hour
sum by (app) (count_over_time({namespace="production"} |= "error" [1h]))

# Logs around a specific time (for incident investigation)
{namespace="production", app="checkout-service"} | json | ts >= "2024-01-15T10:20:00Z" and ts <= "2024-01-15T10:30:00Z"
```

---

## Kubernetes Events

Kubernetes events provide visibility into cluster operations:

```bash
# View recent events
kubectl get events -n production --sort-by='.lastTimestamp'

# Watch events in real-time
kubectl get events -n production --watch

# Common important events:
#   - Pod scheduling failures
#   - Image pull errors
#   - OOMKilled
#   - Liveness/readiness probe failures
#   - Volume mount failures
```

### Exporting Events as Metrics

Use **kube-events-exporter** or **kubernetes-event-exporter**:

```yaml
# kubernetes-event-exporter config
apiVersion: v1
kind: ConfigMap
metadata:
  name: event-exporter-config
  namespace: monitoring
data:
  config.yaml: |
    logLevel: error
    logFormat: json
    route:
      routes:
        - match:
            - receiver: "loki"
    receivers:
      - name: "loki"
        loki:
          url: http://loki:3100/loki/api/v1/push
          streamLabels:
            source: kubernetes-events
```

---

## Key Takeaways

1. Kubernetes monitoring requires **four layers**: infrastructure, K8s state, containers, and applications
2. **Metrics Server** is for autoscaling, **Prometheus** is for full monitoring
3. **kube-state-metrics** provides K8s object state (deployment replicas, pod status, etc.)
4. **Node Exporter** provides host-level metrics (CPU, memory, disk, network)
5. **cAdvisor** (built into kubelet) provides container-level resource metrics
6. The **Prometheus Operator** with CRDs (ServiceMonitor, PrometheusRule) is the Kubernetes-native way to configure monitoring
7. **kube-prometheus-stack** Helm chart is the recommended all-in-one deployment
8. Use **Fluent Bit as a DaemonSet** for log collection, shipping to Loki or Elasticsearch
9. Import **community Grafana dashboards** as a starting point, then customize
10. Monitor **Kubernetes events** for cluster operational issues

---

**Previous Lesson:** [07 - Alerting](07-alerting.md)
**Next Lesson:** [09 - Observability Best Practices](09-observability-best-practices.md)
