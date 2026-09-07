# Lab 03: Matrix Builds

## Overview

In this lab, you will use GitHub Actions' **matrix strategy** to test your application across multiple runtime versions and operating systems simultaneously. Matrix builds are essential for ensuring cross-platform compatibility and supporting multiple language versions.

---

## Objectives

By the end of this lab, you will be able to:

- Define a matrix strategy in a GitHub Actions workflow
- Test across multiple Node.js versions (18, 20, 22)
- Test across multiple operating systems (Ubuntu, macOS, Windows)
- Use matrix variables in steps
- Exclude specific combinations from the matrix
- Include additional one-off combinations
- Handle platform-specific commands
- Use `fail-fast` to control matrix failure behavior

---

## Prerequisites

- Completed **Lab 02** (Node.js project with tests in `github-actions-labs`)
- Understanding of why cross-version/cross-platform testing matters

---

## Step-by-Step Instructions

### Step 1: Understand the Matrix Concept

A matrix strategy creates multiple job instances from a set of variable combinations. For example:

| | ubuntu-latest | macos-latest | windows-latest |
|---|---|---|---|
| **Node 18** | Job 1 | Job 2 | Job 3 |
| **Node 20** | Job 4 | Job 5 | Job 6 |
| **Node 22** | Job 7 | Job 8 | Job 9 |

This gives you **9 parallel jobs** from a single job definition.

### Step 2: Create a Basic Matrix Workflow

Create `.github/workflows/matrix-builds.yml`:

```yaml
name: Matrix Builds

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test-matrix:
    name: Test (Node ${{ matrix.node-version }}, ${{ matrix.os }})
    runs-on: ${{ matrix.os }}

    strategy:
      matrix:
        node-version: [18, 20, 22]
        os: [ubuntu-latest, macos-latest, windows-latest]

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js ${{ matrix.node-version }}
        uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
          cache: "npm"

      - name: Display environment
        run: |
          echo "Node version: $(node --version)"
          echo "npm version: $(npm --version)"
          echo "OS: ${{ matrix.os }}"

      - name: Install dependencies
        run: npm ci

      - name: Run tests
        run: npm test
```

### Step 3: Commit and Observe

```bash
git add .github/workflows/matrix-builds.yml
git commit -m "Add matrix build workflow"
git push origin main
```

Go to the **Actions** tab. You should see **9 jobs** running in parallel (3 Node versions x 3 operating systems).

### Step 4: Add fail-fast Configuration

By default, if any matrix job fails, all other running jobs are cancelled. You can control this behavior:

```yaml
    strategy:
      fail-fast: false
      matrix:
        node-version: [18, 20, 22]
        os: [ubuntu-latest, macos-latest, windows-latest]
```

Setting `fail-fast: false` lets all jobs complete even if one fails. This is useful for understanding the full picture of compatibility.

### Step 5: Exclude Specific Combinations

Sometimes certain combinations are not needed or not supported. Add an `exclude` block:

```yaml
    strategy:
      fail-fast: false
      matrix:
        node-version: [18, 20, 22]
        os: [ubuntu-latest, macos-latest, windows-latest]
        exclude:
          - node-version: 18
            os: macos-latest
          - node-version: 22
            os: windows-latest
```

This reduces the matrix from 9 to 7 jobs by skipping those two combinations.

### Step 6: Include Additional Combinations

Use `include` to add extra variables or one-off combinations:

```yaml
    strategy:
      fail-fast: false
      matrix:
        node-version: [18, 20, 22]
        os: [ubuntu-latest]
        include:
          - node-version: 20
            os: macos-latest
            experimental: false
          - node-version: 22
            os: ubuntu-latest
            experimental: true
```

The `include` entries add the `experimental` variable to specific combinations (or create new ones if they do not already exist).

### Step 7: Use Matrix Variables in Conditional Steps

Update the workflow to use matrix variables in conditions and commands:

```yaml
name: Matrix Builds

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test-matrix:
    name: Test (Node ${{ matrix.node-version }}, ${{ matrix.os }})
    runs-on: ${{ matrix.os }}
    continue-on-error: ${{ matrix.experimental || false }}

    strategy:
      fail-fast: false
      matrix:
        node-version: [18, 20, 22]
        os: [ubuntu-latest, macos-latest, windows-latest]
        include:
          - node-version: 22
            os: ubuntu-latest
            experimental: true

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js ${{ matrix.node-version }}
        uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
          cache: "npm"

      - name: Install dependencies
        run: npm ci

      - name: Run linter
        run: npm run lint

      - name: Run tests
        run: npm test

      - name: Run tests with coverage (Linux only)
        if: runner.os == 'Linux'
        run: npm run test:ci

      - name: Upload coverage (Linux + Node 20 only)
        if: matrix.os == 'ubuntu-latest' && matrix.node-version == 20
        uses: actions/upload-artifact@v4
        with:
          name: coverage-node-${{ matrix.node-version }}
          path: coverage/

      - name: Platform-specific check (Windows)
        if: runner.os == 'Windows'
        run: echo "Running on Windows - PowerShell is the default shell"

      - name: Platform-specific check (Linux/macOS)
        if: runner.os != 'Windows'
        run: echo "Running on ${{ runner.os }} - Bash is the default shell"
```

### Step 8: Add a Summary Job

Add a job that runs after all matrix jobs complete and reports the overall status:

```yaml
  report:
    name: Matrix Results
    runs-on: ubuntu-latest
    needs: test-matrix
    if: always()

    steps:
      - name: Check matrix results
        run: |
          echo "## Matrix Build Results" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          if [ "${{ needs.test-matrix.result }}" == "success" ]; then
            echo "All matrix jobs passed." >> $GITHUB_STEP_SUMMARY
          else
            echo "Some matrix jobs failed. Check individual results above." >> $GITHUB_STEP_SUMMARY
          fi
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "Result: **${{ needs.test-matrix.result }}**" >> $GITHUB_STEP_SUMMARY
```

### Step 9: Full Workflow with Python Matrix (Alternative)

If you prefer Python, here is an equivalent matrix workflow. Create `.github/workflows/matrix-python.yml`:

```yaml
name: Python Matrix Builds

on:
  push:
    branches: [main]

jobs:
  test-python:
    name: Python ${{ matrix.python-version }} on ${{ matrix.os }}
    runs-on: ${{ matrix.os }}

    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.10", "3.11", "3.12"]
        os: [ubuntu-latest, macos-latest, windows-latest]

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Display Python version
        run: python --version

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install flake8 pytest pytest-cov
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
        shell: bash

      - name: Lint with flake8
        run: |
          flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
          flake8 . --count --exit-zero --max-complexity=10 --statistics
        shell: bash

      - name: Run tests with coverage
        run: pytest --cov --cov-report=xml --junitxml=test-results.xml
        shell: bash
```

### Step 10: Commit and Push Final Version

```bash
git add .github/workflows/matrix-builds.yml
git commit -m "Complete matrix build with exclusions and reporting"
git push origin main
```

---

## Expected Outcomes

After completing this lab, you should see:

1. Multiple parallel jobs in the Actions tab, one for each matrix combination.
2. Job names reflecting their matrix variables (e.g., "Test (Node 20, ubuntu-latest)").
3. Excluded combinations not appearing in the job list.
4. Coverage artifacts uploaded only from the designated combination (Linux + Node 20).
5. A summary job that reports the overall matrix result.
6. All jobs completing independently when `fail-fast: false` is set.

---

## Bonus Challenges

1. **Add a max-parallel limit** to control how many matrix jobs run concurrently:
   ```yaml
   strategy:
     max-parallel: 3
     matrix:
       node-version: [18, 20, 22]
       os: [ubuntu-latest, macos-latest, windows-latest]
   ```

2. **Create a dynamic matrix** using a preceding job that outputs the matrix as JSON:
   ```yaml
   setup:
     runs-on: ubuntu-latest
     outputs:
       matrix: ${{ steps.set-matrix.outputs.matrix }}
     steps:
       - id: set-matrix
         run: echo 'matrix={"node-version":[18,20,22]}' >> $GITHUB_OUTPUT
   test:
     needs: setup
     strategy:
       matrix: ${{ fromJSON(needs.setup.outputs.matrix) }}
   ```

3. **Add a compatibility report** that creates a markdown table in the job summary showing pass/fail status for each combination.

4. **Test with nightly/beta versions** by including a combination using `node-version: 'latest'` or `node-version: '23'` with `continue-on-error: true`.

5. **Use matrix values in artifact names** to avoid naming conflicts:
   ```yaml
   - uses: actions/upload-artifact@v4
     with:
       name: results-node${{ matrix.node-version }}-${{ matrix.os }}
       path: test-results/
   ```

---

## Key Concepts Learned

- **Matrix Strategy**: Automatically generates multiple job configurations from variable combinations
- **`fail-fast`**: Controls whether remaining matrix jobs are cancelled when one fails
- **`exclude`**: Removes specific combinations from the generated matrix
- **`include`**: Adds variables to existing combinations or defines entirely new ones
- **`continue-on-error`**: Allows a job to be marked as passing even when steps fail (useful for experimental configurations)
- **`runner.os`**: A context value for platform-specific conditional logic (`Linux`, `macOS`, `Windows`)
- **`max-parallel`**: Limits the number of matrix jobs that run concurrently
