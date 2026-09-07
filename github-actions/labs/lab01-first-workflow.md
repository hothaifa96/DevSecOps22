# Lab 01: Your First GitHub Actions Workflow

## Overview

In this lab, you will create your very first GitHub Actions workflow. You will learn the fundamental structure of a workflow file, how to trigger it on code pushes, and how to run basic commands inside a CI runner.

---

## Objectives

By the end of this lab, you will be able to:

- Understand the structure of a GitHub Actions workflow YAML file
- Create a workflow that triggers on `push` events
- Use the `ubuntu-latest` runner
- Run basic shell commands (`echo`, `ls`, `pwd`)
- Use the `actions/checkout` action to clone your repository
- View workflow run logs in the GitHub Actions UI

---

## Prerequisites

- A GitHub account with access to create repositories
- Basic familiarity with Git (clone, add, commit, push)
- A text editor or IDE (VS Code recommended)
- Git installed on your local machine

---

## Step-by-Step Instructions

### Step 1: Create a New GitHub Repository

1. Go to [github.com/new](https://github.com/new).
2. Name your repository `github-actions-labs`.
3. Select **Public** (or Private if you prefer).
4. Check **Add a README file**.
5. Click **Create repository**.
6. Clone the repository to your local machine:

```bash
git clone https://github.com/<your-username>/github-actions-labs.git
cd github-actions-labs
```

### Step 2: Create the Workflow Directory

GitHub Actions workflows must live in the `.github/workflows/` directory at the root of your repository.

```bash
mkdir -p .github/workflows
```

### Step 3: Create Your First Workflow File

Create a file named `.github/workflows/first-workflow.yml`:

```yaml
name: My First Workflow

on:
  push:
    branches:
      - main

jobs:
  hello-world:
    name: Hello World Job
    runs-on: ubuntu-latest

    steps:
      - name: Print a greeting
        run: echo "Hello, GitHub Actions!"

      - name: Print the current date
        run: date

      - name: Print the runner OS
        run: echo "This job is running on ${{ runner.os }}"

      - name: Print the event that triggered this workflow
        run: echo "This workflow was triggered by a ${{ github.event_name }} event"
```

### Step 4: Understand the Workflow Structure

Take a moment to understand each section:

| Section | Purpose |
|---------|---------|
| `name` | Display name of the workflow |
| `on` | Event trigger (push to main branch) |
| `jobs` | Collection of jobs to run |
| `runs-on` | The type of runner (virtual machine) |
| `steps` | Sequential list of tasks within a job |
| `run` | Shell command to execute |

### Step 5: Commit and Push

```bash
git add .github/workflows/first-workflow.yml
git commit -m "Add first GitHub Actions workflow"
git push origin main
```

### Step 6: View the Workflow Run

1. Go to your repository on GitHub.
2. Click on the **Actions** tab.
3. You should see your workflow **My First Workflow** running or completed.
4. Click on the workflow run to see the details.
5. Click on the **Hello World Job** to expand the step logs.
6. Verify that each step executed and printed the expected output.

### Step 7: Add Checkout and File Listing

Now update your workflow to check out your code and list the repository files. Edit `.github/workflows/first-workflow.yml`:

```yaml
name: My First Workflow

on:
  push:
    branches:
      - main

jobs:
  hello-world:
    name: Hello World Job
    runs-on: ubuntu-latest

    steps:
      - name: Print a greeting
        run: echo "Hello, GitHub Actions!"

      - name: Print the current date
        run: date

      - name: Print the runner OS
        run: echo "This job is running on ${{ runner.os }}"

      - name: Print the event that triggered this workflow
        run: echo "This workflow was triggered by a ${{ github.event_name }} event"

      - name: Checkout repository code
        uses: actions/checkout@v4

      - name: List repository files
        run: |
          echo "--- Repository root contents ---"
          ls -la
          echo ""
          echo "--- Workflow files ---"
          ls -la .github/workflows/
          echo ""
          echo "--- Current working directory ---"
          pwd

      - name: Display README contents
        run: cat README.md

      - name: Show Git information
        run: |
          echo "Branch: ${{ github.ref_name }}"
          echo "Commit SHA: ${{ github.sha }}"
          echo "Repository: ${{ github.repository }}"
          echo "Actor: ${{ github.actor }}"
```

### Step 8: Commit and Verify

```bash
git add .github/workflows/first-workflow.yml
git commit -m "Add checkout and file listing steps"
git push origin main
```

Go back to the **Actions** tab and verify the new steps execute correctly.

### Step 9: Add a Second Job

Add a second job to understand how multiple jobs work. Update your workflow:

```yaml
name: My First Workflow

on:
  push:
    branches:
      - main

jobs:
  hello-world:
    name: Hello World Job
    runs-on: ubuntu-latest
    steps:
      - name: Print a greeting
        run: echo "Hello from Job 1!"

      - name: Checkout repository code
        uses: actions/checkout@v4

      - name: List files
        run: ls -la

  explore-runner:
    name: Explore the Runner
    runs-on: ubuntu-latest
    steps:
      - name: Show system info
        run: |
          echo "=== OS Information ==="
          uname -a
          echo ""
          echo "=== CPU Info ==="
          nproc
          echo ""
          echo "=== Memory Info ==="
          free -h
          echo ""
          echo "=== Disk Space ==="
          df -h
          echo ""
          echo "=== Installed Tools ==="
          node --version
          python3 --version
          docker --version
          git --version
```

Commit, push, and observe that both jobs run **in parallel** by default.

---

## Expected Outcomes

After completing this lab, you should see:

1. A workflow file at `.github/workflows/first-workflow.yml` in your repository.
2. Successful workflow runs visible in the **Actions** tab.
3. Step logs showing:
   - The "Hello, GitHub Actions!" greeting
   - The current date and runner OS
   - A full file listing of your repository after checkout
   - The contents of your README
   - Git context information (branch, SHA, repository, actor)
4. Two jobs running in parallel in the final workflow version.

---

## Bonus Challenges

1. **Add a `workflow_dispatch` trigger** so you can manually run the workflow from the Actions tab. Add `workflow_dispatch:` under the `on:` section and test it.

2. **Add a `pull_request` trigger** that runs on PRs to `main`. Create a branch, push a change, open a PR, and observe the workflow run.

3. **Add a conditional step** using `if:` that only runs when the commit message contains the word "deploy":
   ```yaml
   - name: Deploy notice
     if: contains(github.event.head_commit.message, 'deploy')
     run: echo "This commit is tagged for deployment!"
   ```

4. **Chain jobs with dependencies** using the `needs:` keyword so the second job waits for the first to complete:
   ```yaml
   explore-runner:
     needs: hello-world
     runs-on: ubuntu-latest
   ```

5. **Explore the `github` context** by printing the entire context as JSON:
   ```yaml
   - name: Dump GitHub context
     run: echo '${{ toJSON(github) }}'
   ```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Workflow does not trigger | Ensure the file is in `.github/workflows/` and the branch matches |
| YAML syntax error | Validate your YAML at [yamllint.com](https://www.yamllint.com/) |
| Actions tab not visible | Ensure Actions is enabled in repository Settings > Actions |
| Checkout fails | Make sure you use `actions/checkout@v4` (with the `@v4` tag) |

---

## Key Concepts Learned

- **Workflow**: An automated process defined in a YAML file
- **Event/Trigger**: What causes the workflow to run (`push`, `pull_request`, etc.)
- **Job**: A set of steps that execute on the same runner
- **Step**: An individual task (shell command or action)
- **Action**: A reusable unit of code (`actions/checkout@v4`)
- **Runner**: The virtual machine that executes the job
