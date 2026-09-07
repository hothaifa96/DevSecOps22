# Lab 01: Prometheus Setup

## Objective

Install and configure Prometheus, explore the UI, scrape metrics from targets, and write basic PromQL queries.

## Prerequisites

- Docker and Docker Compose installed
- Basic understanding of YAML
- A terminal/command line

## Duration: 45-60 minutes

---

## Part 1: Install Prometheus with Docker

### Step 1: Create the Project Directory

```bash
mkdir -p ~/observability-lab/prometheus
cd ~/observability-lab/prometheus
```

### Step 2: Create the Prometheus Configuration

Create `prometheus.yml`:

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  # Prometheus scrapes itself
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
```

### Step 3: Create Docker Compose File

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:v2.48.0
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=15d'
      - '--web.enable-lifecycle'
    restart: unless-stopped

volumes:
  prometheus-data:
```

### Step 4: Start Prometheus

```bash
docker compose up -d
```

### Step 5: Verify Prometheus is Running

```bash
# Check container status
docker compose ps

# Check Prometheus health
curl http://localhost:9090/-/healthy
```

Open your browser and navigate to **http://localhost:9090**.

### Checkpoint

- [ ] Prometheus UI is accessible at http://localhost:9090
- [ ] Status > Targets shows "prometheus" as UP

---

## Part 2: Add Monitoring Targets

### Step 6: Add Node Exporter

Update `docker-compose.yml` to add node-exporter:

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:v2.48.0
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - ./rules/:/etc/prometheus/rules/
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=15d'
      - '--web.enable-lifecycle'
    restart: unless-stopped

  node-exporter:
    image: quay.io/prometheus/node-exporter:v1.7.0
    container_name: node-exporter
    ports:
      - "9100:9100"
    command:
      - '--path.rootfs=/host'
    volumes:
      - '/:/host:ro,rslave'
    restart: unless-stopped

volumes:
  prometheus-data:
```

### Step 7: Update Prometheus Configuration

Update `prometheus.yml` to scrape node-exporter:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
```

### Step 8: Restart the Stack

```bash
docker compose up -d
```

### Step 9: Reload Prometheus Configuration (Alternative to Restart)

```bash
# Send SIGHUP to reload config
curl -X POST http://localhost:9090/-/reload
```

### Step 10: Verify Targets

1. Go to **http://localhost:9090/targets**
2. You should see both `prometheus` and `node-exporter` targets as **UP**

### Step 11: Explore Node Exporter Metrics

```bash
# View raw metrics from node-exporter
curl http://localhost:9100/metrics | head -50
```

### Checkpoint

- [ ] Node exporter is running on port 9100
- [ ] Both targets show as UP in Prometheus targets page
- [ ] You can see raw metrics from node-exporter

---

## Part 3: Explore the Prometheus UI

### Step 12: Navigate the UI

Explore these sections:

1. **Graph** (http://localhost:9090/graph) — Execute PromQL queries
2. **Alerts** (http://localhost:9090/alerts) — View alert rules
3. **Status > Targets** — See scrape targets and their health
4. **Status > Configuration** — View the loaded configuration
5. **Status > Rules** — View recording and alerting rules
6. **Status > TSDB Status** — View database statistics

### Step 13: View Available Metrics

In the **Graph** tab, click the dropdown next to the query input. You'll see all available metrics. Try typing to filter:

- `node_` — Node exporter metrics
- `prometheus_` — Prometheus self-metrics
- `up` — Target health metric

---

## Part 4: Write Basic PromQL Queries

### Step 14: Simple Queries

Execute these queries in the **Graph** tab (http://localhost:9090/graph):

**Query 1: Check target health**
```promql
up
```
→ Returns 1 for each healthy target, 0 for unhealthy

**Query 2: Total memory**
```promql
node_memory_MemTotal_bytes
```
→ Switch to the **Graph** tab to see it as a time series

**Query 3: Available memory**
```promql
node_memory_MemAvailable_bytes
```

**Query 4: Memory usage percentage**
```promql
(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100
```

### Step 15: Working with CPU Metrics

**Query 5: CPU usage by mode (idle, system, user, etc.)**
```promql
node_cpu_seconds_total
```

**Query 6: CPU idle rate**
```promql
rate(node_cpu_seconds_total{mode="idle"}[5m])
```

**Query 7: CPU usage percentage (overall)**
```promql
100 - (avg(irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)
```

### Step 16: Disk Metrics

**Query 8: Disk space total**
```promql
node_filesystem_size_bytes{mountpoint="/"}
```

**Query 9: Disk space available**
```promql
node_filesystem_avail_bytes{mountpoint="/"}
```

**Query 10: Disk usage percentage**
```promql
(1 - node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100
```

### Step 17: Network Metrics

**Query 11: Network receive rate (bytes/sec)**
```promql
rate(node_network_receive_bytes_total{device!="lo"}[5m])
```

**Query 12: Network transmit rate (bytes/sec)**
```promql
rate(node_network_transmit_bytes_total{device!="lo"}[5m])
```

### Step 18: Prometheus Self-Metrics

**Query 13: Total time series in the database**
```promql
prometheus_tsdb_head_series
```

**Query 14: Ingestion rate (samples per second)**
```promql
rate(prometheus_tsdb_head_samples_appended_total[5m])
```

**Query 15: Scrape duration**
```promql
scrape_duration_seconds
```

### Checkpoint

- [ ] You can execute PromQL queries in the Prometheus UI
- [ ] You understand the difference between instant vectors and graphs
- [ ] You've used `rate()` and arithmetic operators

---

## Part 5: Aggregation and Advanced Queries

### Step 19: Aggregation Operators

**Query 16: Sum of all CPU time across all CPUs**
```promql
sum(rate(node_cpu_seconds_total[5m])) by (mode)
```

**Query 17: Average CPU usage across instances (useful with multiple nodes)**
```promql
avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) by (instance)
```

**Query 18: Top 5 metrics by sample count**
```promql
topk(5, prometheus_tsdb_head_series)
```

### Step 20: Prediction

**Query 19: Predict when disk will be full (linear prediction)**
```promql
predict_linear(node_filesystem_avail_bytes{mountpoint="/"}[1h], 24*3600)
```
→ Predicts available disk space 24 hours from now based on the last 1 hour trend

### Step 21: Time-Based Functions

**Query 20: Maximum memory usage in the last hour**
```promql
max_over_time(node_memory_MemAvailable_bytes[1h])
```

**Query 21: Minimum memory usage in the last hour**
```promql
min_over_time(node_memory_MemAvailable_bytes[1h])
```

---

## Part 6: Add Recording Rules

### Step 22: Create Recording Rules

Create the rules directory and file:

```bash
mkdir -p ~/observability-lab/prometheus/rules
```

Create `rules/recording_rules.yml`:

```yaml
groups:
  - name: node_rules
    interval: 15s
    rules:
      - record: instance:node_cpu:usage_percentage
        expr: 100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

      - record: instance:node_memory:usage_percentage
        expr: (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100

      - record: instance:node_disk:usage_percentage
        expr: |
          (node_filesystem_size_bytes{mountpoint="/"} - node_filesystem_avail_bytes{mountpoint="/"})
          / node_filesystem_size_bytes{mountpoint="/"} * 100

      - record: instance:node_network:receive_bytes_rate5m
        expr: rate(node_network_receive_bytes_total{device!="lo"}[5m])
```

### Step 23: Update Prometheus Configuration

Add the rule file to `prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - /etc/prometheus/rules/*.yml

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
```

### Step 24: Reload and Verify

```bash
# Reload config
curl -X POST http://localhost:9090/-/reload

# Wait a few seconds, then check rules
curl http://localhost:9090/api/v1/rules | python3 -m json.tool
```

### Step 25: Query Recording Rules

```promql
instance:node_cpu:usage_percentage
instance:node_memory:usage_percentage
instance:node_disk:usage_percentage
```

These pre-computed metrics are faster to query and can be used in dashboards and alerts.

### Checkpoint

- [ ] Recording rules are loaded (check Status > Rules)
- [ ] You can query the recording rule metrics
- [ ] You understand why recording rules improve performance

---

## Part 7: Add Basic Alerting Rules

### Step 26: Create Alerting Rules

Create `rules/alerting_rules.yml`:

```yaml
groups:
  - name: node_alerts
    rules:
      - alert: HighCPUUsage
        expr: instance:node_cpu:usage_percentage > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage on {{ $labels.instance }}"
          description: "CPU usage is {{ printf \"%.1f\" $value }}%"

      - alert: HighMemoryUsage
        expr: instance:node_memory:usage_percentage > 85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage on {{ $labels.instance }}"
          description: "Memory usage is {{ printf \"%.1f\" $value }}%"

      - alert: DiskSpaceRunningLow
        expr: instance:node_disk:usage_percentage > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Disk space running low on {{ $labels.instance }}"
          description: "Disk usage is {{ printf \"%.1f\" $value }}%"

      - alert: InstanceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Instance {{ $labels.instance }} is down"
          description: "{{ $labels.instance }} of job {{ $labels.job }} has been down for more than 1 minute."
```

### Step 27: Reload and Verify Alerts

```bash
curl -X POST http://localhost:9090/-/reload
```

1. Go to **http://localhost:9090/alerts**
2. You should see your alerting rules listed
3. They should be in "Inactive" state (green) unless thresholds are exceeded

### Step 28: Test the InstanceDown Alert

```bash
# Stop node-exporter
docker compose stop node-exporter

# Wait 1 minute, then check alerts at http://localhost:9090/alerts
# The InstanceDown alert should transition: Inactive → Pending → Firing

# Restart node-exporter
docker compose start node-exporter
```

### Checkpoint

- [ ] Alerting rules are visible at http://localhost:9090/alerts
- [ ] You tested the InstanceDown alert by stopping node-exporter
- [ ] You understand the Inactive → Pending → Firing lifecycle

---

## Part 8: Using the Prometheus API

### Step 29: Query the API

```bash
# Instant query
curl -s 'http://localhost:9090/api/v1/query?query=up' | python3 -m json.tool

# Range query (last 5 minutes, 1-minute step)
curl -s 'http://localhost:9090/api/v1/query_range?query=up&start='$(date -v-5M +%s 2>/dev/null || date -d '5 minutes ago' +%s)'&end='$(date +%s)'&step=60' | python3 -m json.tool

# List all targets
curl -s 'http://localhost:9090/api/v1/targets' | python3 -m json.tool

# List all label values for job
curl -s 'http://localhost:9090/api/v1/label/job/values' | python3 -m json.tool

# List all metric names
curl -s 'http://localhost:9090/api/v1/label/__name__/values' | python3 -m json.tool | head -30
```

---

## Cleanup

```bash
cd ~/observability-lab/prometheus
docker compose down -v
```

---

## Summary

In this lab you:

1. Installed Prometheus using Docker Compose
2. Added Node Exporter as a scrape target
3. Explored the Prometheus UI (Graph, Targets, Status)
4. Wrote 21+ PromQL queries covering CPU, memory, disk, and network
5. Created recording rules for pre-computed metrics
6. Created alerting rules and tested them
7. Queried the Prometheus HTTP API

## What's Next

- **Lab 02:** Install Grafana and build dashboards using these metrics
- **Lab 03:** Set up centralized logging with Loki

---

## Bonus Challenges

1. Add a second node-exporter instance and write queries that aggregate across both
2. Create a recording rule that calculates the error rate percentage
3. Add the blackbox exporter and probe an external URL
4. Explore the `prometheus_http_requests_total` metric to understand how much traffic the Prometheus UI generates
