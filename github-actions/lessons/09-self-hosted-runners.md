# Lesson 9: Self-Hosted Runners

## Table of Contents

- [What Are Self-Hosted Runners?](#what-are-self-hosted-runners)
- [When to Use Self-Hosted Runners](#when-to-use-self-hosted-runners)
- [Setting Up Self-Hosted Runners](#setting-up-self-hosted-runners)
  - [Adding a Runner (Manual)](#adding-a-runner-manual)
  - [Runner as a Systemd Service](#runner-as-a-systemd-service)
- [Runner Labels](#runner-labels)
- [Runner Groups](#runner-groups)
- [Using Self-Hosted Runners in Workflows](#using-self-hosted-runners-in-workflows)
- [Ephemeral Runners](#ephemeral-runners)
- [Autoscaling Runners](#autoscaling-runners)
  - [Actions Runner Controller (ARC)](#actions-runner-controller-arc)
  - [Terraform-Based Autoscaling](#terraform-based-autoscaling)
- [Security Considerations](#security-considerations)
- [Runner Maintenance](#runner-maintenance)
- [Monitoring and Troubleshooting](#monitoring-and-troubleshooting)
- [Summary](#summary)

---

## What Are Self-Hosted Runners?

**Self-hosted runners** are machines that you manage and register with GitHub to execute workflow jobs. Unlike GitHub-hosted runners (managed by GitHub), you control the hardware, operating system, software, and network.

### GitHub-Hosted vs Self-Hosted

| Feature | GitHub-Hosted | Self-Hosted |
|---------|--------------|-------------|
| **Management** | Managed by GitHub | Managed by you |
| **Provisioning** | Automatic (fresh VM per job) | Manual setup or autoscaling |
| **Cost** | Per-minute billing | Your infrastructure costs |
| **Environment** | Clean VM every job | Persistent or ephemeral |
| **Software** | Pre-installed tools | Your custom tools |
| **Hardware** | Standardized (2-core, 7 GB) | Any hardware (GPU, ARM, etc.) |
| **Network** | GitHub's network | Your network (VPN, firewall access) |
| **IP Address** | Dynamic (shared pool) | Static (your IPs) |
| **OS options** | Ubuntu, Windows, macOS | Any OS that supports the runner |
| **Security** | Isolated VMs (clean each run) | Shared state between runs (unless ephemeral) |

---

## When to Use Self-Hosted Runners

### Good Use Cases

| Scenario | Why Self-Hosted |
|----------|----------------|
| **Special hardware** | GPUs, ARM processors, high memory/CPU |
| **Network access** | Access to internal resources (databases, APIs behind firewalls) |
| **Compliance** | Data must stay on-premises (HIPAA, SOC2, etc.) |
| **Cost optimization** | High volume workflows (cheaper than GitHub-hosted at scale) |
| **Custom software** | Licensed tools, proprietary SDKs |
| **Static IPs** | API allowlisting, firewall rules |
| **Large builds** | Need more disk space, RAM, or CPU than GitHub-hosted provides |

### When to Stick with GitHub-Hosted

| Scenario | Why GitHub-Hosted |
|----------|-------------------|
| **Standard CI/CD** | Simple build/test workflows |
| **Open source** | Unlimited free minutes for public repos |
| **Low maintenance** | No runners to manage |
| **Security isolation** | Fresh VM per job, no state leakage |
| **Quick start** | No setup required |

---

## Setting Up Self-Hosted Runners

### Adding a Runner (Manual)

#### 1. Get the Registration Token

Go to **Settings > Actions > Runners > New self-hosted runner** (or use the API):

```bash
# Via API
TOKEN=$(curl -s -X POST \
  -H "Authorization: token $GITHUB_PAT" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/OWNER/REPO/actions/runners/registration-token \
  | jq -r '.token')
```

#### 2. Install the Runner (Linux)

```bash
# Create a directory
mkdir actions-runner && cd actions-runner

# Download the latest runner package
curl -o actions-runner-linux-x64-2.320.0.tar.gz -L \
  https://github.com/actions/runner/releases/download/v2.320.0/actions-runner-linux-x64-2.320.0.tar.gz

# Extract
tar xzf ./actions-runner-linux-x64-2.320.0.tar.gz

# Configure the runner
./config.sh --url https://github.com/OWNER/REPO \
  --token YOUR_REGISTRATION_TOKEN \
  --name my-runner \
  --labels linux,x64,custom \
  --work _work

# Run interactively (for testing)
./run.sh
```

#### 3. Install the Runner (macOS)

```bash
mkdir actions-runner && cd actions-runner

curl -o actions-runner-osx-x64-2.320.0.tar.gz -L \
  https://github.com/actions/runner/releases/download/v2.320.0/actions-runner-osx-x64-2.320.0.tar.gz

tar xzf ./actions-runner-osx-x64-2.320.0.tar.gz

./config.sh --url https://github.com/OWNER/REPO \
  --token YOUR_REGISTRATION_TOKEN \
  --name mac-runner

./run.sh
```

#### 4. Install the Runner (Windows)

```powershell
mkdir actions-runner; cd actions-runner

Invoke-WebRequest -Uri https://github.com/actions/runner/releases/download/v2.320.0/actions-runner-win-x64-2.320.0.zip -OutFile actions-runner-win-x64-2.320.0.zip

Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::ExtractToDirectory("$PWD/actions-runner-win-x64-2.320.0.zip", "$PWD")

.\config.cmd --url https://github.com/OWNER/REPO --token YOUR_REGISTRATION_TOKEN

.\run.cmd
```

### Runner as a Systemd Service

For production, run the runner as a background service:

```bash
# Install the service (Linux)
sudo ./svc.sh install

# Start the service
sudo ./svc.sh start

# Check status
sudo ./svc.sh status

# Stop the service
sudo ./svc.sh stop

# Uninstall the service
sudo ./svc.sh uninstall
```

The service configuration is at `/etc/systemd/system/actions.runner.OWNER-REPO.RUNNER_NAME.service`.

### Runner via Docker

Run the runner in a Docker container:

```dockerfile
# Dockerfile for a self-hosted runner
FROM ubuntu:22.04

ARG RUNNER_VERSION=2.320.0

RUN apt-get update && apt-get install -y \
    curl jq build-essential libssl-dev libffi-dev \
    python3 python3-venv python3-dev python3-pip \
    nodejs npm docker.io git \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m runner

WORKDIR /home/runner

RUN curl -o actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz -L \
    https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz \
    && tar xzf ./actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz \
    && rm actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz \
    && ./bin/installdependencies.sh

RUN chown -R runner:runner /home/runner

USER runner

ENTRYPOINT ["./config.sh"]
```

---

## Runner Labels

Labels categorize runners so workflows can target specific ones.

### Default Labels

Every self-hosted runner automatically gets these labels:
- `self-hosted`
- OS label: `linux`, `windows`, or `macos`
- Architecture label: `x64`, `arm64`, `arm`

### Custom Labels

Add custom labels during registration or after:

```bash
# During registration
./config.sh --url https://github.com/OWNER/REPO \
  --token TOKEN \
  --labels gpu,docker,large-disk

# Add labels later via GitHub UI:
# Settings > Actions > Runners > Click runner > Edit labels
```

### Using Labels in Workflows

```yaml
jobs:
  # Match any self-hosted runner
  basic:
    runs-on: self-hosted

  # Match runner with specific labels (AND logic)
  gpu-job:
    runs-on: [self-hosted, linux, gpu]

  # Match runner with custom labels
  build:
    runs-on: [self-hosted, docker, large-disk]

  # Dynamic label selection
  deploy:
    runs-on: [self-hosted, "${{ inputs.environment }}"]
```

---

## Runner Groups

Runner groups organize runners and control access (available on GitHub Team and Enterprise plans).

### Creating Runner Groups

1. Go to **Organization Settings > Actions > Runner groups**
2. Click **New runner group**
3. Name the group and select which repositories can use it

### Use Cases

```
Runner Group: "production-runners"
  - Repositories: deployment-repo, infra-repo
  - Runners: prod-runner-1, prod-runner-2

Runner Group: "gpu-runners"
  - Repositories: ml-training-repo
  - Runners: gpu-runner-1, gpu-runner-2

Runner Group: "default"
  - Repositories: All repositories
  - Runners: general-runner-1, general-runner-2
```

### Referencing Runner Groups

Runner groups are referenced via labels. Assign runners in a group with a group-specific label:

```yaml
jobs:
  train:
    runs-on: [self-hosted, gpu-pool]     # Matches runners labeled gpu-pool
```

---

## Using Self-Hosted Runners in Workflows

### Basic Usage

```yaml
jobs:
  build:
    runs-on: self-hosted
    steps:
      - uses: actions/checkout@v4
      - run: |
          echo "Running on: $(hostname)"
          echo "OS: $(uname -a)"
          echo "Working directory: $(pwd)"
```

### Mixed Runners (Self-Hosted + GitHub-Hosted)

```yaml
jobs:
  # Tests run on GitHub-hosted (clean environment, parallel)
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: [18, 20, 22]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
      - run: npm ci && npm test

  # Build runs on self-hosted (access to internal registry)
  build:
    needs: test
    runs-on: [self-hosted, linux, docker]
    steps:
      - uses: actions/checkout@v4
      - name: Build and push to internal registry
        run: |
          docker build -t internal-registry.corp.com/myapp:${{ github.sha }} .
          docker push internal-registry.corp.com/myapp:${{ github.sha }}

  # Deploy runs on self-hosted (access to internal network)
  deploy:
    needs: build
    runs-on: [self-hosted, linux]
    environment: production
    steps:
      - name: Deploy to internal Kubernetes
        run: |
          kubectl set image deployment/myapp \
            myapp=internal-registry.corp.com/myapp:${{ github.sha }}
```

---

## Ephemeral Runners

Ephemeral runners are **disposable** — they execute one job and then unregister. This provides the same clean-state guarantee as GitHub-hosted runners.

### Configuring Ephemeral Mode

```bash
./config.sh --url https://github.com/OWNER/REPO \
  --token TOKEN \
  --ephemeral \
  --name ephemeral-runner-$RANDOM
```

### Benefits of Ephemeral Runners

| Benefit | Description |
|---------|-------------|
| **Clean state** | No leftover files, processes, or credentials from previous jobs |
| **Security** | Reduced risk of data leakage between jobs |
| **Consistency** | Every job starts from the same baseline |
| **Autoscaling** | Natural fit for autoscaling solutions |

### Ephemeral Runner Lifecycle

```
1. Runner registers with GitHub (--ephemeral)
2. Runner picks up ONE job
3. Job executes
4. Runner automatically unregisters
5. Runner process exits
6. Orchestrator creates a new runner instance
```

### Docker-Based Ephemeral Runner

```bash
#!/bin/bash
# start-ephemeral-runner.sh

while true; do
  # Get registration token
  TOKEN=$(curl -s -X POST \
    -H "Authorization: token $GITHUB_PAT" \
    https://api.github.com/repos/OWNER/REPO/actions/runners/registration-token \
    | jq -r '.token')

  # Start runner container (exits after one job)
  docker run --rm \
    -e RUNNER_TOKEN="$TOKEN" \
    -e RUNNER_REPO="https://github.com/OWNER/REPO" \
    -e RUNNER_EPHEMERAL=true \
    -v /var/run/docker.sock:/var/run/docker.sock \
    my-runner-image:latest

  echo "Runner completed a job, starting a new one..."
  sleep 2
done
```

---

## Autoscaling Runners

### Actions Runner Controller (ARC)

**ARC** is the official Kubernetes-based autoscaler for GitHub Actions runners. It's the recommended solution for Kubernetes environments.

#### Architecture

```
┌─────────────────────────────────────────┐
│ Kubernetes Cluster                       │
│                                          │
│  ┌──────────────┐   ┌────────────────┐  │
│  │ ARC          │   │ Runner Scale   │  │
│  │ Controller   │──▶│ Set            │  │
│  │ (watches for │   │ (manages pods) │  │
│  │  webhook     │   │                │  │
│  │  events)     │   │ ┌────────────┐ │  │
│  └──────────────┘   │ │ Runner Pod │ │  │
│                      │ │ (ephemeral)│ │  │
│  ┌──────────────┐   │ └────────────┘ │  │
│  │ Listener     │   │ ┌────────────┐ │  │
│  │ (receives    │   │ │ Runner Pod │ │  │
│  │  webhooks    │   │ │ (ephemeral)│ │  │
│  │  from GitHub)│   │ └────────────┘ │  │
│  └──────────────┘   └────────────────┘  │
│                                          │
└─────────────────────────────────────────┘
```

#### Installing ARC with Helm

```bash
# Add the Helm repository
helm repo add oci://ghcr.io/actions/actions-runner-controller-charts

# Install the controller
helm install arc \
  --namespace arc-systems \
  --create-namespace \
  oci://ghcr.io/actions/actions-runner-controller-charts/gha-runner-scale-set-controller

# Install a runner scale set
helm install arc-runner-set \
  --namespace arc-runners \
  --create-namespace \
  oci://ghcr.io/actions/actions-runner-controller-charts/gha-runner-scale-set \
  --set githubConfigUrl="https://github.com/OWNER/REPO" \
  --set githubConfigSecret.github_token="$GITHUB_PAT" \
  --set minRunners=1 \
  --set maxRunners=10
```

#### ARC Runner Scale Set Configuration

```yaml
# values.yaml for the runner scale set
githubConfigUrl: "https://github.com/my-org"
githubConfigSecret:
  github_token: "ghp_xxxx"

minRunners: 1
maxRunners: 20

runnerGroup: "default"

template:
  spec:
    containers:
      - name: runner
        image: ghcr.io/actions/actions-runner:latest
        resources:
          requests:
            cpu: "500m"
            memory: "512Mi"
          limits:
            cpu: "2"
            memory: "4Gi"
        volumeMounts:
          - name: work
            mountPath: /home/runner/_work
    volumes:
      - name: work
        emptyDir: {}
```

#### Using ARC Runners in Workflows

```yaml
jobs:
  build:
    runs-on: arc-runner-set     # Name of your runner scale set
    steps:
      - uses: actions/checkout@v4
      - run: echo "Running on ARC-managed runner in Kubernetes"
```

### Terraform-Based Autoscaling

For AWS-based autoscaling using EC2 instances:

```hcl
# terraform/main.tf (simplified)
module "github-runner" {
  source  = "philips-labs/github-runner/aws"
  version = "5.0.0"

  aws_region = "us-east-1"

  github_app = {
    key_base64     = var.github_app_key_base64
    id             = var.github_app_id
    webhook_secret = var.webhook_secret
  }

  # Runner configuration
  enable_organization_runners = true
  runner_extra_labels         = ["linux", "x64", "aws"]

  # Scaling configuration
  minimum_running_time_in_minutes = 5
  delay_webhook_event             = 0

  # Instance configuration
  instance_types = ["m5.large", "m5.xlarge"]
  runners_maximum_count = 20

  # Use ephemeral runners
  enable_ephemeral_runners = true
}
```

---

## Security Considerations

Self-hosted runners introduce security responsibilities that don't exist with GitHub-hosted runners.

### Critical Security Rules

#### 1. Never Use Self-Hosted Runners with Public Repos

```
PUBLIC REPO + SELF-HOSTED RUNNER = SECURITY RISK

Anyone can fork a public repo and create a PR.
The PR workflow runs on YOUR self-hosted runner.
The attacker's code runs on YOUR machine.
```

If you must use self-hosted runners with public repos:
- Use ephemeral runners
- Run in isolated containers
- Restrict network access
- Never store credentials on the runner

#### 2. Use Ephemeral Runners

```bash
# Always use --ephemeral for security
./config.sh --url https://github.com/OWNER/REPO \
  --token TOKEN \
  --ephemeral
```

#### 3. Limit Runner Access

```yaml
# Use runner groups to restrict which repos can use which runners
# Organization Settings > Actions > Runner groups

# Production runners — only accessible by deploy repos
# General runners — accessible by all repos
```

#### 4. Run as Non-Root User

```bash
# Create a dedicated user
sudo useradd -m github-runner
sudo -u github-runner ./config.sh --url ... --token ...
```

#### 5. Isolate the Runner Environment

```bash
# Use Docker-in-Docker for isolation
docker run --rm \
  --security-opt=no-new-privileges \
  --cap-drop=ALL \
  -v /var/run/docker.sock:/var/run/docker.sock \
  my-runner-image
```

#### 6. Network Segmentation

```
┌─────────────────────────────────────────┐
│ Runner Network (DMZ)                     │
│                                          │
│  ┌──────────┐   ┌──────────┐            │
│  │ Runner 1 │   │ Runner 2 │            │
│  └──────────┘   └──────────┘            │
│       │              │                   │
│       └──────┬───────┘                   │
│              │                           │
│         ┌────▼────┐                      │
│         │Firewall │                      │
│         └────┬────┘                      │
│              │                           │
└──────────────┼───────────────────────────┘
               │
    ┌──────────▼──────────┐
    │ Internal Network     │
    │ (Limited access)     │
    └──────────────────────┘
```

### Security Checklist

- [ ] Use ephemeral runners (or clean state between jobs)
- [ ] Don't use self-hosted runners for public repositories
- [ ] Run as a non-root, dedicated user
- [ ] Use runner groups to limit repository access
- [ ] Keep the runner software updated
- [ ] Monitor runner logs for suspicious activity
- [ ] Use network segmentation
- [ ] Don't store secrets or credentials on the runner
- [ ] Use Docker isolation when possible
- [ ] Audit which workflows run on self-hosted runners

---

## Runner Maintenance

### Updating the Runner

The runner automatically updates itself in most cases. For manual updates:

```bash
# Stop the runner
sudo ./svc.sh stop

# Download and extract new version
curl -o actions-runner-linux-x64-NEW_VERSION.tar.gz -L \
  https://github.com/actions/runner/releases/download/vNEW_VERSION/actions-runner-linux-x64-NEW_VERSION.tar.gz
tar xzf ./actions-runner-linux-x64-NEW_VERSION.tar.gz

# Restart
sudo ./svc.sh start
```

### Removing a Runner

```bash
# Via the runner machine
./config.sh remove --token YOUR_REMOVAL_TOKEN

# Via API (force remove)
curl -X DELETE \
  -H "Authorization: token $GITHUB_PAT" \
  https://api.github.com/repos/OWNER/REPO/actions/runners/RUNNER_ID

# Via GitHub CLI
gh api repos/OWNER/REPO/actions/runners/RUNNER_ID -X DELETE
```

### Cleaning Up Runner State

For non-ephemeral runners, periodically clean up:

```bash
#!/bin/bash
# cleanup-runner.sh — Run via cron or after each job

# Clean work directory
rm -rf /home/runner/_work/*

# Clean Docker (if used)
docker system prune -af --volumes

# Clean temp files
rm -rf /tmp/runner-*

# Clean package manager caches
rm -rf ~/.npm/_cacache
rm -rf ~/.cache/pip

echo "Runner cleanup complete"
```

---

## Monitoring and Troubleshooting

### Checking Runner Status

```bash
# Via GitHub CLI
gh api repos/OWNER/REPO/actions/runners --jq '.runners[] | {name, status, busy, labels: [.labels[].name]}'

# Via API
curl -H "Authorization: token $GITHUB_PAT" \
  https://api.github.com/repos/OWNER/REPO/actions/runners
```

### Runner Logs

```bash
# Service logs (systemd)
journalctl -u actions.runner.OWNER-REPO.RUNNER_NAME -f

# Runner application logs
tail -f /home/runner/actions-runner/_diag/Runner_*.log
tail -f /home/runner/actions-runner/_diag/Worker_*.log
```

### Common Issues

| Issue | Cause | Solution |
|-------|-------|---------|
| Runner shows "Offline" | Service stopped, network issue | Check service status, verify connectivity |
| Job queued indefinitely | No matching runner available | Check labels, runner status |
| "Could not resolve host" | DNS issue on runner | Check `/etc/resolv.conf`, network config |
| Runner picks up wrong jobs | Labels too broad | Use more specific labels |
| Disk full | Build artifacts accumulating | Add cleanup scripts, use ephemeral runners |
| Permission denied | Wrong user, missing sudo | Check runner user permissions |
| Docker socket permission | User not in docker group | `sudo usermod -aG docker github-runner` |

### Health Check Script

```bash
#!/bin/bash
# health-check.sh

RUNNER_DIR="/home/runner/actions-runner"

# Check if runner service is running
if systemctl is-active --quiet "actions.runner.*"; then
    echo "Runner service: RUNNING"
else
    echo "Runner service: STOPPED"
    exit 1
fi

# Check disk space (fail if <10% free)
DISK_USAGE=$(df -h "$RUNNER_DIR" | awk 'NR==2 {print $5}' | tr -d '%')
if [ "$DISK_USAGE" -gt 90 ]; then
    echo "Disk usage: CRITICAL ($DISK_USAGE%)"
    exit 1
else
    echo "Disk usage: OK ($DISK_USAGE%)"
fi

# Check connectivity to GitHub
if curl -s --max-time 5 https://github.com > /dev/null; then
    echo "GitHub connectivity: OK"
else
    echo "GitHub connectivity: FAILED"
    exit 1
fi

echo "Health check: PASSED"
```

---

## Summary

| Feature | Description |
|---------|-------------|
| **Self-hosted runners** | Your own machines registered with GitHub |
| **Labels** | Categorize runners (OS, arch, custom) |
| **Runner groups** | Organize runners, control repo access (Team/Enterprise) |
| **Ephemeral runners** | One job per runner instance, then destroy |
| **ARC** | Kubernetes-based autoscaling (official solution) |
| **Security** | Never use with public repos, use ephemeral, non-root |

### Key Takeaways

1. **Use self-hosted runners when needed** — special hardware, network access, compliance, or cost
2. **Prefer ephemeral runners** for security — no state leakage between jobs
3. **Never use self-hosted runners with public repositories** without extreme isolation
4. **Use runner labels** to target specific runner capabilities
5. **ARC (Actions Runner Controller)** is the recommended Kubernetes autoscaling solution
6. **Keep runners updated** — the runner software auto-updates, but verify
7. **Monitor runner health** — disk space, connectivity, service status
8. **Use runner groups** to control which repositories can use which runners
9. **Run as non-root** and isolate runners from sensitive internal resources

---

**Next Lesson:** [10 - Advanced Patterns](./10-advanced-patterns.md) — Monorepo workflows, conditional jobs, composite actions, and security scanning.
