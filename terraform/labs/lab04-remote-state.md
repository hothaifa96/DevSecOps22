# Lab 04: Remote State Management

## Difficulty: Intermediate

## Objectives

By the end of this lab, you will be able to:

- Explain why remote state is critical for team collaboration and security
- Create an S3 backend for Terraform state storage
- Enable state locking with DynamoDB
- Migrate local state to a remote backend
- Use `terraform state` commands: `list`, `show`, `mv`, `rm`, `pull`, `push`
- Access remote state from another Terraform project using `terraform_remote_state`

## Prerequisites

- Completed Labs 01–03
- AWS CLI configured with permissions to create S3 buckets and DynamoDB tables
- Terraform v1.0+ installed

## Estimated Time

75 minutes

---

## Part 1: Why Remote State?

### The Problems with Local State

| Problem | Risk |
|---------|------|
| State on one developer's machine | No team collaboration; single point of failure |
| State committed to Git | Sensitive data (passwords, keys) exposed |
| No locking mechanism | Concurrent applies corrupt state |
| No versioning | Cannot roll back to a previous state |
| No encryption at rest | Compliance violations |

### The Solution: S3 + DynamoDB Backend

- **S3** — stores the state file with encryption, versioning, and access control
- **DynamoDB** — provides state locking to prevent concurrent modifications

---

## Part 2: Create the Backend Infrastructure

> **Chicken-and-egg problem:** You need infrastructure (S3 + DynamoDB) to store state, but that infrastructure itself needs Terraform. We solve this by creating the backend resources first with local state, then migrating.

### Step 2.1: Set Up the Bootstrap Project

```bash
mkdir -p ~/terraform-labs/lab04/bootstrap
cd ~/terraform-labs/lab04/bootstrap
```

### Step 2.2: Create the Bootstrap Configuration

Create `main.tf`:

```hcl
# main.tf — Bootstrap: Create the S3 backend infrastructure

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
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name used in resource naming"
  type        = string
  default     = "devsecops-lab04"
}

# ──────────────────────────────────────────────
# Random suffix to ensure unique S3 bucket name
# ──────────────────────────────────────────────
resource "random_id" "suffix" {
  byte_length = 4
}

locals {
  bucket_name = "${var.project_name}-tfstate-${random_id.suffix.hex}"
  table_name  = "${var.project_name}-tflock"
}

# ──────────────────────────────────────────────
# S3 Bucket for Terraform State
# ──────────────────────────────────────────────
resource "aws_s3_bucket" "terraform_state" {
  bucket = local.bucket_name

  # Prevent accidental deletion of this bucket
  lifecycle {
    prevent_destroy = false # Set to true in production
  }

  tags = {
    Name        = local.bucket_name
    Purpose     = "Terraform State Storage"
    ManagedBy   = "Terraform-Bootstrap"
    Environment = "shared"
  }
}

# Enable versioning so we can see the full history of state files
resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Enable server-side encryption by default
resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

# Block all public access to the S3 bucket
resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ──────────────────────────────────────────────
# DynamoDB Table for State Locking
# ──────────────────────────────────────────────
resource "aws_dynamodb_table" "terraform_lock" {
  name         = local.table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = {
    Name        = local.table_name
    Purpose     = "Terraform State Locking"
    ManagedBy   = "Terraform-Bootstrap"
    Environment = "shared"
  }
}

# ──────────────────────────────────────────────
# Outputs — needed to configure the backend
# ──────────────────────────────────────────────
output "s3_bucket_name" {
  description = "S3 bucket name for Terraform state"
  value       = aws_s3_bucket.terraform_state.id
}

output "s3_bucket_arn" {
  description = "S3 bucket ARN"
  value       = aws_s3_bucket.terraform_state.arn
}

output "dynamodb_table_name" {
  description = "DynamoDB table name for state locking"
  value       = aws_dynamodb_table.terraform_lock.name
}

output "aws_region" {
  description = "AWS region"
  value       = var.aws_region
}

output "backend_config" {
  description = "Copy this into your backend configuration"
  value       = <<-EOT

    backend "s3" {
      bucket         = "${aws_s3_bucket.terraform_state.id}"
      key            = "YOUR_PROJECT/terraform.tfstate"
      region         = "${var.aws_region}"
      dynamodb_table = "${aws_dynamodb_table.terraform_lock.name}"
      encrypt        = true
    }
  EOT
}
```

### Step 2.3: Deploy the Backend Infrastructure

```bash
terraform init
terraform plan
terraform apply -auto-approve
```

**Save the outputs — you will need them:**

```bash
# Store the values for later use
export TF_STATE_BUCKET=$(terraform output -raw s3_bucket_name)
export TF_LOCK_TABLE=$(terraform output -raw dynamodb_table_name)
export TF_REGION=$(terraform output -raw aws_region)

echo "Bucket: $TF_STATE_BUCKET"
echo "Table:  $TF_LOCK_TABLE"
echo "Region: $TF_REGION"
```

---

## Part 3: Use the Remote Backend

### Step 3.1: Create the Main Project

```bash
mkdir -p ~/terraform-labs/lab04/main-project
cd ~/terraform-labs/lab04/main-project
```

### Step 3.2: Configure the S3 Backend

Create `providers.tf` (replace the placeholder values with your outputs from Part 2):

```hcl
# providers.tf

terraform {
  required_version = ">= 1.0.0"

  # Remote backend configuration
  backend "s3" {
    bucket         = "REPLACE_WITH_YOUR_BUCKET_NAME"  # e.g., devsecops-lab04-tfstate-a1b2c3d4
    key            = "lab04/main/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "REPLACE_WITH_YOUR_TABLE_NAME"   # e.g., devsecops-lab04-tflock
    encrypt        = true
  }

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
      Project     = "DevSecOps-Lab04"
      Environment = "lab"
      ManagedBy   = "terraform"
    }
  }
}
```

### Step 3.3: Create Sample Resources

Create `main.tf`:

```hcl
# main.tf

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "development"
}

# Security group to demonstrate state management
resource "aws_security_group" "web" {
  name        = "lab04-web-sg"
  description = "Web server security group for Lab 04"

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "lab04-web-sg"
  }
}

resource "aws_security_group" "db" {
  name        = "lab04-db-sg"
  description = "Database security group for Lab 04"

  ingress {
    description     = "PostgreSQL from web"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.web.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "lab04-db-sg"
  }
}

# Outputs
output "web_sg_id" {
  description = "Web security group ID"
  value       = aws_security_group.web.id
}

output "db_sg_id" {
  description = "Database security group ID"
  value       = aws_security_group.db.id
}

output "environment" {
  description = "Current environment"
  value       = var.environment
}
```

### Step 3.4: Initialize with Remote Backend

```bash
terraform init
```

**Expected Output:**

```
Initializing the backend...

Successfully configured the backend "s3"! Terraform will automatically
use this backend unless the backend configuration changes.
```

### Step 3.5: Apply the Configuration

```bash
terraform apply -auto-approve
```

### Step 3.6: Verify Remote State

```bash
# The local directory should NOT have a terraform.tfstate file
ls terraform.tfstate 2>/dev/null || echo "No local state file — it is in S3!"

# Verify the state is in S3
aws s3 ls s3://$TF_STATE_BUCKET/lab04/main/
```

**Expected Output:**

```
No local state file — it is in S3!
2024-XX-XX XX:XX:XX     XXXX terraform.tfstate
```

---

## Part 4: State Commands

### Step 4.1: `terraform state list`

List all resources tracked by Terraform:

```bash
terraform state list
```

**Expected Output:**

```
aws_security_group.db
aws_security_group.web
```

### Step 4.2: `terraform state show`

View detailed information about a specific resource:

```bash
terraform state show aws_security_group.web
```

This shows all attributes of the resource as Terraform knows them.

### Step 4.3: `terraform state pull`

Download the remote state file to stdout:

```bash
# View the remote state
terraform state pull | python3 -m json.tool | head -50

# Save it to a local file for inspection
terraform state pull > state-backup.json
```

### Step 4.4: `terraform state mv`

Rename a resource in the state (without destroying/recreating it):

```bash
# First, rename in state
terraform state mv aws_security_group.web aws_security_group.frontend

# The plan will now show an error because main.tf still references "web"
terraform plan
```

You will see an error because the code still uses `aws_security_group.web`. Let's fix it:

```bash
# Undo the move
terraform state mv aws_security_group.frontend aws_security_group.web

# Verify it is back
terraform state list
terraform plan  # Should show "No changes"
```

> **Use Case:** `state mv` is essential when refactoring code — renaming resources, moving resources into modules, etc.

### Step 4.5: `terraform state rm`

Remove a resource from state **without destroying it** in the cloud:

```bash
# Remove the DB security group from Terraform's tracking
terraform state rm aws_security_group.db

# Now Terraform doesn't know about it
terraform state list

# Plan will want to create a NEW db security group
terraform plan
```

**Expected Plan Output:**

```
Plan: 1 to add, 0 to change, 0 to destroy.
```

Re-import it to fix the state (preview of Lab 07):

```bash
# Get the security group ID from AWS
DB_SG_ID=$(aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=lab04-db-sg" \
  --query "SecurityGroups[0].GroupId" --output text)

echo "Re-importing: $DB_SG_ID"

# Import it back
terraform import aws_security_group.db $DB_SG_ID

# Verify
terraform plan  # Should show "No changes" or minor tag diffs
```

### Step 4.6: Examine State Locking

Open two terminal windows and try to apply simultaneously:

**Terminal 1:**

```bash
cd ~/terraform-labs/lab04/main-project
terraform apply -auto-approve
```

**Terminal 2 (while Terminal 1 is running):**

```bash
cd ~/terraform-labs/lab04/main-project
terraform plan
```

**Expected Output in Terminal 2:**

```
Error: Error acquiring the state lock

Error message: ConditionalCheckFailedException: The conditional request failed
Lock Info:
  ID:        xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
  Path:      devsecops-lab04-tfstate-xxx/lab04/main/terraform.tfstate
  Operation: OperationTypeApply
  Who:       user@hostname
  Version:   1.x.x
  Created:   2024-XX-XX XX:XX:XX.XXX UTC
```

This proves DynamoDB locking is working!

> **Force Unlock (Emergency Only):**
> ```bash
> terraform force-unlock LOCK_ID
> ```
> Only use this if a lock is stuck due to a crashed Terraform process.

---

## Part 5: Access Remote State from Another Project

### Step 5.1: Create a Second Project

```bash
mkdir -p ~/terraform-labs/lab04/app-project
cd ~/terraform-labs/lab04/app-project
```

### Step 5.2: Reference Remote State

Create `main.tf`:

```hcl
# main.tf — Reads state from the main-project

terraform {
  required_version = ">= 1.0.0"

  backend "s3" {
    bucket         = "REPLACE_WITH_YOUR_BUCKET_NAME"
    key            = "lab04/app/terraform.tfstate"    # Different key!
    region         = "us-east-1"
    dynamodb_table = "REPLACE_WITH_YOUR_TABLE_NAME"
    encrypt        = true
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

# Read the state from the main project
data "terraform_remote_state" "main" {
  backend = "s3"
  config = {
    bucket = "REPLACE_WITH_YOUR_BUCKET_NAME"
    key    = "lab04/main/terraform.tfstate"
    region = "us-east-1"
  }
}

# Use outputs from the remote state
output "main_project_web_sg" {
  description = "Web SG ID from main project"
  value       = data.terraform_remote_state.main.outputs.web_sg_id
}

output "main_project_db_sg" {
  description = "DB SG ID from main project"
  value       = data.terraform_remote_state.main.outputs.db_sg_id
}

output "main_project_environment" {
  description = "Environment from main project"
  value       = data.terraform_remote_state.main.outputs.environment
}
```

### Step 5.3: Apply and Verify Cross-Project State Access

```bash
terraform init
terraform apply -auto-approve
```

**Expected Output:**

```
Apply complete! Resources: 0 added, 0 changed, 0 destroyed.

Outputs:

main_project_db_sg = "sg-0abcdef1234567890"
main_project_environment = "development"
main_project_web_sg = "sg-0abcdef9876543210"
```

You have successfully read another project's state.

---

## Part 6: State File Versioning

### Step 6.1: View S3 Versioning

```bash
# List all versions of the state file
aws s3api list-object-versions \
  --bucket $TF_STATE_BUCKET \
  --prefix "lab04/main/terraform.tfstate" \
  --query "Versions[].{VersionId:VersionId,LastModified:LastModified,Size:Size}" \
  --output table
```

### Step 6.2: Recover a Previous State Version (Demonstration)

```bash
# Get the previous version ID
PREV_VERSION=$(aws s3api list-object-versions \
  --bucket $TF_STATE_BUCKET \
  --prefix "lab04/main/terraform.tfstate" \
  --query "Versions[1].VersionId" --output text)

echo "Previous version: $PREV_VERSION"

# Download it (for inspection only)
aws s3api get-object \
  --bucket $TF_STATE_BUCKET \
  --key "lab04/main/terraform.tfstate" \
  --version-id $PREV_VERSION \
  previous-state.json

cat previous-state.json | python3 -m json.tool | head -30
```

> **DevSecOps Note:** S3 versioning gives you state history. In a disaster recovery scenario, you can restore a previous state version.

---

## Expected Outcomes

After completing this lab, you should have:

- [x] Created an S3 bucket with encryption, versioning, and public access blocking
- [x] Created a DynamoDB table for state locking
- [x] Configured a Terraform project to use the S3 backend
- [x] Verified that state is stored remotely (no local `terraform.tfstate`)
- [x] Used `state list`, `state show`, `state pull`, `state mv`, and `state rm`
- [x] Observed state locking in action
- [x] Read remote state from a separate project using `terraform_remote_state`
- [x] Examined state file versioning in S3

---

## Bonus Challenges

### Challenge 1: Migrate Existing Local State to S3

Create a project with local state, add the S3 backend configuration, and run `terraform init -migrate-state` to move the state to S3.

### Challenge 2: Backend Partial Configuration

Instead of hardcoding the backend config, use partial configuration:

```hcl
backend "s3" {}
```

And pass values at init time:

```bash
terraform init \
  -backend-config="bucket=YOUR_BUCKET" \
  -backend-config="key=lab04/partial/terraform.tfstate" \
  -backend-config="region=us-east-1" \
  -backend-config="dynamodb_table=YOUR_TABLE" \
  -backend-config="encrypt=true"
```

This is useful in CI/CD pipelines where the backend varies.

### Challenge 3: S3 Bucket Policy

Write an IAM policy that grants **least-privilege** access to the state bucket. It should allow only `s3:GetObject`, `s3:PutObject`, and `s3:ListBucket` for the Terraform state path.

### Challenge 4: Investigate the Lock Table

After running `terraform apply`, quickly check the DynamoDB table:

```bash
aws dynamodb scan --table-name $TF_LOCK_TABLE
```

Try running a long operation and scan the table while it is locked.

---

## Cleanup

**Destroy the app project first:**

```bash
cd ~/terraform-labs/lab04/app-project
terraform destroy -auto-approve
```

**Destroy the main project:**

```bash
cd ~/terraform-labs/lab04/main-project
terraform destroy -auto-approve
```

**Destroy the bootstrap (backend infrastructure):**

```bash
cd ~/terraform-labs/lab04/bootstrap

# Empty the S3 bucket first (required before deletion)
aws s3api list-object-versions --bucket $TF_STATE_BUCKET \
  --query '{Objects: Versions[].{Key:Key,VersionId:VersionId}}' \
  --output json | \
  aws s3api delete-objects --bucket $TF_STATE_BUCKET --delete file:///dev/stdin 2>/dev/null

aws s3api list-object-versions --bucket $TF_STATE_BUCKET \
  --query '{Objects: DeleteMarkers[].{Key:Key,VersionId:VersionId}}' \
  --output json | \
  aws s3api delete-objects --bucket $TF_STATE_BUCKET --delete file:///dev/stdin 2>/dev/null

terraform destroy -auto-approve
```

```bash
cd ~
rm -rf ~/terraform-labs/lab04
```

---

## Next Lab

Proceed to [Lab 05: Terraform Modules](lab05-modules.md) to learn how to create reusable, composable infrastructure components.
