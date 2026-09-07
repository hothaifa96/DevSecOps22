# Lesson 3: Testing Strategies in CI/CD

## Overview

| Topic | Details |
|-------|---------|
| **Duration** | 90 minutes |
| **Level** | Foundational to Intermediate |
| **Prerequisites** | Lesson 01, Lesson 02 |
| **Objectives** | Understand the test pyramid, differentiate test types, apply testing strategies in CI/CD pipelines, understand TDD/BDD, manage test quality and coverage |

---

## 1. Why Testing Is the Foundation of CI/CD

CI/CD without testing is just "automated deploying of bugs to production faster."

Your automated test suite is the **safety net** that gives you the confidence to:
- Merge code frequently (CI)
- Deploy at any time (Continuous Delivery)
- Deploy automatically (Continuous Deployment)

> **The Golden Rule:** If you can't trust your tests, you can't trust your pipeline.

### The Cost of Not Testing

```
Without automated tests:
  Developer pushes code → Builds → Deploys → 😱 Users find bugs

With automated tests:
  Developer pushes code → Builds → Tests catch bug → 🛑 Pipeline stops → Developer fixes
```

---

## 2. The Test Pyramid

The **Test Pyramid** (introduced by Mike Cohn) is the most important mental model for testing strategy. It describes the ideal distribution of test types.

### The Pyramid

```
                        ╱╲
                       ╱  ╲
                      ╱ E2E╲           Few tests
                     ╱ Tests╲          Slow (minutes)
                    ╱────────╲         Expensive to maintain
                   ╱Integration╲       Test full user journeys
                  ╱   Tests     ╲      Medium quantity
                 ╱───────────────╲     Moderate speed (seconds-minutes)
                ╱   Unit Tests    ╲    Test component interactions
               ╱___________________╲   Many tests
                                       Fast (milliseconds)
                                       Cheap to write & maintain
                                       Test individual units
```

### Why a Pyramid (Not a Rectangle)?

| Layer | Count | Speed | Cost | Flakiness | Confidence |
|-------|-------|-------|------|-----------|------------|
| **Unit** | Hundreds–thousands | Milliseconds each | Very low | Very low | Low (isolated) |
| **Integration** | Dozens–hundreds | Seconds each | Medium | Low-medium | Medium |
| **E2E** | Tens | Minutes each | High | High | High (realistic) |

**The ideal balance:** Lots of fast, cheap unit tests at the base; fewer, slower, more expensive E2E tests at the top. Each layer catches different types of bugs.

### Anti-Patterns: Inverted Pyramid and Ice Cream Cone

```
Anti-Pattern 1: Inverted Pyramid      Anti-Pattern 2: Ice Cream Cone
(Too many E2E, few unit tests)         (Manual testing dominates)

        _______________                        ___________
       ╱    E2E Tests  ╲                      │  Manual   │
      ╱   (too many!)   ╲                     │  Testing  │
     ╱───────────────────╲                    │ (most)    │
    ╱ Integration (some)  ╲                   │───────────│
   ╱───────────────────────╲                  │    E2E    │
  ╱   Unit Tests (too few!) ╲                 │───────────│
 ╱___________________________╲                │   Unit    │
                                               └───────────┘
Result: Slow, flaky, expensive             Result: Can't do CI/CD at all
```

---

## 3. Unit Tests

### What They Are

Unit tests verify the smallest testable parts of an application — individual functions, methods, or classes — in isolation.

### Characteristics

| Property | Detail |
|----------|--------|
| **Scope** | Single function, method, or class |
| **Dependencies** | Mocked or stubbed (no real DB, API, filesystem) |
| **Speed** | Milliseconds per test |
| **Who writes them** | The developer who wrote the code |
| **When they run** | On every commit, before merge |

### Example: Unit Test (Python)

```python
# Function under test
def calculate_discount(price, discount_percent):
    if discount_percent < 0 or discount_percent > 100:
        raise ValueError("Discount must be between 0 and 100")
    return price * (1 - discount_percent / 100)

# Unit tests
def test_calculate_discount_normal():
    assert calculate_discount(100, 20) == 80.0

def test_calculate_discount_zero():
    assert calculate_discount(100, 0) == 100.0

def test_calculate_discount_full():
    assert calculate_discount(100, 100) == 0.0

def test_calculate_discount_invalid():
    with pytest.raises(ValueError):
        calculate_discount(100, 150)
```

### Example: Unit Test (JavaScript)

```javascript
// Function under test
function calculateDiscount(price, discountPercent) {
  if (discountPercent < 0 || discountPercent > 100) {
    throw new Error("Discount must be between 0 and 100");
  }
  return price * (1 - discountPercent / 100);
}

// Unit tests (Jest)
describe("calculateDiscount", () => {
  test("applies 20% discount correctly", () => {
    expect(calculateDiscount(100, 20)).toBe(80);
  });

  test("handles zero discount", () => {
    expect(calculateDiscount(100, 0)).toBe(100);
  });

  test("throws on invalid discount", () => {
    expect(() => calculateDiscount(100, 150)).toThrow();
  });
});
```

### What Makes a Good Unit Test

Follow the **F.I.R.S.T.** principles:

| Principle | Meaning |
|-----------|---------|
| **Fast** | Runs in milliseconds (no I/O, no network, no DB) |
| **Isolated** | Does not depend on other tests or shared state |
| **Repeatable** | Produces the same result every time, in any environment |
| **Self-validating** | Passes or fails — no manual inspection needed |
| **Timely** | Written at the same time as (or before) the production code |

### Mocking and Stubbing

Unit tests isolate the code under test by replacing dependencies:

```
Real System:                      Unit Test (with mock):
┌──────────┐    ┌─────────┐      ┌──────────┐    ┌──────────────┐
│ OrderSvc │───▶│ Database │      │ OrderSvc │───▶│ Mock Database│
└──────────┘    └─────────┘      └──────────┘    │ (returns fake│
                                                   │  data)       │
                                                   └──────────────┘
```

- **Mock** — An object that records how it was called and can assert on interactions.
- **Stub** — An object that returns predetermined data (but doesn't assert on calls).
- **Fake** — A lightweight implementation (e.g., in-memory database instead of PostgreSQL).

---

## 4. Integration Tests

### What They Are

Integration tests verify that **multiple components work together correctly** — that the "seams" between modules, services, or systems are functioning.

### Characteristics

| Property | Detail |
|----------|--------|
| **Scope** | Multiple components interacting (API + DB, Service A + Service B) |
| **Dependencies** | Real (or realistic) — actual database, actual API calls |
| **Speed** | Seconds to minutes per test |
| **Infrastructure** | May require Docker containers, test databases, message queues |
| **When they run** | On every commit or PR, after unit tests |

### Types of Integration Tests

```
1. Component Integration:      Service ←→ Database
2. API Contract Testing:       Service A ←→ Service B (verify API contract)
3. Message Queue Testing:      Producer ←→ Queue ←→ Consumer
4. External Service Testing:   Application ←→ Third-Party API (with sandbox)
```

### Example: API Integration Test

```python
# Integration test — tests the real API endpoint with a real test database
import requests

BASE_URL = "http://localhost:8080"

def test_create_and_get_user():
    # Create a user
    response = requests.post(f"{BASE_URL}/api/users", json={
        "name": "Alice",
        "email": "alice@example.com"
    })
    assert response.status_code == 201
    user_id = response.json()["id"]
    
    # Retrieve the user
    response = requests.get(f"{BASE_URL}/api/users/{user_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Alice"
    assert response.json()["email"] == "alice@example.com"
    
    # Clean up
    requests.delete(f"{BASE_URL}/api/users/{user_id}")
```

### Contract Testing

When services communicate via APIs, **contract testing** ensures both sides agree on the API format:

```
Consumer (Frontend)                     Provider (Backend API)
defines expected                        verifies it meets
contract:                               the contract:
┌─────────────────────┐                ┌─────────────────────┐
│ "When I call         │                │ "My endpoint         │
│  GET /api/users/1,   │◄──Contract───▶│  GET /api/users/1    │
│  I expect:           │    (Pact,     │  returns:            │
│  { name: string,     │    OpenAPI)   │  { name: string,     │
│    email: string }"  │                │    email: string }"  │
└─────────────────────┘                └─────────────────────┘
```

Tools: **Pact**, **Spring Cloud Contract**, **OpenAPI/Swagger validators**

---

## 5. End-to-End (E2E) Tests

### What They Are

E2E tests simulate **real user behavior** from start to finish — clicking buttons, filling forms, navigating pages — against a fully deployed application.

### Characteristics

| Property | Detail |
|----------|--------|
| **Scope** | Entire application stack (frontend + backend + database + external services) |
| **Dependencies** | Full environment (staging or dedicated test environment) |
| **Speed** | Minutes per test |
| **Flakiness** | High — many moving parts can cause intermittent failures |
| **When they run** | After staging deployment, before production promotion |

### Example: E2E Test (Playwright)

```javascript
// E2E test — simulates a user logging in and viewing their dashboard
const { test, expect } = require("@playwright/test");

test("user can log in and see dashboard", async ({ page }) => {
  // Navigate to the login page
  await page.goto("https://staging.myapp.com/login");
  
  // Fill in credentials
  await page.fill('[data-testid="email"]', "alice@example.com");
  await page.fill('[data-testid="password"]', "securepassword");
  await page.click('[data-testid="login-button"]');
  
  // Verify redirect to dashboard
  await expect(page).toHaveURL(/.*dashboard/);
  await expect(page.locator("h1")).toContainText("Welcome, Alice");
  
  // Verify key dashboard elements
  await expect(page.locator('[data-testid="recent-orders"]')).toBeVisible();
  await expect(page.locator('[data-testid="account-balance"]')).toBeVisible();
});
```

### Managing E2E Test Flakiness

E2E tests are notoriously flaky. Strategies to reduce flakiness:

| Strategy | How It Helps |
|----------|-------------|
| **Use `data-testid` attributes** | Don't rely on CSS classes or text that may change |
| **Wait for elements properly** | Use explicit waits, not `sleep()` |
| **Isolate test data** | Each test creates its own data, doesn't depend on shared state |
| **Retry failed tests** | Automatically retry once before marking as failed |
| **Run in consistent environments** | Use Docker or dedicated test infrastructure |
| **Limit E2E test count** | Only test critical user journeys (login, checkout, signup) |
| **Quarantine flaky tests** | Mark consistently flaky tests and fix them separately |

---

## 6. Smoke Tests

### What They Are

Smoke tests are a **small, fast subset of tests** that verify the most critical functionality works after a deployment. The name comes from electronics — if you plug in a device and see smoke, you know something is fundamentally wrong.

### When to Use

- **After every deployment** (to any environment)
- **Before running the full test suite** (fail fast)
- **As a health check** for production

### Example: Smoke Test Suite

```
Smoke Tests for E-Commerce App (30 seconds total):
  ✅ Homepage loads (HTTP 200)
  ✅ Login page is accessible
  ✅ API health endpoint returns OK
  ✅ Database connection is alive
  ✅ User can search for a product
  ✅ Cart page loads
```

```bash
#!/bin/bash
# Simple smoke test script
BASE_URL="${1:-http://localhost:8080}"

echo "Running smoke tests against $BASE_URL"

# Test 1: Homepage loads
curl -sf "$BASE_URL/" > /dev/null && echo "✅ Homepage OK" || echo "❌ Homepage FAILED"

# Test 2: Health endpoint
curl -sf "$BASE_URL/healthz" > /dev/null && echo "✅ Health OK" || echo "❌ Health FAILED"

# Test 3: API responds
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/status")
[ "$STATUS" -eq 200 ] && echo "✅ API OK" || echo "❌ API FAILED (HTTP $STATUS)"

# Test 4: Login page
curl -sf "$BASE_URL/login" > /dev/null && echo "✅ Login page OK" || echo "❌ Login page FAILED"
```

---

## 7. Load and Performance Tests

### What They Are

Performance tests verify that the application meets **speed, scalability, and stability requirements** under expected (and peak) load.

### Types of Performance Tests

| Test Type | What It Does | Example Scenario |
|-----------|-------------|-----------------|
| **Load Test** | Simulates expected concurrent users | 1,000 users browsing simultaneously |
| **Stress Test** | Pushes beyond normal capacity to find breaking point | Ramp from 1,000 to 10,000 users |
| **Spike Test** | Simulates sudden traffic surge | 0 → 5,000 users in 10 seconds |
| **Soak Test** | Runs at normal load for extended period | 500 users for 24 hours (find memory leaks) |
| **Scalability Test** | Verifies the system scales with added resources | Double the servers, does throughput double? |

### When to Run Performance Tests

```
Pipeline Integration:
                                                 ┌── Nightly: Full load test suite
Build → Unit Tests → Integration Tests → Deploy  ┤
        to Staging                                └── Per-release: Baseline comparison
                                                       (compare against last release)
```

Performance tests are typically too slow for every commit. Run them:
- **Nightly** (scheduled pipeline)
- **Per-release** (before production deployment)
- **On-demand** (when investigating performance concerns)

### Example: Load Test Script (k6)

```javascript
// k6 load test
import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  stages: [
    { duration: "1m", target: 100 },   // Ramp up to 100 users
    { duration: "3m", target: 100 },   // Stay at 100 users
    { duration: "1m", target: 0 },     // Ramp down
  ],
  thresholds: {
    http_req_duration: ["p(95)<500"],   // 95% of requests under 500ms
    http_req_failed: ["rate<0.01"],     // Error rate under 1%
  },
};

export default function () {
  const res = http.get("https://staging.myapp.com/api/products");
  check(res, {
    "status is 200": (r) => r.status === 200,
    "response time < 500ms": (r) => r.timings.duration < 500,
  });
  sleep(1);
}
```

### Performance Budgets

Define thresholds that fail the pipeline if exceeded:

| Metric | Threshold | Action if Exceeded |
|--------|-----------|-------------------|
| p95 response time | < 500ms | Block deployment |
| p99 response time | < 1000ms | Block deployment |
| Error rate | < 1% | Block deployment |
| Throughput | > 500 req/s | Warn |
| Memory usage | < 80% of limit | Warn |

---

## 8. Chaos Testing

### What It Is

Chaos testing (or **chaos engineering**) deliberately introduces failures into a system to verify that it handles them gracefully. The philosophy: if failures are going to happen in production (and they will), it's better to practice dealing with them.

### Principles of Chaos Engineering

1. **Start with a hypothesis** — "If a database replica fails, the system should continue serving reads from the primary."
2. **Introduce controlled failure** — Kill the replica.
3. **Observe the impact** — Did the system recover? Were users affected?
4. **Learn and improve** — Fix any weaknesses discovered.

### Common Chaos Experiments

| Experiment | What It Tests |
|-----------|--------------|
| Kill a container/pod | Auto-restart and self-healing |
| Introduce network latency | Timeout handling, circuit breakers |
| Fill a disk | Graceful handling of disk pressure |
| Exhaust memory | OOM handling, memory limits |
| Kill a database connection | Connection retry logic, failover |
| Simulate DNS failure | Service discovery resilience |
| Clock skew | Time-dependent logic correctness |

### Chaos Testing in CI/CD

```
Pipeline Stage: Chaos Testing (runs in staging)
  ├── Experiment 1: Kill 1 of 3 API pods
  │   └── Verify: requests still succeed, auto-scaling triggers
  ├── Experiment 2: Introduce 500ms network latency
  │   └── Verify: circuit breaker opens, timeout errors are handled
  └── Experiment 3: Database failover
      └── Verify: application reconnects to new primary
```

**Tools:** Chaos Monkey (Netflix), Litmus Chaos, Gremlin, Chaos Mesh

---

## 9. Test Coverage

### What It Is

**Test coverage** measures the percentage of your code that is exercised by automated tests. It's a useful metric but has important limitations.

### Types of Coverage

| Coverage Type | What It Measures | Example |
|---|---|---|
| **Line coverage** | % of lines executed by tests | 85% of lines are run |
| **Branch coverage** | % of if/else branches taken | 70% of branches are tested |
| **Function coverage** | % of functions called by tests | 90% of functions are called |
| **Statement coverage** | % of statements executed | 85% of statements are run |

### Coverage Targets

| Coverage Level | Interpretation |
|---|---|
| **< 50%** | Dangerously low — major gaps in testing |
| **50–70%** | Acceptable for many projects — focus on critical paths |
| **70–85%** | Good — most organizations should aim here |
| **85–95%** | Very good — diminishing returns beyond this |
| **100%** | Often impractical; may lead to low-value tests |

### Coverage in CI/CD Pipelines

```
Pipeline Configuration:
  - Fail the build if coverage drops below 80%
  - Warn if new code has less than 90% coverage
  - Generate coverage report and publish as artifact
  - Track coverage trend over time (prevent gradual decline)
```

### The Coverage Trap

> **Warning:** High coverage does not mean high quality. You can have 100% line coverage and still miss critical bugs.

```python
# 100% line coverage but terrible test:
def divide(a, b):
    return a / b

def test_divide():
    assert divide(10, 2) == 5  # ✅ Covers the line
    # But never tests: divide(10, 0) → ZeroDivisionError!
```

**Coverage tells you what code is NOT tested (useful). It doesn't tell you if the tests are good (limited).**

### Better Metrics Than Coverage Alone

| Metric | What It Tells You |
|--------|------------------|
| **Mutation testing** | Can your tests detect artificially introduced bugs? |
| **Bug escape rate** | How many bugs reach production despite tests? |
| **Test failure signal** | Do failing tests actually indicate real bugs? |
| **Mean time to detect** | How quickly do tests catch newly introduced bugs? |

---

## 10. Test-Driven Development (TDD)

### What It Is

TDD is a development practice where you **write tests before writing production code**. It follows a strict cycle:

### The Red-Green-Refactor Cycle

```
        ┌───────────────────────────────────────────┐
        │                                           │
        ▼                                           │
   ┌─────────┐     ┌─────────┐     ┌───────────┐  │
   │  RED     │────▶│  GREEN  │────▶│ REFACTOR  │──┘
   │          │     │         │     │           │
   │ Write a  │     │ Write   │     │ Clean up  │
   │ failing  │     │ minimal │     │ the code  │
   │ test     │     │ code to │     │ (tests    │
   │          │     │ pass    │     │ still     │
   │          │     │         │     │ pass)     │
   └─────────┘     └─────────┘     └───────────┘
```

1. **RED** — Write a test for the next piece of functionality. Run it — it should **fail** (because the code doesn't exist yet).
2. **GREEN** — Write the **minimum** code needed to make the test pass. Don't over-engineer.
3. **REFACTOR** — Improve the code's design while keeping all tests green.

### TDD Example

**Requirement:** Build a function that validates email addresses.

```python
# Step 1 — RED: Write a failing test
def test_valid_email():
    assert is_valid_email("user@example.com") == True
# ❌ NameError: is_valid_email is not defined

# Step 2 — GREEN: Write minimal code to pass
def is_valid_email(email):
    return "@" in email and "." in email

# ✅ Test passes

# Step 3 — RED: Write another failing test
def test_invalid_email_no_at():
    assert is_valid_email("userexample.com") == False

def test_invalid_email_no_domain():
    assert is_valid_email("user@") == False
# ❌ "user@" passes because "." check is too loose

# Step 4 — GREEN: Improve the implementation
import re
def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

# ✅ All tests pass

# Step 5 — REFACTOR: Clean up, add docstring, extract constants
```

### Benefits of TDD

- **Forces design thinking** — You think about the interface before the implementation.
- **Built-in test coverage** — Every piece of code has a test by definition.
- **Confidence to refactor** — You can restructure code knowing tests will catch regressions.
- **Living documentation** — Tests describe what the code should do.

---

## 11. Behavior-Driven Development (BDD)

### What It Is

BDD extends TDD by writing tests in **human-readable language** that describes business behavior. It bridges the gap between technical and non-technical stakeholders.

### Gherkin Syntax

BDD tests are written in **Gherkin** — a structured, natural-language format:

```gherkin
Feature: User Login
  As a registered user
  I want to log in to my account
  So that I can access my dashboard

  Scenario: Successful login
    Given I am on the login page
    When I enter "alice@example.com" as my email
    And I enter "securepassword" as my password
    And I click the "Log In" button
    Then I should be redirected to the dashboard
    And I should see "Welcome, Alice"

  Scenario: Failed login with wrong password
    Given I am on the login page
    When I enter "alice@example.com" as my email
    And I enter "wrongpassword" as my password
    And I click the "Log In" button
    Then I should see "Invalid email or password"
    And I should remain on the login page
```

### BDD Tools

| Language | Tool |
|----------|------|
| Python | Behave, pytest-bdd |
| JavaScript | Cucumber.js |
| Java | Cucumber-JVM |
| Ruby | Cucumber |
| .NET | SpecFlow |

### TDD vs. BDD

| Aspect | TDD | BDD |
|--------|-----|-----|
| **Audience** | Developers | Developers + Business + QA |
| **Language** | Code (programming language) | Natural language (Gherkin) |
| **Focus** | Technical correctness | Business behavior |
| **Granularity** | Unit/function level | Feature/scenario level |
| **Collaboration** | Developer-centric | Cross-team collaboration |

---

## 12. Testing Strategy for CI/CD — Putting It All Together

### Recommended Pipeline Test Configuration

```
On every commit (< 10 minutes):
  ├── Linting / static analysis         (seconds)
  ├── Unit tests                        (1-3 minutes)
  ├── Component integration tests       (2-5 minutes)
  └── Security: dependency scan         (1 minute)

On PR merge to main (< 20 minutes):
  ├── Everything above, plus:
  ├── Full integration test suite       (5-10 minutes)
  ├── Contract tests                    (2-3 minutes)
  ├── Container image build + scan      (3-5 minutes)
  └── Deploy to staging + smoke tests   (3-5 minutes)

Nightly (< 2 hours):
  ├── Full E2E test suite               (30-60 minutes)
  ├── Performance / load tests          (30-60 minutes)
  ├── Full security scan (DAST)         (30-60 minutes)
  └── Soak test (extended)              (hours, separate)

Per-release:
  ├── Full regression suite
  ├── Chaos testing
  ├── Manual exploratory testing (human QA)
  └── Accessibility testing
```

### Test Data Management

| Approach | Pros | Cons |
|----------|------|------|
| **Seed data scripts** | Repeatable, version-controlled | Can get out of sync with schema |
| **Factory patterns** | Tests create exactly what they need | Slower than pre-seeded data |
| **Database snapshots** | Realistic data | Large, hard to maintain |
| **Anonymized production data** | Most realistic | Privacy concerns, requires scrubbing |
| **In-memory databases** | Fast, no cleanup needed | May not match production DB behavior |

### Handling Flaky Tests

```
Flaky Test Decision Tree:

  Is the test flaky?
       │
       ├── YES
       │    │
       │    ├── Is it a timing issue? → Add proper waits/retries
       │    ├── Is it a data issue?   → Isolate test data
       │    ├── Is it an environment issue? → Stabilize test environment
       │    ├── Is it inherently non-deterministic? → Quarantine & fix
       │    └── Has it been flaky for > 2 weeks? → Delete and rewrite
       │
       └── NO → Keep it running ✅
```

---

## 13. Review Questions

1. **Draw the test pyramid and explain why there should be more unit tests than E2E tests.**
2. **What is the difference between a mock, a stub, and a fake?** Give an example of when to use each.
3. **Your E2E test suite takes 45 minutes and has a 15% flaky failure rate.** What three actions would you take?
4. **Explain the Red-Green-Refactor cycle of TDD.** Why is the "red" step important?
5. **A developer says: "We have 95% code coverage, so we don't need to worry about bugs."** What would you tell them?
6. **When should chaos testing run in a CI/CD pipeline?** Why not on every commit?
7. **Design a testing strategy (which test types and when) for a REST API that processes financial transactions.**

---

## 14. Further Reading

- **Book:** *Test-Driven Development by Example* by Kent Beck
- **Book:** *Growing Object-Oriented Software, Guided by Tests* by Steve Freeman & Nat Pryce
- **Article:** [The Practical Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html) by Ham Vocke
- **Article:** [Testing Strategies in a Microservice Architecture](https://martinfowler.com/articles/microservice-testing/) by Toby Clemson
- **Tool:** [Pact — Contract Testing](https://pact.io/)
- **Tool:** [k6 — Load Testing](https://k6.io/)

---

*Previous: [02 - CI/CD Pipeline Stages](02-cicd-pipeline-stages.md) | Next: [04 - Deployment Strategies](04-deployment-strategies.md)*
