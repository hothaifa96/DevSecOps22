x# Lab 02 — Pipeline Basics: Hello World and Syntax

**Objective:** Write your first Declarative Pipeline, understand the structure, and practice using `echo`, `sh`, `env`, and `post`.

**Prerequisites:**
- Jenkins running with Pipeline plugin installed
- No Git repo needed for this lab

**Estimated Time:** 20 minutes

---

## Part 1 — Create a Pipeline Job

1. Click **New Item**
2. Name: `lab-02-pipeline-hello-world`
3. Select **Pipeline**
4. Click **OK**

---

## Part 2 — Hello World Pipeline

On the configuration page, scroll to **Pipeline** section.

Select **Pipeline script** and paste the following:

```groovy
pipeline {
    agent any

    stages {
        stage('Hello') {
            steps {
                echo 'Hello, World!'
                echo 'This is my first Jenkins pipeline.'
            }
        }
    }
}
```

Click **Save** then **Build Now**.

### Console Output Expected

```
[Pipeline] Start of Pipeline
[Pipeline] node
[Pipeline] { (Hello)
[Pipeline] echo
Hello, World!
[Pipeline] echo
This is my first Jenkins pipeline.
[Pipeline] }
Finished: SUCCESS
```

---

## Part 3 — Multiple Stages

Update the pipeline script to:

```groovy
pipeline {
    agent any

    stages {
        stage('Stage 1 — Greet') {
            steps {
                echo 'Starting the pipeline...'
                echo 'Stage 1 is running!'
            }
        }

        stage('Stage 2 — System Info') {
            steps {
                echo 'Stage 2 is running!'
                sh 'uname -a'
                sh 'whoami'
                sh 'pwd'
                sh 'date'
            }
        }

        stage('Stage 3 — Finish') {
            steps {
                echo 'Stage 3 — we made it to the end!'
            }
        }
    }
}
```

Click **Save → Build Now** and watch the **Stage View** at the top of the job page.

> **Tip:** Each box in the Stage View represents one stage. Green = passed, Red = failed.

---

## Part 4 — Using Environment Variables

Update the pipeline to print built-in Jenkins variables:

```groovy
pipeline {
    agent any

    environment {
        MY_NAME    = 'Jenkins Student'
        MY_COURSE  = 'DevSecOps'
        BUILD_INFO = "Build #${env.BUILD_NUMBER} on ${env.NODE_NAME}"
    }

    stages {
        stage('Print Custom Variables') {
            steps {
                echo "Hello, ${env.MY_NAME}!"
                echo "Course: ${env.MY_COURSE}"
                echo "Info: ${env.BUILD_INFO}"
            }
        }

        stage('Print Built-in Variables') {
            steps {
                echo "Job Name      : ${env.JOB_NAME}"
                echo "Build Number  : ${env.BUILD_NUMBER}"
                echo "Build URL     : ${env.BUILD_URL}"
                echo "Workspace     : ${env.WORKSPACE}"
                echo "Node Name     : ${env.NODE_NAME}"
            }
        }

        stage('Shell with Variables') {
            steps {
                // Groovy interpolation (double quotes) — resolved before shell
                sh "echo 'Running job: ${env.JOB_NAME}'"

                // Shell variable (single quotes) — resolved by shell at runtime
                sh 'echo "Build number from shell: $BUILD_NUMBER"'
            }
        }
    }
}
```

---

## Part 5 — Using `post` Block

```groovy
pipeline {
    agent any

    stages {
        stage('Work') {
            steps {
                echo 'Doing some work...'
                sh 'sleep 2'
                echo 'Work done!'
            }
        }
    }

    post {
        always {
            echo "POST — always: Build #${env.BUILD_NUMBER} finished."
        }
        success {
            echo 'POST — success: The pipeline PASSED!'
        }
        failure {
            echo 'POST — failure: The pipeline FAILED!'
        }
    }
}
```

Build and check the console. You should see the `always` and `success` messages at the bottom.

### Trigger a Failure

Now intentionally break it by adding `sh 'exit 1'` inside the Work stage:

```groovy
stage('Work') {
    steps {
        echo 'About to fail...'
        sh 'exit 1'
    }
}
```

Build again. You should see `POST — failure` in the console. Then remove `sh 'exit 1'` and rebuild to restore.

---

## Part 6 — `when` Condition

```groovy
pipeline {
    agent any

    environment {
        DEPLOY = 'true'
    }

    stages {
        stage('Always Runs') {
            steps {
                echo 'This stage always runs.'
            }
        }

        stage('Only When DEPLOY is true') {
            when {
                environment name: 'DEPLOY', value: 'true'
            }
            steps {
                echo 'DEPLOY is true — running this stage.'
            }
        }

        stage('Only When DEPLOY is false') {
            when {
                environment name: 'DEPLOY', value: 'false'
            }
            steps {
                echo 'This will be SKIPPED because DEPLOY=true.'
            }
        }
    }
}
```

Build it. The third stage should be **skipped** (shown in grey in Stage View).

---

## Part 7 — `options` and `timeout`

```groovy
pipeline {
    agent any

    options {
        timestamps()
        buildDiscarder(logRotator(numToKeepStr: '5'))
        timeout(time: 5, unit: 'MINUTES')
    }

    stages {
        stage('Fast Stage') {
            steps {
                echo 'This runs fast.'
            }
        }

        stage('Slow Stage') {
            options {
                timeout(time: 30, unit: 'SECONDS')
            }
            steps {
                echo 'This stage has its own 30-second timeout.'
                sh 'sleep 5'
                echo 'Completed within timeout!'
            }
        }
    }

    post {
        always {
            echo "Duration: ${currentBuild.durationString}"
        }
    }
}
```

> **Try this:** Change `sleep 5` to `sleep 60`. The stage will time out and the build will fail with a timeout error.

---

## Exercises

**Exercise 1:** Add a stage called `Math` that calculates and prints a value using a `script {}` block:

```groovy
stage('Math') {
    steps {
        script {
            def a = 10
            def b = 25
            def sum = a + b
            echo "Sum of ${a} and ${b} = ${sum}"
        }
    }
}
```

**Exercise 2:** Use `retry(3)` to retry a flaky step:

```groovy
stage('Retry Example') {
    steps {
        retry(3) {
            sh '''
                RAND=$((RANDOM % 3))
                echo "Random value: $RAND"
                if [ "$RAND" -ne "0" ]; then
                    echo "Simulated failure — will retry..."
                    exit 1
                fi
                echo "Success!"
            '''
        }
    }
}
```

**Exercise 3:** Add a `parameters` block with a `string` parameter called `YOUR_NAME`. Print `"Hello, <YOUR_NAME>!"` in a stage. Use **Build with Parameters** to provide a value.

---

## Summary

| Concept | Syntax |
|---------|--------|
| Minimal pipeline | `pipeline { agent any; stages { stage('X') { steps { echo '...' } } } }` |
| Custom env var | `environment { KEY = 'value' }` |
| Access env var | `${env.KEY}` in Groovy, `$KEY` in shell |
| Post actions | `post { always {} success {} failure {} }` |
| Skip a stage | `when { environment name: 'X', value: 'Y' }` |
| Options | `options { timestamps(); timeout(time: 5, unit: 'MINUTES') }` |
| Groovy logic | `script { def x = 1 + 2; echo "${x}" }` |
| Retry | `retry(3) { sh '...' }` |
