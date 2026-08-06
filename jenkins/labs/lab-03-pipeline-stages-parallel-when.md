# Lab 03 — Pipeline Stages: Parallel, When, and Parameters

**Objective:** Practice parallel stages, conditional `when` blocks, `parameters`, and stage-level agents using `echo` and `sh` steps.

**Prerequisites:**
- Jenkins running with Pipeline plugin
- Lab 02 completed

**Estimated Time:** 25 minutes

---

## Part 1 — Parallel Stages

Parallel stages run at the same time and reduce total build time.

Create a new Pipeline job called `lab-03-parallel`:

```groovy
pipeline {
    agent any

    stages {
        stage('Sequential Before') {
            steps {
                echo 'This runs BEFORE the parallel block.'
                sh 'sleep 1'
            }
        }

        stage('Parallel Quality Checks') {
            parallel {
                stage('Unit Tests') {
                    steps {
                        echo 'Running unit tests...'
                        sh 'sleep 3'
                        echo 'Unit tests PASSED!'
                    }
                }

                stage('Lint') {
                    steps {
                        echo 'Running linter...'
                        sh 'sleep 2'
                        echo 'Lint PASSED!'
                    }
                }

                stage('Security Scan') {
                    steps {
                        echo 'Running security scan...'
                        sh 'sleep 4'
                        echo 'Security scan PASSED!'
                    }
                }
            }
        }

        stage('Sequential After') {
            steps {
                echo 'All parallel stages finished — continuing.'
            }
        }
    }

    post {
        always {
            echo "Total duration: ${currentBuild.durationString}"
        }
    }
}
```

### What to Observe
- In the Stage View, all three parallel stages show columns side by side
- Total build time is roughly the slowest branch (~4s) not the sum (~9s)
- The sequential stages still wait for the parallel block to complete

---

## Part 2 — `failFast` in Parallel

```groovy
pipeline {
    agent any

    stages {
        stage('Parallel with failFast') {
            failFast true
            parallel {
                stage('Fast Stage') {
                    steps {
                        echo 'Fast stage starting...'
                        sh 'sleep 1'
                        echo 'Fast stage done.'
                    }
                }

                stage('Failing Stage') {
                    steps {
                        echo 'This stage will fail after 2 seconds...'
                        sh 'sleep 2 && exit 1'
                    }
                }

                stage('Slow Stage') {
                    steps {
                        echo 'Slow stage — would take 10 seconds...'
                        sh 'sleep 10'
                        echo 'Slow stage done.'
                    }
                }
            }
        }
    }
}
```

> **Observe:** The Slow Stage is **aborted** as soon as the Failing Stage fails because `failFast true` is set. The whole pipeline fails.

---

## Part 3 — `parameters` with `when`

```groovy
pipeline {
    agent any

    parameters {
        choice(
            name: 'TARGET_ENV',
            choices: ['dev', 'staging', 'production'],
            description: 'Which environment to deploy to?'
        )
        booleanParam(
            name: 'RUN_TESTS',
            defaultValue: true,
            description: 'Run the test suite?'
        )
        string(
            name: 'IMAGE_TAG',
            defaultValue: 'latest',
            description: 'Docker image tag to deploy'
        )
    }

    stages {
        stage('Show Parameters') {
            steps {
                echo "Target environment : ${params.TARGET_ENV}"
                echo "Run tests          : ${params.RUN_TESTS}"
                echo "Image tag          : ${params.IMAGE_TAG}"
            }
        }

        stage('Tests') {
            when {
                expression { params.RUN_TESTS == true }
            }
            steps {
                echo "Running tests for image tag: ${params.IMAGE_TAG}"
                sh 'sleep 2'
                echo 'Tests passed!'
            }
        }

        stage('Deploy to Dev') {
            when {
                expression { params.TARGET_ENV == 'dev' }
            }
            steps {
                echo "Deploying ${params.IMAGE_TAG} to DEV environment"
                sh 'echo "helm upgrade --install myapp ./helm --set image.tag=${IMAGE_TAG} --namespace dev"'
            }
        }

        stage('Deploy to Staging') {
            when {
                expression { params.TARGET_ENV == 'staging' }
            }
            steps {
                echo "Deploying ${params.IMAGE_TAG} to STAGING environment"
                sh 'echo "helm upgrade --install myapp ./helm --set image.tag=${IMAGE_TAG} --namespace staging"'
            }
        }

        stage('Approve Production') {
            when {
                expression { params.TARGET_ENV == 'production' }
            }
            steps {
                input message: "Deploy ${params.IMAGE_TAG} to PRODUCTION?", ok: 'Deploy'
            }
        }

        stage('Deploy to Production') {
            when {
                expression { params.TARGET_ENV == 'production' }
            }
            steps {
                echo "Deploying ${params.IMAGE_TAG} to PRODUCTION"
                sh 'echo "helm upgrade --install myapp ./helm --set image.tag=${IMAGE_TAG} --namespace production --set replicaCount=3"'
            }
        }
    }

    post {
        success {
            echo "Deployment of ${params.IMAGE_TAG} to ${params.TARGET_ENV} SUCCEEDED!"
        }
        failure {
            echo "Deployment of ${params.IMAGE_TAG} to ${params.TARGET_ENV} FAILED!"
        }
    }
}
```

### How to Run with Parameters

1. After saving, click **Build with Parameters** (replaces "Build Now")
2. Select `staging` from the dropdown
3. Leave RUN_TESTS checked
4. Enter `v1.2.3` as IMAGE_TAG
5. Click **Build**

Only the `Tests` and `Deploy to Staging` stages should run. The others are skipped.

---

## Part 4 — Nested Sequential Stages

Stages can be nested inside a parent stage to group related work:

```groovy
pipeline {
    agent any

    stages {
        stage('Build Pipeline') {
            stages {
                stage('Compile') {
                    steps {
                        echo 'Compiling source code...'
                        sh 'sleep 1'
                        echo 'Compilation done.'
                    }
                }

                stage('Package') {
                    steps {
                        echo 'Packaging application...'
                        sh 'sleep 1'
                        echo 'Package created: myapp-1.0.jar'
                    }
                }

                stage('Verify Package') {
                    steps {
                        echo 'Verifying package integrity...'
                        sh 'echo "Checksum: abc123def456"'
                    }
                }
            }
        }

        stage('Test Pipeline') {
            stages {
                stage('Unit Tests') {
                    steps {
                        echo 'Running unit tests...'
                        sh 'sleep 2'
                        echo 'All unit tests passed.'
                    }
                }

                stage('Integration Tests') {
                    steps {
                        echo 'Running integration tests...'
                        sh 'sleep 2'
                        echo 'All integration tests passed.'
                    }
                }
            }
        }

        stage('Deploy') {
            steps {
                echo 'Deploying...'
                sh 'sleep 1'
                echo 'Deploy complete!'
            }
        }
    }
}
```

---

## Part 5 — Dynamic Variables in Stages

Compute values at runtime and share them between stages:

```groovy
pipeline {
    agent any

    environment {
        APP_VERSION = ''
        BUILD_DATE  = ''
    }

    stages {
        stage('Set Variables') {
            steps {
                script {
                    env.APP_VERSION = "1.0.${env.BUILD_NUMBER}"
                    env.BUILD_DATE  = sh(script: 'date +%Y-%m-%d', returnStdout: true).trim()
                }
                echo "App version : ${env.APP_VERSION}"
                echo "Build date  : ${env.BUILD_DATE}"
            }
        }

        stage('Build') {
            steps {
                echo "Building version ${env.APP_VERSION} on ${env.BUILD_DATE}"
                sh "echo 'app-${APP_VERSION}-${BUILD_DATE}.jar' > artifact-name.txt"
                sh 'cat artifact-name.txt'
            }
        }

        stage('Tag') {
            steps {
                echo "Tagging Docker image as: myapp:${env.APP_VERSION}"
                sh "echo 'docker tag myapp:latest myapp:${APP_VERSION}'"
            }
        }

        stage('Summary') {
            steps {
                script {
                    currentBuild.displayName = "#${env.BUILD_NUMBER} — v${env.APP_VERSION}"
                    currentBuild.description = "Built on ${env.BUILD_DATE}"
                }
                echo "Build summary set in Jenkins UI."
            }
        }
    }
}
```

After running, look at the Build History — the build entry should show `#N — v1.0.N` instead of the default `#N`.

---

## Exercises

**Exercise 1:** Add a `matrix` of test environments using parallel stages:

```groovy
stage('Test Matrix') {
    parallel {
        stage('Test on Node 18') {
            steps {
                echo 'Testing with Node 18'
                sh 'node --version || echo "Node not installed — simulating"'
            }
        }
        stage('Test on Node 20') {
            steps {
                echo 'Testing with Node 20'
            }
        }
        stage('Test on Node 22') {
            steps {
                echo 'Testing with Node 22'
            }
        }
    }
}
```

**Exercise 2:** Add a `when { branch 'main' }` stage to a Multibranch pipeline (or simulate with `when { expression { env.BRANCH_NAME == 'main' } }`). Build it and observe the stage is skipped when the value doesn't match.

**Exercise 3:** Create a pipeline that uses `stash` and `unstash` to "pass a file" between two stages:

```groovy
stage('Create File') {
    steps {
        sh 'echo "contents from stage 1" > output.txt'
        stash name: 'my-output', includes: 'output.txt'
    }
}

stage('Read File') {
    steps {
        unstash 'my-output'
        sh 'cat output.txt'
        echo 'File successfully passed between stages!'
    }
}
```

---

## Summary

| Concept | Key Syntax |
|---------|-----------|
| Parallel stages | `stage('X') { parallel { stage('A') {} stage('B') {} } }` |
| Fail fast | `failFast true` inside parallel |
| Parameters | `parameters { choice(...) booleanParam(...) string(...) }` |
| Conditional stage | `when { expression { params.X == 'value' } }` |
| Nested stages | `stage('Parent') { stages { stage('Child') {} } }` |
| Runtime variable | `script { env.KEY = sh(script: '...', returnStdout: true).trim() }` |
| Build display name | `currentBuild.displayName = "..."` |
| Pass files across stages | `stash` / `unstash` |
