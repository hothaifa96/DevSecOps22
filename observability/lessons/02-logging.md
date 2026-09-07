# Lesson 02: Logging

## Table of Contents

- [Introduction to Logging](#introduction-to-logging)
- [Structured vs Unstructured Logging](#structured-vs-unstructured-logging)
- [Log Levels](#log-levels)
- [Centralized Logging Architecture](#centralized-logging-architecture)
- [The ELK Stack](#the-elk-stack)
- [The EFK Stack](#the-efk-stack)
- [Loki + Grafana](#loki--grafana)
- [Log Aggregation Patterns](#log-aggregation-patterns)
- [Log Retention and Storage Strategies](#log-retention-and-storage-strategies)
- [Logging Best Practices](#logging-best-practices)
- [Key Takeaways](#key-takeaways)

---

## Introduction to Logging

Logs are the most fundamental form of observability data. Every application produces logs — they are timestamped, immutable records of discrete events that happened in your system.

### What Makes a Good Log Entry?

A good log entry answers **five questions**:
1. **When** did it happen? (timestamp)
2. **Where** did it happen? (service, host, function)
3. **What** happened? (event description)
4. **Who** was affected? (user ID, request ID)
5. **How severe** is it? (log level)

### The Evolution of Logging

```
Phase 1: printf("error occurred")              ← Useless
Phase 2: print(f"Error in {function}: {err}")   ← Better, but unstructured
Phase 3: logger.error("Payment failed",          ← Structured, queryable
           extra={"user_id": "123",
                  "amount": 99.99,
                  "error": str(err)})
```

---

## Structured vs Unstructured Logging

### Unstructured Logging (Bad)

```
2024-01-15 10:23:45 ERROR Payment failed for user 789 - timeout after 5000ms on /api/checkout
```

**Problems:**
- Hard to parse programmatically
- Inconsistent format across services
- Can't easily filter by user_id, endpoint, or error type
- Regex-based parsing is fragile and slow

### Structured Logging (Good)

```json
{
  "timestamp": "2024-01-15T10:23:45.123Z",
  "level": "ERROR",
  "logger": "payment.processor",
  "message": "Payment processing failed",
  "service": "checkout-service",
  "version": "2.4.1",
  "environment": "production",
  "trace_id": "abc123def456",
  "span_id": "span789",
  "user_id": "user-789",
  "endpoint": "/api/v2/checkout",
  "method": "POST",
  "error_type": "TimeoutException",
  "error_message": "upstream payment gateway did not respond within 5000ms",
  "duration_ms": 5023,
  "payment_amount": 99.99,
  "payment_currency": "USD",
  "retry_count": 2
}
```

**Advantages:**
- Machine-parseable (JSON)
- Consistent schema across services
- Filterable on any field
- Correlatable with traces via `trace_id`

### Implementing Structured Logging

#### Python (structlog)

```python
import structlog

# Configure structlog
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()

# Usage
logger.info("order.created",
    user_id="user-789",
    order_id="order-456",
    total_amount=99.99,
    items_count=3
)

logger.error("payment.failed",
    user_id="user-789",
    order_id="order-456",
    error="TimeoutException",
    gateway="stripe",
    retry_count=2
)
```

#### Node.js (winston)

```javascript
const winston = require('winston');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  defaultMeta: {
    service: 'checkout-service',
    version: '2.4.1',
    environment: process.env.NODE_ENV
  },
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: 'app.log' })
  ]
});

// Usage
logger.info('Order created', {
  userId: 'user-789',
  orderId: 'order-456',
  totalAmount: 99.99,
  itemsCount: 3
});

logger.error('Payment failed', {
  userId: 'user-789',
  orderId: 'order-456',
  error: 'TimeoutException',
  gateway: 'stripe',
  retryCount: 2
});
```

#### Go (zerolog)

```go
package main

import (
    "os"
    "github.com/rs/zerolog"
    "github.com/rs/zerolog/log"
)

func main() {
    zerolog.TimeFieldFormat = zerolog.TimeFormatUnix

    logger := zerolog.New(os.Stdout).With().
        Timestamp().
        Str("service", "checkout-service").
        Str("version", "2.4.1").
        Logger()

    logger.Info().
        Str("user_id", "user-789").
        Str("order_id", "order-456").
        Float64("total_amount", 99.99).
        Int("items_count", 3).
        Msg("Order created")

    logger.Error().
        Str("user_id", "user-789").
        Err(err).
        Str("gateway", "stripe").
        Int("retry_count", 2).
        Msg("Payment failed")
}
```

---

## Log Levels

Log levels indicate the **severity** of an event. Use them consistently across all services.

| Level | When to Use | Example |
|-------|------------|---------|
| **TRACE** | Very detailed debugging, method entry/exit | `Entering processPayment() with args: {...}` |
| **DEBUG** | Detailed information for diagnosing issues | `Cache miss for key user:789, querying database` |
| **INFO** | Normal operations, milestones, business events | `Order order-456 created for user-789, total: $99.99` |
| **WARN** | Something unexpected but recoverable | `Payment retry 2/3 for order-456, previous attempt timed out` |
| **ERROR** | An operation failed but the service continues | `Payment failed for order-456: TimeoutException from Stripe` |
| **FATAL** | The service cannot continue and must stop | `Cannot connect to database after 10 retries, shutting down` |

### Log Level Guidelines

```
Production Environment:
  Default level: INFO
  Temporarily set to DEBUG for troubleshooting

Development Environment:
  Default level: DEBUG

Staging Environment:
  Default level: DEBUG or INFO

Per-service overrides:
  Noisy services → WARN
  Critical services under investigation → DEBUG
```

### Dynamic Log Level Changes

Enable changing log levels at runtime without redeployment:

```yaml
# ConfigMap for dynamic log levels
apiVersion: v1
kind: ConfigMap
metadata:
  name: logging-config
data:
  LOG_LEVEL: "INFO"
  # Change to "DEBUG" temporarily during incident investigation
```

---

## Centralized Logging Architecture

### Why Centralize Logs?

In a microservices environment, logs are scattered across dozens of containers:

```
Without Centralization:
  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
  │ Service A │  │ Service B │  │ Service C │  │ Service D │
  │  logs/    │  │  logs/    │  │  logs/    │  │  logs/    │
  └──────────┘  └──────────┘  └──────────┘  └──────────┘
  SSH + grep     SSH + grep     SSH + grep     SSH + grep
  on each        on each        on each        on each
  container      container      container      container

With Centralization:
  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
  │ Service A │  │ Service B │  │ Service C │  │ Service D │
  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘
        │               │               │               │
        └───────────────┴───────┬───────┴───────────────┘
                                │
                     ┌──────────▼──────────┐
                     │  Central Log Store   │
                     │  (Search, Filter,    │
                     │   Alert, Visualize)  │
                     └─────────────────────┘
```

### Common Centralized Logging Architectures

```
Option 1: ELK Stack
  Beats/Logstash → Elasticsearch → Kibana

Option 2: EFK Stack (Kubernetes-native)
  Fluentd/Fluent Bit → Elasticsearch → Kibana

Option 3: Loki Stack (lightweight)
  Promtail → Loki → Grafana

Option 4: Cloud-native
  AWS CloudWatch Logs / GCP Cloud Logging / Azure Monitor Logs
```

---

## The ELK Stack

The **ELK Stack** (Elasticsearch, Logstash, Kibana) is the most popular open-source logging solution.

### Architecture

```
┌─────────────┐     ┌─────────────┐     ┌───────────────┐     ┌─────────┐
│ Applications │────▶│  Logstash    │────▶│ Elasticsearch │────▶│ Kibana  │
│ (log output) │     │ (process &  │     │  (store &     │     │ (query  │
│              │     │  transform) │     │   index)      │     │  & viz) │
└─────────────┘     └─────────────┘     └───────────────┘     └─────────┘
```

### Elasticsearch

Elasticsearch is a distributed search and analytics engine that stores and indexes log data.

```json
// Example: Searching for payment errors in the last hour
GET /logs-2024.01.15/_search
{
  "query": {
    "bool": {
      "must": [
        { "match": { "level": "ERROR" } },
        { "match": { "service": "payment-service" } }
      ],
      "filter": [
        { "range": { "@timestamp": { "gte": "now-1h" } } }
      ]
    }
  },
  "sort": [{ "@timestamp": { "order": "desc" } }],
  "size": 50
}
```

### Logstash

Logstash ingests, transforms, and ships log data.

```ruby
# logstash.conf
input {
  beats {
    port => 5044
  }
  tcp {
    port => 5000
    codec => json
  }
}

filter {
  # Parse JSON logs
  json {
    source => "message"
  }

  # Add geo-IP information
  geoip {
    source => "client_ip"
  }

  # Parse timestamps
  date {
    match => ["timestamp", "ISO8601"]
    target => "@timestamp"
  }

  # Add environment tag
  mutate {
    add_field => { "environment" => "production" }
  }

  # Drop debug logs in production
  if [level] == "DEBUG" {
    drop {}
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "logs-%{[service]}-%{+YYYY.MM.dd}"
  }
}
```

### Kibana

Kibana provides visualization and exploration of Elasticsearch data:

- **Discover** — Search and filter logs in real-time
- **Visualize** — Create charts from log data (error rates over time, top error types)
- **Dashboard** — Combine multiple visualizations into a single view
- **Alerts** — Trigger notifications based on log patterns

### Docker Compose for ELK

```yaml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms1g -Xmx1g"
    ports:
      - "9200:9200"
    volumes:
      - es-data:/usr/share/elasticsearch/data

  logstash:
    image: docker.elastic.co/logstash/logstash:8.11.0
    ports:
      - "5044:5044"
      - "5000:5000"
    volumes:
      - ./logstash/pipeline:/usr/share/logstash/pipeline
    depends_on:
      - elasticsearch

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    depends_on:
      - elasticsearch

volumes:
  es-data:
```

---

## The EFK Stack

The **EFK Stack** replaces Logstash with **Fluentd** (or **Fluent Bit**), which is more Kubernetes-native and lightweight.

### Fluentd vs Fluent Bit

| Feature | Fluentd | Fluent Bit |
|---------|---------|------------|
| **Language** | Ruby + C | C |
| **Memory** | ~60MB | ~1MB |
| **Plugins** | 1000+ | ~100 |
| **Use Case** | Log aggregator | Log forwarder (edge) |
| **Deployment** | Centralized or DaemonSet | DaemonSet on every node |

### Fluent Bit Configuration

```ini
# fluent-bit.conf
[SERVICE]
    Flush         5
    Log_Level     info
    Parsers_File  parsers.conf

[INPUT]
    Name              tail
    Path              /var/log/containers/*.log
    Parser            docker
    Tag               kube.*
    Refresh_Interval  5
    Mem_Buf_Limit     50MB

[FILTER]
    Name                kubernetes
    Match               kube.*
    Kube_URL            https://kubernetes.default.svc:443
    Kube_Tag_Prefix     kube.var.log.containers.
    Merge_Log           On
    K8S-Logging.Parser  On
    K8S-Logging.Exclude On

[FILTER]
    Name    modify
    Match   *
    Add     cluster production-us-east-1

[OUTPUT]
    Name            es
    Match           *
    Host            elasticsearch.logging.svc.cluster.local
    Port            9200
    Index           fluent-bit
    Type            _doc
    Logstash_Format On
    Logstash_Prefix k8s-logs
    Retry_Limit     3
```

### Kubernetes DaemonSet for Fluent Bit

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
```

---

## Loki + Grafana

**Grafana Loki** is a horizontally-scalable, highly-available log aggregation system inspired by Prometheus. It indexes only metadata (labels), not the full text of log lines.

### Why Loki?

| Feature | Elasticsearch | Loki |
|---------|--------------|------|
| **Indexing** | Full-text index | Labels only |
| **Storage Cost** | High | Low (10-100x cheaper) |
| **Query Language** | Elasticsearch DSL | LogQL (similar to PromQL) |
| **Complexity** | High (JVM tuning, sharding) | Low |
| **Best For** | Full-text search at scale | Label-based filtering, Grafana integration |

### Loki Architecture

```
┌──────────┐     ┌─────────┐     ┌──────────┐     ┌─────────┐
│ Promtail  │────▶│  Loki   │────▶│ Storage  │     │ Grafana │
│ (agent)   │     │ (index  │     │ (S3/GCS/ │◀────│ (query  │
│           │     │  + store│     │  local)  │     │  & viz) │
└──────────┘     └─────────┘     └──────────┘     └─────────┘
```

### Promtail Configuration

```yaml
# promtail-config.yaml
server:
  http_listen_port: 9080

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: containers
    static_configs:
      - targets:
          - localhost
        labels:
          job: containerlogs
          __path__: /var/log/containers/*.log

    pipeline_stages:
      - docker: {}
      - json:
          expressions:
            level: level
            service: service
            trace_id: trace_id
      - labels:
          level:
          service:
      - timestamp:
          source: timestamp
          format: RFC3339Nano
```

### LogQL Examples

```logql
# Show all error logs from checkout-service
{service="checkout-service"} |= "error"

# Parse JSON logs and filter by status code
{job="nginx"} | json | status >= 500

# Count errors per service in the last hour
count_over_time({level="error"}[1h])

# Top 10 services by error count
topk(10, count_over_time({level="error"}[1h]))

# Rate of log lines per second
rate({service="api-gateway"}[5m])

# Filter with regex
{service=~"checkout.*"} |~ "timeout|error"

# Pipeline: parse, filter, format
{service="checkout-service"}
  | json
  | duration_ms > 1000
  | line_format "{{.user_id}} - {{.endpoint}} - {{.duration_ms}}ms"
```

### Docker Compose for Loki Stack

```yaml
version: '3.8'

services:
  loki:
    image: grafana/loki:2.9.0
    ports:
      - "3100:3100"
    volumes:
      - ./loki-config.yaml:/etc/loki/local-config.yaml
      - loki-data:/loki
    command: -config.file=/etc/loki/local-config.yaml

  promtail:
    image: grafana/promtail:2.9.0
    volumes:
      - /var/log:/var/log
      - ./promtail-config.yaml:/etc/promtail/config.yaml
    command: -config.file=/etc/promtail/config.yaml
    depends_on:
      - loki

  grafana:
    image: grafana/grafana:10.2.0
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-data:/var/lib/grafana
    depends_on:
      - loki

volumes:
  loki-data:
  grafana-data:
```

---

## Log Aggregation Patterns

### Pattern 1: Direct Shipping

```
Application → Log Aggregator (Elasticsearch/Loki)
```
Simple but creates tight coupling and can overwhelm the aggregator.

### Pattern 2: Agent-Based Collection

```
Application → stdout/file → Agent (Fluent Bit/Promtail) → Aggregator
```
Recommended pattern. Applications write to stdout (12-factor app), agents handle shipping.

### Pattern 3: Sidecar Pattern (Kubernetes)

```yaml
# Each pod has a logging sidecar
spec:
  containers:
  - name: app
    image: my-app:latest
    volumeMounts:
    - name: shared-logs
      mountPath: /var/log/app
  - name: log-shipper
    image: fluent/fluent-bit:latest
    volumeMounts:
    - name: shared-logs
      mountPath: /var/log/app
      readOnly: true
  volumes:
  - name: shared-logs
    emptyDir: {}
```

### Pattern 4: Message Queue Buffer

```
Application → Agent → Kafka/Redis → Logstash → Elasticsearch
```
Adds resilience. If Elasticsearch is down, logs are buffered in the queue.

```
              ┌──────────┐     ┌─────────┐     ┌───────────────┐
 Applications─┤ Fluent   ├────▶│  Kafka  │────▶│ Elasticsearch │
              │ Bit      │     │ (buffer)│     │               │
              └──────────┘     └─────────┘     └───────────────┘
                                    │
                            Survives downstream
                              outages
```

---

## Log Retention and Storage Strategies

### Retention Policies

```
Hot Storage (SSD/NVMe):
  - Last 7 days
  - Fast queries, expensive storage

Warm Storage (HDD):
  - 7-30 days
  - Slower queries, cheaper storage

Cold Storage (S3/GCS):
  - 30-365 days
  - Very slow queries, very cheap storage

Archive/Delete:
  - > 365 days (or per compliance requirements)
  - Object storage with lifecycle policies
```

### Elasticsearch Index Lifecycle Management (ILM)

```json
PUT _ilm/policy/log-retention-policy
{
  "policy": {
    "phases": {
      "hot": {
        "min_age": "0ms",
        "actions": {
          "rollover": {
            "max_size": "50GB",
            "max_age": "1d"
          }
        }
      },
      "warm": {
        "min_age": "7d",
        "actions": {
          "shrink": { "number_of_shards": 1 },
          "forcemerge": { "max_num_segments": 1 }
        }
      },
      "cold": {
        "min_age": "30d",
        "actions": {
          "searchable_snapshot": {
            "snapshot_repository": "my-s3-repo"
          }
        }
      },
      "delete": {
        "min_age": "365d",
        "actions": {
          "delete": {}
        }
      }
    }
  }
}
```

### Loki Retention

```yaml
# loki-config.yaml
limits_config:
  retention_period: 720h  # 30 days

compactor:
  working_directory: /loki/compactor
  shared_store: filesystem
  compaction_interval: 10m
  retention_enabled: true
  retention_delete_delay: 2h
  retention_delete_worker_count: 150
```

---

## Logging Best Practices

### Do's

1. **Use structured logging** (JSON) in all services
2. **Include correlation IDs** (trace_id, request_id) in every log entry
3. **Log at the appropriate level** — use INFO for business events, ERROR for failures
4. **Write logs to stdout** — let the platform handle collection (12-factor app)
5. **Include context** — user_id, order_id, endpoint, duration
6. **Sanitize sensitive data** — never log passwords, tokens, PII, or credit card numbers
7. **Use consistent field names** across all services (agree on a schema)

### Don'ts

1. **Don't log in tight loops** — it will overwhelm your logging infrastructure
2. **Don't use string concatenation** for log messages (performance hit)
3. **Don't log sensitive data** — PII, passwords, API keys, tokens
4. **Don't rely on log parsing** with regex — use structured logging instead
5. **Don't ignore log volume** — monitor your logging costs
6. **Don't use TRACE/DEBUG in production** by default

### Sensitive Data Handling

```python
import structlog
import re

def sanitize_processor(logger, method_name, event_dict):
    """Remove sensitive fields from log entries."""
    sensitive_fields = ['password', 'token', 'api_key', 'credit_card', 'ssn']
    for field in sensitive_fields:
        if field in event_dict:
            event_dict[field] = '***REDACTED***'

    # Mask email addresses
    if 'email' in event_dict:
        email = event_dict['email']
        event_dict['email'] = re.sub(r'(.)(.*)(@.*)', r'\1***\3', email)

    return event_dict

structlog.configure(
    processors=[
        sanitize_processor,
        structlog.processors.JSONRenderer()
    ]
)
```

---

## Key Takeaways

1. **Structured logging** (JSON) is essential for searchability and analysis
2. Use **consistent log levels** across all services — agree on conventions
3. **Centralize logs** — never SSH into containers to read logs
4. Choose your stack wisely: **ELK** for full-text search, **Loki** for cost-effective label-based querying
5. Always include **correlation IDs** (trace_id) to connect logs across services
6. Implement proper **retention policies** to manage storage costs
7. **Never log sensitive data** — implement sanitization at the logging framework level
8. Applications should log to **stdout** and let infrastructure handle collection

---

**Previous Lesson:** [01 - Introduction to Observability](01-introduction-to-observability.md)
**Next Lesson:** [03 - Metrics](03-metrics.md)
