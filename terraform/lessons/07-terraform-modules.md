# Lesson 7: Terraform Modules

---

## Table of Contents

1. [What Are Modules?](#what-are-modules)
2. [Root Module vs. Child Modules](#root-module-vs-child-modules)
3. [Creating Your First Module](#creating-your-first-module)
4. [Module Sources](#module-sources)
5. [Module Versioning](#module-versioning)
6. [The Terraform Registry](#the-terraform-registry)
7. [Module Composition Patterns](#module-composition-patterns)
8. [Module Best Practices](#module-best-practices)
9. [Key Takeaways](#key-takeaways)

---

## What Are Modules?

A **module** is a container for multiple Terraform resources that are used together. Every Terraform configuration is at least one module (the root module). Modules let you:

- **Organize** code into logical groups
- **Reuse** common infrastructure patterns
- **Encapsulate** complexity behind simple interfaces
- **Enforce standards** across teams

Think of modules like functions in programming -- they take inputs (variables), create resources, and return outputs.

### Without Modules (Monolithic)

```
project/
└── main.tf          # 500+ lines of VPC, subnets, security groups,
                     # EC2 instances, RDS, load balancers, IAM...
```

### With Modules (Organized)

```
project/
├── main.tf          # Calls modules
├── variables.tf     # Root variables
├── outputs.tf       # Root outputs
└── modules/
    ├── networking/   # VPC, subnets, route tables
    ├── compute/      # EC2 instances, auto-scaling
    ├── database/     # RDS, ElastiCache
    └── security/     # IAM roles, security groups
```

---

## Root Module vs. Child Modules

### Root Module

The root module is the directory where you run `terraform apply`. It is the entry point of your configuration.

```
my-project/          # <-- This is the root module
├── main.tf
├── variables.tf
├── outputs.tf
└── terraform.tfvars
```

### Child Modules

Child modules are modules called by the root module (or by other modules):

```hcl
# Root module's main.tf
module "vpc" {                    # "vpc" is a child module
  source = "./modules/networking"
  # ...
}

module "web_servers" {            # "web_servers" is a child module
  source = "./modules/compute"
  # ...
}
```

### Module Nesting

Modules can call other modules:

```
root module
├── module "vpc" (child)
│   └── module "subnets" (grandchild)
├── module "web" (child)
│   ├── module "ec2" (grandchild)
│   └── module "alb" (grandchild)
└── module "database" (child)
```

> **Best Practice**: Avoid deep nesting (more than 3 levels). It becomes hard to understand and debug.

---

## Creating Your First Module

### Module Structure

A module is simply a directory containing `.tf` files:

```
modules/
└── vpc/
    ├── main.tf        # Resources
    ├── variables.tf   # Input variables
    ├── outputs.tf     # Output values
    └── README.md      # Documentation
```

### Step 1: Define the Module

```hcl
# modules/vpc/variables.tf
variable "vpc_name" {
  type        = string
  description = "Name of the VPC"
}

variable "vpc_cidr" {
  type        = string
  description = "CIDR block for the VPC"
  default     = "10.0.0.0/16"
}

variable "public_subnets" {
  type        = list(string)
  description = "List of public subnet CIDR blocks"
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnets" {
  type        = list(string)
  description = "List of private subnet CIDR blocks"
  default     = ["10.0.101.0/24", "10.0.102.0/24"]
}

variable "availability_zones" {
  type        = list(string)
  description = "Availability zones"
}

variable "environment" {
  type        = string
  description = "Environment name"
}

variable "tags" {
  type        = map(string)
  description = "Additional tags"
  default     = {}
}
```

```hcl
# modules/vpc/main.tf
locals {
  common_tags = merge(var.tags, {
    Module      = "vpc"
    Environment = var.environment
    ManagedBy   = "Terraform"
  })
}

resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(local.common_tags, {
    Name = var.vpc_name
  })
}

resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id

  tags = merge(local.common_tags, {
    Name = "${var.vpc_name}-igw"
  })
}

resource "aws_subnet" "public" {
  count = length(var.public_subnets)

  vpc_id                  = aws_vpc.this.id
  cidr_block              = var.public_subnets[count.index]
  availability_zone       = var.availability_zones[count.index % length(var.availability_zones)]
  map_public_ip_on_launch = true

  tags = merge(local.common_tags, {
    Name = "${var.vpc_name}-public-${count.index + 1}"
    Tier = "public"
  })
}

resource "aws_subnet" "private" {
  count = length(var.private_subnets)

  vpc_id            = aws_vpc.this.id
  cidr_block        = var.private_subnets[count.index]
  availability_zone = var.availability_zones[count.index % length(var.availability_zones)]

  tags = merge(local.common_tags, {
    Name = "${var.vpc_name}-private-${count.index + 1}"
    Tier = "private"
  })
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.this.id
  }

  tags = merge(local.common_tags, {
    Name = "${var.vpc_name}-public-rt"
  })
}

resource "aws_route_table_association" "public" {
  count = length(var.public_subnets)

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}
```

```hcl
# modules/vpc/outputs.tf
output "vpc_id" {
  value       = aws_vpc.this.id
  description = "The ID of the VPC"
}

output "vpc_cidr_block" {
  value       = aws_vpc.this.cidr_block
  description = "The CIDR block of the VPC"
}

output "public_subnet_ids" {
  value       = aws_subnet.public[*].id
  description = "List of public subnet IDs"
}

output "private_subnet_ids" {
  value       = aws_subnet.private[*].id
  description = "List of private subnet IDs"
}

output "internet_gateway_id" {
  value       = aws_internet_gateway.this.id
  description = "The ID of the Internet Gateway"
}
```

### Step 2: Call the Module

```hcl
# main.tf (root module)
module "vpc" {
  source = "./modules/vpc"

  vpc_name           = "production-vpc"
  vpc_cidr           = "10.0.0.0/16"
  public_subnets     = ["10.0.1.0/24", "10.0.2.0/24"]
  private_subnets    = ["10.0.101.0/24", "10.0.102.0/24"]
  availability_zones = ["us-east-1a", "us-east-1b"]
  environment        = "production"

  tags = {
    Project = "MyApp"
    Team    = "Platform"
  }
}

# Use module outputs
resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.micro"
  subnet_id     = module.vpc.public_subnet_ids[0]  # Reference module output

  tags = {
    Name = "web-server"
  }
}

# Root outputs
output "vpc_id" {
  value = module.vpc.vpc_id
}
```

### Step 3: Initialize and Apply

```bash
# Download module (even local modules need init)
terraform init

# Plan and apply
terraform plan
terraform apply
```

---

## Module Sources

Modules can be loaded from various sources:

### Local Paths

```hcl
module "vpc" {
  source = "./modules/vpc"           # Relative path
}

module "vpc" {
  source = "/opt/terraform/modules/vpc"  # Absolute path
}
```

### Terraform Registry

```hcl
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.5.1"

  name = "my-vpc"
  cidr = "10.0.0.0/16"
  # ...
}
```

### GitHub

```hcl
# HTTPS
module "vpc" {
  source = "github.com/terraform-aws-modules/terraform-aws-vpc"
}

# SSH
module "vpc" {
  source = "git@github.com:terraform-aws-modules/terraform-aws-vpc.git"
}

# Specific branch or tag
module "vpc" {
  source = "github.com/terraform-aws-modules/terraform-aws-vpc?ref=v5.5.1"
}

# Subdirectory
module "subnet" {
  source = "github.com/my-org/terraform-modules//modules/subnet?ref=main"
}
```

### Generic Git

```hcl
module "vpc" {
  source = "git::https://example.com/modules.git//vpc?ref=v1.0.0"
}

module "vpc" {
  source = "git::ssh://git@example.com/modules.git//vpc?ref=v1.0.0"
}
```

### S3 Bucket

```hcl
module "vpc" {
  source = "s3::https://s3-eu-west-1.amazonaws.com/my-modules/vpc.zip"
}
```

### HTTP URLs

```hcl
module "vpc" {
  source = "https://example.com/modules/vpc.zip"
}
```

---

## Module Versioning

### Registry Modules

```hcl
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.5.1"       # Exact version
}

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"      # Any 5.x version
}

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = ">= 5.0, < 6.0"  # Range
}
```

### Git-Based Modules

Use `ref` to pin a specific version:

```hcl
# Pin to a tag (recommended)
module "vpc" {
  source = "git::https://github.com/my-org/modules.git//vpc?ref=v1.2.3"
}

# Pin to a commit SHA (most precise)
module "vpc" {
  source = "git::https://github.com/my-org/modules.git//vpc?ref=abc1234"
}

# Pin to a branch (not recommended for production)
module "vpc" {
  source = "git::https://github.com/my-org/modules.git//vpc?ref=main"
}
```

> **Best Practice**: Always pin module versions. Use semantic versioning tags for Git modules.

---

## The Terraform Registry

The [Terraform Registry](https://registry.terraform.io/) hosts thousands of pre-built modules.

### Popular AWS Modules

| Module | Source | Description |
|--------|--------|-------------|
| VPC | `terraform-aws-modules/vpc/aws` | Complete VPC with subnets, NAT, etc. |
| EKS | `terraform-aws-modules/eks/aws` | Managed Kubernetes cluster |
| RDS | `terraform-aws-modules/rds/aws` | Relational Database Service |
| S3 | `terraform-aws-modules/s3-bucket/aws` | S3 bucket with best practices |
| ALB | `terraform-aws-modules/alb/aws` | Application Load Balancer |
| Security Group | `terraform-aws-modules/security-group/aws` | Security groups with common rules |

### Using a Registry Module

```hcl
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.5.1"

  name = "my-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["us-east-1a", "us-east-1b", "us-east-1c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway   = true
  single_nat_gateway   = true
  enable_dns_hostnames = true

  tags = {
    Environment = "production"
    Terraform   = "true"
  }
}

module "web_server_sg" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "5.1.0"

  name        = "web-server-sg"
  description = "Security group for web servers"
  vpc_id      = module.vpc.vpc_id

  ingress_with_cidr_blocks = [
    {
      from_port   = 80
      to_port     = 80
      protocol    = "tcp"
      description = "HTTP"
      cidr_blocks = "0.0.0.0/0"
    },
    {
      from_port   = 443
      to_port     = 443
      protocol    = "tcp"
      description = "HTTPS"
      cidr_blocks = "0.0.0.0/0"
    },
  ]

  egress_with_cidr_blocks = [
    {
      from_port   = 0
      to_port     = 0
      protocol    = "-1"
      cidr_blocks = "0.0.0.0/0"
    },
  ]
}
```

### Publishing a Module to the Registry

To publish a module, your GitHub repository must:

1. Be named `terraform-<PROVIDER>-<NAME>` (e.g., `terraform-aws-vpc`)
2. Have a `README.md`
3. Use semantic versioning tags (e.g., `v1.0.0`)
4. Follow the standard module structure

```
terraform-aws-my-module/
├── README.md
├── main.tf
├── variables.tf
├── outputs.tf
├── versions.tf
├── examples/
│   ├── simple/
│   │   └── main.tf
│   └── complete/
│       └── main.tf
└── modules/
    └── submodule/
        ├── main.tf
        ├── variables.tf
        └── outputs.tf
```

---

## Module Composition Patterns

### Pattern 1: Flat Modules

Each module is independent and called directly from the root:

```hcl
module "vpc" {
  source = "./modules/vpc"
  # ...
}

module "security" {
  source = "./modules/security"
  vpc_id = module.vpc.vpc_id
}

module "compute" {
  source     = "./modules/compute"
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.public_subnet_ids
  sg_ids     = [module.security.web_sg_id]
}

module "database" {
  source     = "./modules/database"
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnet_ids
  sg_ids     = [module.security.db_sg_id]
}
```

### Pattern 2: Wrapper Module (Application Stack)

A single module that composes multiple sub-modules:

```hcl
# modules/app-stack/main.tf
module "vpc" {
  source = "../vpc"
  # ...
}

module "compute" {
  source     = "../compute"
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.public_subnet_ids
}

module "database" {
  source     = "../database"
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnet_ids
}
```

```hcl
# root main.tf
module "production" {
  source      = "./modules/app-stack"
  environment = "production"
  # ...
}
```

### Pattern 3: Multi-Environment with Modules

```hcl
# environments/dev/main.tf
module "app" {
  source = "../../modules/app-stack"

  environment    = "dev"
  instance_type  = "t3.micro"
  instance_count = 1
  db_class       = "db.t3.micro"
}

# environments/prod/main.tf
module "app" {
  source = "../../modules/app-stack"

  environment    = "prod"
  instance_type  = "t3.large"
  instance_count = 3
  db_class       = "db.r5.large"
}
```

```
project/
├── modules/
│   └── app-stack/
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
└── environments/
    ├── dev/
    │   ├── main.tf
    │   ├── backend.tf
    │   └── terraform.tfvars
    ├── staging/
    │   ├── main.tf
    │   ├── backend.tf
    │   └── terraform.tfvars
    └── prod/
        ├── main.tf
        ├── backend.tf
        └── terraform.tfvars
```

---

## Module Best Practices

### 1. Keep Modules Focused

Each module should do **one thing well**:

```
# Good: Focused modules
modules/
├── vpc/          # Just VPC, subnets, route tables
├── security/     # Just security groups, NACLs
├── compute/      # Just EC2, ASG, launch templates
└── database/     # Just RDS, parameter groups

# Bad: Kitchen-sink module
modules/
└── everything/   # VPC + EC2 + RDS + IAM + ... (too much)
```

### 2. Use Standard File Names

```
module/
├── main.tf          # Primary resources
├── variables.tf     # All input variables
├── outputs.tf       # All outputs
├── versions.tf      # Provider and Terraform version requirements
├── locals.tf        # Local values (if needed)
├── data.tf          # Data sources (if needed)
└── README.md        # Documentation
```

### 3. Document Your Modules

Include a clear README:

```markdown
# VPC Module

Creates a VPC with public and private subnets across multiple AZs.

## Usage

​```hcl
module "vpc" {
  source = "./modules/vpc"

  vpc_name           = "my-vpc"
  vpc_cidr           = "10.0.0.0/16"
  availability_zones = ["us-east-1a", "us-east-1b"]
}
​```

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|----------|
| vpc_name | Name of the VPC | string | - | yes |
| vpc_cidr | CIDR block | string | "10.0.0.0/16" | no |

## Outputs

| Name | Description |
|------|-------------|
| vpc_id | The VPC ID |
| public_subnet_ids | List of public subnet IDs |
```

You can auto-generate documentation with `terraform-docs`:

```bash
# Install terraform-docs
brew install terraform-docs

# Generate README
terraform-docs markdown table ./modules/vpc > ./modules/vpc/README.md
```

### 4. Use `terraform-docs` for Automated Documentation

```bash
# Generate markdown table from a module
terraform-docs markdown table ./modules/vpc/

# Output:
# | Name | Description | Type | Default | Required |
# |------|-------------|------|---------|----------|
# | vpc_name | Name of the VPC | `string` | n/a | yes |
# ...
```

### 5. Include Examples

```
modules/vpc/
├── main.tf
├── variables.tf
├── outputs.tf
└── examples/
    ├── simple/
    │   └── main.tf      # Minimal usage example
    └── complete/
        └── main.tf      # Full-featured example
```

### 6. Expose Only What's Needed

Only output values that consumers actually need:

```hcl
# Good: Specific outputs
output "vpc_id" {
  value = aws_vpc.this.id
}

output "public_subnet_ids" {
  value = aws_subnet.public[*].id
}

# Avoid: Exposing entire resources
# output "vpc" {
#   value = aws_vpc.this  # Exposes everything, including potentially sensitive data
# }
```

### 7. Validate Inputs

```hcl
variable "environment" {
  type = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}
```

### 8. Pin Provider Versions in Modules

```hcl
# modules/vpc/versions.tf
terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"  # Minimum version, let root module pin exact
    }
  }
}
```

---

## Key Takeaways

1. **Modules are the building blocks** of reusable Terraform configurations
2. **Every Terraform directory is a module** -- the one you run `apply` in is the root module
3. **Keep modules focused** -- each module should handle one concern (networking, compute, etc.)
4. **Always version your modules** -- pin exact versions for registry, use Git tags for custom modules
5. **The Terraform Registry** provides battle-tested modules for common infrastructure patterns
6. **Use standard file names** (`main.tf`, `variables.tf`, `outputs.tf`) for consistency
7. **Document your modules** with READMEs and examples; use `terraform-docs` for automation
8. **Expose only necessary outputs** to maintain clean interfaces between modules
9. **Validate inputs** in modules to catch errors early
10. **Avoid deep nesting** -- keep module hierarchies shallow and understandable

---

## What's Next?

In the next lesson, we will explore Terraform expressions and functions -- the tools for data manipulation and logic in your configurations.

[Previous Lesson: Terraform State](./06-terraform-state.md) | [Next Lesson: Terraform Expressions -->](./08-terraform-expressions.md)
