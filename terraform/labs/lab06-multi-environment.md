# Lab 06: Multi-Environment Management

## Difficulty: Intermediate–Advanced

## Objectives

By the end of this lab, you will be able to:

- Manage multiple environments (dev/staging/prod) using two approaches
- Use Terraform **workspaces** for lightweight environment separation
- Use a **directory structure** for full environment isolation
- Create per-environment `.tfvars` files with environment-specific values
- Understand the trade-offs between workspaces and directory structures
- Apply DevSecOps principles to environment promotion

## Prerequisites

- Completed Labs 01–05
- AWS CLI configured
- Terraform v1.0+ installed

## Estimated Time

75 minutes

---

## Part 1: Understanding the Two Approaches

### Approach A: Workspaces

- **Same code, same directory, different state files**
- Workspaces create isolated state within the same backend
- Environment differences are handled by `terraform.workspace` and `.tfvars`

| Pros | Cons |
|------|------|
| Simple to set up | Shared code can drift between envs |
| DRY — no code duplication | Cannot have different provider versions |
| Easy to switch between envs | State paths can be confusing |
| Good for similar environments | Not suitable for very different envs |

### Approach B: Directory Structure

- **Separate directory per environment with its own state**
- Shared logic lives in modules; each environment has its own root configuration

| Pros | Cons |
|------|------|
| Full isolation between envs | Some code duplication |
| Different provider versions per env | More files to maintain |
| Independent state and backends | Must keep envs in sync manually |
| Clearer blast radius | Larger repository |

### When to Use Which?

| Scenario | Recommendation |
|----------|----------------|
| Environments are nearly identical | Workspaces |
| Environments differ significantly | Directory structure |
| Small team, few resources | Workspaces |
| Large team, strict change control | Directory structure |
| CI/CD with environment promotion | Directory structure |
| Quick prototyping | Workspaces |

---

## Part 2: Approach A — Terraform Workspaces

### Step 2.1: Set Up the Project

```bash
mkdir -p ~/terraform-labs/lab06/workspaces
cd ~/terraform-labs/lab06/workspaces
```

### Step 2.2: Create the Configuration

Create `variables.tf`:

```hcl
# variables.tf

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "devsecops"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t2.micro"
}

variable "instance_count" {
  description = "Number of instances"
  type        = number
  default     = 1
}

variable "enable_monitoring" {
  description = "Enable detailed monitoring"
  type        = bool
  default     = false
}

variable "allowed_ssh_cidrs" {
  description = "CIDR blocks allowed for SSH"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "extra_tags" {
  description = "Additional tags"
  type        = map(string)
  default     = {}
}
```

Create `main.tf`:

```hcl
# main.tf — Workspace-based multi-environment configuration

terraform {
  required_version = ">= 1.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = terraform.workspace
      ManagedBy   = "terraform"
      Workspace   = terraform.workspace
    }
  }
}

# ──────────────────────────────────────────────
# Environment-Aware Locals
# ──────────────────────────────────────────────
locals {
  # Use terraform.workspace for the environment name
  environment = terraform.workspace
  name_prefix = "${var.project_name}-${local.environment}"

  # Environment-specific configurations via maps
  instance_type_map = {
    default = "t2.micro"
    dev     = "t2.micro"
    staging = "t2.small"
    prod    = "t2.medium"
  }

  instance_count_map = {
    default = 1
    dev     = 1
    staging = 2
    prod    = 3
  }

  cidr_map = {
    default = "10.0.0.0/16"
    dev     = "10.0.0.0/16"
    staging = "10.1.0.0/16"
    prod    = "10.2.0.0/16"
  }

  # Look up by workspace or fall back to default
  resolved_instance_type = lookup(local.instance_type_map, local.environment, local.instance_type_map["default"])
  resolved_instance_count = lookup(local.instance_count_map, local.environment, local.instance_count_map["default"])
  resolved_cidr = lookup(local.cidr_map, local.environment, local.cidr_map["default"])

  is_production = local.environment == "prod"

  all_tags = merge(var.extra_tags, {
    Project     = var.project_name
    Environment = local.environment
  })
}

# ──────────────────────────────────────────────
# VPC (environment-specific CIDR)
# ──────────────────────────────────────────────
resource "aws_vpc" "main" {
  cidr_block           = local.resolved_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = merge(local.all_tags, {
    Name = "${local.name_prefix}-vpc"
  })
}

# ──────────────────────────────────────────────
# Subnets
# ──────────────────────────────────────────────
resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(local.resolved_cidr, 8, 1)
  map_public_ip_on_launch = !local.is_production
  availability_zone       = "${var.aws_region}a"

  tags = merge(local.all_tags, {
    Name = "${local.name_prefix}-public-subnet"
    Tier = "public"
  })
}

# ──────────────────────────────────────────────
# Security Group (stricter in production)
# ──────────────────────────────────────────────
resource "aws_security_group" "web" {
  name        = "${local.name_prefix}-web-sg"
  description = "Web security group for ${local.environment}"
  vpc_id      = aws_vpc.main.id

  # HTTPS — always allowed
  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTP — only in non-production
  dynamic "ingress" {
    for_each = local.is_production ? [] : [1]
    content {
      description = "HTTP (non-production only)"
      from_port   = 80
      to_port     = 80
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
    }
  }

  # SSH — only in non-production
  dynamic "ingress" {
    for_each = local.is_production ? [] : [1]
    content {
      description = "SSH (non-production only)"
      from_port   = 22
      to_port     = 22
      protocol    = "tcp"
      cidr_blocks = var.allowed_ssh_cidrs
    }
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.all_tags, {
    Name = "${local.name_prefix}-web-sg"
  })
}

# ──────────────────────────────────────────────
# Internet Gateway
# ──────────────────────────────────────────────
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = merge(local.all_tags, {
    Name = "${local.name_prefix}-igw"
  })
}
```

Create `outputs.tf`:

```hcl
# outputs.tf

output "environment" {
  description = "Current environment (workspace)"
  value       = terraform.workspace
}

output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "vpc_cidr" {
  description = "VPC CIDR"
  value       = aws_vpc.main.cidr_block
}

output "instance_type" {
  description = "Resolved instance type for this environment"
  value       = local.resolved_instance_type
}

output "instance_count" {
  description = "Resolved instance count for this environment"
  value       = local.resolved_instance_count
}

output "is_production" {
  description = "Whether this is the production environment"
  value       = local.is_production
}

output "security_group_id" {
  description = "Web security group ID"
  value       = aws_security_group.web.id
}
```

### Step 2.3: Create Per-Environment tfvars Files

Create `dev.tfvars`:

```hcl
# dev.tfvars
instance_type      = "t2.micro"
instance_count     = 1
enable_monitoring  = false
allowed_ssh_cidrs  = ["0.0.0.0/0"]

extra_tags = {
  CostCenter = "development"
}
```

Create `staging.tfvars`:

```hcl
# staging.tfvars
instance_type      = "t2.small"
instance_count     = 2
enable_monitoring  = true
allowed_ssh_cidrs  = ["10.0.0.0/8"]

extra_tags = {
  CostCenter = "staging"
}
```

Create `prod.tfvars`:

```hcl
# prod.tfvars
instance_type      = "t2.medium"
instance_count     = 3
enable_monitoring  = true
allowed_ssh_cidrs  = []

extra_tags = {
  CostCenter = "production"
  Compliance = "SOC2"
  DataClass  = "confidential"
}
```

### Step 2.4: Work with Workspaces

```bash
# Initialize
terraform init

# List workspaces (only "default" exists)
terraform workspace list
```

**Expected Output:**

```
* default
```

```bash
# Create environment workspaces
terraform workspace new dev
terraform workspace new staging
terraform workspace new prod

# List all workspaces
terraform workspace list
```

**Expected Output:**

```
  default
  dev
  staging
* prod
```

### Step 2.5: Deploy the Dev Environment

```bash
# Switch to dev workspace
terraform workspace select dev

# Verify
terraform workspace show

# Plan with dev-specific tfvars
terraform plan -var-file="dev.tfvars"

# Apply
terraform apply -var-file="dev.tfvars" -auto-approve
```

Review the outputs:

```bash
terraform output
```

**Expected Output:**

```
environment     = "dev"
instance_count  = 1
instance_type   = "t2.micro"
is_production   = false
vpc_cidr        = "10.0.0.0/16"
vpc_id          = "vpc-..."
```

### Step 2.6: Deploy the Staging Environment

```bash
terraform workspace select staging
terraform apply -var-file="staging.tfvars" -auto-approve
terraform output
```

### Step 2.7: Compare Environments

```bash
# Quick comparison
for ws in dev staging; do
  echo "=== $ws ==="
  terraform workspace select $ws
  terraform output -json | python3 -m json.tool
  echo ""
done
```

### Step 2.8: Understand Workspace State

```bash
# Workspaces create separate state files
ls terraform.tfstate.d/
```

**Expected Output:**

```
dev/    prod/    staging/
```

Each workspace has its own `terraform.tfstate` inside its directory.

---

## Part 3: Approach B — Directory Structure

### Step 3.1: Set Up the Directory Structure

```bash
mkdir -p ~/terraform-labs/lab06/directory-structure/{modules/network,environments/{dev,staging,prod}}
cd ~/terraform-labs/lab06/directory-structure
```

### Step 3.2: Create the Shared Network Module

Create `modules/network/variables.tf`:

```hcl
# modules/network/variables.tf

variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "enable_ssh" {
  description = "Allow SSH access"
  type        = bool
  default     = false
}

variable "tags" {
  description = "Common tags"
  type        = map(string)
  default     = {}
}
```

Create `modules/network/main.tf`:

```hcl
# modules/network/main.tf

resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-vpc"
  })
}

resource "aws_subnet" "public" {
  vpc_id     = aws_vpc.this.id
  cidr_block = cidrsubnet(var.vpc_cidr, 8, 1)

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-public"
  })
}

resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-igw"
  })
}

resource "aws_security_group" "web" {
  name        = "${var.name_prefix}-web-sg"
  description = "Web SG for ${var.environment}"
  vpc_id      = aws_vpc.this.id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  dynamic "ingress" {
    for_each = var.enable_ssh ? [1] : []
    content {
      from_port   = 22
      to_port     = 22
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
    }
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-web-sg"
  })
}
```

Create `modules/network/outputs.tf`:

```hcl
# modules/network/outputs.tf

output "vpc_id" {
  value = aws_vpc.this.id
}

output "vpc_cidr" {
  value = aws_vpc.this.cidr_block
}

output "public_subnet_id" {
  value = aws_subnet.public.id
}

output "security_group_id" {
  value = aws_security_group.web.id
}
```

### Step 3.3: Create the Dev Environment

Create `environments/dev/main.tf`:

```hcl
# environments/dev/main.tf

terraform {
  required_version = ">= 1.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"

  default_tags {
    tags = {
      Project     = "devsecops"
      Environment = "dev"
      ManagedBy   = "terraform"
    }
  }
}

module "network" {
  source = "../../modules/network"

  name_prefix = "devsecops-dev"
  vpc_cidr    = "10.0.0.0/16"
  environment = "dev"
  enable_ssh  = true

  tags = {
    CostCenter = "development"
  }
}

output "vpc_id" {
  value = module.network.vpc_id
}

output "environment" {
  value = "dev"
}
```

### Step 3.4: Create the Staging Environment

Create `environments/staging/main.tf`:

```hcl
# environments/staging/main.tf

terraform {
  required_version = ">= 1.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"

  default_tags {
    tags = {
      Project     = "devsecops"
      Environment = "staging"
      ManagedBy   = "terraform"
    }
  }
}

module "network" {
  source = "../../modules/network"

  name_prefix = "devsecops-staging"
  vpc_cidr    = "10.1.0.0/16"
  environment = "staging"
  enable_ssh  = true  # SSH allowed in staging for debugging

  tags = {
    CostCenter = "staging"
  }
}

output "vpc_id" {
  value = module.network.vpc_id
}

output "environment" {
  value = "staging"
}
```

### Step 3.5: Create the Prod Environment

Create `environments/prod/main.tf`:

```hcl
# environments/prod/main.tf

terraform {
  required_version = ">= 1.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"

  default_tags {
    tags = {
      Project     = "devsecops"
      Environment = "prod"
      ManagedBy   = "terraform"
      Compliance  = "SOC2"
    }
  }
}

module "network" {
  source = "../../modules/network"

  name_prefix = "devsecops-prod"
  vpc_cidr    = "10.2.0.0/16"
  environment = "prod"
  enable_ssh  = false  # No SSH in production!

  tags = {
    CostCenter = "production"
    Compliance = "SOC2"
    DataClass  = "confidential"
  }
}

output "vpc_id" {
  value = module.network.vpc_id
}

output "environment" {
  value = "prod"
}
```

### Step 3.6: Deploy Each Environment Independently

```bash
# Deploy dev
cd ~/terraform-labs/lab06/directory-structure/environments/dev
terraform init
terraform apply -auto-approve

# Deploy staging
cd ~/terraform-labs/lab06/directory-structure/environments/staging
terraform init
terraform apply -auto-approve

# Each has completely isolated state
```

### Step 3.7: Compare the Environments

```bash
for env in dev staging; do
  echo "=== $env ==="
  cd ~/terraform-labs/lab06/directory-structure/environments/$env
  terraform output
  echo ""
done
```

---

## Part 4: CI/CD Integration Pattern

### Step 4.1: Makefile for Environment Management

Create a `Makefile` at the project root (for the directory structure approach):

```bash
cd ~/terraform-labs/lab06/directory-structure
```

Create `Makefile`:

```makefile
# Makefile — Multi-environment Terraform management

ENV ?= dev
DIR = environments/$(ENV)

.PHONY: init plan apply destroy output fmt validate

init:
	@echo "Initializing $(ENV)..."
	cd $(DIR) && terraform init

plan:
	@echo "Planning $(ENV)..."
	cd $(DIR) && terraform plan

apply:
	@echo "Applying $(ENV)..."
	cd $(DIR) && terraform apply -auto-approve

destroy:
	@echo "Destroying $(ENV)..."
	cd $(DIR) && terraform destroy -auto-approve

output:
	@echo "Outputs for $(ENV):"
	cd $(DIR) && terraform output

fmt:
	terraform fmt -recursive

validate:
	@for dir in environments/*/; do \
		echo "Validating $$dir..."; \
		cd $$dir && terraform validate && cd ../..; \
	done

# Deploy all environments in order
deploy-all: deploy-dev deploy-staging

deploy-dev:
	$(MAKE) apply ENV=dev

deploy-staging:
	$(MAKE) apply ENV=staging

# Destroy all environments in reverse order
destroy-all:
	$(MAKE) destroy ENV=staging
	$(MAKE) destroy ENV=dev
```

### Step 4.2: Use the Makefile

```bash
# Format all files
make fmt

# Plan dev
make plan ENV=dev

# Apply staging
make apply ENV=staging

# View outputs
make output ENV=dev
```

### Step 4.3: CI/CD Script Pattern

Create `scripts/deploy.sh`:

```bash
#!/bin/bash
# scripts/deploy.sh — CI/CD deployment script

set -euo pipefail

ENVIRONMENT=${1:?"Usage: $0 <environment>"}
VALID_ENVS=("dev" "staging" "prod")

# Validate environment
if [[ ! " ${VALID_ENVS[*]} " =~ " ${ENVIRONMENT} " ]]; then
  echo "ERROR: Invalid environment '$ENVIRONMENT'. Valid: ${VALID_ENVS[*]}"
  exit 1
fi

ENV_DIR="environments/${ENVIRONMENT}"

echo "========================================="
echo "Deploying: ${ENVIRONMENT}"
echo "Directory: ${ENV_DIR}"
echo "========================================="

cd "${ENV_DIR}"

# Initialize
echo "--- terraform init ---"
terraform init -input=false

# Plan
echo "--- terraform plan ---"
terraform plan -input=false -out=tfplan

# Apply (in CI/CD, you might add an approval gate here)
if [[ "${ENVIRONMENT}" == "prod" ]]; then
  echo ""
  echo "PRODUCTION DEPLOYMENT — Requires manual approval"
  echo "Run: terraform apply tfplan"
  echo ""
else
  echo "--- terraform apply ---"
  terraform apply -input=false tfplan
fi

# Show outputs
echo "--- outputs ---"
terraform output

echo "========================================="
echo "Deployment complete: ${ENVIRONMENT}"
echo "========================================="
```

```bash
chmod +x scripts/deploy.sh
```

---

## Part 5: Environment Promotion Workflow

### The Ideal DevSecOps Promotion Flow

```
Code Change → Dev → Security Scan → Staging → Integration Tests → Prod
     ↓          ↓         ↓             ↓            ↓              ↓
  PR Review   Apply    tfsec/         Apply      Automated        Apply
              auto     checkov        auto       tests          manual
                                                                approval
```

### Step 5.1: Simulate a Promotion

```bash
# 1. Make a change in dev
cd ~/terraform-labs/lab06/directory-structure/environments/dev
# (Edit main.tf to add a tag, for example)

# 2. Apply to dev
terraform apply -auto-approve

# 3. If successful, apply the same change to staging
cd ~/terraform-labs/lab06/directory-structure/environments/staging
# (Apply the same edit)
terraform apply -auto-approve

# 4. Production requires manual approval
cd ~/terraform-labs/lab06/directory-structure/environments/prod
terraform plan
# Review carefully, then:
# terraform apply
```

---

## Expected Outcomes

After completing this lab, you should have:

- [x] Created and managed Terraform workspaces (dev, staging, prod)
- [x] Used `terraform.workspace` to drive environment-specific behavior
- [x] Created a directory-based multi-environment setup
- [x] Written per-environment `.tfvars` files
- [x] Used lookup maps for environment-specific values
- [x] Understood workspace state isolation (`terraform.tfstate.d/`)
- [x] Created a Makefile and CI/CD script for environment management
- [x] Understood the trade-offs between workspaces and directory structures

---

## Decision Matrix

| Factor | Workspaces | Directory Structure |
|--------|-----------|-------------------|
| Code duplication | None | Minimal (in root configs) |
| State isolation | Same backend, different paths | Completely separate |
| Blast radius | Shared lock file | Fully independent |
| Complexity | Lower | Higher |
| Team scalability | Limited | Better |
| CI/CD integration | Requires workspace switch | Natural directory mapping |
| Provider versioning | Shared | Independent |
| **Recommendation** | Small teams, similar envs | **Production workloads** |

---

## Bonus Challenges

### Challenge 1: Workspace + Remote State

Configure the workspace approach to use an S3 backend. Observe how Terraform creates different state paths per workspace:

```
s3://bucket/env:/dev/terraform.tfstate
s3://bucket/env:/staging/terraform.tfstate
s3://bucket/env:/prod/terraform.tfstate
```

### Challenge 2: Terragrunt

Research [Terragrunt](https://terragrunt.gruntwork.io/) as an alternative for managing multiple environments. Write a `terragrunt.hcl` that achieves the same result as the directory structure approach with less duplication.

### Challenge 3: Feature Flags

Add a `feature_flags` variable (map of bools) that toggles experimental features per environment:

```hcl
variable "feature_flags" {
  type = map(bool)
  default = {
    new_dashboard = false
    api_v2        = false
    canary_deploy = false
  }
}
```

Use it to conditionally create resources.

### Challenge 4: Cross-Environment References

In the directory-structure approach, have the staging environment read the dev VPC ID from remote state using `terraform_remote_state`. This simulates VPC peering between environments.

---

## Cleanup

**Workspaces approach:**

```bash
cd ~/terraform-labs/lab06/workspaces

for ws in dev staging; do
  terraform workspace select $ws
  terraform destroy -auto-approve
done

terraform workspace select default
```

**Directory structure approach:**

```bash
for env in staging dev; do
  cd ~/terraform-labs/lab06/directory-structure/environments/$env
  terraform destroy -auto-approve
done
```

```bash
cd ~
rm -rf ~/terraform-labs/lab06
```

---

## Next Lab

Proceed to [Lab 07: Terraform Import](lab07-terraform-import.md) to learn how to bring existing cloud resources under Terraform management.
