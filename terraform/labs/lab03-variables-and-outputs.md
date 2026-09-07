# Lab 03: Variables and Outputs Deep Dive

## Difficulty: Intermediate

## Objectives

By the end of this lab, you will be able to:

- Use all Terraform variable types: `string`, `number`, `bool`, `list`, `map`, `set`, and `object`
- Create and use `.tfvars` files for different configurations
- Use `locals` for computed values and intermediate expressions
- Apply conditional expressions and built-in functions
- Define rich outputs including sensitive values
- Understand variable precedence and validation

## Prerequisites

- Completed [Lab 01](lab01-first-terraform-project.md) and [Lab 02](lab02-aws-ec2-instance.md)
- Terraform installed (v1.0+)
- AWS CLI configured (optional — this lab can be done with the `local` provider only)

## Estimated Time

60 minutes

---

## Part 1: Variable Types

### Step 1.1: Set Up the Project

```bash
mkdir -p ~/terraform-labs/lab03
cd ~/terraform-labs/lab03
```

### Step 1.2: Create Variables with Every Type

Create `variables.tf`:

```hcl
# variables.tf — Demonstrating all Terraform variable types

# ──────────────────────────────────────
# String
# ──────────────────────────────────────
variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "devsecops-lab03"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "development"

  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be one of: development, staging, production."
  }
}

# ──────────────────────────────────────
# Number
# ──────────────────────────────────────
variable "instance_count" {
  description = "Number of instances to create"
  type        = number
  default     = 2

  validation {
    condition     = var.instance_count > 0 && var.instance_count <= 10
    error_message = "Instance count must be between 1 and 10."
  }
}

variable "disk_size_gb" {
  description = "Root disk size in GB"
  type        = number
  default     = 20
}

# ──────────────────────────────────────
# Boolean
# ──────────────────────────────────────
variable "enable_monitoring" {
  description = "Enable detailed monitoring"
  type        = bool
  default     = true
}

variable "enable_public_access" {
  description = "Enable public IP assignment"
  type        = bool
  default     = false
}

# ──────────────────────────────────────
# List (ordered collection of same type)
# ──────────────────────────────────────
variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

variable "allowed_ports" {
  description = "List of allowed ingress ports"
  type        = list(number)
  default     = [22, 80, 443]
}

# ──────────────────────────────────────
# Map (key-value pairs of same type)
# ──────────────────────────────────────
variable "common_tags" {
  description = "Common tags applied to all resources"
  type        = map(string)
  default = {
    Project   = "DevSecOps"
    ManagedBy = "Terraform"
    Team      = "Platform"
  }
}

variable "instance_types" {
  description = "Instance type per environment"
  type        = map(string)
  default = {
    development = "t2.micro"
    staging     = "t2.small"
    production  = "t2.medium"
  }
}

# ──────────────────────────────────────
# Set (unordered collection of unique values)
# ──────────────────────────────────────
variable "security_protocols" {
  description = "Set of allowed security protocols"
  type        = set(string)
  default     = ["TLSv1.2", "TLSv1.3"]
}

# ──────────────────────────────────────
# Object (structured type with named attributes)
# ──────────────────────────────────────
variable "database_config" {
  description = "Database configuration object"
  type = object({
    engine         = string
    engine_version = string
    instance_class = string
    storage_gb     = number
    multi_az       = bool
    backup_retention_days = number
  })
  default = {
    engine                = "postgres"
    engine_version        = "15.4"
    instance_class        = "db.t3.micro"
    storage_gb            = 20
    multi_az              = false
    backup_retention_days = 7
  }
}

# ──────────────────────────────────────
# Tuple (ordered collection of potentially different types)
# ──────────────────────────────────────
variable "notification_config" {
  description = "Notification config: [email, severity_level, enabled]"
  type        = tuple([string, number, bool])
  default     = ["admin@example.com", 3, true]
}

# ──────────────────────────────────────
# Complex nested types
# ──────────────────────────────────────
variable "services" {
  description = "Map of services to deploy"
  type = map(object({
    port        = number
    protocol    = string
    health_path = string
    replicas    = number
    enabled     = bool
  }))
  default = {
    web_app = {
      port        = 8080
      protocol    = "HTTP"
      health_path = "/health"
      replicas    = 2
      enabled     = true
    }
    api = {
      port        = 3000
      protocol    = "HTTP"
      health_path = "/api/health"
      replicas    = 3
      enabled     = true
    }
    worker = {
      port        = 0
      protocol    = "TCP"
      health_path = "/status"
      replicas    = 1
      enabled     = false
    }
  }
}

# ──────────────────────────────────────
# Sensitive variable
# ──────────────────────────────────────
variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
  default     = "lab-password-change-me"
}
```

---

## Part 2: Using Locals

### Step 2.1: Create Locals for Computed Values

Create `locals.tf`:

```hcl
# locals.tf — Computed values and intermediate expressions

locals {
  # ── Naming Convention ───────────────────
  name_prefix = "${var.project_name}-${var.environment}"

  # ── Environment-Based Logic ─────────────
  is_production = var.environment == "production"
  is_dev        = var.environment == "development"

  # ── Conditional Values ──────────────────
  instance_type = var.instance_types[var.environment]
  disk_size     = local.is_production ? var.disk_size_gb * 2 : var.disk_size_gb
  monitoring    = local.is_production ? true : var.enable_monitoring

  # ── Merged Tags ─────────────────────────
  all_tags = merge(
    var.common_tags,
    {
      Environment = var.environment
      Name        = local.name_prefix
      CreatedAt   = timestamp()
    }
  )

  # ── Computed from Complex Types ─────────
  enabled_services = {
    for name, config in var.services : name => config if config.enabled
  }

  total_replicas = sum([for _, svc in local.enabled_services : svc.replicas])

  service_ports = [for _, svc in local.enabled_services : svc.port if svc.port > 0]

  # ── String Manipulation ─────────────────
  az_short_names = [for az in var.availability_zones : replace(az, "us-east-1", "use1-")]

  environment_upper = upper(var.environment)
  environment_title = title(var.environment)

  # ── Conditional list building ───────────
  ingress_ports = concat(
    var.allowed_ports,
    local.is_production ? [8443] : [],
    local.is_dev ? [8080, 9090] : []
  )

  # ── Map transformation ─────────────────
  tag_list = [for key, value in local.all_tags : {
    key   = key
    value = value
  }]
}
```

---

## Part 3: Create Resources Using Variables and Locals

### Step 3.1: Create the Main Configuration

Create `main.tf`:

```hcl
# main.tf — Using variables, locals, and conditionals

terraform {
  required_version = ">= 1.0.0"

  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.0"
    }
  }
}

# ──────────────────────────────────────────────
# Generate a deployment summary file
# ──────────────────────────────────────────────
resource "local_file" "deployment_summary" {
  filename = "${path.module}/output/deployment-summary.json"
  content = jsonencode({
    project     = var.project_name
    environment = var.environment
    settings = {
      instance_type     = local.instance_type
      instance_count    = var.instance_count
      disk_size_gb      = local.disk_size
      monitoring        = local.monitoring
      public_access     = var.enable_public_access
      is_production     = local.is_production
    }
    database = var.database_config
    enabled_services = local.enabled_services
    total_replicas   = local.total_replicas
    tags             = local.all_tags
  })

  file_permission = "0644"
}

# ──────────────────────────────────────────────
# Generate per-service configuration files
# ──────────────────────────────────────────────
resource "local_file" "service_config" {
  for_each = local.enabled_services

  filename = "${path.module}/output/services/${each.key}.json"
  content = jsonencode({
    service_name = each.key
    environment  = var.environment
    port         = each.value.port
    protocol     = each.value.protocol
    health_path  = each.value.health_path
    replicas     = local.is_production ? each.value.replicas * 2 : each.value.replicas
    full_name    = "${local.name_prefix}-${each.key}"
    tags         = local.all_tags
  })

  file_permission = "0644"
}

# ──────────────────────────────────────────────
# Generate numbered instance configs using count
# ──────────────────────────────────────────────
resource "local_file" "instance_config" {
  count = var.instance_count

  filename = "${path.module}/output/instances/instance-${count.index}.json"
  content = jsonencode({
    instance_index    = count.index
    instance_name     = "${local.name_prefix}-${format("%02d", count.index)}"
    availability_zone = var.availability_zones[count.index % length(var.availability_zones)]
    instance_type     = local.instance_type
    disk_size_gb      = local.disk_size
    tags = merge(local.all_tags, {
      InstanceIndex = count.index
    })
  })

  file_permission = "0644"
}

# ──────────────────────────────────────────────
# Generate security group rules file
# ──────────────────────────────────────────────
resource "local_file" "security_rules" {
  filename = "${path.module}/output/security-rules.json"
  content = jsonencode({
    ingress_ports      = local.ingress_ports
    service_ports      = local.service_ports
    security_protocols = var.security_protocols
    public_access      = var.enable_public_access
    environment_notice = local.is_production ? "PRODUCTION: Extra security rules applied" : "Non-production environment"
  })

  file_permission = "0644"
}

# ──────────────────────────────────────────────
# Conditional resource: only created in production
# ──────────────────────────────────────────────
resource "local_file" "production_runbook" {
  count = local.is_production ? 1 : 0

  filename = "${path.module}/output/PRODUCTION-RUNBOOK.md"
  content  = <<-EOT
    # Production Runbook
    ## Project: ${var.project_name}
    ## Environment: ${var.environment}

    ### Alerts
    - Notification Email: ${var.notification_config[0]}
    - Severity Level: ${var.notification_config[1]}
    - Notifications Enabled: ${var.notification_config[2]}

    ### Database
    - Engine: ${var.database_config.engine} ${var.database_config.engine_version}
    - Multi-AZ: ${var.database_config.multi_az}
    - Backup Retention: ${var.database_config.backup_retention_days} days

    ### Services
    ${join("\n", [for name, svc in local.enabled_services : "- ${name}: port ${svc.port}, ${svc.replicas * 2} replicas"])}
  EOT

  file_permission = "0644"
}
```

---

## Part 4: Define Outputs

### Step 4.1: Create Comprehensive Outputs

Create `outputs.tf`:

```hcl
# outputs.tf — Demonstrating different output types

# ── Simple string output ──────────────────
output "name_prefix" {
  description = "The computed name prefix for all resources"
  value       = local.name_prefix
}

# ── Conditional output ────────────────────
output "environment_notice" {
  description = "Environment-specific notice"
  value       = local.is_production ? "WARNING: This is PRODUCTION!" : "This is a ${var.environment} environment."
}

# ── Map output ────────────────────────────
output "instance_type_map" {
  description = "Instance types per environment"
  value       = var.instance_types
}

output "selected_instance_type" {
  description = "Instance type for current environment"
  value       = local.instance_type
}

# ── List output ───────────────────────────
output "availability_zones" {
  description = "Configured availability zones"
  value       = var.availability_zones
}

output "az_short_names" {
  description = "Shortened availability zone names"
  value       = local.az_short_names
}

# ── Computed outputs ──────────────────────
output "enabled_services" {
  description = "Services that are enabled"
  value       = keys(local.enabled_services)
}

output "total_replicas" {
  description = "Total number of replicas across all enabled services"
  value       = local.total_replicas
}

output "ingress_ports" {
  description = "All ingress ports (environment-specific)"
  value       = local.ingress_ports
}

# ── Sensitive output ──────────────────────
output "db_connection_string" {
  description = "Database connection string (sensitive)"
  value       = "postgresql://admin:${var.db_password}@db.${local.name_prefix}.internal:5432/app"
  sensitive   = true
}

# ── Complex output ────────────────────────
output "deployment_summary" {
  description = "Full deployment summary"
  value = {
    project         = var.project_name
    environment     = var.environment
    instance_type   = local.instance_type
    instance_count  = var.instance_count
    disk_size       = local.disk_size
    is_production   = local.is_production
    enabled_services = keys(local.enabled_services)
    total_replicas  = local.total_replicas
    tags            = local.all_tags
  }
}

# ── Per-service output using for expression ──
output "service_endpoints" {
  description = "Service endpoints"
  value = {
    for name, svc in local.enabled_services :
    name => "http://${local.name_prefix}-${name}.internal:${svc.port}${svc.health_path}"
  }
}

# ── Output from count-based resources ─────
output "instance_names" {
  description = "Names of all instances"
  value       = [for i in range(var.instance_count) : "${local.name_prefix}-${format("%02d", i)}"]
}
```

---

## Part 5: Create `.tfvars` Files

### Step 5.1: Default Variables File

Create `terraform.tfvars`:

```hcl
# terraform.tfvars — Default variable overrides
# This file is automatically loaded by Terraform

project_name         = "devsecops-lab03"
environment          = "development"
instance_count       = 2
enable_monitoring    = true
enable_public_access = false
```

### Step 5.2: Development Environment File

Create `dev.tfvars`:

```hcl
# dev.tfvars — Development environment overrides

project_name         = "devsecops-lab03"
environment          = "development"
instance_count       = 1
disk_size_gb         = 10
enable_monitoring    = false
enable_public_access = true

allowed_ports = [22, 80, 443, 8080, 9090, 3000]

common_tags = {
  Project   = "DevSecOps"
  ManagedBy = "Terraform"
  Team      = "Platform"
  CostCenter = "development"
}

database_config = {
  engine                = "postgres"
  engine_version        = "15.4"
  instance_class        = "db.t3.micro"
  storage_gb            = 10
  multi_az              = false
  backup_retention_days = 1
}
```

### Step 5.3: Production Environment File

Create `prod.tfvars`:

```hcl
# prod.tfvars — Production environment overrides

project_name         = "devsecops-lab03"
environment          = "production"
instance_count       = 4
disk_size_gb         = 50
enable_monitoring    = true
enable_public_access = false

allowed_ports = [80, 443]

common_tags = {
  Project     = "DevSecOps"
  ManagedBy   = "Terraform"
  Team        = "Platform"
  CostCenter  = "production"
  Compliance  = "SOC2"
  DataClass   = "confidential"
}

database_config = {
  engine                = "postgres"
  engine_version        = "15.4"
  instance_class        = "db.r6g.large"
  storage_gb            = 100
  multi_az              = true
  backup_retention_days = 30
}

services = {
  web_app = {
    port        = 8080
    protocol    = "HTTPS"
    health_path = "/health"
    replicas    = 4
    enabled     = true
  }
  api = {
    port        = 3000
    protocol    = "HTTPS"
    health_path = "/api/health"
    replicas    = 6
    enabled     = true
  }
  worker = {
    port        = 0
    protocol    = "TCP"
    health_path = "/status"
    replicas    = 3
    enabled     = true
  }
}
```

---

## Part 6: Run and Compare Environments

### Step 6.1: Initialize the Project

```bash
terraform init
```

### Step 6.2: Apply with Development Settings

```bash
# Create output directory
mkdir -p output/services output/instances

terraform apply -var-file="dev.tfvars" -auto-approve
```

Examine the generated files:

```bash
echo "=== Deployment Summary ==="
cat output/deployment-summary.json | python3 -m json.tool

echo "=== Services ==="
ls output/services/
cat output/services/web_app.json | python3 -m json.tool

echo "=== Instances ==="
ls output/instances/

echo "=== Security Rules ==="
cat output/security-rules.json | python3 -m json.tool
```

### Step 6.3: Review the Outputs

```bash
terraform output
terraform output -json deployment_summary | python3 -m json.tool
terraform output enabled_services
terraform output ingress_ports
```

Try accessing the sensitive output:

```bash
# This will show (sensitive)
terraform output db_connection_string

# This will show the actual value
terraform output -raw db_connection_string
```

### Step 6.4: Destroy and Apply with Production Settings

```bash
terraform destroy -var-file="dev.tfvars" -auto-approve
mkdir -p output/services output/instances

terraform apply -var-file="prod.tfvars" -auto-approve
```

Compare the differences:

```bash
echo "=== Production Deployment ==="
cat output/deployment-summary.json | python3 -m json.tool

echo "=== Production Runbook ==="
cat output/PRODUCTION-RUNBOOK.md

echo "=== Production Services ==="
ls output/services/
```

**Notice these differences between dev and prod:**

| Setting | Development | Production |
|---------|-------------|------------|
| Instance count | 1 | 4 |
| Disk size | 10 GB | 100 GB (doubled by local) |
| Instance type | t2.micro | t2.medium |
| Services enabled | 2 (web, api) | 3 (web, api, worker) |
| Replicas | Normal | Doubled |
| Ingress ports | 6 ports + dev extras | 2 ports + prod extras |
| Runbook generated | No | Yes |

---

## Part 7: Variable Precedence

### Step 7.1: Understand the Precedence Order

Terraform loads variables in this order (later sources override earlier ones):

1. Default values in `variables.tf`
2. `terraform.tfvars` (auto-loaded)
3. `*.auto.tfvars` files (auto-loaded, alphabetical order)
4. `-var-file` flag
5. `-var` flag on command line
6. `TF_VAR_` environment variables

### Step 7.2: Test Precedence

```bash
# The -var flag overrides everything
terraform plan \
  -var-file="prod.tfvars" \
  -var="instance_count=1" \
  -var="environment=staging"
```

```bash
# Environment variables also work
export TF_VAR_project_name="env-var-project"
terraform plan -var-file="dev.tfvars"
unset TF_VAR_project_name
```

### Step 7.3: Test Validation

```bash
# This should fail validation
terraform plan -var="environment=invalid"
```

**Expected Error:**

```
Error: Invalid value for variable

  on variables.tf line X:
   X: variable "environment" {

Environment must be one of: development, staging, production.
```

```bash
# This should also fail
terraform plan -var="instance_count=99"
```

---

## Expected Outcomes

After completing this lab, you should have:

- [x] Declared variables of every Terraform type (string, number, bool, list, map, set, object, tuple)
- [x] Implemented variable validation rules
- [x] Used locals for computed values, conditionals, and transformations
- [x] Created `.tfvars` files for different environments
- [x] Used conditional expressions (`? :`) for environment-specific behavior
- [x] Created conditional resources with `count`
- [x] Used `for_each` with filtered maps
- [x] Used `for` expressions for list and map transformations
- [x] Worked with sensitive variables and outputs
- [x] Understood variable precedence rules

---

## Bonus Challenges

### Challenge 1: Custom Validation

Add a validation block to `disk_size_gb` that ensures it is a multiple of 10 and at least 10 GB.

<details>
<summary>Hint</summary>

```hcl
validation {
  condition     = var.disk_size_gb >= 10 && var.disk_size_gb % 10 == 0
  error_message = "Disk size must be at least 10 GB and a multiple of 10."
}
```

</details>

### Challenge 2: `nullable` Variables

Experiment with the `nullable = false` argument on a variable. What happens if someone passes `null`?

### Challenge 3: Type Constraints with `optional()`

Create an object variable where some attributes are optional with defaults:

```hcl
variable "cache_config" {
  type = object({
    enabled = bool
    ttl     = optional(number, 300)
    engine  = optional(string, "redis")
    size    = optional(string, "cache.t3.micro")
  })
}
```

Test it with partial inputs.

### Challenge 4: Generate a CSV Report

Use the `join()` and `format()` functions to generate a CSV file from the services data. The CSV should have headers: `name,port,protocol,replicas`.

<details>
<summary>Hint</summary>

```hcl
resource "local_file" "csv_report" {
  filename = "${path.module}/output/services-report.csv"
  content = join("\n", concat(
    ["name,port,protocol,replicas"],
    [for name, svc in local.enabled_services :
      "${name},${svc.port},${svc.protocol},${svc.replicas}"
    ]
  ))
}
```

</details>

---

## Cleanup

```bash
terraform destroy -var-file="dev.tfvars" -auto-approve
cd ~
rm -rf ~/terraform-labs/lab03
```

---

## Next Lab

Proceed to [Lab 04: Remote State Management](lab04-remote-state.md) to learn about storing Terraform state securely in the cloud.
