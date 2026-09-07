# Lesson 06: Prometheus Deep Dive

## Table of Contents

- [Architecture Deep Dive](#architecture-deep-dive)
- [Configuration](#configuration)
- [Service Discovery](#service-discovery)
- [Scraping Mechanics](#scraping-mechanics)
- [Storage and TSDB](#storage-and-tsdb)
- [Federation](#federation)
- [Long-Term Storage: Thanos](#long-term-storage-thanos)
- [Long-Term Storage: Cortex/Mimir](#long-term-storage-cortexmimir)
- [High Availability](#high-availability)
- [Security](#security)
- [Key Takeaways](#key-takeaways)

---

## Architecture Deep Dive

### Component Overview

```
                    ┌──────────────────────────────────────────────┐
                    │              Prometheus Server                │
                    │                                              │
                    │  ┌──────────┐  ┌──────────┐  ┌───────────┐  │
Targets ◀──scrape──│  │ Retrieval │  │  TSDB    │  │ HTTP      │──│──▶ Grafana
  /metrics         │  │ (scraper) │  │ (storage)│  │ Server    │  │    PromQL
                    │  └────┬─────┘  └────▲─────┘  │ (query)   │  │    API
                    │       │             │         └───────────┘  │
                    │       ▼             │                        │
                    │  ┌──────────────────┴──┐                    │
Service ────────────│  │ Service Discovery   │                    │
Discovery           │  │ (find targets)      │                    │
(K8s, Consul,       │  └─────────────────────┘                    │
 DNS, file)         │                                              │
                    │  ┌─────────────────────┐                    │
                    │  │ Rule Engine         │                    │
                    │  │ - Recording rules   │                    │
                    │  │ - Alerting rules    │──────────────────────▶ Alertmanager
                    │  └─────────────────────┘                    │
                    └──────────────────────────────────────────────┘
```

### How Prometheus Works (Request Flow)

```
1. Service Discovery finds targets (pods, services, nodes)
2. Retrieval scrapes /metrics from each target every scrape_interval
3. Scraped data is stored in the TSDB (Time Series Database)
4. Rule Engine evaluates recording and alerting rules periodically
5. HTTP Server serves PromQL queries from Grafana/API clients
6. Alertmanager receives firing alerts and routes notifications
```

### TSDB Data Model

```
Metric: http_requests_total{method="GET", endpoint="/api/users", status="200", instance="app:8080"}

This is a TIME SERIES:
  (metric_name, label_set) → [(timestamp, value), (timestamp, value), ...]

  1705312800 → 1000
  1705312815 → 1005    (+5 in 15s)
  1705312830 → 1012    (+7 in 15s)
  1705312845 → 1020    (+8 in 15s)
```

---

## Configuration

### Complete prometheus.yml

```yaml
# Global configuration
global:
  scrape_interval: 15s         # Default scrape interval
  scrape_timeout: 10s          # Timeout for each scrape
  evaluation_interval: 15s     # How often to evaluate rules
  external_labels:             # Labels added to all time series and alerts
    cluster: production-us-east-1
    environment: production

# Alertmanager configuration
alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager-0:9093
          - alertmanager-1:9093
      timeout: 10s
      api_version: v2

# Rule files
rule_files:
  - /etc/prometheus/rules/recording_rules.yml
  - /etc/prometheus/rules/alerting_rules.yml
  - /etc/prometheus/rules/*.yml

# Scrape configurations
scrape_configs:
  # ─────────────────────────────────────
  # Prometheus self-monitoring
  # ─────────────────────────────────────
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
    metrics_path: /metrics

  # ─────────────────────────────────────
  # Node Exporter (system metrics)
  # ─────────────────────────────────────
  - job_name: 'node-exporter'
    static_configs:
      - targets:
        - 'node1:9100'
        - 'node2:9100'
        - 'node3:9100'
        labels:
          datacenter: us-east-1

  # ─────────────────────────────────────
  # Application with custom scrape settings
  # ─────────────────────────────────────
  - job_name: 'my-app'
    scrape_interval: 10s
    scrape_timeout: 5s
    metrics_path: /metrics
    scheme: https
    tls_config:
      ca_file: /etc/prometheus/ca.crt
    basic_auth:
      username: prometheus
      password_file: /etc/prometheus/password
    static_configs:
      - targets: ['app1:8080', 'app2:8080']

  # ─────────────────────────────────────
  # Blackbox exporter (endpoint probing)
  # ─────────────────────────────────────
  - job_name: 'blackbox-http'
    metrics_path: /probe
    params:
      module: [http_2xx]
    static_configs:
      - targets:
        - https://example.com
        - https://api.example.com/health
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: blackbox-exporter:9115

  # ─────────────────────────────────────
  # Kubernetes service discovery (pods)
  # ─────────────────────────────────────
  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      # Only scrape pods with annotation prometheus.io/scrape: "true"
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      # Use custom metrics path if specified
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
      # Use custom port if specified
      - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
        action: replace
        regex: ([^:]+)(?::\d+)?;(\d+)
        replacement: $1:$2
        target_label: __address__
      # Add pod labels
      - action: labelmap
        regex: __meta_kubernetes_pod_label_(.+)
      # Add namespace label
      - source_labels: [__meta_kubernetes_namespace]
        action: replace
        target_label: namespace
      # Add pod name label
      - source_labels: [__meta_kubernetes_pod_name]
        action: replace
        target_label: pod
```

### Relabeling Explained

Relabeling is Prometheus's powerful mechanism for modifying labels during scraping:

```yaml
relabel_configs:
  # KEEP: Only keep targets matching regex
  - source_labels: [__meta_kubernetes_pod_label_app]
    action: keep
    regex: (api|web|worker)

  # DROP: Remove targets matching regex
  - source_labels: [__meta_kubernetes_namespace]
    action: drop
    regex: (kube-system|kube-public)

  # REPLACE: Replace label value
  - source_labels: [__meta_kubernetes_namespace]
    target_label: namespace
    action: replace

  # LABELMAP: Copy metadata labels to target labels
  - action: labelmap
    regex: __meta_kubernetes_pod_label_(.+)
    replacement: k8s_$1

  # HASHMOD: Shard targets across Prometheus instances
  - source_labels: [__address__]
    modulus: 3
    target_label: __tmp_hash
    action: hashmod
  - source_labels: [__tmp_hash]
    regex: 0
    action: keep
```

### metric_relabel_configs (Post-Scrape)

Applied **after** scraping, to filter or modify scraped metrics:

```yaml
metric_relabel_configs:
  # Drop expensive metrics
  - source_labels: [__name__]
    regex: go_gc_.*
    action: drop

  # Drop high-cardinality labels
  - regex: instance
    action: labeldrop

  # Rename a metric
  - source_labels: [__name__]
    regex: old_metric_name
    target_label: __name__
    replacement: new_metric_name
```

---

## Service Discovery

Prometheus automatically discovers scrape targets through various mechanisms.

### Kubernetes SD

```yaml
# Discover all pods
kubernetes_sd_configs:
  - role: pod
    namespaces:
      names: [production, staging]

# Discover services
kubernetes_sd_configs:
  - role: service

# Discover endpoints
kubernetes_sd_configs:
  - role: endpoints

# Discover nodes
kubernetes_sd_configs:
  - role: node

# Discover ingresses
kubernetes_sd_configs:
  - role: ingress
```

### Kubernetes Pod Annotations Pattern

The most common pattern: pods opt-in to scraping via annotations:

```yaml
# Pod/Deployment manifest
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  template:
    metadata:
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
        prometheus.io/path: "/metrics"
    spec:
      containers:
      - name: my-app
        image: my-app:latest
        ports:
        - containerPort: 8080
```

### Consul SD

```yaml
- job_name: 'consul-services'
  consul_sd_configs:
    - server: consul:8500
      services: []  # Empty = all services
  relabel_configs:
    - source_labels: [__meta_consul_service]
      target_label: service
    - source_labels: [__meta_consul_dc]
      target_label: datacenter
    - source_labels: [__meta_consul_tags]
      regex: .*,prometheus,.*
      action: keep
```

### DNS SD

```yaml
- job_name: 'dns-discovery'
  dns_sd_configs:
    - names:
      - 'api.service.consul'
      - 'web.service.consul'
      type: SRV
      refresh_interval: 30s
```

### File SD (Dynamic File-Based Discovery)

```yaml
- job_name: 'file-discovery'
  file_sd_configs:
    - files:
      - /etc/prometheus/targets/*.json
      refresh_interval: 5m
```

```json
// /etc/prometheus/targets/apps.json
[
  {
    "targets": ["app1:8080", "app2:8080"],
    "labels": {
      "service": "api",
      "environment": "production"
    }
  },
  {
    "targets": ["worker1:8080", "worker2:8080"],
    "labels": {
      "service": "worker",
      "environment": "production"
    }
  }
]
```

---

## Scraping Mechanics

### The Scrape Lifecycle

```
1. Service Discovery → Find target: app:8080
2. Relabeling → Apply relabel_configs
3. HTTP Request → GET http://app:8080/metrics
4. Parse Response → Parse Prometheus text format
5. Post-Relabeling → Apply metric_relabel_configs
6. Append to TSDB → Store time series with timestamp
7. Update up metric → up{job="my-app",instance="app:8080"} = 1
```

### The /metrics Endpoint

Applications expose metrics in Prometheus text format:

```
# HELP http_requests_total Total number of HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="/api/users",status="200"} 15234
http_requests_total{method="POST",endpoint="/api/orders",status="201"} 892
http_requests_total{method="GET",endpoint="/api/users",status="500"} 12

# HELP http_request_duration_seconds HTTP request duration in seconds
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{method="GET",le="0.01"} 1000
http_request_duration_seconds_bucket{method="GET",le="0.05"} 4500
http_request_duration_seconds_bucket{method="GET",le="0.1"} 8000
http_request_duration_seconds_bucket{method="GET",le="0.5"} 9500
http_request_duration_seconds_bucket{method="GET",le="1"} 9900
http_request_duration_seconds_bucket{method="GET",le="+Inf"} 10000
http_request_duration_seconds_sum{method="GET"} 245.67
http_request_duration_seconds_count{method="GET"} 10000

# HELP process_resident_memory_bytes Resident memory size in bytes
# TYPE process_resident_memory_bytes gauge
process_resident_memory_bytes 52428800

# HELP up Target status (1 = up, 0 = down)
# TYPE up gauge
up 1
```

### Scrape Meta-Metrics

Prometheus tracks scrape health automatically:

```promql
# Is the target up?
up{job="my-app"}

# How long did the last scrape take?
scrape_duration_seconds{job="my-app"}

# How many samples were scraped?
scrape_samples_scraped{job="my-app"}

# How many time series were created?
scrape_series_added{job="my-app"}
```

---

## Storage and TSDB

### TSDB Architecture

```
Data Directory: /prometheus/data/
├── 01BKGV7JBM69T2G1BGBGM6KB12/   # Block (2 hours of data)
│   ├── meta.json                    # Block metadata
│   ├── chunks/                      # Compressed time series chunks
│   │   └── 000001
│   ├── index                        # Inverted index for fast label lookups
│   └── tombstones                   # Deleted series markers
├── 01BKGTZQ1SYQJTR4PB43C8PD98/   # Another 2-hour block
├── 01BKGTZQ1ZCJTR4PB43C8PD99/   # Compacted block
├── wal/                            # Write-Ahead Log
│   ├── 00000001
│   └── 00000002
└── lock
```

### Storage Configuration

```yaml
# Command-line flags
prometheus:
  args:
    - '--storage.tsdb.path=/prometheus/data'
    - '--storage.tsdb.retention.time=30d'        # Keep data for 30 days
    - '--storage.tsdb.retention.size=50GB'        # Or limit by size
    - '--storage.tsdb.min-block-duration=2h'      # Minimum block size
    - '--storage.tsdb.max-block-duration=72h'     # Maximum block size (after compaction)
    - '--storage.tsdb.wal-compression'            # Compress WAL
```

### Storage Sizing

```
Formula:
  disk_space = retention_time × ingestion_rate × bytes_per_sample

Example:
  Retention: 15 days
  Active time series: 1,000,000
  Scrape interval: 15s
  Bytes per sample: ~2 bytes (after compression)

  Samples per day = 1,000,000 × (86400 / 15) = 5,760,000,000
  Bytes per day = 5,760,000,000 × 2 = ~11.5 GB
  Total = 15 × 11.5 GB = ~172 GB

  Add 20% overhead for WAL and compaction:
  Total = ~206 GB
```

### Useful TSDB Admin Commands

```bash
# Check TSDB status
curl http://localhost:9090/api/v1/status/tsdb | jq

# Delete time series (requires --web.enable-admin-api)
curl -X POST 'http://localhost:9090/api/v1/admin/tsdb/delete_series?match[]={job="old-service"}'

# Clean tombstones
curl -X POST http://localhost:9090/api/v1/admin/tsdb/clean_tombstones

# Snapshot (backup)
curl -X POST http://localhost:9090/api/v1/admin/tsdb/snapshot
```

---

## Federation

Federation allows one Prometheus server to scrape selected metrics from another Prometheus server. Useful for hierarchical setups.

### Hierarchical Federation

```
                    ┌──────────────────┐
                    │  Global          │
                    │  Prometheus      │  ← Aggregated metrics only
                    └────────┬─────────┘
                             │ federate
                ┌────────────┼────────────┐
                │            │            │
    ┌───────────▼──┐  ┌─────▼──────┐  ┌──▼───────────┐
    │ DC1          │  │ DC2        │  │ DC3          │
    │ Prometheus   │  │ Prometheus │  │ Prometheus   │
    └──────────────┘  └────────────┘  └──────────────┘
         │                  │                │
    Local targets      Local targets    Local targets
```

### Federation Configuration

```yaml
# Global Prometheus: scrape federated metrics from DC Prometheus instances
scrape_configs:
  - job_name: 'federate-dc1'
    scrape_interval: 30s
    honor_labels: true
    metrics_path: /federate
    params:
      'match[]':
        # Only pull aggregated recording rules
        - '{__name__=~"job:.*"}'
        - '{__name__=~"instance:.*"}'
        # Pull specific important metrics
        - 'up'
    static_configs:
      - targets:
        - 'prometheus-dc1:9090'
        labels:
          datacenter: dc1

  - job_name: 'federate-dc2'
    scrape_interval: 30s
    honor_labels: true
    metrics_path: /federate
    params:
      'match[]':
        - '{__name__=~"job:.*"}'
        - '{__name__=~"instance:.*"}'
    static_configs:
      - targets:
        - 'prometheus-dc2:9090'
        labels:
          datacenter: dc2
```

---

## Long-Term Storage: Thanos

**Thanos** extends Prometheus with long-term storage, global query view, and high availability.

### Thanos Architecture

```
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ Prometheus A │   │ Prometheus B │   │ Prometheus C │
│ + Sidecar    │   │ + Sidecar    │   │ + Sidecar    │
└──────┬───────┘   └──────┬───────┘   └──────┬───────┘
       │                  │                   │
       │ Upload blocks    │                   │
       ▼                  ▼                   ▼
    ┌─────────────────────────────────────────────┐
    │              Object Storage (S3/GCS)        │
    └─────────────────────┬───────────────────────┘
                          │
              ┌───────────┼───────────┐
              │           │           │
       ┌──────▼──┐  ┌─────▼────┐  ┌──▼──────┐
       │ Thanos  │  │ Thanos   │  │ Thanos  │
       │ Store   │  │ Compact  │  │ Query   │──▶ Grafana
       │ Gateway │  │          │  │         │
       └─────────┘  └──────────┘  └─────────┘
```

### Thanos Components

| Component | Purpose |
|-----------|---------|
| **Sidecar** | Runs alongside Prometheus, uploads blocks to object storage |
| **Store Gateway** | Serves historical data from object storage |
| **Query** | Global query view across all Prometheus instances and Store Gateways |
| **Compactor** | Compacts and downsamples data in object storage |
| **Ruler** | Evaluates recording and alerting rules against Thanos data |

### Thanos Sidecar with Prometheus

```yaml
# docker-compose.yml
services:
  prometheus:
    image: prom/prometheus:v2.48.0
    volumes:
      - prometheus-data:/prometheus
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.min-block-duration=2h'
      - '--storage.tsdb.max-block-duration=2h'  # Required for Thanos
      - '--web.enable-lifecycle'

  thanos-sidecar:
    image: thanosio/thanos:v0.32.0
    volumes:
      - prometheus-data:/prometheus
      - ./bucket.yml:/etc/thanos/bucket.yml
    command:
      - sidecar
      - --prometheus.url=http://prometheus:9090
      - --tsdb.path=/prometheus
      - --objstore.config-file=/etc/thanos/bucket.yml
      - --grpc-address=0.0.0.0:10901
      - --http-address=0.0.0.0:10902

  thanos-query:
    image: thanosio/thanos:v0.32.0
    command:
      - query
      - --grpc-address=0.0.0.0:10901
      - --http-address=0.0.0.0:9090
      - --store=thanos-sidecar:10901
      - --store=thanos-store:10901
    ports:
      - "19090:9090"

  thanos-store:
    image: thanosio/thanos:v0.32.0
    volumes:
      - ./bucket.yml:/etc/thanos/bucket.yml
    command:
      - store
      - --objstore.config-file=/etc/thanos/bucket.yml
      - --grpc-address=0.0.0.0:10901
      - --http-address=0.0.0.0:10902
```

```yaml
# bucket.yml (S3 configuration)
type: S3
config:
  bucket: thanos-metrics
  endpoint: s3.amazonaws.com
  region: us-east-1
  access_key: ${AWS_ACCESS_KEY_ID}
  secret_key: ${AWS_SECRET_ACCESS_KEY}
```

---

## Long-Term Storage: Cortex/Mimir

**Grafana Mimir** (successor to Cortex) is a horizontally-scalable, long-term storage solution for Prometheus.

### Mimir vs Thanos

| Feature | Thanos | Mimir |
|---------|--------|-------|
| **Architecture** | Sidecar + object storage | Push-based (remote write) |
| **Prometheus Changes** | Minimal (sidecar) | Requires remote_write config |
| **Multi-tenancy** | Limited | Native |
| **Query Performance** | Good | Excellent (built-in caching) |
| **Complexity** | Moderate | Higher (more components) |
| **Best For** | Extending existing Prometheus | Large-scale, multi-tenant |

### Remote Write Configuration

```yaml
# prometheus.yml
remote_write:
  - url: http://mimir:9009/api/v1/push
    headers:
      X-Scope-OrgID: my-tenant
    queue_config:
      max_samples_per_send: 1000
      batch_send_deadline: 5s
      min_backoff: 30ms
      max_backoff: 5s
    write_relabel_configs:
      # Only send specific metrics to long-term storage
      - source_labels: [__name__]
        regex: '(http_requests_total|http_request_duration_seconds_.*|up)'
        action: keep
```

---

## High Availability

### Prometheus HA with Thanos

Run two identical Prometheus instances scraping the same targets:

```yaml
# Prometheus A
global:
  external_labels:
    cluster: production
    replica: A  # Different replica label

# Prometheus B
global:
  external_labels:
    cluster: production
    replica: B  # Different replica label
```

Thanos Query deduplicates data:
```bash
thanos query \
  --store=prometheus-a-sidecar:10901 \
  --store=prometheus-b-sidecar:10901 \
  --query.replica-label=replica  # Deduplicate on replica label
```

### Alertmanager HA

```yaml
# Run multiple Alertmanager instances in a cluster
alertmanager:
  command:
    - '--cluster.peer=alertmanager-0:9094'
    - '--cluster.peer=alertmanager-1:9094'
    - '--cluster.listen-address=0.0.0.0:9094'
```

---

## Security

### Authentication

```yaml
# Enable basic auth for scrape targets
scrape_configs:
  - job_name: 'secure-app'
    basic_auth:
      username: prometheus
      password_file: /etc/prometheus/password

# Or use bearer token
  - job_name: 'secure-app-token'
    authorization:
      type: Bearer
      credentials_file: /etc/prometheus/token
```

### TLS

```yaml
# Scrape over HTTPS
scrape_configs:
  - job_name: 'tls-app'
    scheme: https
    tls_config:
      ca_file: /etc/prometheus/ca.crt
      cert_file: /etc/prometheus/client.crt
      key_file: /etc/prometheus/client.key
      insecure_skip_verify: false

# Prometheus web server TLS
# web-config.yml
tls_server_config:
  cert_file: /etc/prometheus/server.crt
  key_file: /etc/prometheus/server.key
  client_auth_type: RequireAndVerifyClientCert
  client_ca_file: /etc/prometheus/ca.crt
```

### Prometheus with Kubernetes RBAC

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: prometheus
rules:
  - apiGroups: [""]
    resources:
      - nodes
      - nodes/metrics
      - services
      - endpoints
      - pods
    verbs: ["get", "list", "watch"]
  - apiGroups: [""]
    resources:
      - configmaps
    verbs: ["get"]
  - nonResourceURLs: ["/metrics"]
    verbs: ["get"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: prometheus
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: prometheus
subjects:
  - kind: ServiceAccount
    name: prometheus
    namespace: monitoring
```

---

## Key Takeaways

1. Prometheus uses a **pull model** with service discovery to find and scrape targets
2. **Relabeling** is powerful — use `relabel_configs` for target filtering and `metric_relabel_configs` for metric filtering
3. **Kubernetes service discovery** with pod annotations is the standard pattern
4. The **TSDB** stores data in 2-hour blocks with WAL for durability
5. **Federation** enables hierarchical Prometheus setups across data centers
6. For **long-term storage**, choose **Thanos** (sidecar pattern) or **Mimir** (remote write)
7. Run Prometheus in **HA pairs** with Thanos for deduplication
8. Always configure proper **RBAC and TLS** in production environments

---

**Previous Lesson:** [05 - Grafana](05-grafana.md)
**Next Lesson:** [07 - Alerting](07-alerting.md)
