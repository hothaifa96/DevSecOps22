# Lab 01 — Freestyle Job

**Objective:** Create and run a Freestyle job that clones a GitHub repo and prints build information.

**Prerequisites:**
- Jenkins is running (any install method)
- Git plugin installed
- A GitHub account with a public repo 

**Estimated Time:** 20 minutes

---

## Part 1 — Create the Freestyle Job

### Step 1 — Open Jenkins and Create a New Job

1. Go to `http://localhost:8080` and log in
2. Click **New Item** in the left sidebar
3. Enter the job name: `lab-01-freestyle`
4. Select **Freestyle project**
5. Click **OK**

---

## Part 2 — Configure General Settings

On the job configuration page:

1. **Description:** `My first freestyle job — prints build info`
2. Check **Discard old builds**
   - Strategy: Log Rotation
   - Max # of builds to keep: `5`

---

## Part 3 — Configure Source Code Management

1. Select **Git**
2. Set the following fields:

```
Repository URL:  ********
Branch Specifier: */main
```

> If using a private repo, click **Add** next to Credentials and add a GitHub username/token credential.

---

## Part 4 — Configure Build Triggers

1. Check **Build periodically**
2. Schedule: `H/5 * * * *`
   - This polls every 5 minutes (for learning purposes only — use webhooks in production)

---

## Part 5 — Configure Build Steps

Click **Add build step → Execute shell** and paste:

```bash
#!/bin/bash
echo "============================================"
echo "  BUILD INFORMATION"
echo "============================================"
echo "Job Name    : $JOB_NAME"
echo "Build Number: $BUILD_NUMBER"
echo "Build URL   : $BUILD_URL"
echo "Workspace   : $WORKSPACE"
echo "Node Name   : $NODE_NAME"
echo "Git Branch  : $GIT_BRANCH"
echo "Git Commit  : $GIT_COMMIT"
echo "============================================"

echo ""
echo "--- Files in workspace ---"
ls -la

echo ""
echo "--- Git log (last 3 commits) ---"
git log --oneline -3
```

---

## Part 6 — Configure Post-Build Actions

1. Click **Add post-build action → Archive the Artifacts**

```
Files to archive: **/*.md
```

2. Click **Add post-build action → Set GitHub commit status**
   - Status Result: `One of the default messages and statuses`

---

## Part 7 — Save and Run

1. Click **Save**
2. Click **Build Now** in the left sidebar
3. Click on **#1** under Build History
4. Click **Console Output**

### Expected Console Output

```
Cloning repository https://github.com/hothaifa96/DevSecOps22.git
 > git init /home/jenkins/workspace/lab-01-freestyle
Fetching upstream changes from https://github.com/hothaifa96/DevSecOps22.git
...
============================================
  BUILD INFORMATION
============================================
Job Name    : lab-01-freestyle
Build Number: 1
Build URL   : http://localhost:8080/job/lab-01-freestyle/1/
Workspace   : /home/jenkins/workspace/lab-01-freestyle
Node Name   : built-in
Git Branch  : origin/main
Git Commit  : a1b2c3d4e5f6...
============================================

--- Files in workspace ---
total 32
drwxr-xr-x ...
...

--- Git log (last 3 commits) ---
a1b2c3d Add tutorial files
f1e2d3c Initial commit
...
Finished: SUCCESS
```

---

## Part 8 — Add a Second Build Step

1. Go to **Configure**
2. Click **Add build step → Execute shell** again (second step)

```bash
#!/bin/bash
echo "--- Running a simple check ---"

# Count markdown files
MD_COUNT=$(find . -name "*.md" | wc -l)
echo "Markdown files found: $MD_COUNT"

# Check if a specific file exists
if [ -f "README.md" ]; then
    echo "README.md EXISTS"
    echo "First 5 lines:"
    head -5 README.md
else
    echo "README.md NOT FOUND"
fi

echo "Build step 2 complete!"
```

3. Click **Save** then **Build Now**

---

## Part 9 — Chain to Another Job

1. Create a second job called `lab-01-freestyle-downstream`
2. In the **Build Triggers** section, check **Build after other projects are built**
   ```
   Projects to watch: lab-01-freestyle
   Trigger only if build is stable: ✅
   ```
3. Add a build step:
   ```bash
   echo "I was triggered by lab-01-freestyle!"
   echo "Upstream build: $UPSTREAM_BUILD_NUMBER"
   ```

Now when `lab-01-freestyle` passes, it automatically triggers `lab-01-freestyle-downstream`.

---

## Exercises

**Exercise 1:** Add a build step that creates a `build-info.txt` file with the build number and date, then archive it.

```bash
echo "Build: $BUILD_NUMBER" > build-info.txt
echo "Date: $(date)" >> build-info.txt
echo "Branch: $GIT_BRANCH" >> build-info.txt
```

**Exercise 2:** Make the build FAIL intentionally by adding `exit 1` at the end of a build step. Observe what happens. Then remove it and rebuild.

**Exercise 3:** Change the branch to `*/non-existent-branch` and see how Jenkins reports an SCM error.

---

## Summary

| What you did | Jenkins concept |
|-------------|----------------|
| Created a Freestyle project | Job type |
| Configured Git SCM | Source Code Management |
| Added shell build steps | Build steps (sequential) |
| Archived artifacts | Post-build actions |
| Chained two jobs | Downstream triggers |
| Read `$BUILD_NUMBER`, `$GIT_COMMIT` | Built-in environment variables |
