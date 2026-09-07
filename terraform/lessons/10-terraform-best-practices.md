# Lesson 10: Terraform Best Practices

---

## Table of Contents

1. [Directory Structure](#directory-structure)
2. [Naming Conventions](#naming-conventions)
3. [Version Pinning](#version-pinning)
4. [State Management Best Practices](#state-management-best-practices)
5. [Security Best Practices](#security-best-practices)
6. [Code Quality](#code-quality)
7. [CI/CD with Terraform](#cicd-with-terraform)
8. [Terragrunt Overview](#terragrunt-overview)
9. [Policy as Code](#policy-as-code)
10. [Summary Checklist](#summary-checklist)
11. [Key Takeaways](#key-takeaways)

---

## Directory Structure

### Small Projects (Single Environment)

```
project/
├── main.tf              # Primary resources
├── variables.tf         # Input variable declarations
├── outputs.tf           # Output declarations
├── locals.tf            # Local values
├── data.tf              # Data sources
├── versions.tf          # Provider and Terraform version constraints
├── terraform.tfvars     # Variable values
├── .gitignore           # Git ignore rules
└── README.md            # Project documentation
```

### Medium Projects (Multiple Environments)

```
project/
├── modules/
│   ├── networking/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── README.md
│   ├── compute/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── README.md
│   └── database/
│       ├── main.tf
│       ├── variables.tf
│       ├── outputs.tf
│       └── README.md
├── environments/
│   ├── dev/
│   │   ├── main.tf
│   │   ├── backend.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── terraform.tfvars
│   ├── staging/
│   │   ├── main.tf
│   │   ├── backend.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── terraform.tfvars
│   └── prod/
│       ├── main.tf
│       ├── backend.tf
│       ├── variables.tf
│       ├── outputs.tf
│       └── terraform.tfvars
└── README.md
```

### Large Projects (Multi-Team, Multi-Account)

```
infrastructure/
├── modules/                        # Shared modules (internal registry)
│   ├── vpc/
│   ├── eks-cluster/
│   ├── rds-postgres/
│   └── s3-secure-bucket/
├── accounts/
│   ├── shared-services/            # Shared account
│   │   ├── networking/
│   │   ├── dns/
│   │   └── monitoring/
│   ├── dev/                        # Dev account
│   │   ├── app-a/
│   │   ├── app-b/
│   │   └── shared/
│   ├── staging/                    # Staging account
│   │   ├── app-a/
│   │   ├── app-b/
│   │   └── shared/
│   └── prod/                       # Prod account
│       ├── app-a/
│       ├── app-b/
│       └── shared/
├── policies/                       # OPA/Sentinel policies
│   ├── enforce-tags.rego
│   ├── restrict-instance-types.rego
│   └── require-encryption.rego
└── .github/workflows/              # CI/CD pipelines
    ├── terraform-plan.yml
    └── terraform-apply.yml
```

### Essential .gitignore

```gitignore
# Terraform
**/.terraform/
*.tfstate
*.tfstate.*
crash.log
crash.*.log
override.tf
override.tf.json
*_override.tf
*_override.tf.json

# Sensitive variable files
*.tfvars
!example.tfvars
!*.auto.tfvars

# Keep lock file
!.terraform.lock.hcl

# IDE
.idea/
.vscode/
*.swp
*.swo
```

---

## Naming Conventions

### Resource Naming

```hcl
# Use underscores in Terraform names (HCL convention)
resource "aws_instance" "web_server" { }      # Good
resource "aws_instance" "web-server" { }      # Avoid (hyphens)
resource "aws_instance" "WebServer" { }       # Avoid (PascalCase)

# Use descriptive names
resource "aws_security_group" "web_http" { }  # Good: describes purpose
resource "aws_security_group" "sg1" { }       # Bad: meaningless

# Use "this" for single-instance modules
# Inside modules/vpc/main.tf:
resource "aws_vpc" "this" { }                 # Good for modules
```

### Cloud Resource Naming (Tags / Names in the Cloud)

```hcl
# Use hyphens for cloud resource names (cloud convention)
locals {
  name_prefix = "${var.project}-${var.environment}"
}

resource "aws_vpc" "this" {
  tags = {
    Name = "${local.name_prefix}-vpc"    # "myapp-prod-vpc"
  }
}

resource "aws_s3_bucket" "data" {
  bucket = "${local.name_prefix}-data"    # "myapp-prod-data"
}
```

### File Naming

```hcl
# Standard files every configuration should have:
main.tf          # Primary resources (or split by concern)
variables.tf     # ALL input variables
outputs.tf       # ALL outputs
versions.tf      # Terraform and provider versions
locals.tf        # Local values
data.tf          # Data sources

# For larger configurations, split main.tf by concern:
networking.tf    # VPC, subnets, route tables
compute.tf       # EC2, ASG, launch templates
database.tf      # RDS, ElastiCache
security.tf      # IAM, security groups
monitoring.tf    # CloudWatch, SNS
```

### Variable Naming

```hcl
# Use descriptive, consistent names
variable "vpc_cidr_block" { }        # Good
variable "cidr" { }                   # Bad: too vague

# Group related variables with a prefix
variable "db_instance_class" { }
variable "db_engine_version" { }
variable "db_storage_size_gb" { }
variable "db_backup_retention_days" { }

# Use boolean names that read as questions
variable "enable_monitoring" { }      # Good: "enable_monitoring = true"
variable "create_dns_record" { }      # Good: "create_dns_record = false"
variable "monitoring" { }             # Bad: unclear if it's a bool, string, or object
```

---

## Version Pinning

### Pin Terraform Version

```hcl
# versions.tf
terraform {
  required_version = "~> 1.7.0"  # Pin to specific minor version

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.31"  # Allow patch updates within 5.31.x
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.85"
    }
  }
}
```

### Version Constraint Best Practices

```hcl
# For root modules: pin tightly
version = "~> 5.31.0"   # Only allows 5.31.x (recommended for production)

# For shared modules: pin loosely
version = ">= 5.0"      # Allows any 5.x+ (gives consumers flexibility)
```

### Commit the Lock File

```bash
# Always commit .terraform.lock.hcl
git add .terraform.lock.hcl
git commit -m "Update provider lock file"

# Update providers (when you intentionally want newer versions)
terraform init -upgrade
```

### Use `.terraform-version` for Team Consistency

```bash
# .terraform-version (used by tfenv, tfswitcher)
1.7.3
```

```bash
# Install and use tfenv for version management
brew install tfenv
tfenv install 1.7.3
tfenv use 1.7.3
```

---

## State Management Best Practices

### 1. Always Use Remote State for Teams

```hcl
terraform {
  backend "s3" {
    bucket         = "company-terraform-state"
    key            = "team/project/env/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-locks"
    kms_key_id     = "arn:aws:kms:us-east-1:123456789012:key/..."
  }
}
```

### 2. One State Per Environment Per Project

```
# Good: Separate state files
s3://state-bucket/myapp/dev/terraform.tfstate
s3://state-bucket/myapp/staging/terraform.tfstate
s3://state-bucket/myapp/prod/terraform.tfstate

# Bad: Everything in one state
s3://state-bucket/everything.tfstate
```

### 3. Keep State Small

Split large configurations into smaller, focused state files:

```
# Instead of one massive state:
├── everything/          # 200+ resources in one state

# Split by concern:
├── networking/          # VPC, subnets (changes rarely)
├── compute/             # EC2, ASG (changes often)
├── database/            # RDS (changes rarely)
└── monitoring/          # CloudWatch (changes sometimes)
```

Use `terraform_remote_state` data source to share data between states:

```hcl
# In compute/main.tf
data "terraform_remote_state" "networking" {
  backend = "s3"
  config = {
    bucket = "company-terraform-state"
    key    = "networking/prod/terraform.tfstate"
    region = "us-east-1"
  }
}

resource "aws_instance" "web" {
  subnet_id = data.terraform_remote_state.networking.outputs.public_subnet_ids[0]
}
```

### 4. Never Edit State Manually

```bash
# Use state commands instead
terraform state mv    # Rename/move resources
terraform state rm    # Remove resources
terraform import      # Import existing resources

# Never do this:
# vim terraform.tfstate  # NEVER!
```

---

## Security Best Practices

### 1. No Secrets in Code or State

```hcl
# BAD: Hardcoded secrets
resource "aws_db_instance" "main" {
  password = "SuperSecret123!"  # NEVER!
}

# GOOD: Use sensitive variables
variable "db_password" {
  type      = string
  sensitive = true
}

resource "aws_db_instance" "main" {
  password = var.db_password
}

# BETTER: Generate passwords with Terraform
resource "random_password" "db" {
  length  = 32
  special = true
}

resource "aws_db_instance" "main" {
  password = random_password.db.result
}

# BEST: Use a secrets manager
data "aws_secretsmanager_secret_version" "db_password" {
  secret_id = "prod/database/password"
}

resource "aws_db_instance" "main" {
  password = data.aws_secretsmanager_secret_version.db_password.secret_string
}
```

### 2. Encrypt State

```hcl
# S3 backend with KMS encryption
terraform {
  backend "s3" {
    encrypt    = true
    kms_key_id = "arn:aws:kms:..."
  }
}
```

### 3. Restrict State Access

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "TerraformStateAccess",
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject"],
      "Resource": "arn:aws:s3:::company-terraform-state/*",
      "Condition": {
        "StringEquals": {
          "aws:PrincipalOrgID": "o-1234567890"
        }
      }
    }
  ]
}
```

### 4. Use OIDC for CI/CD (No Long-Lived Credentials)

```hcl
# GitHub Actions OIDC provider
resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]
}

resource "aws_iam_role" "github_actions" {
  name = "github-actions-terraform"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Federated = aws_iam_openid_connect_provider.github.arn
      }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringLike = {
          "token.actions.githubusercontent.com:sub" = "repo:my-org/my-repo:*"
        }
      }
    }]
  })
}
```

### 5. Scan IaC for Security Issues

```bash
# tfsec -- Terraform static analysis
tfsec .
# Output:
#  Result: S3 bucket does not have encryption enabled
#  Severity: HIGH
#  Location: main.tf:15

# checkov -- Policy-as-code scanner
checkov -d .
# Output:
# Passed checks: 45, Failed checks: 3, Skipped checks: 0

# trivy -- Multi-purpose security scanner
trivy config .

# terrascan -- Compliance scanner
terrascan scan -t aws
```

### 6. Use Least-Privilege IAM for Terraform

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "TerraformEC2",
      "Effect": "Allow",
      "Action": [
        "ec2:Describe*",
        "ec2:CreateTags",
        "ec2:RunInstances",
        "ec2:TerminateInstances"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:RequestedRegion": "us-east-1"
        }
      }
    }
  ]
}
```

---

## Code Quality

### Formatting

```bash
# Auto-format all .tf files
terraform fmt -recursive

# Check formatting (useful in CI)
terraform fmt -check -recursive
# Exit code 0 = formatted, exit code 3 = needs formatting
```

### Validation

```bash
# Validate configuration syntax
terraform validate

# Output:
# Success! The configuration is valid.
```

### Linting with TFLint

```bash
# Install TFLint
brew install tflint

# Initialize (downloads plugins)
tflint --init

# Run linter
tflint

# Output:
# Warning: instance_type is t2.micro, consider using t3.micro (aws_instance_previous_type)
```

`.tflint.hcl` configuration:

```hcl
plugin "aws" {
  enabled = true
  version = "0.28.0"
  source  = "github.com/terraform-linters/tflint-ruleset-aws"
}

rule "terraform_naming_convention" {
  enabled = true
}

rule "terraform_documented_variables" {
  enabled = true
}

rule "terraform_documented_outputs" {
  enabled = true
}
```

### Documentation with terraform-docs

```bash
# Install
brew install terraform-docs

# Generate README for a module
terraform-docs markdown table ./modules/vpc/ > ./modules/vpc/README.md

# Auto-update README between markers
terraform-docs markdown table --output-file README.md --output-mode inject ./modules/vpc/
```

### Pre-Commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/antonbabenko/pre-commit-terraform
    rev: v1.86.0
    hooks:
      - id: terraform_fmt
      - id: terraform_validate
      - id: terraform_tflint
      - id: terraform_tfsec
      - id: terraform_docs
        args:
          - --hook-config=--path-to-file=README.md
          - --hook-config=--add-to-existing-file=true
```

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Now hooks run automatically on every git commit
```

---

## CI/CD with Terraform

### GitHub Actions: Plan on PR, Apply on Merge

```yaml
# .github/workflows/terraform.yml
name: Terraform

on:
  pull_request:
    branches: [main]
    paths: ['terraform/**']
  push:
    branches: [main]
    paths: ['terraform/**']

permissions:
  id-token: write   # For OIDC
  contents: read
  pull-requests: write  # For PR comments

jobs:
  terraform-plan:
    name: Terraform Plan
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Configure AWS Credentials (OIDC)
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/github-actions-terraform
          aws-region: us-east-1

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: 1.7.3

      - name: Terraform Init
        run: terraform init
        working-directory: terraform/

      - name: Terraform Format Check
        run: terraform fmt -check -recursive
        working-directory: terraform/

      - name: Terraform Validate
        run: terraform validate
        working-directory: terraform/

      - name: Run tfsec
        uses: aquasecurity/tfsec-action@v1.0.3
        with:
          working_directory: terraform/

      - name: Terraform Plan
        id: plan
        run: terraform plan -no-color -out=tfplan
        working-directory: terraform/

      - name: Comment Plan on PR
        uses: actions/github-script@v7
        with:
          script: |
            const output = `#### Terraform Plan
            \`\`\`
            ${{ steps.plan.outputs.stdout }}
            \`\`\`
            *Pushed by: @${{ github.actor }}*`;
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: output
            });

  terraform-apply:
    name: Terraform Apply
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    environment: production  # Requires approval

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/github-actions-terraform
          aws-region: us-east-1

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: 1.7.3

      - name: Terraform Init
        run: terraform init
        working-directory: terraform/

      - name: Terraform Apply
        run: terraform apply -auto-approve
        working-directory: terraform/
```

### GitLab CI Pipeline

```yaml
# .gitlab-ci.yml
stages:
  - validate
  - plan
  - apply

variables:
  TF_ROOT: terraform/

.terraform-base:
  image: hashicorp/terraform:1.7.3
  before_script:
    - cd $TF_ROOT
    - terraform init

validate:
  extends: .terraform-base
  stage: validate
  script:
    - terraform fmt -check -recursive
    - terraform validate
    - tfsec .

plan:
  extends: .terraform-base
  stage: plan
  script:
    - terraform plan -out=tfplan
  artifacts:
    paths:
      - $TF_ROOT/tfplan
  only:
    - merge_requests
    - main

apply:
  extends: .terraform-base
  stage: apply
  script:
    - terraform apply tfplan
  dependencies:
    - plan
  only:
    - main
  when: manual  # Requires manual approval
```

### CI/CD Best Practices

| Practice | Description |
|----------|-------------|
| **Plan on PR** | Show the plan as a PR comment for review |
| **Apply on merge** | Only apply after PR is approved and merged |
| **Use OIDC** | No long-lived credentials in CI/CD |
| **Require approval** | Manual approval gate for production applies |
| **Lock state** | Prevent concurrent pipeline runs |
| **Scan for security** | Run tfsec/checkov before apply |
| **Save plan artifacts** | Use saved plans to ensure apply matches plan |
| **Pin versions** | Pin Terraform and provider versions in CI |

---

## Terragrunt Overview

[Terragrunt](https://terragrunt.gruntwork.io/) is a thin wrapper for Terraform that provides:

- **DRY configurations** (Don't Repeat Yourself)
- **Automatic remote state management**
- **Multi-account, multi-region orchestration**
- **Dependencies between modules**

### Terragrunt Directory Structure

```
infrastructure/
├── terragrunt.hcl                    # Root config (backend, common vars)
├── modules/                          # Shared Terraform modules
│   ├── vpc/
│   ├── eks/
│   └── rds/
└── environments/
    ├── dev/
    │   ├── us-east-1/
    │   │   ├── vpc/
    │   │   │   └── terragrunt.hcl    # VPC for dev/us-east-1
    │   │   ├── eks/
    │   │   │   └── terragrunt.hcl
    │   │   └── rds/
    │   │       └── terragrunt.hcl
    │   └── region.hcl
    ├── staging/
    │   └── ...
    └── prod/
        └── us-east-1/
            ├── vpc/
            │   └── terragrunt.hcl
            ├── eks/
            │   └── terragrunt.hcl
            └── rds/
                └── terragrunt.hcl
```

### Root terragrunt.hcl

```hcl
# terragrunt.hcl (root)

# Auto-generate backend configuration
remote_state {
  backend = "s3"
  generate = {
    path      = "backend.tf"
    if_exists = "overwrite_terragrunt"
  }
  config = {
    bucket         = "company-terraform-state"
    key            = "${path_relative_to_include()}/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

# Auto-generate provider configuration
generate "provider" {
  path      = "provider.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<EOF
provider "aws" {
  region = "us-east-1"
  default_tags {
    tags = {
      ManagedBy = "Terraform"
    }
  }
}
EOF
}
```

### Module terragrunt.hcl

```hcl
# environments/prod/us-east-1/vpc/terragrunt.hcl

include "root" {
  path = find_in_parent_folders()
}

terraform {
  source = "../../../../modules/vpc"
}

inputs = {
  vpc_name    = "prod-vpc"
  vpc_cidr    = "10.0.0.0/16"
  environment = "prod"
}
```

### Terragrunt Dependencies

```hcl
# environments/prod/us-east-1/eks/terragrunt.hcl

include "root" {
  path = find_in_parent_folders()
}

terraform {
  source = "../../../../modules/eks"
}

dependency "vpc" {
  config_path = "../vpc"
}

inputs = {
  vpc_id     = dependency.vpc.outputs.vpc_id
  subnet_ids = dependency.vpc.outputs.private_subnet_ids
}
```

### Terragrunt Commands

```bash
# Apply a single module
cd environments/prod/us-east-1/vpc
terragrunt apply

# Apply all modules (respects dependencies)
cd environments/prod
terragrunt run-all apply

# Plan all modules
terragrunt run-all plan

# Destroy in reverse dependency order
terragrunt run-all destroy
```

---

## Policy as Code

Policy as Code enforces compliance and security rules on Terraform configurations automatically.

### HashiCorp Sentinel (Terraform Enterprise/Cloud)

Sentinel is HashiCorp's native policy-as-code framework.

```python
# policy: require-tags.sentinel
# All resources must have required tags

import "tfplan/v2" as tfplan

required_tags = ["Environment", "ManagedBy", "Project"]

# Get all resources that support tags
allResources = filter tfplan.resource_changes as _, rc {
    rc.mode is "managed" and
    rc.change.after is not null
}

# Check for required tags
deny_missing_tags = rule {
    all allResources as _, resource {
        all required_tags as tag {
            resource.change.after.tags contains tag
        }
    }
}

main = rule {
    deny_missing_tags
}
```

### Open Policy Agent (OPA) with Rego

OPA is an open-source policy engine that works with any Terraform workflow.

```rego
# policy/require-encryption.rego
package terraform.policies

# Deny unencrypted S3 buckets
deny[msg] {
    resource := input.planned_values.root_module.resources[_]
    resource.type == "aws_s3_bucket"
    not resource.values.server_side_encryption_configuration
    msg := sprintf("S3 bucket '%s' must have encryption enabled", [resource.name])
}

# Deny public S3 buckets
deny[msg] {
    resource := input.planned_values.root_module.resources[_]
    resource.type == "aws_s3_bucket_acl"
    resource.values.acl == "public-read"
    msg := sprintf("S3 bucket ACL '%s' must not be public-read", [resource.name])
}

# Restrict instance types
deny[msg] {
    resource := input.planned_values.root_module.resources[_]
    resource.type == "aws_instance"
    allowed := {"t3.micro", "t3.small", "t3.medium", "t3.large"}
    not allowed[resource.values.instance_type]
    msg := sprintf("Instance '%s' uses disallowed type '%s'", [resource.name, resource.values.instance_type])
}
```

### Using OPA with Terraform in CI/CD

```bash
# Step 1: Generate a Terraform plan in JSON format
terraform plan -out=tfplan
terraform show -json tfplan > tfplan.json

# Step 2: Evaluate policies with OPA
opa eval \
  --data policy/ \
  --input tfplan.json \
  "data.terraform.policies.deny"

# Step 3: Fail if any denials
DENIALS=$(opa eval --data policy/ --input tfplan.json "data.terraform.policies.deny" --format raw)
if [ "$DENIALS" != "[]" ]; then
  echo "Policy violations found: $DENIALS"
  exit 1
fi
```

### Conftest (OPA for Configuration Files)

```bash
# Install conftest
brew install conftest

# Test Terraform plan
terraform show -json tfplan > tfplan.json
conftest test tfplan.json -p policy/

# Output:
# FAIL - tfplan.json - S3 bucket 'data' must have encryption enabled
# FAIL - tfplan.json - Instance 'web' uses disallowed type 'c5.xlarge'
#
# 2 tests, 0 passed, 0 warnings, 2 failures
```

### Security Scanning Tools Summary

| Tool | Type | Open Source | Best For |
|------|------|-------------|----------|
| **tfsec** | Static analysis | Yes | Quick security scanning |
| **checkov** | Policy-as-code | Yes | Compliance checks (CIS, SOC2) |
| **Sentinel** | Policy-as-code | No (HashiCorp) | Terraform Cloud/Enterprise |
| **OPA/Conftest** | Policy engine | Yes | Custom policies, any CI/CD |
| **TFLint** | Linter | Yes | Best practices, provider-specific rules |
| **Trivy** | Multi-scanner | Yes | IaC + containers + code |
| **Terrascan** | Compliance | Yes | Multi-framework compliance |
| **Snyk IaC** | Security | Freemium | Developer-friendly scanning |

---

## Summary Checklist

### Before Every PR

- [ ] `terraform fmt -check -recursive`
- [ ] `terraform validate`
- [ ] `tflint`
- [ ] `tfsec` or `checkov`
- [ ] `terraform plan` (reviewed by team)

### Repository Setup

- [ ] `.gitignore` includes state files and `.terraform/`
- [ ] `.terraform.lock.hcl` is committed
- [ ] Pre-commit hooks configured
- [ ] CI/CD pipeline configured (plan on PR, apply on merge)

### State Management

- [ ] Remote backend configured (S3, Azure Blob, GCS, or TF Cloud)
- [ ] State encryption enabled
- [ ] State locking enabled
- [ ] State versioning enabled
- [ ] Access restricted with IAM/RBAC

### Security

- [ ] No hardcoded secrets in code
- [ ] Sensitive variables marked with `sensitive = true`
- [ ] OIDC used for CI/CD authentication (no long-lived credentials)
- [ ] Least-privilege IAM roles for Terraform
- [ ] Security scanning in CI/CD pipeline
- [ ] Policy as code enforced (OPA, Sentinel, or checkov)

### Code Quality

- [ ] Terraform and provider versions pinned
- [ ] Modules are documented with README and examples
- [ ] Variables have descriptions and validation
- [ ] Outputs have descriptions
- [ ] Resources have meaningful names and tags
- [ ] `lifecycle` blocks used for critical resources

---

## Key Takeaways

1. **Organize code with consistent structure** -- use separate files for variables, outputs, and versions
2. **Follow naming conventions** -- underscores in HCL, hyphens in cloud resource names
3. **Pin all versions** -- Terraform, providers, and modules to prevent surprise breaking changes
4. **Remote state is mandatory for teams** -- encrypt it, lock it, version it, restrict access
5. **Never store secrets in code or state** -- use secrets managers, OIDC, and sensitive variables
6. **Automate with CI/CD** -- plan on PR, scan for security, apply after approval on merge
7. **Enforce policies** -- use tfsec, checkov, OPA, or Sentinel to catch issues before deployment
8. **Use pre-commit hooks** -- catch formatting, validation, and security issues before code is pushed
9. **Terragrunt helps at scale** -- DRY configs, auto-backend, dependency management
10. **Treat Terraform code like application code** -- review it, test it, scan it, version it

---

## Course Complete!

Congratulations! You have completed all 10 lessons of the Terraform module in the DevSecOps course. You now have a solid foundation in:

- Infrastructure as Code principles
- Terraform core concepts (providers, resources, variables, state)
- Advanced features (modules, expressions, workspaces)
- Production best practices (security, CI/CD, policy as code)

### Recommended Next Steps

1. **Practice**: Build a complete infrastructure project on AWS/Azure/GCP
2. **Get Certified**: Study for the [HashiCorp Terraform Associate](https://www.hashicorp.com/certification/terraform-associate) certification
3. **Explore**: Try Terragrunt, Atlantis, or Terraform Cloud for team workflows
4. **Contribute**: Build and share your own Terraform modules

[Previous Lesson: Terraform Workspaces](./09-terraform-workspaces.md) | [Cheatsheet: Terraform Commands](../cheatsheet/terraform-commands-cheatsheet.md)
