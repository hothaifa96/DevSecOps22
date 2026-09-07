# Lab 08: Advanced Terraform

## Difficulty: Advanced

## Objectives

By the end of this lab, you will be able to:

- Use **dynamic blocks** to generate repeating nested blocks from data
- Apply **`for_each`** with complex data structures (maps of objects)
- Use **data sources** to query existing infrastructure
- Work with **provisioners** and understand their use cases and risks
- Use **`null_resource`** and **`terraform_data`** for custom workflows
- Combine these techniques for real-world infrastructure patterns

## Prerequisites

- Completed Labs 01–07
- AWS CLI configured
- Terraform v1.5+ installed
- Strong understanding of HCL syntax and Terraform fundamentals

## Estimated Time

90 minutes

---

## Part 1: Dynamic Blocks

### What Are Dynamic Blocks?

Dynamic blocks generate repeating nested blocks from a collection. They replace copy-pasting similar blocks that differ only in their values.

**Without dynamic blocks (repetitive):**

```hcl
resource "aws_security_group" "example" {
  ingress { from_port = 80; to_port = 80; protocol = "tcp"; cidr_blocks = ["0.0.0.0/0"] }
  ingress { from_port = 443; to_port = 443; protocol = "tcp"; cidr_blocks = ["0.0.0.0/0"] }
  ingress { from_port = 22; to_port = 22; protocol = "tcp"; cidr_blocks = ["10.0.0.0/8"] }
}
```

**With dynamic blocks (data-driven):**

```hcl
resource "aws_security_group" "example" {
  dynamic "ingress" {
    for_each = var.ingress_rules
    content {
      from_port   = ingress.value.port
      to_port     = ingress.value.port
      protocol    = ingress.value.protocol
      cidr_blocks = ingress.value.cidrs
    }
  }
}
```

### Step 1.1: Set Up the Project

```bash
mkdir -p ~/terraform-labs/lab08
cd ~/terraform-labs/lab08
```

### Step 1.2: Create the Configuration

Create `providers.tf`:

```hcl
# providers.tf

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project   = "DevSecOps-Lab08"
      ManagedBy = "terraform"
    }
  }
}
```

### Step 1.3: Define Complex Variables

Create `variables.tf`:

```hcl
# variables.tf

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# ──────────────────────────────────────────────
# Complex variable for security group rules
# ──────────────────────────────────────────────
variable "security_groups" {
  description = "Map of security groups to create with their rules"
  type = map(object({
    description = string
    ingress_rules = list(object({
      description = string
      from_port   = number
      to_port     = number
      protocol    = string
      cidr_blocks = list(string)
    }))
    egress_rules = list(object({
      description = string
      from_port   = number
      to_port     = number
      protocol    = string
      cidr_blocks = list(string)
    }))
  }))

  default = {
    web = {
      description = "Web server security group"
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
        }
      ]
      egress_rules = [
        {
          description = "All outbound"
          from_port   = 0
          to_port     = 0
          protocol    = "-1"
          cidr_blocks = ["0.0.0.0/0"]
        }
      ]
    }

    app = {
      description = "Application server security group"
      ingress_rules = [
        {
          description = "App port"
          from_port   = 8080
          to_port     = 8080
          protocol    = "tcp"
          cidr_blocks = ["10.0.0.0/8"]
        },
        {
          description = "Health check"
          from_port   = 8081
          to_port     = 8081
          protocol    = "tcp"
          cidr_blocks = ["10.0.0.0/8"]
        },
        {
          description = "Metrics"
          from_port   = 9090
          to_port     = 9090
          protocol    = "tcp"
          cidr_blocks = ["10.0.0.0/8"]
        }
      ]
      egress_rules = [
        {
          description = "All outbound"
          from_port   = 0
          to_port     = 0
          protocol    = "-1"
          cidr_blocks = ["0.0.0.0/0"]
        }
      ]
    }

    db = {
      description = "Database security group"
      ingress_rules = [
        {
          description = "PostgreSQL"
          from_port   = 5432
          to_port     = 5432
          protocol    = "tcp"
          cidr_blocks = ["10.0.0.0/16"]
        },
        {
          description = "Redis"
          from_port   = 6379
          to_port     = 6379
          protocol    = "tcp"
          cidr_blocks = ["10.0.0.0/16"]
        }
      ]
      egress_rules = [
        {
          description = "All outbound"
          from_port   = 0
          to_port     = 0
          protocol    = "-1"
          cidr_blocks = ["0.0.0.0/0"]
        }
      ]
    }
  }
}

# ──────────────────────────────────────────────
# Variable for IAM users
# ──────────────────────────────────────────────
variable "iam_users" {
  description = "Map of IAM users to create"
  type = map(object({
    groups = list(string)
    tags   = map(string)
  }))
  default = {
    "alice" = {
      groups = ["developers", "readers"]
      tags   = { Department = "Engineering", Role = "Developer" }
    }
    "bob" = {
      groups = ["developers"]
      tags   = { Department = "Engineering", Role = "Senior Developer" }
    }
    "carol" = {
      groups = ["admins", "developers", "readers"]
      tags   = { Department = "DevOps", Role = "SRE" }
    }
  }
}

# ──────────────────────────────────────────────
# Variable for S3 bucket configurations
# ──────────────────────────────────────────────
variable "s3_buckets" {
  description = "Map of S3 buckets to create"
  type = map(object({
    versioning = bool
    lifecycle_rules = list(object({
      id                     = string
      prefix                 = string
      enabled                = bool
      transition_days        = number
      transition_class       = string
      expiration_days        = optional(number, 0)
    }))
    cors_rules = optional(list(object({
      allowed_headers = list(string)
      allowed_methods = list(string)
      allowed_origins = list(string)
      max_age_seconds = number
    })), [])
  }))
  default = {
    "app-assets" = {
      versioning = true
      lifecycle_rules = [
        {
          id               = "archive-old-versions"
          prefix           = ""
          enabled          = true
          transition_days  = 30
          transition_class = "STANDARD_IA"
          expiration_days  = 365
        },
        {
          id               = "archive-logs"
          prefix           = "logs/"
          enabled          = true
          transition_days  = 7
          transition_class = "GLACIER"
          expiration_days  = 90
        }
      ]
      cors_rules = [
        {
          allowed_headers = ["*"]
          allowed_methods = ["GET", "HEAD"]
          allowed_origins = ["https://example.com"]
          max_age_seconds = 3600
        }
      ]
    }
    "app-backups" = {
      versioning = false
      lifecycle_rules = [
        {
          id               = "expire-old-backups"
          prefix           = ""
          enabled          = true
          transition_days  = 90
          transition_class = "DEEP_ARCHIVE"
          expiration_days  = 730
        }
      ]
      cors_rules = []
    }
  }
}
```

---

## Part 2: Dynamic Blocks with `for_each`

### Step 2.1: Security Groups with Dynamic Blocks

Create `security-groups.tf`:

```hcl
# security-groups.tf — Dynamic blocks + for_each

# Get the default VPC
data "aws_vpc" "default" {
  default = true
}

# Create multiple security groups from a complex variable
resource "aws_security_group" "managed" {
  for_each = var.security_groups

  name        = "lab08-${each.key}-sg"
  description = each.value.description
  vpc_id      = data.aws_vpc.default.id

  # Dynamic ingress rules
  dynamic "ingress" {
    for_each = each.value.ingress_rules
    content {
      description = ingress.value.description
      from_port   = ingress.value.from_port
      to_port     = ingress.value.to_port
      protocol    = ingress.value.protocol
      cidr_blocks = ingress.value.cidr_blocks
    }
  }

  # Dynamic egress rules
  dynamic "egress" {
    for_each = each.value.egress_rules
    content {
      description = egress.value.description
      from_port   = egress.value.from_port
      to_port     = egress.value.to_port
      protocol    = egress.value.protocol
      cidr_blocks = egress.value.cidr_blocks
    }
  }

  tags = {
    Name = "lab08-${each.key}-sg"
    Tier = each.key
  }
}
```

---

## Part 3: `for_each` with Complex Data Structures

### Step 3.1: S3 Buckets with Nested Dynamic Blocks

Create `s3-buckets.tf`:

```hcl
# s3-buckets.tf — Nested dynamic blocks

resource "random_id" "bucket_suffix" {
  byte_length = 4
}

resource "aws_s3_bucket" "managed" {
  for_each = var.s3_buckets

  bucket = "lab08-${each.key}-${random_id.bucket_suffix.hex}"

  tags = {
    Name    = each.key
    Purpose = each.key
  }
}

# Versioning configuration
resource "aws_s3_bucket_versioning" "managed" {
  for_each = { for k, v in var.s3_buckets : k => v if v.versioning }

  bucket = aws_s3_bucket.managed[each.key].id

  versioning_configuration {
    status = "Enabled"
  }
}

# Lifecycle rules with dynamic blocks
resource "aws_s3_bucket_lifecycle_configuration" "managed" {
  for_each = { for k, v in var.s3_buckets : k => v if length(v.lifecycle_rules) > 0 }

  bucket = aws_s3_bucket.managed[each.key].id

  dynamic "rule" {
    for_each = each.value.lifecycle_rules
    content {
      id     = rule.value.id
      status = rule.value.enabled ? "Enabled" : "Disabled"

      filter {
        prefix = rule.value.prefix
      }

      transition {
        days          = rule.value.transition_days
        storage_class = rule.value.transition_class
      }

      # Conditionally include expiration
      dynamic "expiration" {
        for_each = rule.value.expiration_days > 0 ? [rule.value.expiration_days] : []
        content {
          days = expiration.value
        }
      }
    }
  }
}

# CORS configuration with dynamic blocks
resource "aws_s3_bucket_cors_configuration" "managed" {
  for_each = { for k, v in var.s3_buckets : k => v if length(v.cors_rules) > 0 }

  bucket = aws_s3_bucket.managed[each.key].id

  dynamic "cors_rule" {
    for_each = each.value.cors_rules
    content {
      allowed_headers = cors_rule.value.allowed_headers
      allowed_methods = cors_rule.value.allowed_methods
      allowed_origins = cors_rule.value.allowed_origins
      max_age_seconds = cors_rule.value.max_age_seconds
    }
  }
}

# Block public access on all buckets
resource "aws_s3_bucket_public_access_block" "managed" {
  for_each = var.s3_buckets

  bucket = aws_s3_bucket.managed[each.key].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
```

---

## Part 4: Data Sources

### Step 4.1: Using Various Data Sources

Create `data-sources.tf`:

```hcl
# data-sources.tf — Querying existing infrastructure

# ──────────────────────────────────────────────
# Get the current AWS account information
# ──────────────────────────────────────────────
data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

# ──────────────────────────────────────────────
# Get the latest Amazon Linux 2023 AMI
# ──────────────────────────────────────────────
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  filter {
    name   = "state"
    values = ["available"]
  }
}

# ──────────────────────────────────────────────
# Get all available AZs in the current region
# ──────────────────────────────────────────────
data "aws_availability_zones" "available" {
  state = "available"

  filter {
    name   = "opt-in-status"
    values = ["opt-in-not-required"]
  }
}

# ──────────────────────────────────────────────
# Get the default VPC subnets
# ──────────────────────────────────────────────
data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# ──────────────────────────────────────────────
# Get details for each subnet
# ──────────────────────────────────────────────
data "aws_subnet" "details" {
  for_each = toset(data.aws_subnets.default.ids)
  id       = each.value
}

# ──────────────────────────────────────────────
# Construct an IAM policy document
# ──────────────────────────────────────────────
data "aws_iam_policy_document" "s3_read_only" {
  statement {
    sid    = "AllowS3ReadOnly"
    effect = "Allow"

    actions = [
      "s3:GetObject",
      "s3:ListBucket",
    ]

    resources = flatten([
      for key, bucket in aws_s3_bucket.managed : [
        bucket.arn,
        "${bucket.arn}/*"
      ]
    ])
  }

  statement {
    sid    = "DenyDeleteOperations"
    effect = "Deny"

    actions = [
      "s3:DeleteBucket",
      "s3:DeleteObject",
    ]

    resources = ["*"]
  }
}

# ──────────────────────────────────────────────
# Create the policy from the data source
# ──────────────────────────────────────────────
resource "aws_iam_policy" "s3_read_only" {
  name        = "lab08-s3-read-only"
  description = "Read-only access to Lab 08 S3 buckets"
  policy      = data.aws_iam_policy_document.s3_read_only.json

  tags = {
    Name = "lab08-s3-read-only"
  }
}

# ──────────────────────────────────────────────
# Generate a report using data sources
# ──────────────────────────────────────────────
resource "local_file" "infrastructure_report" {
  filename = "${path.module}/infrastructure-report.json"
  content = jsonencode({
    account_id = data.aws_caller_identity.current.account_id
    region     = data.aws_region.current.name
    ami_id     = data.aws_ami.amazon_linux.id
    ami_name   = data.aws_ami.amazon_linux.name

    availability_zones = data.aws_availability_zones.available.names

    default_vpc = {
      id      = data.aws_vpc.default.id
      cidr    = data.aws_vpc.default.cidr_block
      subnets = {
        for id, subnet in data.aws_subnet.details :
        id => {
          cidr              = subnet.cidr_block
          availability_zone = subnet.availability_zone
        }
      }
    }

    managed_security_groups = {
      for key, sg in aws_security_group.managed :
      key => {
        id   = sg.id
        name = sg.name
      }
    }

    managed_s3_buckets = {
      for key, bucket in aws_s3_bucket.managed :
      key => {
        name = bucket.id
        arn  = bucket.arn
      }
    }
  })

  file_permission = "0644"
}
```

---

## Part 5: Provisioners and `null_resource`

### Understanding Provisioners

Provisioners execute commands on local or remote machines as part of resource creation or destruction. They are a **last resort** — prefer user_data, configuration management tools (Ansible), or cloud-init.

| Provisioner | Purpose |
|-------------|---------|
| `local-exec` | Run a command on the machine running Terraform |
| `remote-exec` | Run a command on the provisioned resource via SSH/WinRM |
| `file` | Copy files to the provisioned resource |

> **DevSecOps Warning:** Provisioners break Terraform's declarative model. They are not tracked in state, not idempotent by default, and can leave resources in a partially configured state if they fail.

### Step 5.1: Create Provisioner Examples

Create `provisioners.tf`:

```hcl
# provisioners.tf — Provisioners, null_resource, and terraform_data

# ──────────────────────────────────────────────
# null_resource: Custom workflows
# ──────────────────────────────────────────────

# Example 1: Run a local command when security groups change
resource "null_resource" "sg_audit_log" {
  # Triggers re-run when security groups change
  triggers = {
    sg_ids = join(",", [for sg in aws_security_group.managed : sg.id])
  }

  provisioner "local-exec" {
    command = <<-EOT
      echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) - Security groups updated:" >> ${path.module}/audit.log
      echo "  IDs: ${join(", ", [for sg in aws_security_group.managed : sg.id])}" >> ${path.module}/audit.log
      echo "  Names: ${join(", ", [for sg in aws_security_group.managed : sg.name])}" >> ${path.module}/audit.log
      echo "---" >> ${path.module}/audit.log
    EOT
  }
}

# Example 2: Validate infrastructure after creation
resource "null_resource" "post_deploy_validation" {
  depends_on = [
    aws_security_group.managed,
    aws_s3_bucket.managed,
  ]

  triggers = {
    always_run = timestamp()
  }

  provisioner "local-exec" {
    command = <<-EOT
      echo "=== Post-Deployment Validation ==="
      echo "Checking S3 buckets..."
      for bucket in ${join(" ", [for b in aws_s3_bucket.managed : b.id])}; do
        if aws s3api head-bucket --bucket "$bucket" 2>/dev/null; then
          echo "  OK: $bucket exists"
        else
          echo "  FAIL: $bucket not found"
          exit 1
        fi
      done
      echo ""
      echo "Checking security groups..."
      for sg in ${join(" ", [for sg in aws_security_group.managed : sg.id])}; do
        if aws ec2 describe-security-groups --group-ids "$sg" --query 'SecurityGroups[0].GroupId' --output text 2>/dev/null; then
          echo "  OK: $sg exists"
        else
          echo "  FAIL: $sg not found"
          exit 1
        fi
      done
      echo ""
      echo "All validations passed!"
    EOT

    interpreter = ["bash", "-c"]
  }
}

# Example 3: Generate documentation
resource "null_resource" "generate_docs" {
  triggers = {
    sg_config   = jsonencode(var.security_groups)
    bucket_config = jsonencode(var.s3_buckets)
  }

  provisioner "local-exec" {
    command = <<-EOT
      cat > ${path.module}/INFRASTRUCTURE.md << 'MARKDOWN'
      # Infrastructure Documentation
      ## Generated by Terraform

      ### Security Groups
      ${join("\n", [for key, sg in var.security_groups : "- **${key}**: ${sg.description} (${length(sg.ingress_rules)} ingress rules)"])}

      ### S3 Buckets
      ${join("\n", [for key, bucket in var.s3_buckets : "- **${key}**: versioning=${bucket.versioning}, ${length(bucket.lifecycle_rules)} lifecycle rules"])}

      ### Last Updated
      $(date -u +%Y-%m-%dT%H:%M:%SZ)
      MARKDOWN
    EOT

    interpreter = ["bash", "-c"]
  }
}

# ──────────────────────────────────────────────
# terraform_data: Modern replacement for null_resource
# (Terraform 1.4+)
# ──────────────────────────────────────────────

resource "terraform_data" "deployment_timestamp" {
  input = timestamp()

  provisioner "local-exec" {
    command = "echo 'Deployment completed at: ${self.input}'"
  }
}

# terraform_data with triggers_replace
resource "terraform_data" "config_checksum" {
  triggers_replace = [
    jsonencode(var.security_groups),
    jsonencode(var.s3_buckets),
  ]

  provisioner "local-exec" {
    command = "echo 'Configuration changed — rebuilding dependent resources'"
  }
}
```

---

## Part 6: Advanced `for_each` Patterns

### Step 6.1: Flattening Nested Structures

Create `advanced-patterns.tf`:

```hcl
# advanced-patterns.tf — Advanced for_each and for expressions

# ──────────────────────────────────────────────
# Flatten: Create a flat list from nested data
# ──────────────────────────────────────────────
locals {
  # Flatten IAM user-group memberships into individual assignments
  user_group_memberships = flatten([
    for user_name, user_config in var.iam_users : [
      for group in user_config.groups : {
        user_name  = user_name
        group_name = group
      }
    ]
  ])

  # Convert to a map for for_each (needs unique keys)
  user_group_map = {
    for membership in local.user_group_memberships :
    "${membership.user_name}-${membership.group_name}" => membership
  }

  # Flatten security group rules for a summary
  all_ingress_rules = flatten([
    for sg_name, sg_config in var.security_groups : [
      for rule in sg_config.ingress_rules : {
        sg_name     = sg_name
        description = rule.description
        port        = rule.from_port
        protocol    = rule.protocol
        cidrs       = rule.cidr_blocks
      }
    ]
  ])

  # Group rules by port for analysis
  rules_by_port = {
    for rule in local.all_ingress_rules :
    rule.port => rule...
  }

  # Find all open-to-internet rules (DevSecOps audit)
  public_facing_rules = [
    for rule in local.all_ingress_rules :
    rule if contains(rule.cidrs, "0.0.0.0/0")
  ]
}

# ──────────────────────────────────────────────
# IAM Groups (from unique group names in user configs)
# ──────────────────────────────────────────────
locals {
  all_groups = toset(flatten([for user in var.iam_users : user.groups]))
}

resource "aws_iam_group" "managed" {
  for_each = local.all_groups
  name     = "lab08-${each.value}"
}

# ──────────────────────────────────────────────
# IAM Users
# ──────────────────────────────────────────────
resource "aws_iam_user" "managed" {
  for_each = var.iam_users
  name     = "lab08-${each.key}"

  tags = merge(each.value.tags, {
    ManagedBy = "terraform"
  })
}

# ──────────────────────────────────────────────
# IAM Group Memberships (flattened)
# ──────────────────────────────────────────────
resource "aws_iam_user_group_membership" "managed" {
  for_each = {
    for user_name, user_config in var.iam_users :
    user_name => user_config
  }

  user   = aws_iam_user.managed[each.key].name
  groups = [for g in each.value.groups : aws_iam_group.managed[g].name]
}

# ──────────────────────────────────────────────
# Security Audit Report (using flattened data)
# ──────────────────────────────────────────────
resource "local_file" "security_audit" {
  filename = "${path.module}/security-audit.json"
  content = jsonencode({
    audit_timestamp = timestamp()
    summary = {
      total_security_groups = length(var.security_groups)
      total_ingress_rules   = length(local.all_ingress_rules)
      public_facing_rules   = length(local.public_facing_rules)
      iam_users             = length(var.iam_users)
      iam_groups            = length(local.all_groups)
    }
    public_facing_rules = [
      for rule in local.public_facing_rules : {
        security_group = rule.sg_name
        description    = rule.description
        port           = rule.port
        risk           = rule.port == 22 ? "HIGH" : rule.port == 443 ? "LOW" : "MEDIUM"
      }
    ]
    rules_by_port = {
      for port, rules in local.rules_by_port :
      tostring(port) => [for r in rules : "${r.sg_name}: ${r.description}"]
    }
  })

  file_permission = "0644"
}
```

---

## Part 7: Deploy and Explore

### Step 7.1: Initialize and Apply

```bash
cd ~/terraform-labs/lab08

terraform init
terraform plan
```

Review the plan carefully — you should see:

- 3 security groups (web, app, db) with dynamic ingress/egress rules
- 2 S3 buckets with lifecycle rules and CORS
- IAM users, groups, and group memberships
- An IAM policy generated from a data source
- null_resource provisioners
- Local file outputs (reports)

```bash
terraform apply -auto-approve
```

### Step 7.2: Examine the Results

```bash
# View the security groups
terraform state list | grep aws_security_group

# Show a specific security group with all its dynamic rules
terraform state show 'aws_security_group.managed["web"]'
terraform state show 'aws_security_group.managed["app"]'
terraform state show 'aws_security_group.managed["db"]'

# View IAM users
terraform state list | grep aws_iam_user

# View the infrastructure report
cat infrastructure-report.json | python3 -m json.tool

# View the security audit
cat security-audit.json | python3 -m json.tool

# View the audit log
cat audit.log
```

### Step 7.3: Explore the Data Sources

```bash
# Query data source results
terraform show | grep -A 5 "data.aws_caller_identity"
terraform show | grep -A 5 "data.aws_region"
terraform show | grep -A 3 "data.aws_availability_zones"

# View the generated IAM policy
terraform state show aws_iam_policy.s3_read_only
```

---

## Part 8: Advanced Patterns Reference

### Pattern: Conditional Nested Blocks

```hcl
resource "aws_instance" "example" {
  ami           = data.aws_ami.amazon_linux.id
  instance_type = "t2.micro"

  # Only add EBS block if extra storage needed
  dynamic "ebs_block_device" {
    for_each = var.extra_volumes
    content {
      device_name = ebs_block_device.value.device
      volume_size = ebs_block_device.value.size
      volume_type = ebs_block_device.value.type
      encrypted   = true
    }
  }
}
```

### Pattern: Chained `for_each` with Dependencies

```hcl
# Create resources that depend on other for_each resources
resource "aws_s3_bucket_notification" "events" {
  for_each = {
    for k, v in var.s3_buckets : k => v if length(v.lifecycle_rules) > 0
  }

  bucket = aws_s3_bucket.managed[each.key].id
  # ... notification configuration
}
```

### Pattern: Complex Filtering

```hcl
locals {
  # Only buckets with versioning AND CORS
  versioned_cors_buckets = {
    for k, v in var.s3_buckets : k => v
    if v.versioning && length(v.cors_rules) > 0
  }

  # IAM users in the "admins" group
  admin_users = {
    for name, config in var.iam_users : name => config
    if contains(config.groups, "admins")
  }
}
```

### Pattern: `try()` for Safe Attribute Access

```hcl
locals {
  # Safely access potentially missing attributes
  bucket_domains = {
    for k, v in aws_s3_bucket.managed :
    k => try(v.bucket_regional_domain_name, "unknown")
  }
}
```

---

## Expected Outcomes

After completing this lab, you should have:

- [x] Created security groups with dynamic ingress/egress blocks from complex variables
- [x] Used `for_each` with maps of objects to create multiple S3 buckets
- [x] Applied nested dynamic blocks (lifecycle rules, CORS rules)
- [x] Used data sources to query AWS account info, AMIs, AZs, and subnets
- [x] Built an IAM policy from a `data "aws_iam_policy_document"`
- [x] Used `null_resource` and `terraform_data` with provisioners
- [x] Flattened nested data structures for `for_each`
- [x] Generated security audit and infrastructure reports

---

## Bonus Challenges

### Challenge 1: Dynamic Block Nesting Depth

Create a resource with two levels of nested dynamic blocks. For example, an `aws_lb_listener` with dynamic `action` blocks that each contain a dynamic `forward` block with `target_group` entries.

### Challenge 2: Provider Functions (Terraform 1.8+)

If using Terraform 1.8+, explore provider-defined functions:

```hcl
output "arn_parts" {
  value = provider::aws::arn_parse(aws_iam_policy.s3_read_only.arn)
}
```

### Challenge 3: `precondition` and `postcondition`

Add lifecycle preconditions and postconditions to resources:

```hcl
resource "aws_security_group" "strict" {
  # ...

  lifecycle {
    precondition {
      condition     = !contains(flatten([for r in var.security_groups["web"].ingress_rules : r.cidr_blocks]), "0.0.0.0/0") || var.allow_public_access
      error_message = "Public access (0.0.0.0/0) requires explicit opt-in via allow_public_access variable."
    }
  }
}
```

### Challenge 4: Build a Complete DevSecOps Security Scanner

Extend the security audit report to:
1. Flag all security groups with `0.0.0.0/0` on port 22 as CRITICAL
2. Check that all S3 buckets have public access blocked
3. Verify all IAM users have appropriate group memberships
4. Output the report in a format that can be consumed by a CI/CD pipeline

---

## Cleanup

```bash
cd ~/terraform-labs/lab08
terraform destroy -auto-approve

cd ~
rm -rf ~/terraform-labs/lab08
```

---

## Congratulations!

You have completed all 8 Terraform labs in the DevSecOps course! Here is a summary of what you have learned:

| Lab | Topic | Key Skills |
|-----|-------|-----------|
| 01 | First Project | install, init, plan, apply, destroy |
| 02 | AWS EC2 | Providers, resources, data sources, user_data |
| 03 | Variables & Outputs | All variable types, locals, conditionals, tfvars |
| 04 | Remote State | S3 backend, DynamoDB locking, state commands |
| 05 | Modules | Reusable modules, module outputs, composition |
| 06 | Multi-Environment | Workspaces, directory structure, CI/CD patterns |
| 07 | Import | Importing existing infra, matching config, import blocks |
| 08 | Advanced | Dynamic blocks, complex for_each, provisioners, data sources |

### Recommended Next Steps

1. **Security scanning** — Integrate `tfsec`, `checkov`, or `trivy` into your Terraform workflow
2. **Policy as Code** — Explore Sentinel or Open Policy Agent (OPA) for governance
3. **CI/CD** — Build a full Terraform CI/CD pipeline with GitHub Actions or GitLab CI
4. **Testing** — Explore `terraform test` (built-in) and Terratest for infrastructure testing
5. **Scale** — Use Terragrunt or CDKTF for large-scale Terraform management
