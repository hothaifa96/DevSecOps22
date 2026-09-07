# Lesson 03: Metrics

## Table of Contents

- [What Are Metrics?](#what-are-metrics)
- [Metric Types](#metric-types)
- [Prometheus Architecture](#prometheus-architecture)
- [PromQL Basics](#promql-basics)
- [Exporters](#exporters)
- [Recording Rules](#recording-rules)
- [Alerting Rules](#alerting-rules)
- [Metrics Naming Conventions](#metrics-naming-conventions)
- [Key Takeaways](#key-takeaways)

---

## What Are Metrics?

Metrics are **numeric measurements** collected at regular intervals (typically every 15-60 seconds). They represent the state or behavior of a system over time.

### Why Metrics?

| Characteristic | Metrics | Logs |
|---------------|---------|------|
| **Storage Cost** | Fixed (constant per time series) | Variable (grows with traffic) |
| **Aggregation** | Native (sum, avg, percentile) | Requires post-processing |
| **Alerting** | Purpose-built | Possible but less efficient |
| **Detail** | Low (aggregated values) | High (individual events) |
| **Query Speed** | Very fast | Depends on indexing |
| **Best For** | Trends, dashboards, alerting | Debugging, audit trails |

### Metrics in the Real World

```
Your car's dashboard shows METRICS:
  - Speed: 65 mph (gauge)
  - Odometer: 45,230 miles (counter)
  - Fuel level: 75% (gauge)
  - Trip duration histogram: average trip is 25 minutes

Your car's OBD-II diagnostic port shows LOGS:
  - "2024-01-15 10:23:45 - Cylinder 3 misfire detected"
  - "2024-01-15 10:23:46 - O2 sensor reading: 0.45V"
```

---

## Metric Types

### 1. Counter

A counter is a **cumulative metric that only goes up** (or resets to zero on restart).

```
Use for: Total requests, total errors, bytes transferred

Example:
  http_requests_total = 0
  http_requests_total = 1    (after 1st request)
  http_requests_total = 2    (after 2nd request)
  http_requests_total = 100  (after 100th request)
  http_requests_total = 0    (service restarted)
  http_requests_total = 1    (after 1st request post-restart)
```

```python
# Python (prometheus_client)
from prometheus_client import Counter

REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

# Increment
REQUEST_COUNT.labels(method='GET', endpoint='/api/users', status='200').inc()
REQUEST_COUNT.labels(method='POST', endpoint='/api/orders', status='201').inc()
```

**PromQL with Counters:**
```promql
# Rate of requests per second over the last 5 minutes
rate(http_requests_total[5m])

# Total requests in the last hour
increase(http_requests_total[1h])

# Error rate percentage
rate(http_requests_total{status=~"5.."}[5m])
/
rate(http_requests_total[5m])
* 100
```

### 2. Gauge

A gauge is a metric that can **go up and down**. It represents a current value.

```
Use for: Temperature, memory usage, active connections, queue size

Example:
  active_connections = 5
  active_connections = 8   (3 new connections)
  active_connections = 6   (2 disconnected)
  active_connections = 12  (6 new connections)
```

```python
from prometheus_client import Gauge

ACTIVE_CONNECTIONS = Gauge(
    'active_connections',
    'Number of active connections',
    ['service']
)

# Set absolute value
ACTIVE_CONNECTIONS.labels(service='api').set(42)

# Increment / Decrement
ACTIVE_CONNECTIONS.labels(service='api').inc()   # +1
ACTIVE_CONNECTIONS.labels(service='api').dec()   # -1
ACTIVE_CONNECTIONS.labels(service='api').inc(5)  # +5
```

**PromQL with Gauges:**
```promql
# Current value
node_memory_MemAvailable_bytes

# Average over time
avg_over_time(node_cpu_seconds_total[5m])

# Min/Max over time
min_over_time(node_memory_MemAvailable_bytes[1h])
max_over_time(node_memory_MemAvailable_bytes[1h])
```

### 3. Histogram

A histogram counts observations into **configurable buckets** and provides a sum and count.

```
Use for: Request latency, response sizes

Buckets for HTTP latency (seconds):
  le="0.01"   → 1000 requests  (under 10ms)
  le="0.05"   → 4500 requests  (under 50ms)
  le="0.1"    → 8000 requests  (under 100ms)
  le="0.5"    → 9500 requests  (under 500ms)
  le="1.0"    → 9900 requests  (under 1s)
  le="+Inf"   → 10000 requests (all requests)

  _sum  = 245.67 seconds (total time)
  _count = 10000 (total requests)
```

```python
from prometheus_client import Histogram

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint'],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# Observe a value
REQUEST_LATENCY.labels(method='GET', endpoint='/api/users').observe(0.045)

# Use as a decorator
@REQUEST_LATENCY.labels(method='GET', endpoint='/api/users').time()
def get_users():
    # ... your code ...
    pass
```

**PromQL with Histograms:**
```promql
# 95th percentile latency
histogram_quantile(0.95,
  rate(http_request_duration_seconds_bucket[5m])
)

# 99th percentile latency by endpoint
histogram_quantile(0.99,
  sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint)
)

# Average latency
rate(http_request_duration_seconds_sum[5m])
/
rate(http_request_duration_seconds_count[5m])

# Requests per second
rate(http_request_duration_seconds_count[5m])
```

### 4. Summary

A summary is similar to a histogram but calculates **quantiles on the client side**.

```
Use for: When you need exact quantiles and don't need to aggregate across instances

Output:
  http_request_duration_seconds{quantile="0.5"}  = 0.045
  http_request_duration_seconds{quantile="0.9"}  = 0.12
  http_request_duration_seconds{quantile="0.99"} = 0.85
  http_request_duration_seconds_sum   = 245.67
  http_request_duration_seconds_count = 10000
```

```python
from prometheus_client import Summary

REQUEST_LATENCY = Summary(
    'http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint']
)

REQUEST_LATENCY.labels(method='GET', endpoint='/api/users').observe(0.045)
```

### Histogram vs Summary

| Feature | Histogram | Summary |
|---------|-----------|---------|
| **Quantile Calculation** | Server-side (PromQL) | Client-side |
| **Aggregation** | Can aggregate across instances | Cannot aggregate |
| **Cost** | Fixed buckets (predictable) | Streaming quantiles (more CPU) |
| **Recommendation** | Preferred in most cases | Rare use cases |

---

## Prometheus Architecture

Prometheus is a **pull-based** monitoring system. It scrapes metrics from targets at regular intervals.

```
                              ┌─────────────────┐
                              │   Prometheus     │
                              │   ┌───────────┐  │
                              │   │  TSDB     │  │
  ┌──────────┐  scrape        │   │ (storage) │  │       ┌──────────┐
  │ Target A  │◀──────────────│   └───────────┘  │──────▶│ Grafana  │
  │ /metrics  │               │   ┌───────────┐  │       └──────────┘
  └──────────┘                │   │  Rule     │  │
                              │   │  Engine   │  │       ┌──────────┐
  ┌──────────┐  scrape        │   └───────────┘  │──────▶│Alertmanager│
  │ Target B  │◀──────────────│   ┌───────────┐  │       └──────────┘
  │ /metrics  │               │   │  Service  │  │           │
  └──────────┘                │   │ Discovery │  │       ┌───▼──────┐
                              │   └───────────┘  │       │PagerDuty │
  ┌──────────┐  scrape        │                  │       │Slack     │
  │ Target C  │◀──────────────│                  │       │Email     │
  │ /metrics  │               └─────────────────┘       └──────────┘
  └──────────┘
```

### Key Components

1. **Prometheus Server** — Scrapes and stores time series data
2. **TSDB (Time Series Database)** — Efficient on-disk storage
3. **Service Discovery** — Automatically finds scrape targets
4. **Rule Engine** — Evaluates recording and alerting rules
5. **Alertmanager** — Routes and deduplicates alerts
6. **Client Libraries** — Instrument your applications
7. **Exporters** — Expose metrics from third-party systems

### Pull vs Push Model

```
PULL Model (Prometheus):
  Prometheus ──scrape──▶ Target /metrics
  - Prometheus controls the scrape interval
  - Easy to detect if a target is down (scrape fails)
  - No need to configure targets to "push" anywhere

PUSH Model (Datadog, InfluxDB):
  Application ──push──▶ Metrics Backend
  - Application controls when to send
  - Works for short-lived jobs (batch, serverless)
  - Target must know where to push
```

### Basic Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s       # How often to scrape targets
  evaluation_interval: 15s   # How often to evaluate rules
  scrape_timeout: 10s        # Timeout for each scrape

# Alertmanager configuration
alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

# Recording and alerting rules
rule_files:
  - "recording_rules.yml"
  - "alerting_rules.yml"

# Scrape configurations
scrape_configs:
  # Prometheus scrapes itself
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  # Scrape application metrics
  - job_name: 'my-app'
    scrape_interval: 10s
    static_configs:
      - targets: ['app:8080']
    metrics_path: /metrics

  # Scrape node exporter
  - job_name: 'node-exporter'
    static_configs:
      - targets:
        - 'node1:9100'
        - 'node2:9100'
        - 'node3:9100'

  # Kubernetes service discovery
  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_port]
        action: replace
        target_label: __address__
        regex: (.+)
```

---

## PromQL Basics

PromQL (Prometheus Query Language) is a powerful functional query language for selecting and aggregating time series data.

### Data Types

1. **Instant Vector** — A set of time series with a single sample per series at a given timestamp
2. **Range Vector** — A set of time series with a range of samples over time
3. **Scalar** — A simple numeric floating-point value
4. **String** — A simple string value (rarely used)

### Basic Selectors

```promql
# Select all time series with a given metric name
http_requests_total

# Filter by label (exact match)
http_requests_total{method="GET"}

# Filter by label (regex match)
http_requests_total{status=~"5.."}

# Filter by label (not equal)
http_requests_total{method!="OPTIONS"}

# Filter by label (negative regex)
http_requests_total{endpoint!~"/health|/ready"}

# Multiple label filters
http_requests_total{method="GET", status="200", endpoint="/api/users"}
```

### Range Vectors

```promql
# Select 5-minute range of data
http_requests_total[5m]

# Supported time units: ms, s, m, h, d, w, y
http_requests_total[30s]
http_requests_total[1h]
http_requests_total[7d]
```

### Functions

```promql
# Rate: per-second rate of increase (for counters)
rate(http_requests_total[5m])

# Irate: instant rate (last two data points)
irate(http_requests_total[5m])

# Increase: total increase over a time range
increase(http_requests_total[1h])

# Sum: aggregate across labels
sum(rate(http_requests_total[5m]))

# Sum by specific label
sum by (method) (rate(http_requests_total[5m]))

# Average
avg(rate(http_requests_total[5m]))

# Count
count(up == 1)

# Min / Max
min(node_memory_MemAvailable_bytes)
max(node_cpu_seconds_total)

# Histogram quantile (percentile)
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Topk / Bottomk
topk(5, rate(http_requests_total[5m]))
bottomk(5, node_memory_MemAvailable_bytes)

# Absent (useful for alerting on missing metrics)
absent(up{job="my-service"})
```

### Operators

```promql
# Arithmetic
node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes

# Division (memory usage percentage)
(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100

# Comparison (returns only matching series)
http_requests_total > 1000

# Comparison with bool modifier (returns 0 or 1)
http_requests_total > bool 1000

# Logical AND / OR / UNLESS
up{job="api"} and on(instance) up{job="database"}
```

### Practical PromQL Examples

```promql
# 1. Request rate per second by endpoint
sum by (endpoint) (rate(http_requests_total[5m]))

# 2. Error rate percentage
sum(rate(http_requests_total{status=~"5.."}[5m]))
/
sum(rate(http_requests_total[5m]))
* 100

# 3. 95th percentile latency by service
histogram_quantile(0.95,
  sum by (le, service) (rate(http_request_duration_seconds_bucket[5m]))
)

# 4. CPU usage percentage per node
100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# 5. Memory usage percentage per node
(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100

# 6. Disk space usage
(node_filesystem_size_bytes - node_filesystem_avail_bytes)
/ node_filesystem_size_bytes * 100

# 7. Network throughput (bytes per second)
rate(node_network_receive_bytes_total[5m])
rate(node_network_transmit_bytes_total[5m])

# 8. Container restart count
increase(kube_pod_container_status_restarts_total[1h])

# 9. Pod memory usage vs limit
container_memory_working_set_bytes
/ on (pod, namespace) kube_pod_container_resource_limits{resource="memory"}
* 100

# 10. Availability (SLI) over 30 days
1 - (
  sum(increase(http_requests_total{status=~"5.."}[30d]))
  /
  sum(increase(http_requests_total[30d]))
)
```

---

## Exporters

Exporters are agents that expose metrics from **third-party systems** in Prometheus format.

### Common Exporters

| Exporter | Purpose | Default Port |
|----------|---------|-------------|
| **node_exporter** | Linux host metrics (CPU, memory, disk, network) | 9100 |
| **blackbox_exporter** | Probe endpoints (HTTP, TCP, ICMP, DNS) | 9115 |
| **mysqld_exporter** | MySQL database metrics | 9104 |
| **postgres_exporter** | PostgreSQL database metrics | 9187 |
| **redis_exporter** | Redis metrics | 9121 |
| **mongodb_exporter** | MongoDB metrics | 9216 |
| **nginx_exporter** | NGINX metrics | 9113 |
| **kube-state-metrics** | Kubernetes object state metrics | 8080 |
| **cadvisor** | Container resource metrics | 8080 |

### Node Exporter Setup

```bash
# Run with Docker
docker run -d \
  --name node-exporter \
  --net="host" \
  --pid="host" \
  -v "/:/host:ro,rslave" \
  quay.io/prometheus/node-exporter:latest \
  --path.rootfs=/host

# Verify metrics
curl http://localhost:9100/metrics
```

### Blackbox Exporter (Endpoint Probing)

```yaml
# blackbox.yml
modules:
  http_2xx:
    prober: http
    timeout: 5s
    http:
      valid_http_versions: ["HTTP/1.1", "HTTP/2.0"]
      valid_status_codes: [200]
      method: GET
      follow_redirects: true

  http_post_2xx:
    prober: http
    http:
      method: POST

  tcp_connect:
    prober: tcp
    timeout: 5s

  icmp:
    prober: icmp
    timeout: 5s
```

```yaml
# prometheus.yml - Blackbox scrape config
- job_name: 'blackbox-http'
  metrics_path: /probe
  params:
    module: [http_2xx]
  static_configs:
    - targets:
      - https://example.com
      - https://api.example.com/health
      - https://grafana.example.com
  relabel_configs:
    - source_labels: [__address__]
      target_label: __param_target
    - source_labels: [__param_target]
      target_label: instance
    - target_label: __address__
      replacement: blackbox-exporter:9115
```

---

## Recording Rules

Recording rules **pre-compute** frequently used or expensive PromQL expressions and save the result as a new time series. This improves dashboard performance.

```yaml
# recording_rules.yml
groups:
  - name: http_rules
    interval: 30s
    rules:
      # Request rate by endpoint
      - record: job:http_requests:rate5m
        expr: sum by (job) (rate(http_requests_total[5m]))

      # Error rate percentage
      - record: job:http_errors:ratio_rate5m
        expr: |
          sum by (job) (rate(http_requests_total{status=~"5.."}[5m]))
          /
          sum by (job) (rate(http_requests_total[5m]))

      # 95th percentile latency
      - record: job:http_latency:p95_5m
        expr: |
          histogram_quantile(0.95,
            sum by (job, le) (rate(http_request_duration_seconds_bucket[5m]))
          )

  - name: node_rules
    rules:
      # CPU usage percentage
      - record: instance:node_cpu:usage_percentage
        expr: |
          100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

      # Memory usage percentage
      - record: instance:node_memory:usage_percentage
        expr: |
          (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100

      # Disk usage percentage
      - record: instance:node_disk:usage_percentage
        expr: |
          (node_filesystem_size_bytes{mountpoint="/"} - node_filesystem_avail_bytes{mountpoint="/"})
          / node_filesystem_size_bytes{mountpoint="/"} * 100
```

### Naming Convention for Recording Rules

```
level:metric:operations

Examples:
  job:http_requests:rate5m            # Aggregated at job level
  instance:node_cpu:usage_percentage  # Aggregated at instance level
  namespace:container_memory:sum      # Aggregated at namespace level
```

---

## Alerting Rules

Alerting rules define conditions that trigger alerts when met.

```yaml
# alerting_rules.yml
groups:
  - name: application_alerts
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: job:http_errors:ratio_rate5m > 0.05
        for: 5m
        labels:
          severity: critical
          team: backend
        annotations:
          summary: "High error rate on {{ $labels.job }}"
          description: >
            Error rate is {{ printf "%.2f" $value }}%
            (threshold: 5%) for the last 5 minutes.
          runbook_url: https://wiki.example.com/runbooks/high-error-rate

      # High latency
      - alert: HighLatency
        expr: job:http_latency:p95_5m > 1.0
        for: 5m
        labels:
          severity: warning
          team: backend
        annotations:
          summary: "High latency on {{ $labels.job }}"
          description: >
            95th percentile latency is {{ printf "%.2f" $value }}s
            (threshold: 1s).

  - name: infrastructure_alerts
    rules:
      # Instance down
      - alert: InstanceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Instance {{ $labels.instance }} is down"
          description: "{{ $labels.instance }} of job {{ $labels.job }} has been down for more than 1 minute."

      # High CPU usage
      - alert: HighCPUUsage
        expr: instance:node_cpu:usage_percentage > 85
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage on {{ $labels.instance }}"
          description: "CPU usage is {{ printf \"%.1f\" $value }}%"

      # Disk space running low
      - alert: DiskSpaceLow
        expr: instance:node_disk:usage_percentage > 85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Disk space low on {{ $labels.instance }}"
          description: "Disk usage is {{ printf \"%.1f\" $value }}%"

      # High memory usage
      - alert: HighMemoryUsage
        expr: instance:node_memory:usage_percentage > 90
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High memory usage on {{ $labels.instance }}"
          description: "Memory usage is {{ printf \"%.1f\" $value }}%"
```

---

## Metrics Naming Conventions

Follow the [Prometheus naming best practices](https://prometheus.io/docs/practices/naming/):

### Rules

1. Use **snake_case** for metric names
2. Include a **unit suffix** (`_seconds`, `_bytes`, `_total`)
3. Use **base units** (seconds not milliseconds, bytes not megabytes)
4. Counters should end in `_total`
5. Prefix with the **application or library name**

### Examples

```
Good:
  http_requests_total
  http_request_duration_seconds
  node_memory_MemAvailable_bytes
  process_cpu_seconds_total
  myapp_queue_length
  myapp_orders_created_total

Bad:
  httpRequests            ← camelCase
  request_latency_ms      ← should be _seconds (base unit)
  http_requests            ← counter without _total
  memory_megabytes        ← should be _bytes (base unit)
  requests                ← too vague, no prefix
```

---

## Key Takeaways

1. **Metrics** are numeric, time-series data — compact, fast, and ideal for alerting
2. Understand the four types: **Counter** (cumulative), **Gauge** (current value), **Histogram** (buckets), **Summary** (quantiles)
3. **Prometheus** uses a pull model — it scrapes `/metrics` endpoints
4. **PromQL** is powerful — learn `rate()`, `histogram_quantile()`, `sum by ()`, and aggregation operators
5. **Exporters** bridge the gap between third-party systems and Prometheus
6. Use **recording rules** to pre-compute expensive queries
7. **Alerting rules** define conditions with `for` duration and severity labels
8. Follow **naming conventions** — snake_case, base units, `_total` for counters

---

**Previous Lesson:** [02 - Logging](02-logging.md)
**Next Lesson:** [04 - Tracing](04-tracing.md)
