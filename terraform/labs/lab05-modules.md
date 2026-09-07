# Lab 05: Terraform Modules

## Difficulty: Intermediate–Advanced

## Objectives

By the end of this lab, you will be able to:

- Understand the purpose and structure of Terraform modules
- Create a reusable VPC module with configurable inputs
- Use your custom module in multiple environments
- Pass outputs from one module as inputs to another
- Use public modules from the Terraform Registry
- Follow module best practices for structure and documentation

## Prerequisites

- Completed Labs 01–04
- AWS CLI configured
- Terraform v1.0+ installed
- Understanding of AWS VPC concepts (VPCs, subnets, route tables, Internet Gateways)

## Estimated Time

90 minutes

---

## Part 1: Understanding Modules

### What Is a Module?

A **module** is a container for multiple Terraform resources that are used together. Every Terraform configuration is technically a module (the "root module"). Child modules are reusable blocks you call from the root.

### Module Structure

```
modules/
└── vpc/
    ├── main.tf          # Resources
    ├── variables.tf     # Input variables
    ├── outputs.tf       # Output values
    └── README.md        # Documentation
```

### Why Use Modules?

| Benefit | Description |
|---------|-------------|
| **Reusability** | Write once, use across environments |
| **Consistency** | Same standards everywhere |
| **Abstraction** | Hide complexity behind a simple interface |
| **Testability** | Test modules independently |
| **Collaboration** | Teams share modules via registries |

---

## Part 2: Create a Reusable VPC Module

### Step 2.1: Set Up the Project Structure

```bash
mkdir -p ~/terraform-labs/lab05/{modules/vpc,modules/security-group,environments/dev,environments/prod}
cd ~/terraform-labs/lab05
```

Your directory layout will be:

```
lab05/
├── modules/
│   ├── vpc/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── security-group/
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
└── environments/
    ├── dev/
    │   ├── main.tf
    │   ├── variables.tf
    │   ├── outputs.tf
    │   └── terraform.tfvars
    └── prod/
        ├── main.tf
        ├── variables.tf
        ├── outputs.tf
        └── terraform.tfvars
```

### Step 2.2: Create the VPC Module — Variables

Create `modules/vpc/variables.tf`:

```hcl
# modules/vpc/variables.tf

variable "vpc_name" {
  description = "Name of the VPC"
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"

  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "Must be a valid CIDR block."
  }
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.10.0/24", "10.0.20.0/24"]
}

variable "availability_zones" {
  description = "Availability zones for subnets"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "enable_nat_gateway" {
  description = "Enable NAT Gateway for private subnets"
  type        = bool
  default     = false
}

variable "single_nat_gateway" {
  description = "Use a single NAT Gateway for all AZs (cost saving)"
  type        = bool
  default     = true
}

variable "enable_dns_hostnames" {
  description = "Enable DNS hostnames in the VPC"
  type        = bool
  default     = true
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "common_tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default     = {}
}
```

### Step 2.3: Create the VPC Module — Resources

Create `modules/vpc/main.tf`:

```hcl
# modules/vpc/main.tf

locals {
  # Merge common tags with module-specific tags
  tags = merge(var.common_tags, {
    Module      = "vpc"
    Environment = var.environment
  })
}

# ──────────────────────────────────────────────
# VPC
# ──────────────────────────────────────────────
resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = var.enable_dns_hostnames

  tags = merge(local.tags, {
    Name = var.vpc_name
  })
}

# ──────────────────────────────────────────────
# Internet Gateway
# ──────────────────────────────────────────────
resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id

  tags = merge(local.tags, {
    Name = "${var.vpc_name}-igw"
  })
}

# ──────────────────────────────────────────────
# Public Subnets
# ──────────────────────────────────────────────
resource "aws_subnet" "public" {
  count = length(var.public_subnet_cidrs)

  vpc_id                  = aws_vpc.this.id
  cidr_block              = var.public_subnet_cidrs[count.index]
  availability_zone       = var.availability_zones[count.index % length(var.availability_zones)]
  map_public_ip_on_launch = true

  tags = merge(local.tags, {
    Name = "${var.vpc_name}-public-${var.availability_zones[count.index % length(var.availability_zones)]}"
    Tier = "public"
  })
}

# ──────────────────────────────────────────────
# Private Subnets
# ──────────────────────────────────────────────
resource "aws_subnet" "private" {
  count = length(var.private_subnet_cidrs)

  vpc_id            = aws_vpc.this.id
  cidr_block        = var.private_subnet_cidrs[count.index]
  availability_zone = var.availability_zones[count.index % length(var.availability_zones)]

  tags = merge(local.tags, {
    Name = "${var.vpc_name}-private-${var.availability_zones[count.index % length(var.availability_zones)]}"
    Tier = "private"
  })
}

# ──────────────────────────────────────────────
# Public Route Table
# ──────────────────────────────────────────────
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.this.id
  }

  tags = merge(local.tags, {
    Name = "${var.vpc_name}-public-rt"
  })
}

resource "aws_route_table_association" "public" {
  count = length(var.public_subnet_cidrs)

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# ──────────────────────────────────────────────
# NAT Gateway (conditional)
# ──────────────────────────────────────────────
resource "aws_eip" "nat" {
  count  = var.enable_nat_gateway ? (var.single_nat_gateway ? 1 : length(var.public_subnet_cidrs)) : 0
  domain = "vpc"

  tags = merge(local.tags, {
    Name = "${var.vpc_name}-nat-eip-${count.index}"
  })
}

resource "aws_nat_gateway" "this" {
  count = var.enable_nat_gateway ? (var.single_nat_gateway ? 1 : length(var.public_subnet_cidrs)) : 0

  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  tags = merge(local.tags, {
    Name = "${var.vpc_name}-nat-${count.index}"
  })

  depends_on = [aws_internet_gateway.this]
}

# ──────────────────────────────────────────────
# Private Route Table
# ──────────────────────────────────────────────
resource "aws_route_table" "private" {
  count  = length(var.private_subnet_cidrs)
  vpc_id = aws_vpc.this.id

  tags = merge(local.tags, {
    Name = "${var.vpc_name}-private-rt-${count.index}"
  })
}

resource "aws_route" "private_nat" {
  count = var.enable_nat_gateway ? length(var.private_subnet_cidrs) : 0

  route_table_id         = aws_route_table.private[count.index].id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = var.single_nat_gateway ? aws_nat_gateway.this[0].id : aws_nat_gateway.this[count.index].id
}

resource "aws_route_table_association" "private" {
  count = length(var.private_subnet_cidrs)

  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}
```

### Step 2.4: Create the VPC Module — Outputs

Create `modules/vpc/outputs.tf`:

```hcl
# modules/vpc/outputs.tf

output "vpc_id" {
  description = "The ID of the VPC"
  value       = aws_vpc.this.id
}

output "vpc_cidr" {
  description = "The CIDR block of the VPC"
  value       = aws_vpc.this.cidr_block
}

output "public_subnet_ids" {
  description = "List of public subnet IDs"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "List of private subnet IDs"
  value       = aws_subnet.private[*].id
}

output "public_subnet_cidrs" {
  description = "List of public subnet CIDR blocks"
  value       = aws_subnet.public[*].cidr_block
}

output "private_subnet_cidrs" {
  description = "List of private subnet CIDR blocks"
  value       = aws_subnet.private[*].cidr_block
}

output "internet_gateway_id" {
  description = "The ID of the Internet Gateway"
  value       = aws_internet_gateway.this.id
}

output "nat_gateway_ids" {
  description = "List of NAT Gateway IDs"
  value       = aws_nat_gateway.this[*].id
}

output "public_route_table_id" {
  description = "The ID of the public route table"
  value       = aws_route_table.public.id
}

output "private_route_table_ids" {
  description = "List of private route table IDs"
  value       = aws_route_table.private[*].id
}
```

---

## Part 3: Create a Security Group Module

### Step 3.1: Security Group Module — Variables

Create `modules/security-group/variables.tf`:

```hcl
# modules/security-group/variables.tf

variable "name" {
  description = "Name of the security group"
  type        = string
}

variable "description" {
  description = "Description of the security group"
  type        = string
  default     = "Managed by Terraform"
}

variable "vpc_id" {
  description = "VPC ID where the security group will be created"
  type        = string
}

variable "ingress_rules" {
  description = "List of ingress rules"
  type = list(object({
    description     = string
    from_port       = number
    to_port         = number
    protocol        = string
    cidr_blocks     = optional(list(string), [])
    security_groups = optional(list(string), [])
  }))
  default = []
}

variable "egress_rules" {
  description = "List of egress rules"
  type = list(object({
    description = string
    from_port   = number
    to_port     = number
    protocol    = string
    cidr_blocks = list(string)
  }))
  default = [{
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }]
}

variable "tags" {
  description = "Tags to apply"
  type        = map(string)
  default     = {}
}
```

### Step 3.2: Security Group Module — Resources

Create `modules/security-group/main.tf`:

```hcl
# modules/security-group/main.tf

resource "aws_security_group" "this" {
  name        = var.name
  description = var.description
  vpc_id      = var.vpc_id

  tags = merge(var.tags, {
    Name = var.name
  })
}

resource "aws_security_group_rule" "ingress" {
  count = length(var.ingress_rules)

  type              = "ingress"
  security_group_id = aws_security_group.this.id
  description       = var.ingress_rules[count.index].description
  from_port         = var.ingress_rules[count.index].from_port
  to_port           = var.ingress_rules[count.index].to_port
  protocol          = var.ingress_rules[count.index].protocol
  cidr_blocks       = length(var.ingress_rules[count.index].cidr_blocks) > 0 ? var.ingress_rules[count.index].cidr_blocks : null
  source_security_group_id = length(var.ingress_rules[count.index].security_groups) > 0 ? var.ingress_rules[count.index].security_groups[0] : null
}

resource "aws_security_group_rule" "egress" {
  count = length(var.egress_rules)

  type              = "egress"
  security_group_id = aws_security_group.this.id
  description       = var.egress_rules[count.index].description
  from_port         = var.egress_rules[count.index].from_port
  to_port           = var.egress_rules[count.index].to_port
  protocol          = var.egress_rules[count.index].protocol
  cidr_blocks       = var.egress_rules[count.index].cidr_blocks
}
```

### Step 3.3: Security Group Module — Outputs

Create `modules/security-group/outputs.tf`:

```hcl
# modules/security-group/outputs.tf

output "security_group_id" {
  description = "The ID of the security group"
  value       = aws_security_group.this.id
}

output "security_group_arn" {
  description = "The ARN of the security group"
  value       = aws_security_group.this.arn
}

output "security_group_name" {
  description = "The name of the security group"
  value       = aws_security_group.this.name
}
```

---

## Part 4: Use Modules in the Dev Environment

### Step 4.1: Dev Environment Variables

Create `environments/dev/variables.tf`:

```hcl
# environments/dev/variables.tf

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "devsecops"
}
```

### Step 4.2: Dev Environment Main Configuration

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
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

locals {
  name_prefix = "${var.project_name}-${var.environment}"
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

# ──────────────────────────────────────────────
# VPC Module
# ──────────────────────────────────────────────
module "vpc" {
  source = "../../modules/vpc"

  vpc_name             = "${local.name_prefix}-vpc"
  vpc_cidr             = "10.0.0.0/16"
  public_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24"]
  private_subnet_cidrs = ["10.0.10.0/24", "10.0.20.0/24"]
  availability_zones   = ["${var.aws_region}a", "${var.aws_region}b"]
  enable_nat_gateway   = false  # Save costs in dev
  environment          = var.environment
  common_tags          = local.common_tags
}

# ──────────────────────────────────────────────
# Web Security Group Module
# Uses the VPC ID output from the VPC module
# ──────────────────────────────────────────────
module "web_sg" {
  source = "../../modules/security-group"

  name        = "${local.name_prefix}-web-sg"
  description = "Web server security group"
  vpc_id      = module.vpc.vpc_id  # Output from VPC module!

  ingress_rules = [
    {
      description = "HTTP"
      from_port   = 80
      to_port     = 80
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
    },
    {
      description = "HTTPS"
      from_port   = 443
      to_port     = 443
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
    },
    {
      description = "SSH"
      from_port   = 22
      to_port     = 22
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]  # Restrict in production!
    }
  ]

  tags = local.common_tags
}

# ──────────────────────────────────────────────
# Database Security Group Module
# Uses outputs from both VPC and Web SG modules
# ──────────────────────────────────────────────
module "db_sg" {
  source = "../../modules/security-group"

  name        = "${local.name_prefix}-db-sg"
  description = "Database security group"
  vpc_id      = module.vpc.vpc_id  # Output from VPC module!

  ingress_rules = [
    {
      description     = "PostgreSQL from web servers"
      from_port       = 5432
      to_port         = 5432
      protocol        = "tcp"
      security_groups = [module.web_sg.security_group_id]  # Output from Web SG module!
    }
  ]

  tags = local.common_tags
}
```

### Step 4.3: Dev Environment Outputs

Create `environments/dev/outputs.tf`:

```hcl
# environments/dev/outputs.tf

# ── VPC Outputs ───────────────────────────
output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "vpc_cidr" {
  description = "VPC CIDR block"
  value       = module.vpc.vpc_cidr
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = module.vpc.public_subnet_ids
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = module.vpc.private_subnet_ids
}

# ── Security Group Outputs ────────────────
output "web_security_group_id" {
  description = "Web security group ID"
  value       = module.web_sg.security_group_id
}

output "db_security_group_id" {
  description = "Database security group ID"
  value       = module.db_sg.security_group_id
}

# ── Summary ───────────────────────────────
output "summary" {
  description = "Environment summary"
  value = {
    environment      = var.environment
    vpc_id           = module.vpc.vpc_id
    public_subnets   = module.vpc.public_subnet_ids
    private_subnets  = module.vpc.private_subnet_ids
    web_sg           = module.web_sg.security_group_id
    db_sg            = module.db_sg.security_group_id
    nat_gateways     = module.vpc.nat_gateway_ids
  }
}
```

### Step 4.4: Dev Environment tfvars

Create `environments/dev/terraform.tfvars`:

```hcl
# environments/dev/terraform.tfvars

aws_region   = "us-east-1"
environment  = "dev"
project_name = "devsecops"
```

---

## Part 5: Deploy the Dev Environment

### Step 5.1: Initialize and Apply

```bash
cd ~/terraform-labs/lab05/environments/dev

terraform init
terraform plan
terraform apply -auto-approve
```

### Step 5.2: Examine the Module Resources

```bash
# List all resources — note the module prefix
terraform state list
```

**Expected Output:**

```
module.db_sg.aws_security_group.this
module.db_sg.aws_security_group_rule.egress[0]
module.db_sg.aws_security_group_rule.ingress[0]
module.vpc.aws_internet_gateway.this
module.vpc.aws_route_table.private[0]
module.vpc.aws_route_table.private[1]
module.vpc.aws_route_table.public
module.vpc.aws_route_table_association.private[0]
module.vpc.aws_route_table_association.private[1]
module.vpc.aws_route_table_association.public[0]
module.vpc.aws_route_table_association.public[1]
module.vpc.aws_subnet.private[0]
module.vpc.aws_subnet.private[1]
module.vpc.aws_subnet.public[0]
module.vpc.aws_subnet.public[1]
module.vpc.aws_vpc.this
module.web_sg.aws_security_group.this
module.web_sg.aws_security_group_rule.egress[0]
module.web_sg.aws_security_group_rule.ingress[0]
module.web_sg.aws_security_group_rule.ingress[1]
module.web_sg.aws_security_group_rule.ingress[2]
```

### Step 5.3: View Module Outputs

```bash
terraform output
terraform output -json summary | python3 -m json.tool
```

### Step 5.4: Show a Module Resource

```bash
terraform state show module.vpc.aws_vpc.this
terraform state show module.web_sg.aws_security_group.this
```

---

## Part 6: Create the Prod Environment

### Step 6.1: Production Configuration

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
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

locals {
  name_prefix = "${var.project_name}-${var.environment}"
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    Compliance  = "SOC2"
  }
}

# ──────────────────────────────────────────────
# VPC Module — Production Configuration
# ──────────────────────────────────────────────
module "vpc" {
  source = "../../modules/vpc"

  vpc_name             = "${local.name_prefix}-vpc"
  vpc_cidr             = "10.1.0.0/16"  # Different CIDR than dev!
  public_subnet_cidrs  = ["10.1.1.0/24", "10.1.2.0/24", "10.1.3.0/24"]
  private_subnet_cidrs = ["10.1.10.0/24", "10.1.20.0/24", "10.1.30.0/24"]
  availability_zones   = ["${var.aws_region}a", "${var.aws_region}b", "${var.aws_region}c"]
  enable_nat_gateway   = true   # Required in production
  single_nat_gateway   = false  # One NAT per AZ for HA
  environment          = var.environment
  common_tags          = local.common_tags
}

# ──────────────────────────────────────────────
# Web Security Group — Production (more restrictive)
# ──────────────────────────────────────────────
module "web_sg" {
  source = "../../modules/security-group"

  name        = "${local.name_prefix}-web-sg"
  description = "Production web server security group"
  vpc_id      = module.vpc.vpc_id

  ingress_rules = [
    {
      description = "HTTPS only"
      from_port   = 443
      to_port     = 443
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
    }
    # No SSH, no HTTP in production!
  ]

  tags = local.common_tags
}

# ──────────────────────────────────────────────
# Database Security Group
# ──────────────────────────────────────────────
module "db_sg" {
  source = "../../modules/security-group"

  name        = "${local.name_prefix}-db-sg"
  description = "Production database security group"
  vpc_id      = module.vpc.vpc_id

  ingress_rules = [
    {
      description     = "PostgreSQL from web servers"
      from_port       = 5432
      to_port         = 5432
      protocol        = "tcp"
      security_groups = [module.web_sg.security_group_id]
    }
  ]

  tags = local.common_tags
}
```

Create `environments/prod/variables.tf`:

```hcl
# environments/prod/variables.tf

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "prod"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "devsecops"
}
```

Create `environments/prod/outputs.tf`:

```hcl
# environments/prod/outputs.tf

output "vpc_id" {
  value = module.vpc.vpc_id
}

output "public_subnet_ids" {
  value = module.vpc.public_subnet_ids
}

output "private_subnet_ids" {
  value = module.vpc.private_subnet_ids
}

output "nat_gateway_ids" {
  value = module.vpc.nat_gateway_ids
}

output "web_security_group_id" {
  value = module.web_sg.security_group_id
}

output "db_security_group_id" {
  value = module.db_sg.security_group_id
}
```

Create `environments/prod/terraform.tfvars`:

```hcl
# environments/prod/terraform.tfvars

aws_region   = "us-east-1"
environment  = "prod"
project_name = "devsecops"
```

### Step 6.2: Compare Dev vs Prod

| Feature | Dev | Prod |
|---------|-----|------|
| VPC CIDR | `10.0.0.0/16` | `10.1.0.0/16` |
| Availability Zones | 2 | 3 |
| Subnets | 4 (2 public, 2 private) | 6 (3 public, 3 private) |
| NAT Gateway | Disabled | Enabled (multi-AZ) |
| SSH access | Allowed | Blocked |
| HTTP access | Allowed | Blocked (HTTPS only) |

Same modules, different configurations. This is the power of modules.

---

## Part 7: Using Public Registry Modules (Demonstration)

> **Note:** This section is for reference. You do not need to deploy this.

The Terraform Registry has thousands of community modules. Here is how you would use the official AWS VPC module:

```hcl
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.1.0"

  name = "my-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["us-east-1a", "us-east-1b", "us-east-1c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway = true
  single_nat_gateway = true

  tags = {
    Environment = "dev"
    Terraform   = "true"
  }
}
```

Browse available modules at [registry.terraform.io](https://registry.terraform.io/browse/modules).

---

## Expected Outcomes

After completing this lab, you should have:

- [x] Created a reusable VPC module with variables, resources, and outputs
- [x] Created a reusable security group module
- [x] Used modules in a dev environment configuration
- [x] Passed outputs from the VPC module as inputs to the security group module
- [x] Understood how module state is structured (`module.NAME.resource`)
- [x] Compared dev and prod configurations using the same modules
- [x] Learned about public registry modules

---

## Bonus Challenges

### Challenge 1: Add a VPC Flow Log

Extend the VPC module to optionally create a VPC Flow Log to CloudWatch Logs. Use a boolean variable `enable_flow_logs` to toggle it.

### Challenge 2: Module Versioning with Git

Push your VPC module to a Git repository and reference it by tag:

```hcl
module "vpc" {
  source = "git::https://github.com/your-org/terraform-modules.git//vpc?ref=v1.0.0"
}
```

### Challenge 3: Validate Module Inputs

Add validation to the VPC module that ensures:
- Public subnet count matches the AZ count
- Private subnet count matches the AZ count
- VPC CIDR is large enough for all subnets

### Challenge 4: Create an EC2 Module

Create an `ec2-instance` module that takes `vpc_id`, `subnet_id`, and `security_group_ids` as inputs. Use it with the outputs from your VPC and security group modules.

---

## Cleanup

```bash
# Destroy dev
cd ~/terraform-labs/lab05/environments/dev
terraform destroy -auto-approve

# Destroy prod (if deployed)
cd ~/terraform-labs/lab05/environments/prod
terraform destroy -auto-approve

cd ~
rm -rf ~/terraform-labs/lab05
```

---

## Next Lab

Proceed to [Lab 06: Multi-Environment Management](lab06-multi-environment.md) to learn how to manage dev, staging, and prod with workspaces and directory structures.
