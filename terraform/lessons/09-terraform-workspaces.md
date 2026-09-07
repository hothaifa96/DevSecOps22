# Lesson 9: Terraform Workspaces

---

## Table of Contents

1. [What Are Workspaces?](#what-are-workspaces)
2. [Workspace Commands](#workspace-commands)
3. [Using Workspaces for Environments](#using-workspaces-for-environments)
4. [Workspace-Aware Configurations](#workspace-aware-configurations)
5. [Remote Backend Workspaces](#remote-backend-workspaces)
6. [When to Use Workspaces](#when-to-use-workspaces)
7. [When NOT to Use Workspaces](#when-not-to-use-workspaces)
8. [Alternatives to Workspaces](#alternatives-to-workspaces)
9. [Key Takeaways](#key-takeaways)

---

## What Are Workspaces?

Terraform **workspaces** allow you to manage multiple independent instances of state from a single configuration directory. Each workspace has its own state file, so the same infrastructure code can manage completely separate sets of resources.

### How Workspaces Work

```
Same Configuration (.tf files)
         │
    ┌────┴─────┐
    │ Workspace │
    └────┬─────┘
         │
    ┌────┴────────────────────────┐
    │                             │
┌───▼───┐  ┌───────┐  ┌─────────┐
│  dev  │  │staging│  │  prod   │
│ state │  │ state │  │  state  │
└───┬───┘  └───┬───┘  └────┬────┘
    │          │            │
┌───▼───┐  ┌──▼────┐  ┌───▼─────┐
│Dev    │  │Staging│  │Prod     │
│Infra  │  │Infra  │  │Infra    │
└───────┘  └───────┘  └─────────┘
```

### Default Workspace

Every Terraform configuration starts with a single workspace called `default`. You have been using it all along without knowing it.

```bash
$ terraform workspace show
default
```

### State File Location

```
# Local state with workspaces:
project/
├── main.tf
├── terraform.tfstate           # "default" workspace state
└── terraform.tfstate.d/
    ├── dev/
    │   └── terraform.tfstate   # "dev" workspace state
    ├── staging/
    │   └── terraform.tfstate   # "staging" workspace state
    └── prod/
        └── terraform.tfstate   # "prod" workspace state

# S3 backend with workspaces:
# s3://my-bucket/env:/dev/terraform.tfstate
# s3://my-bucket/env:/staging/terraform.tfstate
# s3://my-bucket/env:/prod/terraform.tfstate
```

---

## Workspace Commands

### Create a New Workspace

```bash
$ terraform workspace new dev
Created and switched to workspace "dev"!

$ terraform workspace new staging
Created and switched to workspace "staging"!

$ terraform workspace new prod
Created and switched to workspace "prod"!
```

### List All Workspaces

```bash
$ terraform workspace list
  default
  dev
* staging    # Asterisk (*) marks the current workspace
  prod
```

### Switch Workspaces

```bash
$ terraform workspace select dev
Switched to workspace "dev".

$ terraform workspace select prod
Switched to workspace "prod".
```

### Show Current Workspace

```bash
$ terraform workspace show
prod
```

### Delete a Workspace

```bash
# Must switch away from the workspace first
$ terraform workspace select default

# Can only delete an empty workspace (no resources in state)
$ terraform workspace delete dev
Deleted workspace "dev"!

# Force delete (even if state has resources -- DANGEROUS)
$ terraform workspace delete -force staging
```

---

## Using Workspaces for Environments

### Basic Environment Setup

```hcl
# variables.tf
variable "instance_types" {
  type = map(string)
  default = {
    default = "t3.micro"
    dev     = "t3.micro"
    staging = "t3.small"
    prod    = "t3.large"
  }
}

variable "instance_counts" {
  type = map(number)
  default = {
    default = 1
    dev     = 1
    staging = 2
    prod    = 3
  }
}
```

```hcl
# main.tf
provider "aws" {
  region = "us-east-1"
}

locals {
  environment    = terraform.workspace
  instance_type  = lookup(var.instance_types, terraform.workspace, "t3.micro")
  instance_count = lookup(var.instance_counts, terraform.workspace, 1)

  common_tags = {
    Environment = local.environment
    ManagedBy   = "Terraform"
    Workspace   = terraform.workspace
  }
}

resource "aws_instance" "web" {
  count = local.instance_count

  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = local.instance_type

  tags = merge(local.common_tags, {
    Name = "web-${local.environment}-${count.index + 1}"
  })
}

output "instance_ips" {
  value = aws_instance.web[*].public_ip
}
```

### Deploy to Multiple Environments

```bash
# Deploy to dev
terraform workspace select dev
terraform plan      # Shows: 1 x t3.micro instance
terraform apply

# Deploy to staging
terraform workspace select staging
terraform plan      # Shows: 2 x t3.small instances
terraform apply

# Deploy to production
terraform workspace select prod
terraform plan      # Shows: 3 x t3.large instances
terraform apply
```

---

## Workspace-Aware Configurations

### Using `terraform.workspace`

The `terraform.workspace` variable returns the current workspace name:

```hcl
locals {
  environment = terraform.workspace
}

# Use in resource names
resource "aws_s3_bucket" "data" {
  bucket = "myapp-data-${terraform.workspace}"
  # Creates: myapp-data-dev, myapp-data-staging, myapp-data-prod
}

# Use in tags
resource "aws_instance" "web" {
  tags = {
    Environment = terraform.workspace
  }
}
```

### Conditional Logic Based on Workspace

```hcl
locals {
  is_prod = terraform.workspace == "prod"
}

# Enable features only in production
resource "aws_cloudwatch_metric_alarm" "cpu" {
  count = local.is_prod ? 1 : 0

  alarm_name          = "high-cpu-${terraform.workspace}"
  comparison_operator = "GreaterThanThreshold"
  threshold           = 80
  # ...
}

# Different CIDR blocks per environment
locals {
  vpc_cidrs = {
    dev     = "10.0.0.0/16"
    staging = "10.1.0.0/16"
    prod    = "10.2.0.0/16"
  }
  vpc_cidr = lookup(local.vpc_cidrs, terraform.workspace, "10.99.0.0/16")
}

resource "aws_vpc" "main" {
  cidr_block = local.vpc_cidr
}
```

### Workspace-Specific Variable Files

```bash
# Use workspace name to select tfvars file
terraform plan -var-file="environments/${terraform.workspace}.tfvars"

# Or in a Makefile / script:
ENV=$(terraform workspace show)
terraform apply -var-file="environments/${ENV}.tfvars"
```

### Backend Configuration with Workspaces

```hcl
terraform {
  backend "s3" {
    bucket         = "my-terraform-state"
    key            = "myapp/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-locks"
    encrypt        = true

    # Workspaces are stored as:
    # s3://my-terraform-state/env:/dev/myapp/terraform.tfstate
    # s3://my-terraform-state/env:/staging/myapp/terraform.tfstate
    # s3://my-terraform-state/env:/prod/myapp/terraform.tfstate

    # Use workspace_key_prefix to customize the prefix
    workspace_key_prefix = "environments"
    # s3://my-terraform-state/environments/dev/myapp/terraform.tfstate
  }
}
```

---

## Remote Backend Workspaces

### Terraform Cloud Workspaces

Terraform Cloud has its own workspace concept that differs from CLI workspaces:

```hcl
terraform {
  cloud {
    organization = "my-org"

    # Option 1: Single workspace
    workspaces {
      name = "my-app-prod"
    }

    # Option 2: Workspace by tags (select at runtime)
    workspaces {
      tags = ["my-app"]
    }

    # Option 3: Workspace by prefix
    workspaces {
      project = "my-project"
    }
  }
}
```

### Terraform Cloud vs. CLI Workspaces

| Feature | CLI Workspaces | Terraform Cloud Workspaces |
|---------|---------------|---------------------------|
| **State storage** | Same backend, different keys | Separate workspaces with own state |
| **Variables** | Shared (same .tf files) | Each workspace has own variables |
| **Access control** | None | Role-based access (RBAC) |
| **Run history** | None | Full run history and audit log |
| **Notifications** | None | Slack, email, webhooks |
| **Policy checks** | None | Sentinel policies |
| **Cost estimation** | None | Built-in cost estimation |

---

## When to Use Workspaces

### Good Use Cases

#### 1. Temporary Feature Environments

```bash
# Create a temporary environment for testing a feature
terraform workspace new feature-auth-redesign
terraform apply -var-file="environments/dev.tfvars"

# Test the feature...

# Clean up
terraform destroy
terraform workspace select default
terraform workspace delete feature-auth-redesign
```

#### 2. Developer Sandboxes

```bash
# Each developer gets their own workspace
terraform workspace new dev-alice
terraform workspace new dev-bob

# Alice's environment
terraform workspace select dev-alice
terraform apply
```

#### 3. Regional Deployments (Same Config, Different Regions)

```hcl
locals {
  regions = {
    us = "us-east-1"
    eu = "eu-west-1"
    ap = "ap-southeast-1"
  }
  region = lookup(local.regions, terraform.workspace, "us-east-1")
}

provider "aws" {
  region = local.region
}
```

#### 4. A/B Testing Infrastructure

```bash
terraform workspace new variant-a
terraform apply -var="feature_flags={new_ui=false}"

terraform workspace new variant-b
terraform apply -var="feature_flags={new_ui=true}"
```

---

## When NOT to Use Workspaces

### Bad Use Cases

#### 1. Dev vs. Production (When They Differ Significantly)

If dev and prod have very different configurations (different services, different architectures), workspaces are a poor fit because they share the same `.tf` files.

```
# Bad: Forcing very different environments into one config
# with lots of conditionals
count = terraform.workspace == "prod" ? 3 : 0  # Everywhere!
```

#### 2. Different AWS Accounts per Environment

Workspaces share the same provider configuration. If dev and prod use different AWS accounts, workspaces become awkward.

#### 3. When Teams Need Different Access Controls

Workspaces share the same backend and access permissions. You cannot give Dev team access to the `dev` workspace while restricting `prod` access.

#### 4. When State Isolation is Critical

A mistake in one workspace operation could theoretically affect another (e.g., accidentally running `terraform destroy` in the wrong workspace).

---

## Alternatives to Workspaces

### Alternative 1: Directory-Based Environments (Most Common)

Each environment is a separate directory with its own state:

```
project/
├── modules/              # Shared modules
│   ├── vpc/
│   ├── compute/
│   └── database/
├── environments/
│   ├── dev/
│   │   ├── main.tf       # Calls modules with dev settings
│   │   ├── backend.tf    # Dev state backend
│   │   ├── variables.tf
│   │   └── terraform.tfvars
│   ├── staging/
│   │   ├── main.tf
│   │   ├── backend.tf    # Staging state backend
│   │   ├── variables.tf
│   │   └── terraform.tfvars
│   └── prod/
│       ├── main.tf
│       ├── backend.tf    # Prod state backend (different account!)
│       ├── variables.tf
│       └── terraform.tfvars
```

```bash
# Deploy to dev
cd environments/dev
terraform init
terraform apply

# Deploy to prod (completely isolated)
cd environments/prod
terraform init
terraform apply
```

**Advantages:**
- Complete isolation between environments
- Different backends, providers, and access controls per environment
- Different modules or configurations per environment
- Impossible to accidentally destroy prod when working on dev

### Alternative 2: Terragrunt

[Terragrunt](https://terragrunt.gruntwork.io/) is a thin wrapper that provides DRY Terraform configurations:

```
project/
├── modules/
│   └── app/
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
├── terragrunt.hcl          # Root config (shared settings)
└── environments/
    ├── dev/
    │   └── terragrunt.hcl  # Inherits root, overrides for dev
    ├── staging/
    │   └── terragrunt.hcl
    └── prod/
        └── terragrunt.hcl
```

```hcl
# environments/dev/terragrunt.hcl
include "root" {
  path = find_in_parent_folders()
}

terraform {
  source = "../../modules/app"
}

inputs = {
  environment    = "dev"
  instance_type  = "t3.micro"
  instance_count = 1
}
```

```hcl
# environments/prod/terragrunt.hcl
include "root" {
  path = find_in_parent_folders()
}

terraform {
  source = "../../modules/app"
}

inputs = {
  environment    = "prod"
  instance_type  = "t3.large"
  instance_count = 3
}
```

```bash
# Deploy dev
cd environments/dev && terragrunt apply

# Deploy all environments
terragrunt run-all apply
```

### Alternative 3: Terraform Cloud Workspaces

Terraform Cloud workspaces provide true isolation with access controls, run history, and policy enforcement.

### Comparison

| Feature | CLI Workspaces | Directories | Terragrunt | TF Cloud |
|---------|---------------|-------------|------------|----------|
| **Isolation** | Partial (shared config) | Full | Full | Full |
| **Access control** | No | Yes (separate backends) | Yes | Yes (RBAC) |
| **DRY code** | Yes (one config) | No (duplicated) | Yes | Yes |
| **Complexity** | Low | Medium | Medium | Medium |
| **Blast radius** | Risky | Minimal | Minimal | Minimal |
| **Best for** | Small teams, sandboxes | Most teams | Large teams, many envs | Enterprise |

---

## Key Takeaways

1. **Workspaces provide separate state instances** from the same configuration
2. **`terraform.workspace`** gives you the current workspace name for conditional logic
3. **Workspaces are great for** temporary environments, developer sandboxes, and simple multi-env setups
4. **Workspaces are NOT ideal for** significantly different environments, multi-account setups, or when access control is needed
5. **Directory-based environments** are the most common pattern for production use -- they provide complete isolation
6. **Terragrunt** solves the DRY problem of directory-based environments
7. **Terraform Cloud workspaces** are different from CLI workspaces -- they provide true isolation with RBAC
8. **Always verify your workspace** before running `apply` or `destroy` -- `terraform workspace show`
9. **The default workspace** always exists and cannot be deleted

---

## What's Next?

In the next (and final) lesson, we will cover Terraform best practices for real-world projects, including directory structure, security, CI/CD integration, and policy as code.

[Previous Lesson: Terraform Expressions](./08-terraform-expressions.md) | [Next Lesson: Terraform Best Practices -->](./10-terraform-best-practices.md)
