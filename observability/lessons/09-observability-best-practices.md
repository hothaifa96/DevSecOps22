# Lesson 09: Observability Best Practices

## Table of Contents

- [Golden Signals](#golden-signals)
- [RED Method](#red-method)
- [USE Method](#use-method)
- [Choosing the Right Method](#choosing-the-right-method)
- [Dashboard Design](#dashboard-design)
- [On-Call Best Practices](#on-call-best-practices)
- [Incident Management](#incident-management)
- [Observability Culture](#observability-culture)
- [Key Takeaways](#key-takeaways)

---

## Golden Signals

The **Four Golden Signals**, defined by the Google SRE book, are the most important metrics for monitoring any user-facing system.

### 1. Latency

The time it takes to service a request.

```
Key distinction: Track successful AND failed request latency separately.
A fast 500 error is not the same as a slow 200 success.

Metrics:
  - P50 (median) latency
  - P95 latency
  - P99 latency
  - Average latency (less useful — hides outliers)
```

```promql
# P95 latency by endpoint
histogram_quantile(0.95,
  sum by (le, endpoint) (rate(http_request_duration_seconds_bucket[5m]))
)

# P99 latency (overall)
histogram_quantile(0.99,
  sum by (le) (rate(http_request_duration_seconds_bucket[5m]))
)

# Average latency
sum(rate(http_request_duration_seconds_sum[5m]))
/ sum(rate(http_request_duration_seconds_count[5m]))

# Latency of successful vs failed requests
histogram_quantile(0.95,
  sum by (le, status) (rate(http_request_duration_seconds_bucket[5m]))
)
```

### 2. Traffic

The amount of demand being placed on the system.

```
For HTTP services: Requests per second
For streaming: Sessions, connections
For databases: Queries per second, transactions per second
For messaging: Messages per second
```

```promql
# Total request rate
sum(rate(http_requests_total[5m]))

# Request rate by endpoint
sum by (endpoint) (rate(http_requests_total[5m]))

# Request rate by HTTP method
sum by (method) (rate(http_requests_total[5m]))

# Peak vs current traffic
sum(rate(http_requests_total[5m]))  # Current
max_over_time(sum(rate(http_requests_total[5m]))[24h:5m])  # 24h peak
```

### 3. Errors

The rate of requests that fail.

```
Types of errors:
  - Explicit: HTTP 5xx responses
  - Implicit: HTTP 200 but wrong content
  - Policy-based: Response time > SLO threshold
```

```promql
# Error rate (5xx)
sum(rate(http_requests_total{status=~"5.."}[5m]))
/ sum(rate(http_requests_total[5m])) * 100

# Error rate by endpoint
sum by (endpoint) (rate(http_requests_total{status=~"5.."}[5m]))
/ sum by (endpoint) (rate(http_requests_total[5m])) * 100

# Error count by status code
sum by (status) (increase(http_requests_total{status=~"[45].."}[1h]))

# Slow requests as errors (latency SLO violation)
sum(rate(http_request_duration_seconds_bucket{le="0.5"}[5m]))
/ sum(rate(http_request_duration_seconds_count[5m]))
# If < 0.99, more than 1% of requests exceed 500ms SLO
```

### 4. Saturation

How "full" the system is. Emphasize resources that are most constrained.

```
Common saturation metrics:
  - CPU utilization
  - Memory usage (vs limit)
  - Disk I/O utilization
  - Network bandwidth
  - Thread pool usage
  - Connection pool usage
  - Queue depth
```

```promql
# CPU saturation
100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Memory saturation
(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100

# Disk I/O saturation
rate(node_disk_io_time_seconds_total[5m])

# Container memory vs limit
container_memory_working_set_bytes / on(namespace,pod,container)
kube_pod_container_resource_limits{resource="memory"} * 100

# Thread pool saturation (application-specific)
thread_pool_active_threads / thread_pool_max_threads * 100

# Connection pool saturation
db_pool_active_connections / db_pool_max_connections * 100
```

### Golden Signals Dashboard Layout

```
┌──────────────────────────────────────────────────────────┐
│                  Service: $service                        │
├──────────────┬───────────────┬──────────────┬────────────┤
│   LATENCY    │    TRAFFIC    │    ERRORS    │ SATURATION │
│              │               │              │            │
│  P50: 45ms   │  RPS: 1,234   │  Rate: 0.2%  │  CPU: 45%  │
│  P95: 120ms  │               │              │  Mem: 72%  │
│  P99: 850ms  │               │              │            │
├──────────────┴───────────────┴──────────────┴────────────┤
│                    Latency Over Time                      │
│   ┌──────────────────────────────────────────────────┐   │
│   │  ~~  P50    ───── P95    ━━━━━ P99              │   │
│   │                                                  │   │
│   └──────────────────────────────────────────────────┘   │
├──────────────────────────────────────────────────────────┤
│              Request Rate & Error Rate                    │
│   ┌──────────────────────────────────────────────────┐   │
│   │  ████ Total     ████ Errors (5xx)                │   │
│   │                                                  │   │
│   └──────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
```

---

## RED Method

The **RED Method** (by Tom Wilkie) is a subset of the Golden Signals, focused on **request-driven services** (microservices, APIs).

### R — Rate

Requests per second.

```promql
sum(rate(http_requests_total[5m]))
```

### E — Errors

Failed requests per second (or error ratio).

```promql
# Error rate as a ratio
sum(rate(http_requests_total{status=~"5.."}[5m]))
/ sum(rate(http_requests_total[5m]))
```

### D — Duration

Time per request (latency distribution).

```promql
histogram_quantile(0.99,
  sum by (le) (rate(http_request_duration_seconds_bucket[5m]))
)
```

### When to Use RED

```
Best for:
  - Microservices
  - API services
  - Web applications
  - Any request-response service

Not suitable for:
  - Batch processing
  - Infrastructure components (nodes, disks)
  - Databases (use USE instead)
```

---

## USE Method

The **USE Method** (by Brendan Gregg) is designed for **infrastructure and resource monitoring**.

### U — Utilization

Percentage of time the resource is busy.

```promql
# CPU utilization
100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Disk utilization
rate(node_disk_io_time_seconds_total[5m]) * 100

# Network utilization (% of bandwidth)
rate(node_network_receive_bytes_total[5m]) / 1e9 * 100  # assuming 1Gbps link
```

### S — Saturation

Amount of work the resource can't service (queued, waiting).

```promql
# CPU saturation (load average vs CPU count)
node_load1 / count without (cpu, mode) (node_cpu_seconds_total{mode="idle"})

# Disk saturation (I/O queue depth)
rate(node_disk_io_time_weighted_seconds_total[5m])

# Memory saturation (swap usage)
node_memory_SwapTotal_bytes - node_memory_SwapFree_bytes
```

### E — Errors

Count of error events.

```promql
# Disk errors
rate(node_disk_io_errors_total[5m])

# Network errors
rate(node_network_receive_errs_total[5m])
rate(node_network_transmit_errs_total[5m])

# Memory errors (ECC)
node_edac_correctable_errors_total
```

### USE Method Checklist

| Resource | Utilization | Saturation | Errors |
|----------|------------|------------|--------|
| **CPU** | `node_cpu_seconds_total` | `node_load1` / CPU count | - |
| **Memory** | `1 - MemAvailable/MemTotal` | Swap usage, OOM events | ECC errors |
| **Disk I/O** | `node_disk_io_time` | `node_disk_io_time_weighted` | `node_disk_io_errors` |
| **Disk Space** | `1 - avail/size` | - | Filesystem errors |
| **Network** | `receive/transmit_bytes` | `netdev_budget_ints_total` | `receive/transmit_errs` |

### When to Use USE

```
Best for:
  - Physical servers
  - Virtual machines
  - Kubernetes nodes
  - Database servers
  - Storage systems

Not suitable for:
  - Application-level monitoring
  - Microservices (use RED instead)
```

---

## Choosing the Right Method

```
┌──────────────────────────────────────────────┐
│          What are you monitoring?             │
├──────────────────┬───────────────────────────┤
│                  │                           │
│  Infrastructure  │  Application/Service      │
│  (node, disk,    │  (API, web app,           │
│   network)       │   microservice)           │
│                  │                           │
│  USE Method      │  RED Method               │
│  - Utilization   │  - Rate                   │
│  - Saturation    │  - Errors                 │
│  - Errors        │  - Duration               │
│                  │                           │
├──────────────────┴───────────────────────────┤
│                                              │
│  For a complete picture, use BOTH:           │
│  Golden Signals = RED + Saturation           │
│                                              │
└──────────────────────────────────────────────┘
```

---

## Dashboard Design

### Principles of Good Dashboard Design

#### 1. Start with the User Journey

```
Level 1: Executive Overview (1 dashboard)
  "Is the business healthy?"
  - Revenue processing rate
  - Overall availability (SLO status)
  - Active users
  - Error budget remaining

Level 2: Service Overview (1 per service)
  "Is this service healthy?"
  - Golden Signals (latency, traffic, errors, saturation)
  - Dependency health
  - Recent deployments

Level 3: Detailed Investigation (per component)
  "What's wrong with this specific component?"
  - Detailed metrics
  - Logs panel
  - Trace links
```

#### 2. Design for Scanning, Not Reading

```
Good Dashboard:
┌─────────┬─────────┬─────────┬─────────┐
│ 99.9%   │ 1,234   │ 0.2%    │ 45%     │  ← Key numbers at top (Stat panels)
│ Avail.  │  RPS    │ Errors  │  CPU    │
├─────────┴─────────┴─────────┴─────────┤
│      Latency Over Time (P50/P95/P99)  │  ← Trends in the middle
│      ~~~~~~~~~~~~~~~~~~~~~~            │
├───────────────────────────────────────┤
│      Request Rate & Errors            │  ← Details at the bottom
│      ██████████████████████            │
├───────────────────────────────────────┤
│      Top Errors (Table)               │  ← Drill-down at the very bottom
│      | endpoint | count | error |     │
└───────────────────────────────────────┘
```

#### 3. Use Consistent Color Coding

```
Green:   Healthy, within threshold
Yellow:  Warning, approaching threshold
Red:     Critical, threshold exceeded
Blue:    Informational, no threshold
Gray:    No data or disabled
```

#### 4. Time Range and Refresh

```
Incident investigation: Last 1h, auto-refresh 10s
Daily review: Last 24h, auto-refresh 1m
Weekly review: Last 7d, auto-refresh 5m
SLO tracking: Last 30d, auto-refresh 15m
```

### Dashboard Anti-Patterns

```
Bad:
  - 50 panels on one dashboard (information overload)
  - No hierarchy (everything at the same level)
  - Graphs without units or legends
  - Using averages instead of percentiles for latency
  - No thresholds on gauges
  - Dashboard sprawl (hundreds of dashboards nobody uses)

Good:
  - 8-12 panels per dashboard
  - Clear hierarchy (overview → details)
  - Every panel has units, legends, and descriptions
  - P50/P95/P99 for latency
  - Color-coded thresholds
  - Regular dashboard cleanup (delete unused dashboards)
```

### Dashboard Checklist

```
For every dashboard, verify:
  [ ] Has a clear title and description
  [ ] Variables for service/namespace/environment
  [ ] Key metrics visible without scrolling
  [ ] Consistent time ranges across panels
  [ ] Color thresholds set appropriately
  [ ] Units specified on all panels
  [ ] Legend shows useful information
  [ ] Links to related dashboards
  [ ] Links to runbooks
  [ ] Works across all variable values
```

---

## On-Call Best Practices

### On-Call Rotation Design

```
Primary On-Call:
  - Rotation: Weekly
  - Team size: 5+ engineers (no more than 1 week in 5)
  - Compensation: Extra pay or time off

Secondary On-Call (backup):
  - Escalation after 15 minutes
  - Different timezone if possible

Handoff Process:
  1. Outgoing on-call writes summary of open issues
  2. Incoming on-call reviews dashboards and active alerts
  3. 15-minute handoff meeting (async or sync)
  4. Verify PagerDuty/OpsGenie schedule is correct
```

### On-Call Health Metrics

Track these to prevent burnout:

```
Metrics to track per on-call rotation:
  - Total pages received
  - Pages outside business hours
  - Pages that were actionable (vs noise)
  - Mean time to acknowledge
  - Mean time to resolve
  - Interruptions per shift

Targets:
  - < 2 pages per 12-hour shift
  - < 1 page outside business hours per week
  - > 80% of pages are actionable
  - MTTA < 5 minutes
  - MTTR < 1 hour
```

### On-Call Toolkit

Every on-call engineer should have easy access to:

```
1. Dashboards
   - Service overview dashboards
   - Infrastructure dashboards
   - SLO dashboards

2. Runbooks
   - Indexed by alert name
   - Step-by-step troubleshooting guides

3. Communication
   - Incident Slack channel
   - Escalation contacts
   - Status page access

4. Tools
   - kubectl access
   - Log search (Kibana/Grafana)
   - Trace search (Jaeger)
   - Deployment rollback access

5. Context
   - Recent deployment log
   - Known issues list
   - Architecture diagrams
```

---

## Incident Management

### Incident Severity Levels

| Severity | Description | Response Time | Communication |
|----------|-----------|--------------|---------------|
| **SEV-1** | Complete outage, data loss | Immediate (all hands) | Status page, exec notification |
| **SEV-2** | Major feature broken, degraded performance | 15 minutes | Status page, team notification |
| **SEV-3** | Minor feature broken, workaround exists | 1 hour | Team notification |
| **SEV-4** | Cosmetic issue, low impact | Next business day | Ticket created |

### Incident Lifecycle

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ Detection│──▶│ Response │──▶│  Triage  │──▶│ Resolve  │──▶│ Review   │
│          │   │          │   │          │   │          │   │          │
│ Alert    │   │ Ack page │   │ Assess   │   │ Fix the  │   │ Postmor- │
│ fires    │   │ Join call │   │ severity │   │ issue    │   │ tem      │
│          │   │ Open     │   │ Assign   │   │ Verify   │   │ Action   │
│          │   │ incident │   │ roles    │   │ recovery │   │ items    │
└──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
```

### Incident Roles

```
Incident Commander (IC):
  - Coordinates the response
  - Makes decisions about severity and communication
  - Does NOT debug (stays above the fray)

Technical Lead:
  - Leads the debugging effort
  - Coordinates between teams
  - Decides on remediation approach

Communications Lead:
  - Updates status page
  - Communicates with stakeholders
  - Posts updates in incident channel

Scribe:
  - Documents the timeline
  - Captures actions and decisions
  - Creates the postmortem draft
```

### Postmortem Template

```markdown
# Postmortem: [Incident Title]

## Summary
Brief description of what happened, impact, and duration.

## Timeline (all times UTC)
- 14:23 — Alert fired: HighErrorRate on checkout-service
- 14:25 — On-call engineer acknowledged
- 14:30 — Incident declared SEV-2
- 14:35 — Root cause identified: Bad database migration in deploy v2.4.1
- 14:40 — Rollback initiated
- 14:45 — Service recovered
- 14:50 — Monitoring confirms error rate back to normal
- 15:00 — Incident resolved

## Impact
- Duration: 22 minutes
- Users affected: ~2,500 (unable to complete checkout)
- Revenue impact: ~$12,000 estimated lost revenue
- Error budget consumed: 8% of monthly budget

## Root Cause
The database migration in v2.4.1 added a NOT NULL column without a default
value, causing INSERT failures for the checkout flow.

## Detection
Alert: HighErrorRate fired after 5 minutes of >5% error rate.
Detection time: 7 minutes from deployment to alert.

## Resolution
Rolled back deployment from v2.4.1 to v2.4.0.

## Lessons Learned
### What went well
- Alert fired quickly (within 5 minutes)
- On-call responded within 2 minutes
- Rollback procedure worked smoothly

### What went wrong
- Migration was not tested with realistic data in staging
- No canary deployment was used
- CI pipeline didn't catch the migration issue

## Action Items
| Action | Owner | Priority | Due Date |
|--------|-------|----------|----------|
| Add migration tests with realistic data | @alice | P1 | 2024-01-22 |
| Implement canary deployments for checkout | @bob | P1 | 2024-02-01 |
| Add database migration linting to CI | @carol | P2 | 2024-02-15 |
| Update runbook with rollback steps | @dave | P3 | 2024-01-19 |
```

### Blameless Postmortems

```
Blameless:
  "The migration script didn't have a default value for the new column.
   How can we prevent this class of error in the future?"

Blameful (AVOID):
  "Alice wrote a bad migration and didn't test it properly."

Key principle:
  Focus on SYSTEMS and PROCESSES, not people.
  People make mistakes — build systems that catch mistakes.
```

---

## Observability Culture

### Making Observability Part of Development

```
Definition of Done (updated):
  [ ] Code reviewed and merged
  [ ] Unit tests passing
  [ ] Integration tests passing
  [ ] Metrics exposed for key operations        ← NEW
  [ ] Dashboard updated or created               ← NEW
  [ ] Alerts defined for failure scenarios        ← NEW
  [ ] Runbook created or updated                 ← NEW
  [ ] Deployed to staging and verified            ← NEW
```

### Observability Review Checklist (Code Review)

```
When reviewing a PR, ask:
  [ ] Are new endpoints instrumented with metrics?
  [ ] Are error paths logging structured errors with context?
  [ ] Are external calls wrapped in spans for tracing?
  [ ] Are SLIs defined for new features?
  [ ] Are alerts defined for new failure modes?
  [ ] Are sensitive fields excluded from logs?
```

### Regular Observability Practices

```
Daily:
  - Review overnight alerts and dashboards
  - Check SLO burn rate

Weekly:
  - Review on-call load and alert quality
  - Identify and fix noisy alerts
  - Review top errors and latency outliers

Monthly:
  - SLO review (are targets appropriate?)
  - Dashboard cleanup (delete unused)
  - Runbook review (are they accurate?)
  - On-call retrospective

Quarterly:
  - Observability maturity assessment
  - Tool evaluation (are we using the right tools?)
  - Cost review (logging/metrics storage costs)
  - Game day / chaos engineering exercise
```

---

## Key Takeaways

1. **Golden Signals** (latency, traffic, errors, saturation) are the foundation of service monitoring
2. Use the **RED Method** for microservices and the **USE Method** for infrastructure
3. Design dashboards in a **hierarchy**: executive overview → service overview → detailed investigation
4. **On-call health** matters — track pages per shift and aim for < 2 actionable alerts per shift
5. Follow a structured **incident management** process with clear roles (IC, Tech Lead, Comms Lead, Scribe)
6. Conduct **blameless postmortems** — focus on systems and processes, not people
7. Make observability part of the **definition of done** in your development process
8. **Dashboard design** should prioritize scanning: key numbers at top, trends in middle, details at bottom
9. Regularly audit your observability practices — monthly and quarterly reviews
10. Observability is a **culture**, not a tool — everyone on the team owns it

---

**Previous Lesson:** [08 - Kubernetes Observability](08-kubernetes-observability.md)

---

## Course Summary

Congratulations on completing the Observability module! Here's what you've learned:

| Lesson | Topic | Key Concept |
|--------|-------|-------------|
| 01 | Introduction | Observability vs Monitoring, Three Pillars |
| 02 | Logging | Structured logging, ELK/EFK, Loki |
| 03 | Metrics | Metric types, PromQL, Prometheus |
| 04 | Tracing | OpenTelemetry, Jaeger, context propagation |
| 05 | Grafana | Dashboards, variables, alerting, as-code |
| 06 | Prometheus | Architecture, service discovery, storage, Thanos |
| 07 | Alerting | SLOs, error budgets, burn rates, runbooks |
| 08 | Kubernetes | kube-state-metrics, Prometheus Operator, logging |
| 09 | Best Practices | Golden Signals, RED/USE, incident management |

**Now proceed to the labs to practice these concepts hands-on!**
