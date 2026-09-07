# Lab 02: Build and Test Pipeline

## Overview

In this lab, you will create a complete CI pipeline that installs project dependencies, runs a linter to enforce code quality, executes tests, and uploads test results as artifacts. This is the foundation of any professional CI/CD setup.

---

## Objectives

By the end of this lab, you will be able to:

- Set up a Node.js project with linting and testing
- Create a workflow that installs dependencies using `npm`
- Run ESLint for code quality checks
- Run Jest for unit testing with coverage reporting
- Upload test results and coverage reports as GitHub Actions artifacts
- Understand job failure behavior when tests or linting fail

---

## Prerequisites

- Completed **Lab 01** (repository `github-actions-labs` exists)
- Basic understanding of Node.js and npm
- Familiarity with testing concepts

---

## Step-by-Step Instructions

### Step 1: Initialize the Node.js Project

In your `github-actions-labs` repository, create a Node.js project:

```bash
cd github-actions-labs
npm init -y
```

### Step 2: Install Dependencies

```bash
npm install --save-dev eslint jest
```

### Step 3: Create the Application Code

Create `src/calculator.js`:

```javascript
function add(a, b) {
  if (typeof a !== "number" || typeof b !== "number") {
    throw new Error("Both arguments must be numbers");
  }
  return a + b;
}

function subtract(a, b) {
  if (typeof a !== "number" || typeof b !== "number") {
    throw new Error("Both arguments must be numbers");
  }
  return a - b;
}

function multiply(a, b) {
  if (typeof a !== "number" || typeof b !== "number") {
    throw new Error("Both arguments must be numbers");
  }
  return a * b;
}

function divide(a, b) {
  if (typeof a !== "number" || typeof b !== "number") {
    throw new Error("Both arguments must be numbers");
  }
  if (b === 0) {
    throw new Error("Cannot divide by zero");
  }
  return a / b;
}

module.exports = { add, subtract, multiply, divide };
```

### Step 4: Create Test Files

Create `tests/calculator.test.js`:

```javascript
const { add, subtract, multiply, divide } = require("../src/calculator");

describe("Calculator", () => {
  describe("add", () => {
    test("adds two positive numbers", () => {
      expect(add(2, 3)).toBe(5);
    });

    test("adds negative numbers", () => {
      expect(add(-1, -1)).toBe(-2);
    });

    test("adds zero", () => {
      expect(add(5, 0)).toBe(5);
    });

    test("throws on non-number input", () => {
      expect(() => add("a", 1)).toThrow("Both arguments must be numbers");
    });
  });

  describe("subtract", () => {
    test("subtracts two numbers", () => {
      expect(subtract(5, 3)).toBe(2);
    });

    test("returns negative result", () => {
      expect(subtract(3, 5)).toBe(-2);
    });
  });

  describe("multiply", () => {
    test("multiplies two numbers", () => {
      expect(multiply(3, 4)).toBe(12);
    });

    test("multiplies by zero", () => {
      expect(multiply(5, 0)).toBe(0);
    });
  });

  describe("divide", () => {
    test("divides two numbers", () => {
      expect(divide(10, 2)).toBe(5);
    });

    test("throws on division by zero", () => {
      expect(() => divide(10, 0)).toThrow("Cannot divide by zero");
    });

    test("returns decimal result", () => {
      expect(divide(7, 2)).toBe(3.5);
    });
  });
});
```

### Step 5: Configure ESLint

Create `.eslintrc.json`:

```json
{
  "env": {
    "node": true,
    "jest": true,
    "es2021": true
  },
  "extends": "eslint:recommended",
  "parserOptions": {
    "ecmaVersion": "latest"
  },
  "rules": {
    "no-unused-vars": "warn",
    "no-console": "warn",
    "eqeqeq": "error",
    "no-var": "error",
    "prefer-const": "error"
  }
}
```

### Step 6: Configure Jest

Create `jest.config.js`:

```javascript
module.exports = {
  testEnvironment: "node",
  collectCoverage: true,
  coverageDirectory: "coverage",
  coverageReporters: ["text", "lcov", "json-summary"],
  testResultsProcessor: undefined,
  reporters: [
    "default",
    [
      "jest-junit",
      {
        outputDirectory: "test-results",
        outputName: "junit.xml",
      },
    ],
  ],
};
```

Install the JUnit reporter:

```bash
npm install --save-dev jest-junit
```

### Step 7: Update package.json Scripts

Edit `package.json` to add the following scripts:

```json
{
  "scripts": {
    "test": "jest",
    "test:ci": "jest --ci --reporters=default --reporters=jest-junit",
    "lint": "eslint src/ tests/",
    "lint:fix": "eslint src/ tests/ --fix"
  }
}
```

### Step 8: Verify Locally

Run the linter and tests locally to make sure everything works:

```bash
npm run lint
npm test
```

You should see all tests passing and a coverage report.

### Step 9: Create the CI Workflow

Create `.github/workflows/build-and-test.yml`:

```yaml
name: Build and Test

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    name: Code Linting
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"

      - name: Install dependencies
        run: npm ci

      - name: Run ESLint
        run: npm run lint

  test:
    name: Run Tests
    runs-on: ubuntu-latest
    needs: lint

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"

      - name: Install dependencies
        run: npm ci

      - name: Run tests with coverage
        run: npm run test:ci
        env:
          JEST_JUNIT_OUTPUT_DIR: test-results

      - name: Upload test results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-results
          path: test-results/
          retention-days: 30

      - name: Upload coverage report
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: coverage-report
          path: coverage/
          retention-days: 30

      - name: Display coverage summary
        if: always()
        run: |
          echo "## Test Coverage Summary" >> $GITHUB_STEP_SUMMARY
          echo '```' >> $GITHUB_STEP_SUMMARY
          cat coverage/coverage-summary.json | npx json -a total.lines.pct total.statements.pct total.branches.pct total.functions.pct || true
          echo '```' >> $GITHUB_STEP_SUMMARY

  build:
    name: Build Check
    runs-on: ubuntu-latest
    needs: test

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"

      - name: Install dependencies
        run: npm ci

      - name: Verify project structure
        run: |
          echo "=== Project Structure ==="
          find . -not -path './node_modules/*' -not -path './.git/*' | head -50
          echo ""
          echo "=== Package Info ==="
          node -e "const p = require('./package.json'); console.log(p.name + '@' + p.version)"

      - name: Build status
        run: echo "All checks passed! Project is ready."
```

### Step 10: Add a .gitignore

Create `.gitignore` to avoid committing generated files:

```
node_modules/
coverage/
test-results/
*.log
```

### Step 11: Commit and Push

```bash
git add -A
git commit -m "Add build and test pipeline with linting and artifacts"
git push origin main
```

### Step 12: Verify the Workflow

1. Go to the **Actions** tab in your GitHub repository.
2. Watch the **Build and Test** workflow execute.
3. Observe that the `lint` job runs first, then `test`, then `build` (sequential via `needs`).
4. After completion, click on the workflow run.
5. Scroll down to the **Artifacts** section.
6. Download the `test-results` and `coverage-report` artifacts.
7. Open the JUnit XML file and the coverage HTML report.

### Step 13: Introduce a Linting Error (Observe Failure)

Temporarily add a linting error to see how the pipeline catches issues. Edit `src/calculator.js` and add at the top:

```javascript
var unused = "this should fail linting";
```

Commit and push. Watch the `lint` job fail, which should block the `test` and `build` jobs from running.

Then fix the error, commit, and push again to see the pipeline pass.

---

## Expected Outcomes

After completing this lab, you should see:

1. A three-job pipeline: **lint** -> **test** -> **build** running in sequence.
2. ESLint catching code quality issues and blocking the pipeline on violations.
3. Jest running all tests with a coverage report.
4. Two downloadable artifacts in the workflow run:
   - `test-results` containing a JUnit XML report
   - `coverage-report` containing the full coverage output
5. The pipeline failing when linting errors are present and the downstream jobs being skipped.

---

## Bonus Challenges

1. **Add a coverage threshold** to `jest.config.js` that fails the build if coverage drops below 80%:
   ```javascript
   coverageThreshold: {
     global: {
       branches: 80,
       functions: 80,
       lines: 80,
       statements: 80,
     },
   },
   ```

2. **Add a PR comment with test results** using the `dorny/test-reporter@v1` action:
   ```yaml
   - name: Test Report
     uses: dorny/test-reporter@v1
     if: always()
     with:
       name: Jest Test Results
       path: test-results/junit.xml
       reporter: jest-junit
   ```

3. **Cache node_modules** to speed up builds by comparing the performance difference between cached and non-cached runs.

4. **Add a pre-commit hook** using Husky that runs the linter locally before each commit.

5. **Create a status badge** and add it to your README:
   ```markdown
   ![Build and Test](https://github.com/<user>/<repo>/actions/workflows/build-and-test.yml/badge.svg)
   ```

---

## Key Concepts Learned

- **`npm ci`**: Installs exact dependency versions from `package-lock.json` (preferred in CI over `npm install`)
- **`actions/setup-node@v4`**: Sets up a specific Node.js version with optional dependency caching
- **`actions/upload-artifact@v4`**: Persists files from a workflow run for later download
- **`if: always()`**: Ensures a step runs even if previous steps fail (critical for uploading test results)
- **`needs:`**: Defines job dependencies to enforce execution order
- **Job Summaries**: Using `$GITHUB_STEP_SUMMARY` to add rich content to the workflow run summary page
