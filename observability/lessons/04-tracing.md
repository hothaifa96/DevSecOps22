# Lesson 04: Distributed Tracing

## Table of Contents

- [What is Distributed Tracing?](#what-is-distributed-tracing)
- [Core Concepts](#core-concepts)
- [OpenTelemetry](#opentelemetry)
- [Jaeger](#jaeger)
- [Zipkin](#zipkin)
- [Trace Context Propagation](#trace-context-propagation)
- [Sampling Strategies](#sampling-strategies)
- [Instrumenting Applications](#instrumenting-applications)
- [Tracing Best Practices](#tracing-best-practices)
- [Key Takeaways](#key-takeaways)

---

## What is Distributed Tracing?

Distributed tracing tracks a **single request** as it flows through multiple services in a distributed system. It provides visibility into the entire lifecycle of a request, showing where time is spent and where failures occur.

### The Problem

In a monolithic application, a stack trace shows you the entire call path:

```
Exception in thread "main" java.lang.NullPointerException
    at com.example.OrderService.processPayment(OrderService.java:45)
    at com.example.CheckoutController.checkout(CheckoutController.java:23)
    at com.example.Application.main(Application.java:10)
```

In a microservices architecture, a single request touches many services:

```
User → API Gateway → Auth Service → Cart Service → Inventory Service
                                   → Payment Service → Stripe API
                                   → Notification Service → SendGrid API
```

Without tracing, when the checkout fails, you have **no way to see the full picture**. Each service has its own logs, but there's no thread connecting them.

### The Solution

Distributed tracing creates a **unique trace ID** that follows the request through every service:

```
Trace ID: 4bf92f3577b34da6a3ce929d0e0e4736

Service A (API Gateway)     ──────────────────────────── 200ms total
  │
  ├── Service B (Auth)      ████ 20ms
  │
  ├── Service C (Cart)      ██████████ 50ms
  │   └── Redis             ███ 15ms
  │
  ├── Service D (Payment)   ██████████████████████████ 120ms  ← BOTTLENECK
  │   └── Stripe API        █████████████████████████ 115ms   ← ROOT CAUSE
  │
  └── Service E (Order)     █████ 25ms
      └── PostgreSQL        ███ 12ms
```

Now you can see that the Stripe API call is causing the slow checkout.

---

## Core Concepts

### Trace

A **trace** represents the entire journey of a request through the system. It's a tree of spans.

```
Trace
├── Span A (root span)
│   ├── Span B (child of A)
│   │   └── Span C (child of B)
│   └── Span D (child of A)
│       ├── Span E (child of D)
│       └── Span F (child of D)
```

### Span

A **span** represents a single unit of work within a trace. Every span contains:

```json
{
  "traceId": "4bf92f3577b34da6a3ce929d0e0e4736",
  "spanId": "00f067aa0ba902b7",
  "parentSpanId": "a3ce929d0e0e4736",
  "operationName": "POST /api/checkout",
  "serviceName": "checkout-service",
  "startTime": "2024-01-15T10:23:45.123Z",
  "duration": 200,
  "status": "OK",
  "attributes": {
    "http.method": "POST",
    "http.url": "/api/checkout",
    "http.status_code": 200,
    "user.id": "user-789",
    "order.id": "order-456",
    "order.total": 99.99
  },
  "events": [
    {
      "name": "payment.processed",
      "timestamp": "2024-01-15T10:23:45.200Z",
      "attributes": {
        "payment.method": "credit_card",
        "payment.amount": 99.99
      }
    }
  ]
}
```

### Span Attributes

Attributes are key-value pairs that provide context about a span:

```
Semantic Conventions (standardized attribute names):

HTTP:
  http.method         = "POST"
  http.url            = "https://api.example.com/checkout"
  http.status_code    = 200
  http.request_content_length = 1024

Database:
  db.system           = "postgresql"
  db.statement        = "SELECT * FROM users WHERE id = $1"
  db.operation        = "SELECT"
  db.name             = "users_db"

RPC:
  rpc.system          = "grpc"
  rpc.service         = "PaymentService"
  rpc.method          = "ProcessPayment"

Messaging:
  messaging.system    = "kafka"
  messaging.destination = "orders-topic"
  messaging.operation = "publish"
```

### Span Events

Events are **timestamped annotations** within a span:

```python
span.add_event("cache.miss", attributes={"cache.key": "user:789"})
span.add_event("retry.attempt", attributes={"attempt": 2, "reason": "timeout"})
span.add_event("exception", attributes={
    "exception.type": "TimeoutError",
    "exception.message": "Connection timed out after 5000ms"
})
```

### Span Status

```
OK     — The operation completed successfully
ERROR  — The operation failed
UNSET  — Status not explicitly set (default)
```

### Baggage

**Baggage** is key-value pairs that propagate across all spans in a trace. Unlike span attributes (which are local to a span), baggage travels with the context.

```python
# Service A: Set baggage
from opentelemetry import baggage

ctx = baggage.set_baggage("user.tier", "premium")
ctx = baggage.set_baggage("feature.flag.new-checkout", "true")

# Service D (downstream): Read baggage
tier = baggage.get_baggage("user.tier")  # "premium"
```

**Use sparingly** — baggage adds overhead to every request between services.

---

## OpenTelemetry

**OpenTelemetry (OTel)** is the CNCF standard for observability instrumentation. It provides a unified API, SDK, and tools for generating traces, metrics, and logs.

### Why OpenTelemetry?

Before OTel, you had to choose between incompatible instrumentation libraries:
- OpenTracing (tracing only)
- OpenCensus (tracing + metrics)
- Vendor-specific SDKs (Datadog, New Relic, etc.)

OpenTelemetry **unifies** all of these into one standard.

### Architecture

```
┌──────────────────────────────────────────────┐
│              Application Code                │
│  ┌───────────────────────────────────────┐   │
│  │        OpenTelemetry SDK              │   │
│  │  ┌─────────┐ ┌─────────┐ ┌────────┐  │   │
│  │  │ Traces  │ │ Metrics │ │  Logs  │  │   │
│  │  └────┬────┘ └────┬────┘ └───┬────┘  │   │
│  │       └───────────┼──────────┘        │   │
│  │              ┌────▼────┐              │   │
│  │              │Exporter │              │   │
│  │              └────┬────┘              │   │
│  └───────────────────┼───────────────────┘   │
└──────────────────────┼───────────────────────┘
                       │ OTLP (gRPC/HTTP)
              ┌────────▼────────┐
              │  OTel Collector │ (optional, recommended)
              │  ┌────────────┐ │
              │  │ Receivers  │ │
              │  │ Processors │ │
              │  │ Exporters  │ │
              │  └────────────┘ │
              └────────┬────────┘
                       │
          ┌────────────┼────────────┐
          │            │            │
     ┌────▼───┐  ┌────▼───┐  ┌────▼───┐
     │ Jaeger │  │ Zipkin │  │ Tempo  │
     └────────┘  └────────┘  └────────┘
```

### OpenTelemetry Collector

The OTel Collector is a **vendor-agnostic proxy** that receives, processes, and exports telemetry data.

```yaml
# otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 5s
    send_batch_size: 1024

  memory_limiter:
    check_interval: 1s
    limit_mib: 512
    spike_limit_mib: 128

  attributes:
    actions:
      - key: environment
        value: production
        action: upsert

exporters:
  otlp/jaeger:
    endpoint: jaeger:4317
    tls:
      insecure: true

  prometheus:
    endpoint: 0.0.0.0:8889

  loki:
    endpoint: http://loki:3100/loki/api/v1/push

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, batch, attributes]
      exporters: [otlp/jaeger]

    metrics:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [prometheus]

    logs:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [loki]
```

---

## Jaeger

**Jaeger** is an open-source distributed tracing platform originally developed by Uber.

### Architecture

```
┌──────────┐     ┌───────────┐     ┌─────────────┐     ┌──────────┐
│ App +    │────▶│  Jaeger   │────▶│   Jaeger    │────▶│  Jaeger  │
│ OTel SDK │     │  Agent    │     │  Collector  │     │  Query   │
│          │     │ (sidecar) │     │             │     │  (UI)    │
└──────────┘     └───────────┘     └──────┬──────┘     └──────────┘
                                          │
                                   ┌──────▼──────┐
                                   │   Storage   │
                                   │ (Cassandra/ │
                                   │ Elasticsearch│
                                   │ /Kafka)     │
                                   └─────────────┘
```

### Quick Start with Docker

```bash
# All-in-one Jaeger (development only)
docker run -d \
  --name jaeger \
  -p 16686:16686 \
  -p 4317:4317 \
  -p 4318:4318 \
  -p 14250:14250 \
  jaegertracing/all-in-one:latest

# UI available at http://localhost:16686
# OTLP gRPC at localhost:4317
# OTLP HTTP at localhost:4318
```

### Jaeger UI Features

- **Search traces** by service, operation, tags, duration, and time range
- **Compare traces** side by side
- **Dependency graph** — auto-generated service dependency map
- **Span detail view** — attributes, events, logs within each span
- **Critical path analysis** — identifies the longest path through the trace

---

## Zipkin

**Zipkin** is another popular open-source distributed tracing system, originally developed by Twitter.

### Jaeger vs Zipkin

| Feature | Jaeger | Zipkin |
|---------|--------|--------|
| **Origin** | Uber | Twitter |
| **Language** | Go | Java |
| **Storage** | Cassandra, ES, Kafka, Badger | Cassandra, ES, MySQL, in-memory |
| **UI** | More feature-rich | Simpler |
| **Protocol** | OTLP, Thrift, gRPC | HTTP, Kafka |
| **CNCF** | Graduated project | Not CNCF |
| **Recommendation** | Preferred for new deployments | Legacy or simple setups |

### Zipkin Quick Start

```bash
docker run -d \
  --name zipkin \
  -p 9411:9411 \
  openzipkin/zipkin:latest

# UI available at http://localhost:9411
```

---

## Trace Context Propagation

For tracing to work across services, the **trace context** must be propagated between services. This is done via HTTP headers (or message metadata for async communication).

### W3C Trace Context (Standard)

The W3C Trace Context standard defines two headers:

```
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
             ││ ││                                ││                ││
             ││ ││                                ││                └┤ Flags (01 = sampled)
             ││ ││                                └┤                  
             ││ ││                                 Parent Span ID (16 hex)
             ││ └┤
             ││  Trace ID (32 hex characters)
             └┤
              Version (00)

tracestate: vendor1=value1,vendor2=value2
```

### Propagation in Practice

```
Service A (API Gateway)
  │
  │  HTTP Request to Service B
  │  Headers:
  │    traceparent: 00-abc123-span001-01
  │    tracestate: myvendor=...
  │
  ▼
Service B (Cart Service)
  │  Reads traceparent header
  │  Creates child span with same trace ID
  │
  │  HTTP Request to Service C
  │  Headers:
  │    traceparent: 00-abc123-span002-01  (same trace ID, new span ID)
  │
  ▼
Service C (Inventory Service)
  │  Reads traceparent header
  │  Creates child span with same trace ID
```

### Propagation Formats

| Format | Header | Used By |
|--------|--------|---------|
| **W3C Trace Context** | `traceparent`, `tracestate` | OpenTelemetry (default) |
| **B3 (Zipkin)** | `X-B3-TraceId`, `X-B3-SpanId`, `X-B3-Sampled` | Zipkin, Istio |
| **B3 Single** | `b3` | Zipkin compact format |
| **Jaeger** | `uber-trace-id` | Jaeger legacy |
| **AWS X-Ray** | `X-Amzn-Trace-Id` | AWS services |

### Configuring Propagation in OpenTelemetry

```python
from opentelemetry import trace
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.propagators.b3 import B3MultiFormat
from opentelemetry.propagate import set_global_textmap
from opentelemetry.trace.propagation import TraceContextTextMapPropagator

# Support both W3C and B3 formats (useful during migration)
set_global_textmap(CompositePropagator([
    TraceContextTextMapPropagator(),
    B3MultiFormat()
]))
```

---

## Sampling Strategies

Tracing every request is expensive. Sampling reduces the volume while preserving visibility.

### 1. Head-Based Sampling

Decision made **at the start** of the trace (before any work is done).

```
Always Sample (ratio: 1.0)
  Every request is traced — useful for development

Probabilistic (ratio: 0.1)
  10% of requests are traced — good for moderate traffic

Rate Limiting (rate: 100/s)
  Trace up to 100 requests per second — good for high traffic
```

```python
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

# Sample 10% of traces
sampler = TraceIdRatioBased(0.1)
```

### 2. Tail-Based Sampling

Decision made **at the end** of the trace (after all spans are collected). This allows sampling based on outcome.

```
Tail-based sampling rules:
  - Always keep traces with errors (status = ERROR)
  - Always keep traces longer than 5 seconds
  - Always keep traces from the /checkout endpoint
  - Sample 1% of all other traces
```

```yaml
# OTel Collector tail sampling processor
processors:
  tail_sampling:
    decision_wait: 10s
    num_traces: 100000
    policies:
      # Always keep error traces
      - name: errors
        type: status_code
        status_code:
          status_codes: [ERROR]

      # Always keep slow traces
      - name: slow-traces
        type: latency
        latency:
          threshold_ms: 5000

      # Always keep specific endpoints
      - name: important-endpoints
        type: string_attribute
        string_attribute:
          key: http.url
          values: ["/api/checkout", "/api/payment"]

      # Sample 5% of everything else
      - name: probabilistic
        type: probabilistic
        probabilistic:
          sampling_percentage: 5
```

### 3. Adaptive Sampling

Dynamically adjusts sampling rate based on traffic volume:

```
Low traffic  (< 100 req/s)  → Sample 100%
Medium traffic (100-1000 req/s) → Sample 10%
High traffic (> 1000 req/s) → Sample 1%
```

### Sampling Comparison

| Strategy | Pros | Cons |
|----------|------|------|
| **Head-based** | Simple, low overhead | May miss interesting traces |
| **Tail-based** | Keeps all interesting traces | Requires buffering all spans |
| **Adaptive** | Balances cost and coverage | More complex to configure |

---

## Instrumenting Applications

### Python with OpenTelemetry

```python
# Install
# pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp
# pip install opentelemetry-instrumentation-flask opentelemetry-instrumentation-requests

from flask import Flask
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

# Configure the tracer
resource = Resource.create({
    "service.name": "checkout-service",
    "service.version": "2.4.1",
    "deployment.environment": "production"
})

provider = TracerProvider(resource=resource)
processor = BatchSpanProcessor(
    OTLPSpanExporter(endpoint="http://otel-collector:4317")
)
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

# Create Flask app
app = Flask(__name__)

# Auto-instrument Flask and requests library
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()

# Get a tracer for manual instrumentation
tracer = trace.get_tracer(__name__)

@app.route('/api/checkout', methods=['POST'])
def checkout():
    # Auto-instrumented by FlaskInstrumentor

    with tracer.start_as_current_span("validate_cart") as span:
        span.set_attribute("cart.items_count", 3)
        cart = validate_cart()

    with tracer.start_as_current_span("process_payment") as span:
        span.set_attribute("payment.method", "credit_card")
        span.set_attribute("payment.amount", 99.99)
        try:
            result = process_payment(cart)
        except Exception as e:
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise

    with tracer.start_as_current_span("create_order") as span:
        order = create_order(cart, result)
        span.set_attribute("order.id", order.id)
        span.add_event("order.created", attributes={"order_id": order.id})

    return {"order_id": order.id}
```

### Node.js with OpenTelemetry

```javascript
// tracing.js — Load this BEFORE your application code
'use strict';

const { NodeSDK } = require('@opentelemetry/sdk-node');
const { OTLPTraceExporter } = require('@opentelemetry/exporter-trace-otlp-grpc');
const { getNodeAutoInstrumentations } = require('@opentelemetry/auto-instrumentations-node');
const { Resource } = require('@opentelemetry/resources');
const { SemanticResourceAttributes } = require('@opentelemetry/semantic-conventions');

const sdk = new NodeSDK({
  resource: new Resource({
    [SemanticResourceAttributes.SERVICE_NAME]: 'checkout-service',
    [SemanticResourceAttributes.SERVICE_VERSION]: '2.4.1',
  }),
  traceExporter: new OTLPTraceExporter({
    url: 'http://otel-collector:4317',
  }),
  instrumentations: [
    getNodeAutoInstrumentations({
      '@opentelemetry/instrumentation-http': { enabled: true },
      '@opentelemetry/instrumentation-express': { enabled: true },
      '@opentelemetry/instrumentation-pg': { enabled: true },
      '@opentelemetry/instrumentation-redis': { enabled: true },
    }),
  ],
});

sdk.start();

process.on('SIGTERM', () => {
  sdk.shutdown().then(() => process.exit(0));
});
```

```javascript
// app.js
const express = require('express');
const { trace } = require('@opentelemetry/api');

const app = express();
const tracer = trace.getTracer('checkout-service');

app.post('/api/checkout', async (req, res) => {
  // Create a custom span
  const span = tracer.startSpan('process_checkout');

  try {
    span.setAttribute('user.id', req.user.id);
    span.setAttribute('cart.items', req.body.items.length);

    // Each of these HTTP calls will be auto-traced
    const cart = await validateCart(req.body);
    const payment = await processPayment(cart);
    const order = await createOrder(cart, payment);

    span.addEvent('checkout.completed', {
      'order.id': order.id,
      'total': cart.total,
    });

    res.json({ orderId: order.id });
  } catch (error) {
    span.setStatus({ code: 2, message: error.message }); // ERROR
    span.recordException(error);
    res.status(500).json({ error: error.message });
  } finally {
    span.end();
  }
});

app.listen(8080);
```

### Go with OpenTelemetry

```go
package main

import (
    "context"
    "log"
    "net/http"

    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/attribute"
    "go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc"
    "go.opentelemetry.io/otel/sdk/resource"
    sdktrace "go.opentelemetry.io/otel/sdk/trace"
    semconv "go.opentelemetry.io/otel/semconv/v1.21.0"
    "go.opentelemetry.io/otel/trace"
    "go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp"
)

func initTracer() (*sdktrace.TracerProvider, error) {
    exporter, err := otlptracegrpc.New(context.Background(),
        otlptracegrpc.WithEndpoint("otel-collector:4317"),
        otlptracegrpc.WithInsecure(),
    )
    if err != nil {
        return nil, err
    }

    tp := sdktrace.NewTracerProvider(
        sdktrace.WithBatcher(exporter),
        sdktrace.WithResource(resource.NewWithAttributes(
            semconv.SchemaURL,
            semconv.ServiceNameKey.String("checkout-service"),
            semconv.ServiceVersionKey.String("2.4.1"),
        )),
    )
    otel.SetTracerProvider(tp)
    return tp, nil
}

func checkoutHandler(w http.ResponseWriter, r *http.Request) {
    ctx := r.Context()
    tracer := otel.Tracer("checkout-service")

    ctx, span := tracer.Start(ctx, "process_checkout")
    defer span.End()

    span.SetAttributes(
        attribute.String("user.id", "user-789"),
        attribute.Float64("order.total", 99.99),
    )

    // Process payment (creates a child span)
    processPayment(ctx)
}

func processPayment(ctx context.Context) {
    tracer := otel.Tracer("checkout-service")
    _, span := tracer.Start(ctx, "process_payment")
    defer span.End()

    span.SetAttributes(attribute.String("payment.method", "credit_card"))
    span.AddEvent("payment.processed")
}

func main() {
    tp, _ := initTracer()
    defer tp.Shutdown(context.Background())

    // Wrap handler with OpenTelemetry HTTP instrumentation
    handler := otelhttp.NewHandler(http.HandlerFunc(checkoutHandler), "checkout")
    http.Handle("/api/checkout", handler)

    log.Fatal(http.ListenAndServe(":8080", nil))
}
```

---

## Tracing Best Practices

### 1. Use Semantic Conventions

Follow OpenTelemetry semantic conventions for attribute names:

```
Good:                          Bad:
  http.method                    method
  http.status_code               status
  db.system                      database_type
  rpc.service                    grpc_service
```

### 2. Add Business Context

```python
span.set_attribute("user.id", user_id)
span.set_attribute("order.id", order_id)
span.set_attribute("order.total", total)
span.set_attribute("payment.method", "credit_card")
span.set_attribute("feature.flag.new_checkout", True)
```

### 3. Record Exceptions Properly

```python
try:
    result = process_payment()
except Exception as e:
    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
    span.record_exception(e)
    raise  # Re-raise after recording
```

### 4. Keep Spans Meaningful

```
Good span names:
  "POST /api/checkout"
  "SELECT users"
  "payment.process"
  "kafka.publish orders-topic"

Bad span names:
  "span1"
  "do_stuff"
  "POST /api/users/12345"  ← High cardinality (use attributes for IDs)
```

### 5. Connect Traces to Logs

Include the trace ID in your log entries:

```python
import structlog
from opentelemetry import trace

def add_trace_context(logger, method_name, event_dict):
    span = trace.get_current_span()
    if span.is_recording():
        ctx = span.get_span_context()
        event_dict["trace_id"] = format(ctx.trace_id, '032x')
        event_dict["span_id"] = format(ctx.span_id, '016x')
    return event_dict

structlog.configure(processors=[add_trace_context, ...])
```

### 6. Use Context Propagation for Async

```python
# When using message queues, propagate context in message headers
from opentelemetry.propagate import inject, extract

# Producer: inject context into message headers
headers = {}
inject(headers)
kafka_producer.send("orders", value=order_data, headers=headers)

# Consumer: extract context from message headers
ctx = extract(message.headers)
with tracer.start_as_current_span("process_order", context=ctx):
    process_order(message.value)
```

---

## Key Takeaways

1. **Distributed tracing** shows the full journey of a request across services
2. A **trace** is a tree of **spans**, each representing a unit of work
3. **OpenTelemetry** is the CNCF standard — use it for all new instrumentation
4. **Jaeger** and **Zipkin** are popular trace backends; Jaeger is recommended for new projects
5. **Context propagation** (W3C Trace Context) is critical — traces break without it
6. Use **sampling** to control costs: head-based for simplicity, tail-based for keeping interesting traces
7. Always **connect traces to logs** via trace_id for full correlation
8. Follow **semantic conventions** for consistent attribute naming across services

---

**Previous Lesson:** [03 - Metrics](03-metrics.md)
**Next Lesson:** [05 - Grafana](05-grafana.md)
