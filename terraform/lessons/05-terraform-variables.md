# Lesson 5: Terraform Variables

---

## Table of Contents

1. [Input Variables](#input-variables)
2. [Variable Types](#variable-types)
3. [Variable Definitions and Defaults](#variable-definitions-and-defaults)
4. [Assigning Variable Values](#assigning-variable-values)
5. [Variable Validation](#variable-validation)
6. [Sensitive Variables](#sensitive-variables)
7. [Output Values](#output-values)
8. [Local Values](#local-values)
9. [Variable Precedence](#variable-precedence)
10. [Key Takeaways](#key-takeaways)

---

## Input Variables

Input variables are parameters for your Terraform configuration. They allow you to customize behavior without modifying the source code, making your configurations reusable and flexible.

### Basic Syntax

```hcl
variable "<NAME>" {
  type        = <TYPE>
  description = "<DESCRIPTION>"
  default     = <DEFAULT_VALUE>
  sensitive   = <true|false>
  nullable    = <true|false>

  validation {
    condition     = <BOOLEAN_EXPRESSION>
    error_message = "<ERROR_MESSAGE>"
  }
}
```

### Simple Example

```hcl
# variables.tf
variable "region" {
  type        = string
  description = "The AWS region to deploy resources in"
  default     = "us-east-1"
}

variable "instance_type" {
  type        = string
  description = "The EC2 instance type"
  default     = "t3.micro"
}

variable "environment" {
  type        = string
  description = "The deployment environment (dev, staging, prod)"
}

# main.tf - Reference variables with var.<NAME>
provider "aws" {
  region = var.region
}

resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = var.instance_type

  tags = {
    Environment = var.environment
  }
}
```

---

## Variable Types

Terraform supports both **primitive** and **complex** types.

### Primitive Types

#### `string`

```hcl
variable "project_name" {
  type        = string
  description = "The name of the project"
  default     = "my-app"
}

# Usage
resource "aws_instance" "web" {
  tags = {
    Project = var.project_name  # "my-app"
  }
}
```

#### `number`

```hcl
variable "instance_count" {
  type        = number
  description = "Number of instances to create"
  default     = 2
}

variable "disk_size_gb" {
  type        = number
  description = "Disk size in GB"
  default     = 50
}

# Usage
resource "aws_instance" "web" {
  count         = var.instance_count
  instance_type = "t3.micro"

  root_block_device {
    volume_size = var.disk_size_gb
  }
}
```

#### `bool`

```hcl
variable "enable_monitoring" {
  type        = bool
  description = "Whether to enable detailed monitoring"
  default     = false
}

variable "create_dns_record" {
  type        = bool
  description = "Whether to create a DNS record"
  default     = true
}

# Usage
resource "aws_instance" "web" {
  monitoring = var.enable_monitoring
}

resource "aws_route53_record" "web" {
  count = var.create_dns_record ? 1 : 0  # Conditionally create
  # ...
}
```

### Complex Types

#### `list` (Ordered Collection)

```hcl
variable "availability_zones" {
  type        = list(string)
  description = "List of availability zones"
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

variable "ingress_ports" {
  type        = list(number)
  description = "List of ports to allow"
  default     = [80, 443, 8080]
}

# Usage
resource "aws_subnet" "public" {
  count             = length(var.availability_zones)
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 1}.0/24"
  availability_zone = var.availability_zones[count.index]
}
```

#### `map` (Key-Value Pairs)

```hcl
variable "instance_types" {
  type        = map(string)
  description = "Instance types per environment"
  default = {
    dev     = "t3.micro"
    staging = "t3.small"
    prod    = "t3.large"
  }
}

variable "tags" {
  type        = map(string)
  description = "Common tags for all resources"
  default = {
    Project   = "MyApp"
    ManagedBy = "Terraform"
    Team      = "DevOps"
  }
}

# Usage
resource "aws_instance" "web" {
  instance_type = var.instance_types[var.environment]  # Look up by key
  tags          = var.tags
}
```

#### `set` (Unordered, Unique Collection)

```hcl
variable "allowed_ips" {
  type        = set(string)
  description = "Set of allowed IP addresses"
  default     = ["10.0.0.1", "10.0.0.2", "10.0.0.3"]
}

# Sets are commonly used with for_each
resource "aws_security_group_rule" "allow_ips" {
  for_each = var.allowed_ips

  type              = "ingress"
  from_port         = 22
  to_port           = 22
  protocol          = "tcp"
  cidr_blocks       = ["${each.value}/32"]
  security_group_id = aws_security_group.main.id
}
```

#### `object` (Structured Type)

```hcl
variable "vpc_config" {
  type = object({
    cidr_block           = string
    enable_dns_hostnames = bool
    enable_dns_support   = bool
    name                 = string
  })

  description = "VPC configuration"

  default = {
    cidr_block           = "10.0.0.0/16"
    enable_dns_hostnames = true
    enable_dns_support   = true
    name                 = "main-vpc"
  }
}

# Usage
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_config.cidr_block
  enable_dns_hostnames = var.vpc_config.enable_dns_hostnames
  enable_dns_support   = var.vpc_config.enable_dns_support

  tags = {
    Name = var.vpc_config.name
  }
}
```

#### `tuple` (Fixed-Length Ordered Collection)

```hcl
variable "subnet_config" {
  type = tuple([string, number, bool])
  description = "Tuple of [cidr_block, az_index, is_public]"
  default     = ["10.0.1.0/24", 0, true]
}
```

#### Nested Complex Types

```hcl
variable "web_servers" {
  type = list(object({
    name          = string
    instance_type = string
    ami           = string
    subnet_index  = number
    tags          = map(string)
  }))

  default = [
    {
      name          = "web-1"
      instance_type = "t3.micro"
      ami           = "ami-0c55b159cbfafe1f0"
      subnet_index  = 0
      tags          = { Role = "frontend" }
    },
    {
      name          = "web-2"
      instance_type = "t3.small"
      ami           = "ami-0c55b159cbfafe1f0"
      subnet_index  = 1
      tags          = { Role = "frontend" }
    }
  ]
}

# Usage
resource "aws_instance" "web" {
  for_each = { for server in var.web_servers : server.name => server }

  ami           = each.value.ami
  instance_type = each.value.instance_type
  subnet_id     = aws_subnet.public[each.value.subnet_index].id

  tags = merge(each.value.tags, {
    Name      = each.value.name
    ManagedBy = "Terraform"
  })
}
```

#### `any` Type

```hcl
variable "settings" {
  type        = any
  description = "Flexible settings (type inferred from value)"
  default     = {
    timeout = 30
    retries = 3
    debug   = true
  }
}
```

---

## Assigning Variable Values

There are several ways to set variable values, listed from lowest to highest precedence.

### 1. Default Values

```hcl
variable "region" {
  type    = string
  default = "us-east-1"  # Used if no other value is provided
}
```

### 2. Environment Variables

```bash
# Prefix with TF_VAR_
export TF_VAR_region="us-west-2"
export TF_VAR_instance_type="t3.large"
export TF_VAR_enable_monitoring=true

terraform plan
```

### 3. Variable Definition Files (.tfvars)

**`terraform.tfvars`** (auto-loaded):

```hcl
# terraform.tfvars
region         = "us-east-1"
instance_type  = "t3.micro"
environment    = "production"
instance_count = 3

availability_zones = [
  "us-east-1a",
  "us-east-1b",
]

tags = {
  Project = "MyApp"
  Team    = "DevOps"
}
```

**`*.auto.tfvars`** (also auto-loaded):

```hcl
# production.auto.tfvars
environment = "production"
```

**Named `.tfvars` files** (must be specified with `-var-file`):

```hcl
# environments/dev.tfvars
region         = "us-east-1"
environment    = "dev"
instance_type  = "t3.micro"
instance_count = 1

# environments/prod.tfvars
region         = "us-east-1"
environment    = "prod"
instance_type  = "t3.large"
instance_count = 3
```

```bash
# Use a specific var file
terraform plan -var-file="environments/dev.tfvars"
terraform apply -var-file="environments/prod.tfvars"
```

### 4. Command-Line Flags

```bash
terraform plan -var="region=us-west-2" -var="instance_type=t3.large"
terraform apply -var="environment=staging" -var="instance_count=2"
```

### 5. Interactive Prompt

If a required variable has no default and no value is provided, Terraform will prompt:

```bash
$ terraform plan
var.environment
  The deployment environment (dev, staging, prod)

  Enter a value: dev
```

---

## Variable Validation

Add custom validation rules to catch errors early:

### Single Validation

```hcl
variable "environment" {
  type        = string
  description = "The deployment environment"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}
```

### Multiple Validations

```hcl
variable "instance_type" {
  type        = string
  description = "EC2 instance type"

  validation {
    condition     = can(regex("^t[23]\\.", var.instance_type))
    error_message = "Instance type must be a t2 or t3 type (e.g., t3.micro)."
  }

  validation {
    condition     = !contains(["t2.nano", "t3.nano"], var.instance_type)
    error_message = "Nano instances are not allowed -- they are too small for our workloads."
  }
}
```

### Complex Validations

```hcl
variable "cidr_block" {
  type        = string
  description = "VPC CIDR block"

  validation {
    condition     = can(cidrhost(var.cidr_block, 0))
    error_message = "Must be a valid CIDR block (e.g., 10.0.0.0/16)."
  }

  validation {
    condition     = tonumber(split("/", var.cidr_block)[1]) <= 24
    error_message = "CIDR block must be /24 or larger (smaller number)."
  }
}

variable "name" {
  type        = string
  description = "Resource name"

  validation {
    condition     = length(var.name) >= 3 && length(var.name) <= 63
    error_message = "Name must be between 3 and 63 characters."
  }

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]*[a-z0-9]$", var.name))
    error_message = "Name must start with a letter, contain only lowercase letters, numbers, and hyphens, and end with a letter or number."
  }
}
```

---

## Sensitive Variables

Mark variables as sensitive to prevent their values from appearing in CLI output and logs.

### Declaring Sensitive Variables

```hcl
variable "db_password" {
  type        = string
  description = "Database master password"
  sensitive   = true
}

variable "api_key" {
  type        = string
  description = "External API key"
  sensitive   = true
}
```

### What Sensitive Does

```bash
$ terraform plan

  # aws_db_instance.main will be created
  + resource "aws_db_instance" "main" {
      + password = (sensitive value)    # Value is hidden
      + username = "admin"              # Non-sensitive, shown normally
    }
```

### Using Sensitive Variables

```hcl
resource "aws_db_instance" "main" {
  identifier     = "production-db"
  engine         = "postgres"
  engine_version = "15.4"
  instance_class = "db.r5.large"
  username       = "admin"
  password       = var.db_password  # Sensitive value

  skip_final_snapshot = true
}
```

### Setting Sensitive Variable Values

```bash
# Option 1: Environment variable (recommended for CI/CD)
export TF_VAR_db_password="SuperSecretPassword123!"

# Option 2: .tfvars file (DON'T commit to Git!)
# secrets.tfvars
# db_password = "SuperSecretPassword123!"
terraform apply -var-file="secrets.tfvars"

# Option 3: Command line (visible in shell history -- use with caution)
terraform apply -var="db_password=SuperSecretPassword123!"
```

> **DevSecOps Warning**: Even with `sensitive = true`, the value is still stored in the state file in plain text. Always encrypt your state file and restrict access to it.

---

## Output Values

Output values expose information about your infrastructure after `terraform apply`. They are useful for:

- Displaying important information (IPs, URLs, IDs)
- Passing data between modules
- Providing values for other automation tools

### Basic Syntax

```hcl
output "<NAME>" {
  value       = <EXPRESSION>
  description = "<DESCRIPTION>"
  sensitive   = <true|false>
}
```

### Common Output Examples

```hcl
# outputs.tf

output "vpc_id" {
  value       = aws_vpc.main.id
  description = "The ID of the VPC"
}

output "public_subnet_ids" {
  value       = aws_subnet.public[*].id
  description = "List of public subnet IDs"
}

output "web_server_public_ips" {
  value       = { for k, v in aws_instance.web : k => v.public_ip }
  description = "Map of web server names to public IPs"
}

output "load_balancer_dns" {
  value       = aws_lb.main.dns_name
  description = "DNS name of the load balancer"
}

output "database_endpoint" {
  value       = aws_db_instance.main.endpoint
  description = "Database connection endpoint"
}

output "database_password" {
  value       = aws_db_instance.main.password
  description = "Database password"
  sensitive   = true  # Hide in output
}
```

### Viewing Outputs

```bash
# Show all outputs
terraform output

# Show a specific output
terraform output vpc_id

# Get raw value (for scripting)
terraform output -raw load_balancer_dns

# Get output as JSON
terraform output -json
```

### Using Outputs Between Modules

```hcl
# modules/vpc/outputs.tf
output "vpc_id" {
  value = aws_vpc.main.id
}

output "public_subnet_ids" {
  value = aws_subnet.public[*].id
}

# root main.tf
module "vpc" {
  source = "./modules/vpc"
}

module "web" {
  source     = "./modules/web"
  vpc_id     = module.vpc.vpc_id            # Use output from vpc module
  subnet_ids = module.vpc.public_subnet_ids  # Use output from vpc module
}
```

---

## Local Values

Locals are computed values defined within your configuration. They simplify complex expressions and avoid repetition.

### Basic Syntax

```hcl
locals {
  <NAME> = <EXPRESSION>
}
```

### Common Use Cases

#### Avoiding Repetition

```hcl
locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
    Team        = var.team
    CostCenter  = var.cost_center
  }
}

resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  tags       = merge(local.common_tags, { Name = "main-vpc" })
}

resource "aws_subnet" "public" {
  vpc_id     = aws_vpc.main.id
  cidr_block = "10.0.1.0/24"
  tags       = merge(local.common_tags, { Name = "public-subnet" })
}

resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.micro"
  tags          = merge(local.common_tags, { Name = "web-server", Role = "web" })
}
```

#### Computed Values

```hcl
locals {
  # Construct resource names
  name_prefix = "${var.project}-${var.environment}"

  # Determine instance type based on environment
  instance_type = var.environment == "prod" ? "t3.large" : "t3.micro"

  # Build a full resource name
  vpc_name = "${local.name_prefix}-vpc"
  sg_name  = "${local.name_prefix}-sg"

  # Flatten complex data structures
  subnet_configs = flatten([
    for az_index, az in var.availability_zones : [
      {
        name   = "${local.name_prefix}-public-${az}"
        cidr   = cidrsubnet(var.vpc_cidr, 8, az_index)
        public = true
        az     = az
      },
      {
        name   = "${local.name_prefix}-private-${az}"
        cidr   = cidrsubnet(var.vpc_cidr, 8, az_index + 100)
        public = false
        az     = az
      }
    ]
  ])
}
```

#### Data Transformation

```hcl
variable "users" {
  type = list(object({
    name  = string
    role  = string
    email = string
  }))

  default = [
    { name = "alice", role = "admin", email = "alice@example.com" },
    { name = "bob", role = "developer", email = "bob@example.com" },
    { name = "charlie", role = "admin", email = "charlie@example.com" },
  ]
}

locals {
  # Filter admins only
  admins = [for user in var.users : user if user.role == "admin"]

  # Create a map of name -> email
  user_emails = { for user in var.users : user.name => user.email }

  # Group users by role
  users_by_role = {
    for user in var.users :
    user.role => user.name...  # The ... groups values by key
  }
  # Result: { admin = ["alice", "charlie"], developer = ["bob"] }
}
```

### Variables vs. Locals

| Feature | Variables (`var.`) | Locals (`local.`) |
|---------|-------------------|-------------------|
| **Set by** | User (external input) | Configuration (internal) |
| **Purpose** | Parameterize configs | Simplify expressions |
| **Can be overridden** | Yes | No |
| **Support defaults** | Yes | Always has a value |
| **Support validation** | Yes | No |

---

## Variable Precedence

When the same variable is set in multiple places, Terraform uses the following precedence (highest wins):

```
1. -var or -var-file on command line     (HIGHEST)
2. *.auto.tfvars files (alphabetical)
3. terraform.tfvars file
4. TF_VAR_ environment variables
5. Default value in variable block
6. Interactive prompt (if no default)     (LOWEST)
```

### Example

```hcl
# variables.tf
variable "region" {
  default = "us-east-1"  # Priority 5
}
```

```bash
# Priority 4
export TF_VAR_region="us-west-1"
```

```hcl
# terraform.tfvars -- Priority 3
region = "eu-west-1"
```

```hcl
# production.auto.tfvars -- Priority 2
region = "ap-southeast-1"
```

```bash
# Priority 1 (WINS)
terraform apply -var="region=ca-central-1"
# Result: region = "ca-central-1"
```

---

## Putting It All Together: Real-World Variable Organization

### File Structure

```
project/
├── main.tf              # Resources
├── variables.tf         # Variable declarations
├── outputs.tf           # Output declarations
├── locals.tf            # Local values
├── terraform.tfvars     # Default values
├── versions.tf          # Provider and Terraform version constraints
└── environments/
    ├── dev.tfvars        # Dev overrides
    ├── staging.tfvars    # Staging overrides
    └── prod.tfvars       # Prod overrides
```

### variables.tf

```hcl
# ──────────────────────────────────────────────
# General
# ──────────────────────────────────────────────

variable "project" {
  type        = string
  description = "Project name"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]+$", var.project))
    error_message = "Project name must be lowercase alphanumeric with hyphens."
  }
}

variable "environment" {
  type        = string
  description = "Deployment environment"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Must be dev, staging, or prod."
  }
}

variable "region" {
  type        = string
  description = "AWS region"
  default     = "us-east-1"
}

# ──────────────────────────────────────────────
# Networking
# ──────────────────────────────────────────────

variable "vpc_cidr" {
  type        = string
  description = "VPC CIDR block"
  default     = "10.0.0.0/16"

  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "Must be a valid CIDR block."
  }
}

# ──────────────────────────────────────────────
# Compute
# ──────────────────────────────────────────────

variable "instance_type" {
  type        = string
  description = "EC2 instance type"
  default     = "t3.micro"
}

variable "instance_count" {
  type        = number
  description = "Number of instances"
  default     = 1

  validation {
    condition     = var.instance_count >= 1 && var.instance_count <= 10
    error_message = "Instance count must be between 1 and 10."
  }
}

# ──────────────────────────────────────────────
# Database
# ──────────────────────────────────────────────

variable "db_password" {
  type        = string
  description = "Database master password"
  sensitive   = true

  validation {
    condition     = length(var.db_password) >= 16
    error_message = "Password must be at least 16 characters."
  }
}
```

### environments/prod.tfvars

```hcl
project        = "my-app"
environment    = "prod"
region         = "us-east-1"
vpc_cidr       = "10.0.0.0/16"
instance_type  = "t3.large"
instance_count = 3
```

### Deploy

```bash
terraform plan -var-file="environments/prod.tfvars" -var="db_password=$(vault read -field=password secret/db)"
```

---

## Key Takeaways

1. **Variables make configurations reusable** -- parameterize everything that differs between environments
2. **Use specific types** (`string`, `number`, `bool`, `list`, `map`, `object`) rather than `any`
3. **Add validation rules** to catch errors early, before infrastructure is modified
4. **Mark sensitive variables** with `sensitive = true` to hide them from CLI output
5. **Use `.tfvars` files** per environment for clean separation of values
6. **Locals reduce repetition** -- use them for computed values, common tags, and data transformations
7. **Outputs expose important data** -- use them to display info and pass data between modules
8. **Never commit secrets** to Git -- use environment variables, secrets managers, or encrypted `.tfvars` files
9. **Know the precedence order** -- command-line `-var` flags always win

---

## What's Next?

In the next lesson, we will explore Terraform state -- how it works, why it matters, and how to manage it safely.

[Previous Lesson: Terraform Resources](./04-terraform-resources.md) | [Next Lesson: Terraform State -->](./06-terraform-state.md)
