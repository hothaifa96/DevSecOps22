# Lab 07: Terraform Import

## Difficulty: Advanced

## Objectives

By the end of this lab, you will be able to:

- Import existing AWS resources into Terraform state
- Write Terraform configuration that matches existing infrastructure
- Verify imports produce a clean `terraform plan` (no changes)
- Use both the CLI `terraform import` command and the `import` block (Terraform 1.5+)
- Handle common import challenges and edge cases
- Understand when and why importing is necessary in DevSecOps

## Prerequisites

- Completed Labs 01–06
- AWS CLI configured
- Terraform v1.5+ installed (for `import` blocks)
- Understanding of AWS resources (VPC, EC2, Security Groups, S3)

## Estimated Time

75 minutes

---

## Part 1: Why Import?

### Common Scenarios

| Scenario | Description |
|----------|-------------|
| **Brownfield adoption** | Organization has existing cloud infra, now adopting Terraform |
| **Console-created resources** | Someone created resources via the AWS Console |
| **Migration from other IaC** | Moving from CloudFormation, Pulumi, etc. |
| **Disaster recovery** | Recreating state after a state file loss |
| **Refactoring** | Moving resources between Terraform projects |

### The Import Workflow

```
1. Identify existing resource in AWS
2. Write matching Terraform configuration
3. Import the resource into state
4. Run terraform plan → verify "No changes"
5. Iterate until the plan is clean
```

> **DevSecOps Insight:** Importing is essential for bringing "shadow IT" resources under proper management, ensuring compliance and auditability.

---

## Part 2: Create Resources Outside Terraform (Simulating Existing Infra)

We will use the AWS CLI to create resources that simulate pre-existing infrastructure, then import them.

### Step 2.1: Set Up the Project

```bash
mkdir -p ~/terraform-labs/lab07
cd ~/terraform-labs/lab07
```

### Step 2.2: Create Resources via AWS CLI

```bash
# ── Create a VPC ──────────────────────────────
VPC_ID=$(aws ec2 create-vpc \
  --cidr-block 10.99.0.0/16 \
  --query 'Vpc.VpcId' --output text)

aws ec2 create-tags --resources $VPC_ID \
  --tags Key=Name,Value=legacy-app-vpc Key=Environment,Value=production Key=CreatedBy,Value=manual

aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-support
aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-hostnames

echo "VPC ID: $VPC_ID"

# ── Create a Subnet ──────────────────────────
SUBNET_ID=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.99.1.0/24 \
  --availability-zone us-east-1a \
  --query 'Subnet.SubnetId' --output text)

aws ec2 create-tags --resources $SUBNET_ID \
  --tags Key=Name,Value=legacy-app-subnet Key=Environment,Value=production

echo "Subnet ID: $SUBNET_ID"

# ── Create a Security Group ──────────────────
SG_ID=$(aws ec2 create-security-group \
  --group-name legacy-app-sg \
  --description "Legacy application security group" \
  --vpc-id $VPC_ID \
  --query 'GroupId' --output text)

aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp --port 443 --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp --port 80 --cidr 0.0.0.0/0

aws ec2 create-tags --resources $SG_ID \
  --tags Key=Name,Value=legacy-app-sg Key=Environment,Value=production

echo "Security Group ID: $SG_ID"

# ── Create an S3 Bucket ─────────────────────
BUCKET_NAME="legacy-app-data-$(date +%s)"
aws s3api create-bucket --bucket $BUCKET_NAME --region us-east-1

aws s3api put-bucket-tagging --bucket $BUCKET_NAME \
  --tagging 'TagSet=[{Key=Name,Value=legacy-app-data},{Key=Environment,Value=production}]'

echo "S3 Bucket: $BUCKET_NAME"

# ── Save IDs for later use ───────────────────
cat > resource-ids.env << EOF
export VPC_ID=$VPC_ID
export SUBNET_ID=$SUBNET_ID
export SG_ID=$SG_ID
export BUCKET_NAME=$BUCKET_NAME
EOF

echo ""
echo "Resource IDs saved to resource-ids.env"
cat resource-ids.env
```

### Step 2.3: Verify Resources Exist

```bash
source resource-ids.env

echo "=== VPC ==="
aws ec2 describe-vpcs --vpc-ids $VPC_ID --query 'Vpcs[0].{Id:VpcId,CIDR:CidrBlock,Tags:Tags}' --output table

echo "=== Subnet ==="
aws ec2 describe-subnets --subnet-ids $SUBNET_ID --query 'Subnets[0].{Id:SubnetId,CIDR:CidrBlock,AZ:AvailabilityZone}' --output table

echo "=== Security Group ==="
aws ec2 describe-security-groups --group-ids $SG_ID --query 'SecurityGroups[0].{Id:GroupId,Name:GroupName,Rules:IpPermissions}' --output json

echo "=== S3 Bucket ==="
aws s3api get-bucket-tagging --bucket $BUCKET_NAME --output table
```

---

## Part 3: Method A — CLI Import (`terraform import`)

### Step 3.1: Write the Terraform Configuration

The key challenge: you must write configuration that **matches the existing resource exactly**.

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
  }
}

provider "aws" {
  region = "us-east-1"
}
```

Create `main.tf` — start with empty resource blocks:

```hcl
# main.tf — Resources to import

# ──────────────────────────────────────────────
# VPC
# ──────────────────────────────────────────────
resource "aws_vpc" "legacy" {
  cidr_block           = "10.99.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name        = "legacy-app-vpc"
    Environment = "production"
    CreatedBy   = "manual"
  }
}

# ──────────────────────────────────────────────
# Subnet
# ──────────────────────────────────────────────
resource "aws_subnet" "legacy" {
  vpc_id            = aws_vpc.legacy.id
  cidr_block        = "10.99.1.0/24"
  availability_zone = "us-east-1a"

  tags = {
    Name        = "legacy-app-subnet"
    Environment = "production"
  }
}

# ──────────────────────────────────────────────
# Security Group
# ──────────────────────────────────────────────
resource "aws_security_group" "legacy" {
  name        = "legacy-app-sg"
  description = "Legacy application security group"
  vpc_id      = aws_vpc.legacy.id

  ingress {
    description = ""
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = ""
    from_port   = 80
    to_port     = 80
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
    Name        = "legacy-app-sg"
    Environment = "production"
  }
}

# ──────────────────────────────────────────────
# S3 Bucket
# ──────────────────────────────────────────────
resource "aws_s3_bucket" "legacy" {
  bucket = "" # Will be filled after examining the resource

  tags = {
    Name        = "legacy-app-data"
    Environment = "production"
  }
}
```

### Step 3.2: Initialize Terraform

```bash
terraform init
```

### Step 3.3: Import the VPC

```bash
source resource-ids.env

# Import the VPC
terraform import aws_vpc.legacy $VPC_ID
```

**Expected Output:**

```
aws_vpc.legacy: Importing from ID "vpc-0abc123def456"...
aws_vpc.legacy: Import prepared!
  Prepared aws_vpc.legacy for import
aws_vpc.legacy: Refreshing state... [id=vpc-0abc123def456]

Import successful!

The resources that were imported are shown above. These resources are now in
your Terraform state and will henceforth be managed by Terraform.
```

### Step 3.4: Check the Plan After Import

```bash
terraform plan
```

You may see differences. This is the **iterative matching process**:

```
# aws_vpc.legacy will be updated in-place
~ resource "aws_vpc" "legacy" {
    ~ enable_dns_hostnames = true -> false  # Example diff
  }
```

**Fix any differences** by updating your `main.tf` to match the actual resource. Use `terraform state show` to see the actual values:

```bash
terraform state show aws_vpc.legacy
```

Update `main.tf` to match, then re-run `terraform plan` until you see:

```
No changes. Your infrastructure matches the configuration.
```

### Step 3.5: Import the Remaining Resources

```bash
# Import the subnet
terraform import aws_subnet.legacy $SUBNET_ID

# Import the security group
terraform import aws_security_group.legacy $SG_ID

# Import the S3 bucket
terraform import aws_s3_bucket.legacy $BUCKET_NAME
```

After each import, run `terraform plan` and fix any configuration diffs.

### Step 3.6: Fix the S3 Bucket Name

After importing the S3 bucket, update the bucket attribute in `main.tf`:

```bash
# See the actual bucket name
terraform state show aws_s3_bucket.legacy | grep bucket
```

Update the `bucket` attribute in `main.tf` to the actual name.

### Step 3.7: Iterate Until Clean

```bash
# After each fix, check:
terraform plan
```

**Goal: `No changes. Your infrastructure matches the configuration.`**

> **Tips for matching configuration:**
> - Use `terraform state show RESOURCE` to see all current attributes
> - Pay attention to default values Terraform sets
> - Security group egress rules often have a default that needs matching
> - Tags must match exactly
> - Some attributes are read-only and should not be in your config

---

## Part 4: Method B — Import Blocks (Terraform 1.5+)

The `import` block approach is declarative and can be planned before executing.

### Step 4.1: Create a New Project for Method B

```bash
mkdir -p ~/terraform-labs/lab07/import-blocks
cd ~/terraform-labs/lab07/import-blocks
```

### Step 4.2: Load the Resource IDs

```bash
source ~/terraform-labs/lab07/resource-ids.env
```

### Step 4.3: Create Configuration with Import Blocks

Create `providers.tf`:

```hcl
terraform {
  required_version = ">= 1.5.0"

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
```

Create `imports.tf` (replace placeholders with your actual IDs):

```hcl
# imports.tf — Declarative import blocks

import {
  to = aws_vpc.legacy
  id = "REPLACE_WITH_VPC_ID"
}

import {
  to = aws_subnet.legacy
  id = "REPLACE_WITH_SUBNET_ID"
}

import {
  to = aws_security_group.legacy
  id = "REPLACE_WITH_SG_ID"
}

import {
  to = aws_s3_bucket.legacy
  id = "REPLACE_WITH_BUCKET_NAME"
}
```

### Step 4.4: Generate Configuration Automatically

Terraform 1.5+ can generate configuration from import blocks:

```bash
terraform init

# Generate configuration for all import blocks
terraform plan -generate-config-out=generated.tf
```

**Expected Output:**

```
Planning with import blocks...

aws_vpc.legacy: Preparing import... [id=vpc-xxx]
aws_vpc.legacy: Refreshing state... [id=vpc-xxx]
...

Terraform has generated configuration and written it to generated.tf.
Please review the generated configuration and edit it as necessary.
```

### Step 4.5: Review the Generated Configuration

```bash
cat generated.tf
```

The generated file will contain resource blocks that match the existing infrastructure. Review and clean it up:

- Remove unnecessary computed attributes
- Organize the code
- Add descriptions and comments
- Fix any style issues

### Step 4.6: Plan and Apply the Import

```bash
# Plan — should show imports with no changes
terraform plan
```

**Expected Output:**

```
Plan: 4 to import, 0 to add, 0 to change, 0 to destroy.
```

```bash
# Apply the imports
terraform apply -auto-approve
```

### Step 4.7: Remove Import Blocks After Successful Import

Once the import is complete, remove or comment out the import blocks in `imports.tf` — they are no longer needed:

```bash
# Verify everything is clean
terraform plan
```

```
No changes. Your infrastructure matches the configuration.
```

---

## Part 5: Common Import Challenges

### Challenge 1: Resources with Dependencies

When importing resources that reference each other (e.g., a subnet in a VPC), import the parent first:

```bash
# Correct order:
terraform import aws_vpc.main vpc-xxx          # 1. Parent first
terraform import aws_subnet.main subnet-xxx     # 2. Child second
```

### Challenge 2: Resources Not Importable

Not all resources support import. Check the Terraform documentation for each resource type. The docs will say "Import is supported" or list limitations.

### Challenge 3: Sensitive Attributes

Some imported resources may have sensitive attributes (like RDS passwords) that are not stored in state. You may need to:

1. Import the resource
2. Set the sensitive attribute in your configuration
3. Accept a plan diff for that one attribute
4. Apply the change

### Challenge 4: Provider-Specific ID Formats

Different resources have different ID formats:

| Resource | Import ID Format |
|----------|-----------------|
| `aws_vpc` | `vpc-0abc123` |
| `aws_instance` | `i-0abc123` |
| `aws_security_group` | `sg-0abc123` |
| `aws_s3_bucket` | `bucket-name` (not ARN) |
| `aws_iam_role` | `role-name` (not ARN) |
| `aws_security_group_rule` | `sg-id_type_protocol_from_to_cidr` |
| `aws_route_table_association` | `subnet-id/rtb-id` |

Always check the "Import" section in the Terraform docs for the correct format.

---

## Part 6: Verifying a Clean Import

### Step 6.1: The Verification Checklist

After importing, verify each of these:

```bash
# 1. State has all resources
terraform state list

# 2. Plan shows no changes
terraform plan

# 3. Individual resources match
terraform state show aws_vpc.legacy
terraform state show aws_subnet.legacy
terraform state show aws_security_group.legacy
terraform state show aws_s3_bucket.legacy

# 4. Outputs work
terraform output
```

### Step 6.2: Add Outputs After Import

Add to your configuration:

```hcl
output "imported_resources" {
  value = {
    vpc_id              = aws_vpc.legacy.id
    subnet_id           = aws_subnet.legacy.id
    security_group_id   = aws_security_group.legacy.id
    s3_bucket           = aws_s3_bucket.legacy.id
  }
}
```

```bash
terraform apply -auto-approve
terraform output -json imported_resources | python3 -m json.tool
```

---

## Expected Outcomes

After completing this lab, you should have:

- [x] Created AWS resources manually via the CLI
- [x] Imported resources using `terraform import` (CLI method)
- [x] Used `import` blocks with `terraform plan -generate-config-out` (Terraform 1.5+)
- [x] Iteratively matched configuration to achieve a clean plan
- [x] Used `terraform state show` to inspect imported resource attributes
- [x] Understood import ID formats for common AWS resources
- [x] Handled common import challenges (dependencies, ordering, sensitive data)

---

## Bonus Challenges

### Challenge 1: Import an IAM Role

Create an IAM role via the AWS Console, then import it. IAM resources are trickier because of attached policies.

```bash
# Create a role
aws iam create-role \
  --role-name legacy-app-role \
  --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"ec2.amazonaws.com"},"Action":"sts:AssumeRole"}]}'

# Import it
terraform import aws_iam_role.legacy legacy-app-role
```

### Challenge 2: Import with `for_each`

Import multiple similar resources into a `for_each`-based resource. The import ID format is:

```bash
terraform import 'aws_security_group.groups["web"]' sg-xxx
terraform import 'aws_security_group.groups["db"]' sg-yyy
```

### Challenge 3: Bulk Import Script

Write a bash script that:
1. Lists all VPCs in your account using `aws ec2 describe-vpcs`
2. Generates import blocks for each VPC
3. Generates skeleton Terraform configuration for each

### Challenge 4: Import and Refactor

Import resources, then refactor them into a module using `terraform state mv`:

```bash
# After importing aws_vpc.legacy and aws_subnet.legacy:
terraform state mv aws_vpc.legacy module.network.aws_vpc.this
terraform state mv aws_subnet.legacy module.network.aws_subnet.public
```

---

## Cleanup

### Method A Cleanup

```bash
cd ~/terraform-labs/lab07
source resource-ids.env

# Let Terraform destroy the imported resources
terraform destroy -auto-approve
```

### Method B Cleanup

```bash
cd ~/terraform-labs/lab07/import-blocks
terraform destroy -auto-approve
```

### Manual Cleanup (If Needed)

If the resources were not fully imported, clean up manually:

```bash
source ~/terraform-labs/lab07/resource-ids.env

aws s3 rb s3://$BUCKET_NAME --force
aws ec2 delete-security-group --group-id $SG_ID
aws ec2 delete-subnet --subnet-id $SUBNET_ID
aws ec2 delete-vpc --vpc-id $VPC_ID
aws iam delete-role --role-name legacy-app-role 2>/dev/null
```

```bash
cd ~
rm -rf ~/terraform-labs/lab07
```

---

## Next Lab

Proceed to [Lab 08: Advanced Terraform](lab08-advanced-terraform.md) to master dynamic blocks, complex `for_each`, provisioners, and data sources.
