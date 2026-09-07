# Lesson 1: Introduction to Infrastructure as Code (IaC)

---

## Table of Contents

1. [What is Infrastructure as Code?](#what-is-infrastructure-as-code)
2. [Why IaC Matters](#why-iac-matters)
3. [The IaC Tools Landscape](#the-iac-tools-landscape)
4. [Declarative vs. Imperative Approaches](#declarative-vs-imperative-approaches)
5. [Where Terraform Fits](#where-terraform-fits)
6. [Key Takeaways](#key-takeaways)

---

## What is Infrastructure as Code?

**Infrastructure as Code (IaC)** is the practice of managing and provisioning computing infrastructure through machine-readable configuration files rather than through manual processes or interactive configuration tools.

Instead of clicking through a cloud console to create a virtual machine, you write code that describes exactly what you want:

```hcl
# This code creates an AWS EC2 instance
resource "aws_instance" "web_server" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"

  tags = {
    Name        = "WebServer"
    Environment = "Production"
  }
}
```

### The Evolution of Infrastructure Management

| Era | Method | Example |
|-----|--------|---------|
| **Manual** | SSH into servers, run commands by hand | `ssh admin@server && apt install nginx` |
| **Scripted** | Bash/Python scripts to automate steps | `deploy.sh` |
| **Configuration Management** | Tools to configure existing servers | Ansible, Chef, Puppet |
| **Infrastructure as Code** | Declare desired state of entire infrastructure | Terraform, CloudFormation, Pulumi |

### Traditional vs. IaC Approach

**Traditional (Manual) Process:**
1. Log into AWS Console
2. Navigate to EC2
3. Click "Launch Instance"
4. Select AMI, instance type, security groups...
5. Hope you remember every setting next time
6. Pray the colleague who set up staging did it the same way

**IaC Process:**
1. Write configuration in a `.tf` file
2. Run `terraform apply`
3. Infrastructure is created exactly as described
4. Commit code to Git -- now it's versioned, reviewable, and repeatable

---

## Why IaC Matters

### 1. Consistency and Reproducibility

Every environment (dev, staging, production) is built from the same code. No more "it works on staging but not production" due to configuration drift.

```hcl
# The SAME code deploys to any environment
module "web_app" {
  source      = "./modules/web-app"
  environment = var.environment  # "dev", "staging", "prod"
  instance_count = var.environment == "prod" ? 3 : 1
}
```

### 2. Version Control

Infrastructure changes are tracked in Git just like application code:

```bash
git log --oneline
# a1b2c3d Add load balancer to production
# d4e5f6g Increase instance size for web servers
# h7i8j9k Initial infrastructure setup
```

You can review changes via pull requests, revert problematic changes, and maintain a complete audit trail.

### 3. Speed and Efficiency

Spinning up an entire environment takes minutes instead of hours or days:

```bash
# Create a complete environment in minutes
terraform apply -var="environment=staging"

# Tear it down when you're done
terraform destroy -var="environment=staging"
```

### 4. Cost Management

IaC makes it easy to destroy resources when they are not needed:

```bash
# Spin up a test environment for 2 hours, then tear it down
terraform apply
# ... run tests ...
terraform destroy
# Result: You only pay for 2 hours of infrastructure
```

### 5. Documentation as Code

The infrastructure code itself serves as living documentation. Anyone can read the `.tf` files to understand exactly what infrastructure exists.

### 6. Disaster Recovery

If an entire region goes down, you can rebuild everything from code:

```bash
# Switch to backup region and recreate everything
terraform apply -var="region=us-west-2"
```

### 7. Security and Compliance (DevSecOps)

In a DevSecOps context, IaC enables:

- **Policy as Code**: Enforce security rules automatically (e.g., "all S3 buckets must be encrypted")
- **Automated Scanning**: Tools like `tfsec`, `checkov`, and `Sentinel` scan IaC for vulnerabilities before deployment
- **Audit Trails**: Every infrastructure change is tracked in version control
- **Least Privilege**: Define IAM roles and security groups in code, reviewed by security teams

```bash
# Scan Terraform code for security issues before deploying
tfsec .
checkov -d .
```

---

## The IaC Tools Landscape

### Cloud-Specific Tools

| Tool | Provider | Language | Type |
|------|----------|----------|------|
| **AWS CloudFormation** | AWS | JSON/YAML | Declarative |
| **Azure Resource Manager (ARM)** | Azure | JSON | Declarative |
| **Azure Bicep** | Azure | Bicep DSL | Declarative |
| **Google Cloud Deployment Manager** | GCP | YAML/Python | Declarative |

### Multi-Cloud / Cloud-Agnostic Tools

| Tool | Language | Type | Key Feature |
|------|----------|------|-------------|
| **Terraform** | HCL | Declarative | Multi-cloud, huge provider ecosystem |
| **Pulumi** | Python/JS/Go/C# | Imperative | Use real programming languages |
| **Crossplane** | YAML | Declarative | Kubernetes-native infrastructure |
| **CDK for Terraform (CDKTF)** | Python/JS/Go/C# | Imperative | Terraform + real languages |

### Configuration Management Tools (Complementary)

| Tool | Language | Approach | Best For |
|------|----------|----------|----------|
| **Ansible** | YAML | Procedural/Push | Server configuration, app deployment |
| **Chef** | Ruby | Procedural/Pull | Complex server configuration |
| **Puppet** | Puppet DSL | Declarative/Pull | Large-scale server management |
| **SaltStack** | YAML | Procedural/Push | Event-driven automation |

> **Important Distinction**: Tools like Ansible configure what is *on* servers (install packages, edit configs). Terraform creates the servers (and networks, databases, etc.) themselves. They are often used together.

---

## Declarative vs. Imperative Approaches

### Imperative ("How to do it")

You write step-by-step instructions telling the system *how* to reach the desired state:

```python
# Imperative approach (pseudocode)
create_vpc("my-vpc", cidr="10.0.0.0/16")
create_subnet("my-subnet", vpc="my-vpc", cidr="10.0.1.0/24")
create_security_group("my-sg", vpc="my-vpc", ingress=[80, 443])
create_instance("my-server", subnet="my-subnet", sg="my-sg", type="t2.micro")
```

**Problem**: What happens if you run this again? It tries to create duplicates. You need to add logic:

```python
if not vpc_exists("my-vpc"):
    create_vpc("my-vpc", cidr="10.0.0.0/16")
if not subnet_exists("my-subnet"):
    create_subnet("my-subnet", vpc="my-vpc", cidr="10.0.1.0/24")
# ... and so on for every resource
```

### Declarative ("What the end result should be")

You describe *what* you want, and the tool figures out how to achieve it:

```hcl
# Declarative approach (Terraform)
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}

resource "aws_subnet" "main" {
  vpc_id     = aws_vpc.main.id
  cidr_block = "10.0.1.0/24"
}

resource "aws_security_group" "web" {
  vpc_id = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "web" {
  ami                    = "ami-0c55b159cbfafe1f0"
  instance_type          = "t2.micro"
  subnet_id              = aws_subnet.main.id
  vpc_security_group_ids = [aws_security_group.web.id]
}
```

**Run it once**: Creates everything.
**Run it again**: "No changes. Infrastructure is up-to-date."
**Change instance type to `t2.small`**: Only updates the instance -- everything else stays the same.

### Comparison Summary

| Feature | Imperative | Declarative |
|---------|-----------|-------------|
| **You describe** | Steps to reach the goal | The desired end state |
| **Idempotency** | Must be coded manually | Built-in |
| **Ordering** | You control execution order | Tool determines order |
| **Learning curve** | Familiar (like scripting) | Requires new mental model |
| **Examples** | Pulumi, AWS CDK, scripts | Terraform, CloudFormation, ARM |

---

## Where Terraform Fits

### What is Terraform?

Terraform is an open-source Infrastructure as Code tool created by **HashiCorp** in 2014. It uses a declarative language called **HCL (HashiCorp Configuration Language)** to define infrastructure across any cloud provider or service.

### Why Terraform?

1. **Multi-Cloud Support**: One tool for AWS, Azure, GCP, Kubernetes, GitHub, Datadog, and 3,000+ providers
2. **Declarative Language (HCL)**: Easy to read and write, even for non-programmers
3. **Execution Plans**: `terraform plan` shows you exactly what will change before applying
4. **State Management**: Tracks the current state of your infrastructure
5. **Massive Ecosystem**: Thousands of providers and modules in the Terraform Registry
6. **Open Source**: Free to use, with paid options (Terraform Cloud/Enterprise) for teams

### Terraform in the DevSecOps Pipeline

```
Code Commit → Terraform Plan → Security Scan → Review → Terraform Apply → Monitor
     │              │                │             │            │             │
   Git Push    Show changes     tfsec/checkov   PR Review   Deploy infra   Alerts
                                 OPA/Sentinel   Approval    to cloud
```

In a DevSecOps workflow, Terraform enables:

- **Shift Left**: Catch infrastructure security issues before deployment
- **Automated Compliance**: Enforce policies in the CI/CD pipeline
- **Immutable Infrastructure**: Replace rather than modify servers
- **GitOps**: Infrastructure changes flow through Git-based workflows

### Terraform vs. Other Tools

| Feature | Terraform | CloudFormation | Pulumi | Ansible |
|---------|-----------|----------------|--------|---------|
| **Multi-cloud** | Yes | AWS only | Yes | Yes (config) |
| **Language** | HCL | JSON/YAML | Python/JS/Go | YAML |
| **State management** | Yes | Yes (stacks) | Yes | No |
| **Approach** | Declarative | Declarative | Imperative | Procedural |
| **Best for** | Infrastructure provisioning | AWS infrastructure | Devs who prefer code | Server configuration |
| **Community** | Very large | Large (AWS) | Growing | Very large |

### Real-World Example: What Terraform Can Manage

```
Terraform manages:
├── Cloud Infrastructure (AWS, Azure, GCP)
│   ├── Compute (EC2, VMs, GKE clusters)
│   ├── Networking (VPCs, Subnets, Load Balancers)
│   ├── Storage (S3, Blob Storage, Cloud Storage)
│   └── Databases (RDS, CosmosDB, Cloud SQL)
├── DNS (Route53, Cloudflare, DNSimple)
├── Monitoring (Datadog, PagerDuty, New Relic)
├── Version Control (GitHub repos, teams, branch protection)
├── CI/CD (Jenkins, CircleCI configuration)
├── Kubernetes (namespaces, deployments, services)
└── Security (Vault secrets, IAM roles, certificates)
```

---

## Key Takeaways

1. **IaC treats infrastructure like software** -- versioned, tested, and reviewed through code
2. **Declarative approaches** (like Terraform) describe the desired end state; the tool figures out how to get there
3. **IaC enables DevSecOps** by making infrastructure auditable, scannable, and policy-enforceable
4. **Terraform is cloud-agnostic** and works with 3,000+ providers, making it the most versatile IaC tool
5. **IaC is not optional in modern DevOps** -- it is a fundamental practice for reliable, secure, and scalable infrastructure

---

## What's Next?

In the next lesson, we will install Terraform, learn the HCL syntax, and run our first `terraform init`, `plan`, `apply`, and `destroy` commands.

[Next Lesson: Terraform Basics -->](./02-terraform-basics.md)
