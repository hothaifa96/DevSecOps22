# Lesson 6: Terraform State

---

## Table of Contents

1. [What is Terraform State?](#what-is-terraform-state)
2. [How State Works](#how-state-works)
3. [Local vs. Remote State](#local-vs-remote-state)
4. [Remote Backends](#remote-backends)
5. [State Locking](#state-locking)
6. [State Commands](#state-commands)
7. [Terraform Import](#terraform-import)
8. [State Security in DevSecOps](#state-security-in-devsecops)
9. [Key Takeaways](#key-takeaways)

---

## What is Terraform State?

Terraform state is a **JSON file** that acts as a database mapping your Terraform configuration to real-world infrastructure resources. It is the single source of truth for what Terraform has created and manages.

### Why State Exists

Without state, Terraform would have no way to know:
- Which real resources correspond to which configuration blocks
- What order to destroy resources
- Whether a resource needs to be created, updated, or destroyed

### What State Tracks

```json
{
  "version": 4,
  "terraform_version": "1.7.0",
  "serial": 5,
  "lineage": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "outputs": {
    "vpc_id": {
      "value": "vpc-0123456789abcdef0",
      "type": "string"
    }
  },
  "resources": [
    {
      "mode": "managed",
      "type": "aws_vpc",
      "name": "main",
      "provider": "provider[\"registry.terraform.io/hashicorp/aws\"]",
      "instances": [
        {
          "schema_version": 1,
          "attributes": {
            "id": "vpc-0123456789abcdef0",
            "cidr_block": "10.0.0.0/16",
            "enable_dns_hostnames": true,
            "tags": {
              "Name": "main-vpc"
            }
          }
        }
      ]
    }
  ]
}
```

### Key State Concepts

| Concept | Description |
|---------|-------------|
| **Serial** | Increments with every state change (used for locking) |
| **Lineage** | Unique ID for this state's history (prevents mixing states) |
| **Resources** | List of all managed resources with their current attributes |
| **Outputs** | Cached output values |
| **Version** | State file format version |

---

## How State Works

### The Terraform Workflow with State

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  .tf Files  │     │  State File  │     │  Real Cloud   │
│  (desired)  │     │  (recorded)  │     │  (actual)     │
└──────┬──────┘     └──────┬───────┘     └──────┬────────┘
       │                   │                     │
       └─────────┬─────────┘                     │
                 │                               │
          ┌──────▼──────┐                        │
          │   Compare   │◄───────────────────────┘
          │  (terraform │    Refresh: Read actual
          │    plan)    │    state from cloud
          └──────┬──────┘
                 │
          ┌──────▼──────┐
          │   Changes   │
          │  (create,   │
          │   update,   │
          │   destroy)  │
          └─────────────┘
```

1. **Read**: Terraform reads your `.tf` files (desired state)
2. **Refresh**: Terraform queries the cloud to get the actual state of resources
3. **Compare**: Terraform compares desired state, recorded state, and actual state
4. **Plan**: Terraform determines what changes are needed
5. **Apply**: Terraform makes the changes and updates the state file

### Configuration Drift

**Drift** occurs when someone changes infrastructure outside of Terraform (e.g., via the AWS Console). Terraform detects this by comparing the state file with the actual cloud state.

```bash
# Detect drift without making changes
terraform plan

# Output might show:
# ~ resource "aws_instance" "web" {
#     ~ instance_type = "t3.large" -> "t3.micro"  # Someone changed it manually!
#   }

# Force refresh and detect drift
terraform plan -refresh-only

# Apply refresh to update state to match reality
terraform apply -refresh-only
```

---

## Local vs. Remote State

### Local State

By default, Terraform stores state in a local file called `terraform.tfstate`.

```
project/
├── main.tf
├── terraform.tfstate        # Current state
└── terraform.tfstate.backup # Previous state
```

**Pros:**
- Simple -- works out of the box
- Good for learning and personal projects

**Cons:**
- No collaboration -- only one person has the state
- No locking -- concurrent operations can corrupt state
- Not secure -- state file sits on your laptop
- No backup -- if your disk dies, state is lost

### Remote State

Remote state stores the state file in a shared, durable location:

```hcl
terraform {
  backend "s3" {
    bucket = "my-terraform-state"
    key    = "prod/terraform.tfstate"
    region = "us-east-1"
  }
}
```

**Pros:**
- Shared access for teams
- State locking prevents corruption
- Encryption at rest and in transit
- Versioning for rollback
- Durable storage (99.999999999% for S3)

**Cons:**
- Requires initial setup of the backend
- Additional infrastructure to manage (the state bucket itself)

---

## Remote Backends

### AWS S3 Backend (Most Common)

#### Step 1: Create the Backend Infrastructure

```hcl
# backend-setup/main.tf (apply this FIRST, separately)

provider "aws" {
  region = "us-east-1"
}

# S3 bucket for state storage
resource "aws_s3_bucket" "terraform_state" {
  bucket = "my-company-terraform-state"

  lifecycle {
    prevent_destroy = true
  }
}

# Enable versioning for state history
resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Encrypt state at rest
resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
  }
}

# Block public access
resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# DynamoDB table for state locking
resource "aws_dynamodb_table" "terraform_locks" {
  name         = "terraform-state-locks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = {
    Name      = "Terraform State Lock Table"
    ManagedBy = "Terraform"
  }
}
```

#### Step 2: Configure the Backend

```hcl
# main.tf
terraform {
  backend "s3" {
    bucket         = "my-company-terraform-state"
    key            = "projects/my-app/prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-locks"  # For state locking
  }
}
```

#### Step 3: Initialize with the New Backend

```bash
# Terraform will ask to migrate local state to S3
terraform init

# Output:
# Initializing the backend...
# Do you want to copy existing state to the new backend? yes
# Successfully configured the backend "s3"!
```

### Azure Blob Storage Backend

```hcl
terraform {
  backend "azurerm" {
    resource_group_name  = "rg-terraform-state"
    storage_account_name = "stterraformstate001"
    container_name       = "tfstate"
    key                  = "prod.terraform.tfstate"
  }
}
```

**Setup the backend infrastructure:**

```bash
# Create resource group
az group create --name rg-terraform-state --location eastus

# Create storage account
az storage account create \
  --name stterraformstate001 \
  --resource-group rg-terraform-state \
  --sku Standard_LRS \
  --encryption-services blob

# Create blob container
az storage container create \
  --name tfstate \
  --account-name stterraformstate001
```

### GCS (Google Cloud Storage) Backend

```hcl
terraform {
  backend "gcs" {
    bucket = "my-terraform-state-bucket"
    prefix = "prod/terraform/state"
  }
}
```

**Setup the backend infrastructure:**

```bash
# Create bucket
gsutil mb -p my-project -l us-central1 gs://my-terraform-state-bucket

# Enable versioning
gsutil versioning set on gs://my-terraform-state-bucket
```

### Terraform Cloud / HCP Terraform Backend

```hcl
terraform {
  cloud {
    organization = "my-org"

    workspaces {
      name = "my-app-prod"
    }
  }
}
```

### Backend Configuration with Partial Config

For CI/CD pipelines, you can separate backend config from your code:

```hcl
# main.tf
terraform {
  backend "s3" {}  # Empty -- config provided at init time
}
```

```bash
# backend.hcl
bucket         = "my-company-terraform-state"
key            = "prod/terraform.tfstate"
region         = "us-east-1"
encrypt        = true
dynamodb_table = "terraform-state-locks"
```

```bash
# Initialize with backend config file
terraform init -backend-config=backend.hcl

# Or with individual flags
terraform init \
  -backend-config="bucket=my-company-terraform-state" \
  -backend-config="key=prod/terraform.tfstate" \
  -backend-config="region=us-east-1"
```

---

## State Locking

State locking prevents concurrent operations from corrupting the state file. When one person runs `terraform apply`, the state is locked so no one else can modify it simultaneously.

### How Locking Works

```
User A: terraform apply
  → Acquires lock on state file
  → Makes changes...

User B: terraform apply
  → Tries to acquire lock
  → ERROR: "Error locking state: ConditionalCheckFailedException"
  → Must wait for User A to finish

User A: apply complete
  → Releases lock

User B: terraform apply
  → Acquires lock (success)
  → Makes changes...
```

### Locking by Backend

| Backend | Locking Mechanism |
|---------|-------------------|
| **S3** | DynamoDB table |
| **Azure Blob** | Native blob leasing |
| **GCS** | Native object locking |
| **Terraform Cloud** | Built-in |
| **Local** | Local lock file |

### Force Unlocking (Emergency Only)

```bash
# If a lock is stuck (e.g., process crashed), you can force unlock
terraform force-unlock LOCK_ID

# Get the lock ID from the error message:
# Error locking state: Error acquiring the state lock
# Lock Info:
#   ID:        a1b2c3d4-e5f6-7890-abcd-ef1234567890
#   Path:      my-terraform-state/prod/terraform.tfstate
#   Operation: OperationTypeApply
#   Who:       user@machine
#   Version:   1.7.0
#   Created:   2024-01-15 10:30:00 UTC
```

> **Warning**: Only force-unlock if you are certain no other operation is in progress. Incorrect force-unlock can corrupt state.

---

## State Commands

### Listing Resources

```bash
# List all resources in state
terraform state list

# Output:
# aws_vpc.main
# aws_subnet.public[0]
# aws_subnet.public[1]
# aws_security_group.web
# aws_instance.web["web-1"]
# aws_instance.web["web-2"]

# Filter by resource type
terraform state list aws_instance
```

### Showing Resource Details

```bash
# Show detailed info for a specific resource
terraform state show aws_instance.web[\"web-1\"]

# Output:
# resource "aws_instance" "web" {
#   ami                    = "ami-0c55b159cbfafe1f0"
#   id                     = "i-1234567890abcdef0"
#   instance_type          = "t3.micro"
#   public_ip              = "54.123.45.67"
#   ...
# }
```

### Moving / Renaming Resources

When you rename a resource in your code, Terraform thinks the old one should be destroyed and a new one created. Use `state mv` to update the state instead:

```bash
# Rename a resource (avoids destroy + recreate)
terraform state mv aws_instance.web aws_instance.app_server

# Move a resource into a module
terraform state mv aws_instance.web module.compute.aws_instance.web

# Move between modules
terraform state mv module.old.aws_instance.web module.new.aws_instance.web
```

In Terraform 1.1+, you can also use the `moved` block in code:

```hcl
moved {
  from = aws_instance.web
  to   = aws_instance.app_server
}
```

### Removing Resources from State

Remove a resource from state without destroying the actual infrastructure:

```bash
# Remove from state (resource continues to exist in the cloud)
terraform state rm aws_instance.web

# Use case: "I want Terraform to stop managing this resource"
# The EC2 instance will continue running but Terraform no longer tracks it
```

In Terraform 1.7+, you can use the `removed` block:

```hcl
removed {
  from = aws_instance.web

  lifecycle {
    destroy = false  # Don't destroy the real resource
  }
}
```

### Pulling and Pushing State

```bash
# Download remote state to a local file
terraform state pull > state.json

# Upload a local state file to the remote backend (DANGEROUS)
terraform state push state.json
```

### Replacing (Tainting) Resources

Force recreation of a resource on the next apply:

```bash
# Mark a resource for recreation (Terraform 1.5+)
terraform apply -replace="aws_instance.web"

# Legacy command (still works but deprecated)
terraform taint aws_instance.web
terraform untaint aws_instance.web
```

---

## Terraform Import

`terraform import` brings existing infrastructure under Terraform management by adding it to the state file.

### When to Use Import

- You have infrastructure created manually (via console or CLI)
- You are adopting Terraform for an existing environment
- A resource was removed from state but still exists in the cloud

### Classic Import (CLI)

#### Step 1: Write the Resource Block

```hcl
# main.tf
resource "aws_instance" "existing_server" {
  # Leave arguments empty or minimal for now
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.micro"
}
```

#### Step 2: Run Import

```bash
terraform import aws_instance.existing_server i-1234567890abcdef0
# aws_instance.existing_server: Importing from ID "i-1234567890abcdef0"...
# aws_instance.existing_server: Import successful!
```

#### Step 3: Update Configuration to Match

```bash
# Show the imported resource's current attributes
terraform state show aws_instance.existing_server

# Update main.tf to match the actual configuration
# Then run plan to verify no changes
terraform plan
# Should show: "No changes. Infrastructure is up-to-date."
```

### Import Blocks (Terraform 1.5+)

The modern approach uses `import` blocks in your configuration:

```hcl
# import.tf
import {
  to = aws_instance.existing_server
  id = "i-1234567890abcdef0"
}

import {
  to = aws_s3_bucket.existing_bucket
  id = "my-existing-bucket-name"
}

import {
  to = aws_vpc.existing_vpc
  id = "vpc-0123456789abcdef0"
}
```

```bash
# Generate configuration for imported resources (Terraform 1.5+)
terraform plan -generate-config-out=generated.tf

# Review generated.tf, then apply
terraform apply
```

### Import Examples for Common Resources

```bash
# EC2 Instance
terraform import aws_instance.web i-1234567890abcdef0

# S3 Bucket
terraform import aws_s3_bucket.data my-bucket-name

# VPC
terraform import aws_vpc.main vpc-0123456789abcdef0

# Security Group
terraform import aws_security_group.web sg-0123456789abcdef0

# RDS Instance
terraform import aws_db_instance.main my-database-identifier

# IAM Role
terraform import aws_iam_role.app MyRoleName

# Azure Resource Group
terraform import azurerm_resource_group.example /subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/mygroup

# GCP Compute Instance
terraform import google_compute_instance.web projects/my-project/zones/us-central1-a/instances/my-instance
```

---

## State Security in DevSecOps

### Threats to State

| Threat | Risk | Mitigation |
|--------|------|------------|
| **Plaintext secrets** | Passwords, keys stored in state | Encrypt state, limit access |
| **Unauthorized access** | Anyone with state can see infrastructure | IAM policies, bucket policies |
| **State corruption** | Concurrent modifications | State locking |
| **State loss** | Lost state = unmanaged infra | Versioning, backups |
| **State tampering** | Malicious state modifications | Integrity checks, audit logs |

### Best Practices for State Security

#### 1. Encrypt State at Rest

```hcl
# S3 backend with KMS encryption
terraform {
  backend "s3" {
    bucket         = "my-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    kms_key_id     = "arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012"
    dynamodb_table = "terraform-locks"
  }
}
```

#### 2. Restrict Access with IAM

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject"],
      "Resource": "arn:aws:s3:::my-terraform-state/prod/*",
      "Condition": {
        "StringEquals": {
          "aws:PrincipalTag/Team": "DevOps"
        }
      }
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:DeleteItem"
      ],
      "Resource": "arn:aws:dynamodb:us-east-1:123456789012:table/terraform-locks"
    }
  ]
}
```

#### 3. Enable Bucket Versioning

```hcl
resource "aws_s3_bucket_versioning" "state" {
  bucket = aws_s3_bucket.terraform_state.id
  versioning_configuration {
    status = "Enabled"
  }
}
```

#### 4. Enable Access Logging

```hcl
resource "aws_s3_bucket_logging" "state" {
  bucket = aws_s3_bucket.terraform_state.id

  target_bucket = aws_s3_bucket.log_bucket.id
  target_prefix = "terraform-state-logs/"
}
```

#### 5. Use Separate State Files per Environment

```
terraform-state-bucket/
├── dev/
│   └── terraform.tfstate
├── staging/
│   └── terraform.tfstate
└── prod/
    └── terraform.tfstate
```

This limits the blast radius -- a compromised dev state does not expose production resources.

---

## Key Takeaways

1. **State is Terraform's source of truth** -- it maps configuration to real infrastructure
2. **Never use local state for team projects** -- always configure a remote backend
3. **Enable state locking** (DynamoDB for S3, built-in for Azure/GCS) to prevent corruption
4. **Encrypt state at rest and in transit** -- it contains sensitive data
5. **Enable versioning** on your state bucket for rollback capability
6. **Use `terraform state` commands** carefully -- they modify state directly
7. **Use `terraform import`** to bring existing infrastructure under Terraform management
8. **Separate state per environment** to limit blast radius
9. **Never manually edit the state file** -- use CLI commands instead
10. **Treat state as a secret** in your DevSecOps practices

---

## What's Next?

In the next lesson, we will learn about Terraform modules -- how to organize and reuse your infrastructure code.

[Previous Lesson: Terraform Variables](./05-terraform-variables.md) | [Next Lesson: Terraform Modules -->](./07-terraform-modules.md)
