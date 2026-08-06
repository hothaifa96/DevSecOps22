# Lab 04 — Pipeline: Checkout Code from GitHub

**Objective:** Create a pipeline that checks out the course repository from GitHub, inspects files, prints git metadata, and runs tasks on the cloned code.

**Prerequisites:**
- Jenkins running
- Git plugin and Pipeline plugin installed
- Internet access from the Jenkins agent

**Estimated Time:** 30 minutes

---

## Part 1 — Pipeline Job with Inline Script Checkout

### Step 1 — Create the Pipeline Job

1. Click **New Item**
2. Name: `lab-04-checkout-github`
3. Select **Pipeline**
4. Click **OK**

### Step 2 — Paste This Pipeline

```groovy
pipeline {
    agent any

    environment {
        REPO_URL    = 'https://github.com/hothaifa96/DevSecOps22.git'
        REPO_BRANCH = 'main'
    }

    stages {
        stage('Checkout') {
            steps {
                echo "Cloning repository: ${env.REPO_URL}"
                git branch: "${env.REPO_BRANCH}",
                    url:    "${env.REPO_URL}"
                echo 'Checkout complete!'
            }
        }

        stage('Inspect Workspace') {
            steps {
                echo '--- Workspace root ---'
                sh 'ls -la'

                echo '--- Top-level directories ---'
                sh 'find . -maxdepth 1 -type d | sort'
            }
        }

        stage('Git Metadata') {
            steps {
                echo "Branch        : ${env.GIT_BRANCH}"
                echo "Commit SHA    : ${env.GIT_COMMIT}"
                echo "Previous SHA  : ${env.GIT_PREVIOUS_COMMIT}"
                echo "Repo URL      : ${env.GIT_URL}"

                sh 'git log --oneline -5'
                sh 'git status'
            }
        }

        stage('Count Files') {
            steps {
                script {
                    def total = sh(script: 'find . -type f | wc -l', returnStdout: true).trim()
                    def mdFiles = sh(script: 'find . -name "*.md" | wc -l', returnStdout: true).trim()
                    def yamls   = sh(script: 'find . -name "*.yml" -o -name "*.yaml" | wc -l', returnStdout: true).trim()

                    echo "Total files      : ${total}"
                    echo "Markdown files   : ${mdFiles}"
                    echo "YAML files       : ${yamls}"
                }
            }
        }
    }

    post {
        always {
            echo "Build #${env.BUILD_NUMBER} finished."
        }
        success {
            echo "Repository ${env.REPO_URL} cloned and inspected successfully!"
        }
        cleanup {
            cleanWs()
        }
    }
}
```

### Step 3 — Save and Run

Click **Save → Build Now → Console Output**

You should see the repo cloned and the metadata printed.

---

## Part 2 — Checkout Using `checkout scm` (from Jenkinsfile in Repo)

This is the **recommended production pattern** — the `Jenkinsfile` lives in the repo, and Jenkins uses the pipeline job's SCM configuration.

### Step 1 — Create a Pipeline Job

1. Click **New Item** → `lab-04-checkout-scm` → **Pipeline** → **OK**

### Step 2 — Configure SCM in the Job

Scroll to **Pipeline** section:
- Definition: **Pipeline script from SCM**
- SCM: **Git**
- Repository URL: `https://github.com/hothaifa96/DevSecOps22.git`
- Branch: `*/main`
- Script Path: `jenkins/classcode/Jenkinsfile`  ← or create one

### Step 3 — Create the Jenkinsfile

Create or use the file at `jenkins/classcode/Jenkinsfile` in the repo with this content:

```groovy
pipeline {
    agent any

    options {
        timestamps()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    stages {
        stage('Checkout') {
            steps {
                // checkout scm uses the SCM configuration from the job definition
                checkout scm
                echo "Checked out commit: ${env.GIT_COMMIT}"
                echo "Branch: ${env.GIT_BRANCH}"
            }
        }

        stage('Show Repo Structure') {
            steps {
                sh '''
                    echo "=== Repository Structure ==="
                    find . -maxdepth 2 -type d \
                        -not -path "./.git*" \
                        | sort \
                        | sed 's/[^/]*\//  /g'
                '''
            }
        }

        stage('List Jenkins Materials') {
            steps {
                sh '''
                    echo "=== Jenkins Tutorial Files ==="
                    ls -lh jenkins/materials/
                '''
            }
        }

        stage('Print Last Commit') {
            steps {
                sh '''
                    echo "=== Last 3 Commits ==="
                    git log --pretty=format:"%h | %an | %ar | %s" -3
                '''
            }
        }

        stage('Check for Changes') {
            steps {
                script {
                    def changedFiles = sh(
                        script: 'git diff --name-only HEAD~1 HEAD 2>/dev/null || echo "First commit"',
                        returnStdout: true
                    ).trim()

                    echo "Files changed in last commit:\n${changedFiles}"

                    if (changedFiles.contains('jenkins/')) {
                        echo 'Jenkins files were modified in this commit.'
                    } else {
                        echo 'No Jenkins files modified in this commit.'
                    }
                }
            }
        }
    }

    post {
        success {
            echo "Pipeline completed successfully for commit: ${env.GIT_COMMIT?.take(8)}"
        }
        cleanup {
            cleanWs()
        }
    }
}
```

---

## Part 3 — Checkout with Credentials (Private Repo)

For private repositories, store credentials in Jenkins first:

### Step 1 — Add GitHub Token Credential

1. Go to **Manage Jenkins → Credentials → System → Global**
2. Click **Add Credentials**
3. Kind: **Username with password**
4. Username: your GitHub username
5. Password: your GitHub Personal Access Token (PAT)
   - Generate at: GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens
   - Required scopes: `Contents: Read`
6. ID: `github-pat`

### Step 2 — Pipeline Using Stored Credentials

```groovy
pipeline {
    agent any

    stages {
        stage('Checkout Private Repo') {
            steps {
                git branch: 'main',
                    credentialsId: 'github-pat',
                    url: 'https://github.com/YOUR_ORG/YOUR_PRIVATE_REPO.git'

                echo "Cloned private repo successfully!"
                sh 'ls -la'
            }
        }
    }
}
```

### Step 3 — Or Using `checkout` Step for More Control

```groovy
stage('Checkout') {
    steps {
        checkout([
            $class: 'GitSCM',
            branches: [[name: '*/main']],
            extensions: [
                [$class: 'CloneOption', depth: 1, shallow: true],       // Shallow clone
                [$class: 'CleanBeforeCheckout'],                          // Clean workspace
                [$class: 'SubmoduleOption', recursiveSubmodules: true]   // Submodules
            ],
            userRemoteConfigs: [[
                url:           'https://github.com/hothaifa96/DevSecOps22.git',
                credentialsId: 'github-pat'
            ]]
        ])
        echo "Cloned commit: ${env.GIT_COMMIT}"
    }
}
```

---

## Part 4 — Checkout Multiple Repositories

```groovy
pipeline {
    agent any

    stages {
        stage('Checkout App Repo') {
            steps {
                dir('app') {
                    git branch: 'main',
                        url: 'https://github.com/hothaifa96/DevSecOps22.git'
                }
                echo 'App repo cloned into ./app/'
            }
        }

        stage('Checkout Config Repo') {
            steps {
                dir('config') {
                    git branch: 'main',
                        url: 'https://github.com/hothaifa96/DevSecOps22.git'
                }
                echo 'Config repo cloned into ./config/'
            }
        }

        stage('Use Both') {
            steps {
                sh '''
                    echo "=== App repo ==="
                    ls app/

                    echo "=== Config repo ==="
                    ls config/
                '''
            }
        }
    }

    post {
        cleanup { cleanWs() }
    }
}
```

---

## Part 5 — Full Pipeline: Checkout, Inspect, and Report

Combine everything into one complete pipeline:

```groovy
pipeline {
    agent any

    options {
        timestamps()
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 15, unit: 'MINUTES')
    }

    environment {
        REPO_URL = 'https://github.com/hothaifa96/DevSecOps22.git'
        BRANCH   = 'main'
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: "${env.BRANCH}", url: "${env.REPO_URL}"
                script {
                    env.SHORT_SHA = env.GIT_COMMIT.take(8)
                    currentBuild.displayName = "#${env.BUILD_NUMBER} | ${env.SHORT_SHA}"
                    currentBuild.description = "Branch: ${env.BRANCH}"
                }
            }
        }

        stage('Repository Info') {
            parallel {
                stage('Git Log') {
                    steps {
                        sh 'git log --oneline -10'
                    }
                }

                stage('File Stats') {
                    steps {
                        script {
                            def total     = sh(script: 'git ls-files | wc -l', returnStdout: true).trim()
                            def mdCount   = sh(script: 'git ls-files "*.md" | wc -l', returnStdout: true).trim()
                            def yamlCount = sh(script: 'git ls-files "*.yml" "*.yaml" | wc -l', returnStdout: true).trim()
                            def shCount   = sh(script: 'git ls-files "*.sh" | wc -l', returnStdout: true).trim()

                            echo """
╔══════════════════════════════════╗
║       REPOSITORY FILE STATS      ║
╠══════════════════════════════════╣
║  Total tracked files : ${total.padRight(8)}  ║
║  Markdown files      : ${mdCount.padRight(8)}  ║
║  YAML files          : ${yamlCount.padRight(8)}  ║
║  Shell scripts       : ${shCount.padRight(8)}  ║
╚══════════════════════════════════╝
                            """.stripIndent()
                        }
                    }
                }

                stage('Contributors') {
                    steps {
                        sh 'git shortlog -sn --no-merges | head -10'
                    }
                }
            }
        }

        stage('List Jenkins Labs') {
            steps {
                sh '''
                    echo "=== Available Jenkins Labs ==="
                    if [ -d "jenkins/materials" ]; then
                        ls -1 jenkins/materials/*.md | xargs -I{} basename {}
                    else
                        echo "jenkins/materials not found"
                    fi
                '''
            }
        }

        stage('Generate Report') {
            steps {
                script {
                    def report = """
# Build Report

- **Repo:** ${env.REPO_URL}
- **Branch:** ${env.BRANCH}
- **Commit:** ${env.SHORT_SHA}
- **Build:** #${env.BUILD_NUMBER}
- **Date:** ${new Date().toString()}
                    """.stripIndent()

                    writeFile file: 'build-report.md', text: report
                    sh 'cat build-report.md'
                    archiveArtifacts artifacts: 'build-report.md', fingerprint: true
                }
            }
        }
    }

    post {
        success {
            echo "==> Pipeline completed! Commit ${env.SHORT_SHA} from branch ${env.BRANCH}"
        }
        failure {
            echo "==> Pipeline FAILED on commit ${env.SHORT_SHA}"
        }
        cleanup {
            cleanWs()
        }
    }
}
```

---

## Exercises

**Exercise 1:** Modify the pipeline to checkout only a **specific tag** instead of a branch:

```groovy
git branch: 'refs/tags/v1.0.0',
    url: 'https://github.com/hothaifa96/DevSecOps22.git'
```

**Exercise 2:** Add a `when` stage that only runs if a specific file was changed in the last commit:

```groovy
stage('Rebuild Docs') {
    when {
        expression {
            sh(script: 'git diff --name-only HEAD~1 HEAD | grep -q "docs/"', returnStatus: true) == 0
        }
    }
    steps {
        echo 'Docs directory changed — rebuilding documentation...'
    }
}
```

**Exercise 3:** Create a **Multibranch Pipeline** job:

1. Click **New Item** → `lab-04-multibranch` → **Multibranch Pipeline**
2. Set **Branch Sources → Git → Repository URL** to your repo
3. Click **Save**

Jenkins will automatically scan the repository and create one pipeline per branch that contains a `Jenkinsfile`.

---

## Summary

| Checkout Method | When to Use |
|----------------|-------------|
| `git url: '...'` | Quick inline checkout, simple pipelines |
| `checkout scm` | Jenkinsfile stored in the repo (standard) |
| `checkout([...])` | Need shallow clone, submodules, or multiple remotes |
| `dir('folder') { git ... }` | Checkout multiple repos into named directories |
| Multibranch Pipeline | Auto-discover and build every branch with a Jenkinsfile |

| Git Variable | Contains |
|-------------|---------|
| `env.GIT_COMMIT` | Full SHA of current commit |
| `env.GIT_BRANCH` | Branch name (`origin/main`) |
| `env.GIT_URL` | Repository URL |
| `env.GIT_PREVIOUS_COMMIT` | SHA of previous commit |
| `env.BRANCH_NAME` | Short branch name (Multibranch only) |
