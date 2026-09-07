# Lesson 05: Grafana

## Table of Contents

- [Grafana Overview](#grafana-overview)
- [Data Sources](#data-sources)
- [Dashboard Creation](#dashboard-creation)
- [Panels and Visualizations](#panels-and-visualizations)
- [Variables and Templating](#variables-and-templating)
- [Alerting in Grafana](#alerting-in-grafana)
- [Grafana as Code](#grafana-as-code)
- [Key Takeaways](#key-takeaways)

---

## Grafana Overview

**Grafana** is the de facto standard open-source platform for monitoring visualization. It connects to multiple data sources and provides rich, interactive dashboards.

### Why Grafana?

- **Multi-source:** Connect to Prometheus, Elasticsearch, Loki, InfluxDB, CloudWatch, and 100+ more
- **Rich visualizations:** Time series, gauges, heatmaps, tables, geo maps, and more
- **Alerting:** Unified alerting across all data sources
- **Templating:** Dynamic dashboards with variables
- **Community:** Thousands of pre-built dashboards on [grafana.com/dashboards](https://grafana.com/dashboards)
- **Extensibility:** Plugin system for data sources, panels, and apps

### Installation

```bash
# Docker
docker run -d \
  --name grafana \
  -p 3000:3000 \
  -v grafana-data:/var/lib/grafana \
  -e GF_SECURITY_ADMIN_PASSWORD=admin \
  grafana/grafana:10.2.0

# Docker Compose
# See docker-compose.yml examples in this lesson

# Kubernetes (Helm)
helm repo add grafana https://grafana.github.io/helm-charts
helm install grafana grafana/grafana \
  --namespace monitoring \
  --set adminPassword='admin' \
  --set persistence.enabled=true \
  --set persistence.size=10Gi
```

### Grafana UI Overview

```
┌──────────────────────────────────────────────────┐
│  ☰  Grafana         🔍 Search    ➕ + (New)  👤  │
├──────────┬───────────────────────────────────────┤
│          │                                       │
│ Dashboards│    Dashboard Title                   │
│ Explore   │    ┌──────────┐  ┌──────────┐       │
│ Alerting  │    │  Panel 1 │  │  Panel 2 │       │
│ Admin     │    │  (Graph) │  │  (Gauge) │       │
│ Config    │    └──────────┘  └──────────┘       │
│          │    ┌──────────────────────────┐       │
│          │    │       Panel 3            │       │
│          │    │    (Time Series)         │       │
│          │    └──────────────────────────┘       │
│          │                                       │
└──────────┴───────────────────────────────────────┘
```

---

## Data Sources

Data sources are the backends that Grafana queries for data.

### Adding a Prometheus Data Source

**Via UI:**
1. Go to **Configuration > Data Sources > Add data source**
2. Select **Prometheus**
3. Set URL: `http://prometheus:9090`
4. Click **Save & Test**

**Via provisioning (recommended for production):**

```yaml
# /etc/grafana/provisioning/datasources/prometheus.yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    jsonData:
      httpMethod: POST
      timeInterval: 15s
    editable: false

  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    jsonData:
      derivedFields:
        - datasourceUid: tempo
          matcherRegex: "trace_id=(\\w+)"
          name: TraceID
          url: '$${__value.raw}'
    editable: false

  - name: Tempo
    type: tempo
    access: proxy
    url: http://tempo:3200
    editable: false

  - name: Elasticsearch
    type: elasticsearch
    access: proxy
    url: http://elasticsearch:9200
    jsonData:
      index: "logs-*"
      timeField: "@timestamp"
      esVersion: "8.0.0"
    editable: false
```

### Common Data Sources

| Data Source | Type | Use Case |
|------------|------|----------|
| **Prometheus** | Metrics | Time series metrics, alerting |
| **Loki** | Logs | Log aggregation and querying |
| **Elasticsearch** | Logs/Metrics | Full-text log search |
| **Tempo** | Traces | Distributed tracing |
| **Jaeger** | Traces | Distributed tracing |
| **InfluxDB** | Metrics | Time series database |
| **CloudWatch** | Metrics/Logs | AWS monitoring |
| **PostgreSQL** | SQL | Business metrics from databases |

---

## Dashboard Creation

### Dashboard Structure

```
Dashboard
├── Row 1: "Overview"
│   ├── Panel: Request Rate (Time Series)
│   ├── Panel: Error Rate (Gauge)
│   └── Panel: P95 Latency (Stat)
├── Row 2: "HTTP Details"
│   ├── Panel: Requests by Endpoint (Time Series)
│   ├── Panel: Status Code Distribution (Pie Chart)
│   └── Panel: Latency Heatmap (Heatmap)
└── Row 3: "Infrastructure"
    ├── Panel: CPU Usage (Time Series)
    ├── Panel: Memory Usage (Time Series)
    └── Panel: Disk Usage (Bar Gauge)
```

### Creating a Dashboard (Step by Step)

1. Click **+ > New Dashboard**
2. Click **Add visualization**
3. Select data source (e.g., Prometheus)
4. Write your query
5. Choose visualization type
6. Configure panel options
7. Save the dashboard

### Example: Service Overview Dashboard

**Panel 1: Request Rate**
```promql
# Query
sum(rate(http_requests_total{job="$service"}[5m]))
```
- Visualization: **Time Series**
- Legend: `{{method}} {{endpoint}}`
- Unit: `requests/sec`

**Panel 2: Error Rate**
```promql
# Query
sum(rate(http_requests_total{job="$service", status=~"5.."}[5m]))
/
sum(rate(http_requests_total{job="$service"}[5m]))
* 100
```
- Visualization: **Gauge**
- Unit: `percent (0-100)`
- Thresholds: Green (0-1), Yellow (1-5), Red (5-100)

**Panel 3: P95 Latency**
```promql
# Query
histogram_quantile(0.95,
  sum by (le) (rate(http_request_duration_seconds_bucket{job="$service"}[5m]))
)
```
- Visualization: **Stat**
- Unit: `seconds (s)`
- Thresholds: Green (0-0.5), Yellow (0.5-1), Red (1+)

**Panel 4: Latency Heatmap**
```promql
# Query
sum(increase(http_request_duration_seconds_bucket{job="$service"}[5m])) by (le)
```
- Visualization: **Heatmap**
- Color scheme: Spectral

**Panel 5: Top Endpoints by Request Count**
```promql
# Query
topk(10, sum by (endpoint) (rate(http_requests_total{job="$service"}[5m])))
```
- Visualization: **Bar Chart**
- Orientation: Horizontal

---

## Panels and Visualizations

### Time Series Panel

The most common panel. Displays metrics over time.

```promql
# Multiple queries on one panel
# Query A: Total requests
sum(rate(http_requests_total{job="api"}[5m]))

# Query B: Error requests (red line)
sum(rate(http_requests_total{job="api", status=~"5.."}[5m]))

# Query C: Success requests (green line)
sum(rate(http_requests_total{job="api", status=~"2.."}[5m]))
```

Options:
- **Line width, fill opacity, point size**
- **Stack mode:** Normal, Percent
- **Tooltip mode:** Single, All
- **Legend:** Table with min/max/avg/current values

### Stat Panel

Shows a single large value with optional sparkline.

```promql
# Uptime percentage
avg(up{job="api"}) * 100
```

Options:
- **Color mode:** Background, Value, None
- **Graph mode:** Area, None
- **Text mode:** Auto, Value, Name

### Gauge Panel

Shows a value on a gauge with thresholds.

```promql
# CPU usage
100 - (avg(irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)
```

Options:
- **Min/Max:** 0/100
- **Thresholds:** Green (0-70), Yellow (70-85), Red (85-100)
- **Show threshold markers**

### Table Panel

Displays data in a tabular format.

```promql
# Top 10 pods by memory usage
topk(10,
  container_memory_working_set_bytes{namespace="production"}
)
```

Options:
- Column filters and sorting
- Cell display modes (color, gauge, sparkline)
- Column width and alignment

### Bar Gauge Panel

Horizontal or vertical bars with thresholds.

```promql
# Disk usage by mount point
(node_filesystem_size_bytes - node_filesystem_avail_bytes)
/ node_filesystem_size_bytes * 100
```

### Heatmap Panel

Ideal for histograms showing distribution over time.

```promql
# Request latency distribution
sum(increase(http_request_duration_seconds_bucket[5m])) by (le)
```

### Logs Panel

Display log lines from Loki or Elasticsearch.

```logql
# Loki query
{service="checkout-service"} |= "error" | json
```

### Node Graph Panel

Visualize service dependencies and trace topology.

### Geomap Panel

Display geographic data on a world map.

---

## Variables and Templating

Variables make dashboards **dynamic and reusable**. Instead of hardcoding service names, you use dropdown selectors.

### Defining Variables

Go to **Dashboard Settings > Variables > New Variable**.

#### Query Variable (from Prometheus)

```
Name: service
Label: Service
Type: Query
Data source: Prometheus
Query: label_values(http_requests_total, job)
Sort: Alphabetical (asc)
Multi-value: true
Include All option: true
```

#### Query Variable (from labels)

```
Name: namespace
Label: Namespace
Type: Query
Data source: Prometheus
Query: label_values(kube_pod_info, namespace)
```

#### Interval Variable

```
Name: interval
Label: Interval
Type: Interval
Values: 1m, 5m, 15m, 30m, 1h
Auto: true
```

#### Custom Variable

```
Name: environment
Label: Environment
Type: Custom
Values: production, staging, development
```

### Using Variables in Queries

```promql
# Use $variable_name in PromQL
sum(rate(http_requests_total{job="$service", namespace="$namespace"}[$interval]))

# Multi-value variable generates regex
# If user selects: service-a, service-b
# $service becomes: service-a|service-b
sum(rate(http_requests_total{job=~"$service"}[5m]))
```

### Chained Variables

Variables can depend on each other:

```
Variable 1: namespace
  Query: label_values(kube_pod_info, namespace)

Variable 2: pod (depends on namespace)
  Query: label_values(kube_pod_info{namespace="$namespace"}, pod)

Variable 3: container (depends on pod)
  Query: label_values(kube_pod_container_info{pod="$pod"}, container)
```

### Repeating Panels

Panels can repeat for each value of a variable:

1. Edit the panel
2. In Panel Options, set **Repeat by variable** to your variable
3. Set **Max per row** (e.g., 3)

This creates one panel per service/namespace/pod automatically.

---

## Alerting in Grafana

Grafana has a unified alerting system that works across all data sources.

### Alert Rule Components

```
Alert Rule
├── Query: What data to evaluate
├── Condition: When to fire
├── Duration (for): How long condition must be true
├── Labels: severity, team, service
├── Annotations: summary, description, runbook_url
└── Contact Point: Where to send notifications
```

### Creating an Alert Rule

**Step 1: Define the query**

```promql
# Error rate
sum(rate(http_requests_total{job="api", status=~"5.."}[5m]))
/
sum(rate(http_requests_total{job="api"}[5m]))
```

**Step 2: Define the condition**

```
IS ABOVE 0.05  (5% error rate)
```

**Step 3: Set evaluation behavior**

```
Evaluate every: 1m
For: 5m  (must be true for 5 minutes before firing)
```

**Step 4: Add labels and annotations**

```yaml
Labels:
  severity: critical
  team: backend
  service: api

Annotations:
  summary: "High error rate on API service"
  description: "Error rate is {{ $value | printf \"%.2f\" }}%"
  runbook_url: "https://wiki.example.com/runbooks/api-error-rate"
```

### Contact Points

```yaml
# Provisioning contact points
apiVersion: 1

contactPoints:
  - orgId: 1
    name: slack-critical
    receivers:
      - uid: slack-critical
        type: slack
        settings:
          url: https://hooks.slack.com/services/T00/B00/XXXX
          channel: "#alerts-critical"
          title: '{{ template "slack.title" . }}'
          text: '{{ template "slack.text" . }}'

  - orgId: 1
    name: pagerduty-critical
    receivers:
      - uid: pagerduty
        type: pagerduty
        settings:
          integrationKey: YOUR_PAGERDUTY_KEY
          severity: critical
```

### Notification Policies

```yaml
# Provisioning notification policies
apiVersion: 1

policies:
  - orgId: 1
    receiver: slack-default
    group_by: ['alertname', 'service']
    group_wait: 30s
    group_interval: 5m
    repeat_interval: 4h
    routes:
      - receiver: pagerduty-critical
        matchers:
          - severity = critical
        continue: true
      - receiver: slack-critical
        matchers:
          - severity = critical
      - receiver: slack-warning
        matchers:
          - severity = warning
```

### Silence and Mute Timings

```yaml
# Mute timing: Don't alert during maintenance windows
muteTimes:
  - orgId: 1
    name: maintenance-window
    time_intervals:
      - times:
          - start_time: '02:00'
            end_time: '04:00'
        weekdays: ['sunday']
```

---

## Grafana as Code

Managing dashboards through the UI doesn't scale. **Grafana as Code** means storing dashboards in version control.

### Approach 1: JSON Dashboard Export/Import

Export dashboards as JSON and store in Git:

```bash
# Export via API
curl -H "Authorization: Bearer $GRAFANA_TOKEN" \
  http://grafana:3000/api/dashboards/uid/my-dashboard \
  | jq '.dashboard' > dashboards/my-dashboard.json

# Import via API
curl -X POST \
  -H "Authorization: Bearer $GRAFANA_TOKEN" \
  -H "Content-Type: application/json" \
  -d @dashboards/my-dashboard.json \
  http://grafana:3000/api/dashboards/db
```

### Approach 2: Dashboard Provisioning

Store dashboard JSON files on disk and have Grafana auto-load them:

```yaml
# /etc/grafana/provisioning/dashboards/default.yaml
apiVersion: 1

providers:
  - name: 'default'
    orgId: 1
    folder: 'Provisioned'
    folderUid: 'provisioned'
    type: file
    disableDeletion: true
    updateIntervalSeconds: 30
    allowUiUpdates: false
    options:
      path: /var/lib/grafana/dashboards
      foldersFromFilesStructure: true
```

### Approach 3: Grafonnet (Jsonnet)

**Grafonnet** is a Jsonnet library for generating Grafana dashboards programmatically:

```jsonnet
// dashboard.jsonnet
local grafana = import 'grafonnet/grafana.libsonnet';
local dashboard = grafana.dashboard;
local prometheus = grafana.prometheus;
local graphPanel = grafana.graphPanel;
local singlestat = grafana.singlestat;

local requestRatePanel = graphPanel.new(
  title='Request Rate',
  datasource='Prometheus',
  span=6,
).addTarget(
  prometheus.target(
    'sum(rate(http_requests_total{job="$service"}[5m]))',
    legendFormat='{{ method }} {{ endpoint }}',
  )
);

local errorRatePanel = singlestat.new(
  title='Error Rate',
  datasource='Prometheus',
  span=3,
  thresholds='1,5',
  colorValue=true,
  postfix='%',
).addTarget(
  prometheus.target(
    'sum(rate(http_requests_total{job="$service",status=~"5.."}[5m])) / sum(rate(http_requests_total{job="$service"}[5m])) * 100',
  )
);

dashboard.new(
  title='Service Overview',
  uid='service-overview',
  tags=['generated', 'service'],
  editable=false,
  time_from='now-1h',
)
.addTemplate(
  grafana.template.datasource('datasource', 'prometheus', 'Prometheus')
)
.addTemplate(
  grafana.template.new('service', 'Prometheus', 'label_values(http_requests_total, job)')
)
.addPanel(requestRatePanel, gridPos={ x: 0, y: 0, w: 12, h: 8 })
.addPanel(errorRatePanel, gridPos={ x: 12, y: 0, w: 6, h: 8 })
```

```bash
# Generate JSON from Jsonnet
jsonnet -J vendor dashboard.jsonnet > dashboard.json
```

### Approach 4: Terraform

```hcl
# main.tf
terraform {
  required_providers {
    grafana = {
      source  = "grafana/grafana"
      version = "~> 2.0"
    }
  }
}

provider "grafana" {
  url  = "http://grafana:3000"
  auth = var.grafana_api_key
}

resource "grafana_folder" "services" {
  title = "Services"
}

resource "grafana_dashboard" "service_overview" {
  folder      = grafana_folder.services.id
  config_json = file("dashboards/service-overview.json")
}

resource "grafana_data_source" "prometheus" {
  type = "prometheus"
  name = "Prometheus"
  url  = "http://prometheus:9090"

  json_data_encoded = jsonencode({
    httpMethod    = "POST"
    timeInterval  = "15s"
  })
}
```

---

## Key Takeaways

1. **Grafana** is the standard visualization platform — connect it to multiple data sources
2. **Provision data sources** via YAML files, not manual UI configuration
3. Build dashboards with **meaningful panels**: use time series for trends, stats for KPIs, gauges for thresholds
4. **Variables** make dashboards dynamic — use them for service, namespace, and interval selection
5. Set up **alerting** with proper severity levels, contact points, and notification policies
6. Manage dashboards **as code** using provisioning, Grafonnet, or Terraform
7. Use the **Grafana community** — import pre-built dashboards for common tools (Node Exporter, Kubernetes, etc.)

---

**Previous Lesson:** [04 - Tracing](04-tracing.md)
**Next Lesson:** [06 - Prometheus Deep Dive](06-prometheus.md)
