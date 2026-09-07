# Lesson 07: Alerting

## Table of Contents

- [Alerting Philosophy](#alerting-philosophy)
- [Alert Fatigue](#alert-fatigue)
- [Alerting Best Practices](#alerting-best-practices)
- [Alertmanager Deep Dive](#alertmanager-deep-dive)
- [PagerDuty and OpsGenie Integration](#pagerduty-and-opsgenie-integration)
- [Runbooks](#runbooks)
- [SLOs, SLIs, and SLAs](#slos-slis-and-slas)
- [Error Budgets](#error-budgets)
- [Multi-Window Multi-Burn-Rate Alerts](#multi-window-multi-burn-rate-alerts)
- [Key Takeaways](#key-takeaways)

---

## Alerting Philosophy

### The Purpose of Alerting

Alerts exist for one reason: **to notify a human that they need to take action**. If an alert doesn't require human action, it shouldn't page someone.

### The Three Questions Before Creating an Alert

1. **Does this require immediate human intervention?** → If yes, page someone
2. **Will the issue resolve itself?** → If yes, log it, don't page
3. **Can a human actually fix this?** → If no, automate the fix

### Alert Severity Levels

| Severity | Response | Channel | Example |
|----------|----------|---------|---------|
| **Critical (P1)** | Immediate — wake someone up | PagerDuty/OpsGenie phone call | Service is completely down, data loss imminent |
| **Warning (P2)** | Business hours | Slack + email | Error rate elevated, disk 80% full |
| **Info (P3)** | Next business day | Slack + ticket | Certificate expires in 14 days |
| **Notification** | No response needed | Dashboard only | Deployment completed, scaling event |

### What Google SRE Says

> "Every time the pager goes off, I should be able to react with a sense of urgency. I can only react with a sense of urgency a few times a day before I become fatigued."
> — *Google SRE Book*

---

## Alert Fatigue

**Alert fatigue** occurs when responders become desensitized to alerts due to excessive, noisy, or irrelevant notifications.

### Symptoms of Alert Fatigue

```
Week 1:  🚨 Alert! → "Drop everything, investigate immediately!"
Week 4:  🚨 Alert! → "Let me check when I have a moment..."
Week 8:  🚨 Alert! → "It's probably nothing, I'll check later."
Week 12: 🚨 Alert! → *ignored* ← Real outage missed
```

### Common Causes

1. **Too many alerts** — hundreds of alerts per day
2. **Flapping alerts** — alerts that fire and resolve repeatedly
3. **Non-actionable alerts** — alerts that require no human action
4. **Duplicate alerts** — same issue triggers 10 different alerts
5. **Missing context** — "CPU is high" but no indication of impact
6. **Wrong severity** — everything is "critical"

### How to Combat Alert Fatigue

```
1. Audit alerts quarterly
   - Delete alerts nobody acts on
   - Merge duplicate alerts
   - Downgrade severity where appropriate

2. Measure alert quality
   - Track: alerts fired, acknowledged, resolved
   - Target: <5 actionable alerts per on-call shift

3. Require runbooks
   - Every alert must link to a runbook
   - If you can't write a runbook, the alert isn't actionable

4. Use proper thresholds
   - Alert on symptoms (user impact), not causes (CPU usage)
   - Use SLO-based alerts instead of static thresholds
```

---

## Alerting Best Practices

### 1. Alert on Symptoms, Not Causes

```
Bad:  "CPU usage > 85%"
      ↳ CPU can be 95% and the service is fine
      ↳ CPU can be 50% and the service is broken

Good: "Error rate > 1% for /api/checkout"
      ↳ This means users are affected
      ↳ Actionable regardless of the underlying cause
```

### 2. Use the `for` Duration

Avoid alerting on transient spikes:

```yaml
# Bad: fires on a 1-second spike
- alert: HighErrorRate
  expr: error_rate > 0.05

# Good: must be true for 5 minutes
- alert: HighErrorRate
  expr: error_rate > 0.05
  for: 5m
```

### 3. Include Rich Annotations

```yaml
- alert: HighErrorRate
  expr: |
    sum(rate(http_requests_total{status=~"5.."}[5m])) by (job)
    /
    sum(rate(http_requests_total[5m])) by (job)
    > 0.05
  for: 5m
  labels:
    severity: critical
    team: backend
  annotations:
    summary: "High error rate on {{ $labels.job }}"
    description: |
      Error rate is {{ $value | humanizePercentage }}.
      Current error count: {{ with query "sum(increase(http_requests_total{status=~\"5..\",job=\"" }}{{ $labels.job }}{{ "\"}[5m]))" }}{{ . | first | value }}{{ end }}
    impact: "Users are experiencing checkout failures"
    runbook_url: "https://wiki.example.com/runbooks/high-error-rate"
    dashboard_url: "https://grafana.example.com/d/service-overview?var-service={{ $labels.job }}"
    grafana_url: "https://grafana.example.com/explore?expr=rate(http_requests_total{status=~\"5..\",job=\"{{ $labels.job }}\"}[5m])"
```

### 4. Use Inhibition Rules

Prevent dependent alerts from firing:

```yaml
# If the entire cluster is down, don't fire individual service alerts
inhibit_rules:
  - source_matchers:
      - alertname="ClusterDown"
    target_matchers:
      - severity="warning"
    equal: ['cluster']

  - source_matchers:
      - alertname="NodeDown"
    target_matchers:
      - alertname="PodDown"
    equal: ['node']
```

### 5. Group Related Alerts

```yaml
route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 30s      # Wait before sending first notification
  group_interval: 5m    # Wait between grouped notifications
  repeat_interval: 4h   # Resend after 4 hours if still firing
```

### 6. Tiered Alerting

```
Tier 1 — Automated Response (no human)
  Auto-scaling, auto-restart, circuit breaker
  Example: Pod OOMKilled → Kubernetes auto-restarts

Tier 2 — Dashboard Alert (passive notification)
  Slack message, ticket creation
  Example: Memory usage trending up, disk 70% full

Tier 3 — Active Notification (human must respond)
  PagerDuty, OpsGenie phone call
  Example: Error budget burned, service SLO violated
```

---

## Alertmanager Deep Dive

### Architecture

```
                         ┌─────────────────────────────────┐
  Prometheus ──────────▶ │        Alertmanager              │
  (alerting rules)       │                                  │
                         │  ┌──────────┐                    │
                         │  │ Grouping │  Group by labels   │
                         │  └────┬─────┘                    │
                         │       │                          │
                         │  ┌────▼──────┐                   │
                         │  │ Inhibition│  Suppress alerts   │
                         │  └────┬──────┘                   │
                         │       │                          │
                         │  ┌────▼──────┐                   │
                         │  │ Silencing │  Mute during       │
                         │  │           │  maintenance       │
                         │  └────┬──────┘                   │
                         │       │                          │
                         │  ┌────▼──────┐                   │
                         │  │  Routing  │  Route to teams    │
                         │  └────┬──────┘                   │
                         │       │                          │
                         │  ┌────▼──────────┐               │
                         │  │ Notification  │               │
                         │  │ - Slack       │               │
                         │  │ - PagerDuty   │               │
                         │  │ - Email       │               │
                         │  │ - Webhook     │               │
                         │  └───────────────┘               │
                         └─────────────────────────────────┘
```

### Complete Alertmanager Configuration

```yaml
# alertmanager.yml
global:
  resolve_timeout: 5m
  slack_api_url: 'https://hooks.slack.com/services/T00/B00/XXXX'
  pagerduty_url: 'https://events.pagerduty.com/v2/enqueue'

# Notification templates
templates:
  - '/etc/alertmanager/templates/*.tmpl'

# Inhibition rules
inhibit_rules:
  # If critical is firing, suppress warning for same alertname
  - source_matchers:
      - severity="critical"
    target_matchers:
      - severity="warning"
    equal: ['alertname', 'service']

  # If cluster is down, suppress all other alerts for that cluster
  - source_matchers:
      - alertname="ClusterDown"
    target_matchers:
      - severity=~"warning|critical"
    equal: ['cluster']

# Routing tree
route:
  receiver: 'slack-default'
  group_by: ['alertname', 'service', 'namespace']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  routes:
    # Critical alerts → PagerDuty + Slack
    - matchers:
        - severity="critical"
      receiver: 'pagerduty-critical'
      continue: true  # Also send to next matching route

    - matchers:
        - severity="critical"
      receiver: 'slack-critical'

    # Warning alerts → Slack only
    - matchers:
        - severity="warning"
      receiver: 'slack-warnings'
      group_wait: 1m
      repeat_interval: 12h

    # Team-specific routing
    - matchers:
        - team="database"
      receiver: 'slack-database-team'
      routes:
        - matchers:
            - severity="critical"
          receiver: 'pagerduty-database'

    # Watchdog (dead man's switch)
    - matchers:
        - alertname="Watchdog"
      receiver: 'watchdog'
      repeat_interval: 1m

# Receivers
receivers:
  - name: 'slack-default'
    slack_configs:
      - channel: '#alerts'
        send_resolved: true
        title: '{{ .Status | toUpper }} {{ .CommonLabels.alertname }}'
        text: >-
          *Alert:* {{ .CommonAnnotations.summary }}
          *Description:* {{ .CommonAnnotations.description }}
          *Severity:* {{ .CommonLabels.severity }}
          *Service:* {{ .CommonLabels.service }}
          {{ if .CommonAnnotations.runbook_url }}*Runbook:* {{ .CommonAnnotations.runbook_url }}{{ end }}

  - name: 'slack-critical'
    slack_configs:
      - channel: '#alerts-critical'
        send_resolved: true
        color: '{{ if eq .Status "firing" }}danger{{ else }}good{{ end }}'
        title: '{{ .Status | toUpper }} {{ .CommonLabels.alertname }}'
        text: >-
          *Alert:* {{ .CommonAnnotations.summary }}
          *Description:* {{ .CommonAnnotations.description }}
          *Impact:* {{ .CommonAnnotations.impact }}
          *Runbook:* {{ .CommonAnnotations.runbook_url }}
          *Dashboard:* {{ .CommonAnnotations.dashboard_url }}

  - name: 'slack-warnings'
    slack_configs:
      - channel: '#alerts-warnings'
        send_resolved: true

  - name: 'slack-database-team'
    slack_configs:
      - channel: '#team-database-alerts'
        send_resolved: true

  - name: 'pagerduty-critical'
    pagerduty_configs:
      - routing_key: 'YOUR_PAGERDUTY_ROUTING_KEY'
        severity: critical
        description: '{{ .CommonAnnotations.summary }}'
        details:
          description: '{{ .CommonAnnotations.description }}'
          runbook: '{{ .CommonAnnotations.runbook_url }}'
          service: '{{ .CommonLabels.service }}'

  - name: 'pagerduty-database'
    pagerduty_configs:
      - routing_key: 'DATABASE_TEAM_PAGERDUTY_KEY'
        severity: '{{ .CommonLabels.severity }}'

  - name: 'watchdog'
    webhook_configs:
      - url: 'http://deadmansswitch.example.com/ping'
```

---

## PagerDuty and OpsGenie Integration

### PagerDuty Setup

1. Create a service in PagerDuty
2. Add an integration (Events API v2)
3. Copy the **Integration Key** (routing key)

```yaml
# Alertmanager receiver
receivers:
  - name: 'pagerduty'
    pagerduty_configs:
      - routing_key: '<INTEGRATION_KEY>'
        severity: '{{ if eq .CommonLabels.severity "critical" }}critical{{ else }}warning{{ end }}'
        client: 'Alertmanager'
        client_url: 'https://alertmanager.example.com'
        description: '{{ .CommonAnnotations.summary }}'
        details:
          firing: '{{ .Alerts.Firing | len }}'
          resolved: '{{ .Alerts.Resolved | len }}'
          description: '{{ .CommonAnnotations.description }}'
          runbook_url: '{{ .CommonAnnotations.runbook_url }}'
```

### OpsGenie Setup

```yaml
receivers:
  - name: 'opsgenie'
    opsgenie_configs:
      - api_key: '<OPSGENIE_API_KEY>'
        message: '{{ .CommonAnnotations.summary }}'
        description: '{{ .CommonAnnotations.description }}'
        priority: '{{ if eq .CommonLabels.severity "critical" }}P1{{ else if eq .CommonLabels.severity "warning" }}P3{{ else }}P5{{ end }}'
        tags: 'monitoring,{{ .CommonLabels.service }}'
        responders:
          - type: team
            name: '{{ .CommonLabels.team }}'
```

### Escalation Policies

```
PagerDuty Escalation Policy:
  Level 1 (0 min):   On-call engineer
  Level 2 (15 min):  Secondary on-call
  Level 3 (30 min):  Engineering manager
  Level 4 (60 min):  VP Engineering
```

---

## Runbooks

A **runbook** is a documented procedure for responding to a specific alert. Every alert should link to a runbook.

### Runbook Template

```markdown
# Runbook: HighErrorRate

## Alert Details
- **Alert Name:** HighErrorRate
- **Severity:** Critical
- **Service:** checkout-service
- **SLO Impact:** Yes — affects checkout availability SLO

## Description
This alert fires when the HTTP 5xx error rate exceeds 5% for more than 5 minutes
on the checkout service.

## Impact
- Users cannot complete purchases
- Revenue impact: ~$X per minute of downtime

## Investigation Steps

### 1. Check the dashboard
- Open [Service Dashboard](https://grafana.example.com/d/service-overview?var-service=checkout)
- Look at: Error rate by endpoint, Latency distribution, Pod health

### 2. Check recent deployments
```bash
kubectl -n production rollout history deployment/checkout-service
```
- If a recent deployment correlates with the error spike → rollback

### 3. Check downstream dependencies
- Payment service: [Dashboard](https://grafana.example.com/d/payment-service)
- Database: [Dashboard](https://grafana.example.com/d/postgresql)
- Redis: [Dashboard](https://grafana.example.com/d/redis)

### 4. Check logs
```logql
{service="checkout-service"} |= "error" | json | level="ERROR" 
```

### 5. Check resource usage
```promql
container_memory_working_set_bytes{pod=~"checkout.*"} / container_spec_memory_limit_bytes{pod=~"checkout.*"}
```

## Remediation Steps

### If caused by recent deployment:
```bash
kubectl -n production rollout undo deployment/checkout-service
```

### If caused by downstream dependency:
1. Enable circuit breaker
2. Notify dependency team
3. Consider graceful degradation (show "temporarily unavailable")

### If caused by resource exhaustion:
```bash
kubectl -n production scale deployment/checkout-service --replicas=5
```

### If cause is unknown:
1. Restart the pods:
   ```bash
   kubectl -n production rollout restart deployment/checkout-service
   ```
2. Escalate to the checkout team lead

## Escalation
- **Team:** Backend Engineering
- **On-call:** Check PagerDuty schedule
- **Slack:** #team-checkout
- **Escalation after 30 min:** Engineering Manager
```

---

## SLOs, SLIs, and SLAs

### Definitions

```
SLI (Service Level Indicator):
  A quantitative measure of service quality
  Example: "The proportion of successful HTTP requests"

SLO (Service Level Objective):
  A target for an SLI, set by the engineering team
  Example: "99.9% of requests should be successful over a 30-day window"

SLA (Service Level Agreement):
  A contractual promise to customers (with penalties)
  Example: "We guarantee 99.9% uptime; below that, you get credits"

Relationship:
  SLI measures reality → SLO sets the target → SLA makes it contractual

  Always: SLA ≤ SLO (your internal target should be stricter than your promise)
```

### Common SLIs

| SLI | Definition | Calculation |
|-----|-----------|-------------|
| **Availability** | Proportion of successful requests | `good_requests / total_requests` |
| **Latency** | Proportion of requests faster than threshold | `requests_below_threshold / total_requests` |
| **Throughput** | Requests processed per second | `total_requests / time_period` |
| **Correctness** | Proportion of correct responses | `correct_responses / total_responses` |
| **Freshness** | Proportion of data updated within threshold | `fresh_data_points / total_data_points` |

### Defining SLOs in Practice

```yaml
# Example SLO definitions
slos:
  - name: "Checkout Availability"
    sli: "ratio of successful checkout requests (non-5xx)"
    target: 99.9%
    window: 30 days
    promql: |
      sum(rate(http_requests_total{job="checkout",status!~"5.."}[30d]))
      /
      sum(rate(http_requests_total{job="checkout"}[30d]))

  - name: "Checkout Latency"
    sli: "ratio of checkout requests completing in under 500ms"
    target: 99.0%
    window: 30 days
    promql: |
      sum(rate(http_request_duration_seconds_bucket{job="checkout",le="0.5"}[30d]))
      /
      sum(rate(http_request_duration_seconds_count{job="checkout"}[30d]))

  - name: "API Availability"
    sli: "ratio of successful API requests"
    target: 99.95%
    window: 30 days
```

---

## Error Budgets

The **error budget** is the amount of unreliability you're allowed based on your SLO.

### Calculating Error Budgets

```
SLO: 99.9% availability over 30 days

Error Budget = 1 - SLO = 0.1%

In a 30-day month:
  Total minutes = 30 × 24 × 60 = 43,200
  Allowed downtime = 0.1% × 43,200 = 43.2 minutes

In requests (assuming 1M requests/day):
  Total requests = 30 × 1,000,000 = 30,000,000
  Allowed failures = 0.1% × 30,000,000 = 30,000 errors
```

### Error Budget Policies

```
Budget Remaining > 50%:
  → Full speed ahead — deploy new features, experiment
  → Normal release cadence

Budget Remaining 20-50%:
  → Caution — increase testing, slower releases
  → Review recent incidents

Budget Remaining < 20%:
  → Slow down — freeze non-critical deployments
  → Focus on reliability improvements

Budget Exhausted (0%):
  → STOP — freeze all feature deployments
  → All engineering effort goes to reliability
  → Postmortem required for budget-burning incidents
```

### PromQL for Error Budgets

```promql
# Remaining error budget (percentage)
# SLO = 99.9% (0.999), Window = 30 days
(
  1 - (
    sum(increase(http_requests_total{job="checkout", status=~"5.."}[30d]))
    /
    sum(increase(http_requests_total{job="checkout"}[30d]))
  )
  - 0.999
) / (1 - 0.999) * 100

# Simplified: Error budget consumption rate
# How fast are we burning the budget?
(
  1 - (
    sum(rate(http_requests_total{job="checkout", status!~"5.."}[1h]))
    /
    sum(rate(http_requests_total{job="checkout"}[1h]))
  )
) / (1 - 0.999)
# If > 1, we're burning budget faster than allowed
```

---

## Multi-Window Multi-Burn-Rate Alerts

The gold standard for SLO-based alerting. Instead of static thresholds, alert based on **how fast the error budget is being consumed**.

### Concept

```
Burn Rate = Actual error rate / Allowed error rate

If SLO = 99.9%, allowed error rate = 0.1%
If actual error rate = 1%, burn rate = 1% / 0.1% = 10x

At 10x burn rate, the entire 30-day error budget is consumed in 3 days.
```

### Burn Rate Table

| Burn Rate | Budget Consumed In | Alert Window (Long) | Alert Window (Short) | Severity |
|-----------|-------------------|--------------------|--------------------|----------|
| **14.4x** | 2 days | 1 hour | 5 minutes | Critical (page) |
| **6x** | 5 days | 6 hours | 30 minutes | Critical (page) |
| **3x** | 10 days | 1 day | 2 hours | Warning (ticket) |
| **1x** | 30 days | 3 days | 6 hours | Warning (ticket) |

### Implementation

```yaml
# alerting_rules_slo.yml
groups:
  - name: slo-checkout-availability
    rules:
      # Error ratio recording rule
      - record: slo:http_error_ratio:rate5m
        expr: |
          sum(rate(http_requests_total{job="checkout", status=~"5.."}[5m]))
          /
          sum(rate(http_requests_total{job="checkout"}[5m]))

      # ───── Critical: 14.4x burn rate ─────
      # Burns budget in 2 days
      - alert: CheckoutHighBurnRate
        expr: |
          (
            sum(rate(http_requests_total{job="checkout", status=~"5.."}[1h]))
            / sum(rate(http_requests_total{job="checkout"}[1h]))
          ) > (14.4 * 0.001)
          and
          (
            sum(rate(http_requests_total{job="checkout", status=~"5.."}[5m]))
            / sum(rate(http_requests_total{job="checkout"}[5m]))
          ) > (14.4 * 0.001)
        for: 2m
        labels:
          severity: critical
          slo: checkout-availability
        annotations:
          summary: "Checkout error budget burning fast (14.4x)"
          description: "At current rate, 30-day error budget will be exhausted in 2 days."
          runbook_url: "https://wiki.example.com/runbooks/checkout-slo-burn"

      # ───── Critical: 6x burn rate ─────
      # Burns budget in 5 days
      - alert: CheckoutMediumBurnRate
        expr: |
          (
            sum(rate(http_requests_total{job="checkout", status=~"5.."}[6h]))
            / sum(rate(http_requests_total{job="checkout"}[6h]))
          ) > (6 * 0.001)
          and
          (
            sum(rate(http_requests_total{job="checkout", status=~"5.."}[30m]))
            / sum(rate(http_requests_total{job="checkout"}[30m]))
          ) > (6 * 0.001)
        for: 2m
        labels:
          severity: critical
          slo: checkout-availability
        annotations:
          summary: "Checkout error budget burning (6x)"
          description: "At current rate, 30-day error budget will be exhausted in 5 days."

      # ───── Warning: 3x burn rate ─────
      # Burns budget in 10 days
      - alert: CheckoutSlowBurnRate
        expr: |
          (
            sum(rate(http_requests_total{job="checkout", status=~"5.."}[1d]))
            / sum(rate(http_requests_total{job="checkout"}[1d]))
          ) > (3 * 0.001)
          and
          (
            sum(rate(http_requests_total{job="checkout", status=~"5.."}[2h]))
            / sum(rate(http_requests_total{job="checkout"}[2h]))
          ) > (3 * 0.001)
        for: 15m
        labels:
          severity: warning
          slo: checkout-availability
        annotations:
          summary: "Checkout error budget burning slowly (3x)"
          description: "At current rate, 30-day error budget will be exhausted in 10 days."
```

---

## Key Takeaways

1. **Alert on symptoms** (user impact), not causes (CPU usage)
2. **Alert fatigue** is the #1 alerting problem — audit and prune alerts regularly
3. Every alert must be **actionable** and link to a **runbook**
4. Use **proper severity levels** — not everything is critical
5. **Alertmanager** provides grouping, inhibition, silencing, and routing
6. Define **SLIs and SLOs** for your critical services
7. Use **error budgets** to balance feature velocity with reliability
8. Implement **multi-window multi-burn-rate** alerts for sophisticated SLO alerting
9. **Inhibition rules** prevent alert storms — suppress dependent alerts
10. Integrate with **PagerDuty/OpsGenie** for critical alerts and escalation

---

**Previous Lesson:** [06 - Prometheus Deep Dive](06-prometheus.md)
**Next Lesson:** [08 - Kubernetes Observability](08-kubernetes-observability.md)
