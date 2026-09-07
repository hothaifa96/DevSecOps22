# Terraform CLI Commands Cheatsheet

> A comprehensive reference of all common Terraform CLI commands, organized by category.

---

## Table of Contents

- [Core Workflow](#core-workflow)
- [Initialization](#initialization)
- [Planning](#planning)
- [Applying](#applying)
- [Destroying](#destroying)
- [State Management](#state-management)
- [Import](#import)
- [Workspace Management](#workspace-management)
- [Output & Inspection](#output--inspection)
- [Formatting & Validation](#formatting--validation)
- [Provider Management](#provider-management)
- [Debugging & Logging](#debugging--logging)
- [Environment Variables](#environment-variables)
- [Quick Reference Table](#quick-reference-table)

---

## Core Workflow

```bash
# The standard Terraform workflow
terraform init       # 1. Initialize (download providers/modules)
terraform plan       # 2. Preview changes
terraform apply      # 3. Apply changes
terraform destroy    # 4. Tear down infrastructure
```

---

## Initialization

```bash
# Initialize a Terraform working directory
terraform init

# Reinitialize and upgrade providers/modules to latest within constraints
terraform init -upgrade

# Initialize with a backend configuration file
terraform init -backend-config=backend.hcl

# Initialize with backend config flags
terraform init \
  -backend-config="bucket=my-state-bucket" \
  -backend-config="key=prod/terraform.tfstate" \
  -backend-config="region=us-east-1"

# Reconfigure backend (discard existing state config)
terraform init -reconfigure

# Migrate state to a new backend
terraform init -migrate-state

# Initialize without accessing remote backend (offline)
terraform init -backend=false

# Initialize and download modules only (no backend)
terraform init -get=true -backend=false

# Initialize to a specific plugin directory
terraform init -plugin-dir=/path/to/plugins
```

---

## Planning

```bash
# Show execution plan
terraform plan

# Save plan to file (for later apply)
terraform plan -out=tfplan

# Plan with variable values
terraform plan -var="instance_type=t3.large"
terraform plan -var="environment=prod" -var="region=us-east-1"

# Plan with a variable file
terraform plan -var-file="environments/prod.tfvars"

# Plan with multiple variable files
terraform plan -var-file="common.tfvars" -var-file="prod.tfvars"

# Plan for destruction
terraform plan -destroy

# Plan targeting specific resources
terraform plan -target=aws_instance.web
terraform plan -target=module.vpc
terraform plan -target=aws_instance.web[0]
terraform plan -target='aws_instance.web["web-1"]'

# Plan with resource replacement (force recreate)
terraform plan -replace=aws_instance.web

# Plan with refresh-only (detect drift without changing anything)
terraform plan -refresh-only

# Plan without refreshing state (faster, but may miss drift)
terraform plan -refresh=false

# Plan with compact output (no unchanged attributes)
terraform plan -compact-warnings

# Plan with JSON output (for automation)
terraform plan -out=tfplan && terraform show -json tfplan > plan.json

# Plan with parallelism control
terraform plan -parallelism=20

# Plan and generate config for imports (Terraform 1.5+)
terraform plan -generate-config-out=generated.tf
```

---

## Applying

```bash
# Apply changes (with confirmation prompt)
terraform apply

# Apply a saved plan file (no confirmation needed)
terraform apply tfplan

# Apply without confirmation (for CI/CD)
terraform apply -auto-approve

# Apply with variables
terraform apply -var="instance_type=t3.large"
terraform apply -var-file="environments/prod.tfvars"

# Apply targeting specific resources
terraform apply -target=aws_instance.web

# Apply with resource replacement
terraform apply -replace=aws_instance.web

# Apply refresh-only (update state to match reality)
terraform apply -refresh-only

# Apply with parallelism control (default: 10)
terraform apply -parallelism=30

# Apply with auto-approve and variables
terraform apply -auto-approve -var-file="prod.tfvars"
```

---

## Destroying

```bash
# Destroy all managed infrastructure (with confirmation)
terraform destroy

# Destroy without confirmation (for CI/CD)
terraform destroy -auto-approve

# Destroy specific resources
terraform destroy -target=aws_instance.web
terraform destroy -target=module.vpc

# Destroy with variables
terraform destroy -var-file="environments/prod.tfvars"

# Preview destruction (same as plan -destroy)
terraform plan -destroy
```

---

## State Management

### Listing & Showing

```bash
# List all resources in state
terraform state list

# List resources matching a filter
terraform state list aws_instance
terraform state list module.vpc

# Show details of a specific resource
terraform state show aws_instance.web
terraform state show 'aws_instance.web["web-1"]'
terraform state show module.vpc.aws_vpc.this

# Show the entire state (human-readable)
terraform show

# Show state as JSON
terraform show -json

# Show a plan file
terraform show tfplan
terraform show -json tfplan > plan.json
```

### Moving & Renaming

```bash
# Rename a resource in state (prevents destroy + recreate)
terraform state mv aws_instance.web aws_instance.app_server

# Move a resource into a module
terraform state mv aws_instance.web module.compute.aws_instance.web

# Move a resource between modules
terraform state mv module.old.aws_instance.web module.new.aws_instance.web

# Move a module
terraform state mv module.old_name module.new_name

# Dry-run a move (Terraform 1.1+, in-code)
# Add to .tf file:
# moved {
#   from = aws_instance.web
#   to   = aws_instance.app_server
# }
```

### Removing

```bash
# Remove a resource from state (keeps the real resource)
terraform state rm aws_instance.web
terraform state rm 'aws_instance.web["web-1"]'
terraform state rm module.vpc

# In-code removal (Terraform 1.7+):
# removed {
#   from = aws_instance.web
#   lifecycle { destroy = false }
# }
```

### Pulling & Pushing

```bash
# Download remote state to stdout/file
terraform state pull
terraform state pull > state.json

# Upload state to remote backend (DANGEROUS -- use with extreme caution)
terraform state push state.json
terraform state push -force state.json
```

### Replacing (Tainting)

```bash
# Force a resource to be recreated on next apply (modern way)
terraform apply -replace=aws_instance.web

# Legacy taint/untaint commands (still work)
terraform taint aws_instance.web
terraform untaint aws_instance.web
```

### Locking

```bash
# Force-unlock a stuck state lock
terraform force-unlock LOCK_ID

# The LOCK_ID is shown in the error message when a lock conflict occurs
```

---

## Import

```bash
# Import an existing resource into Terraform state
terraform import <RESOURCE_ADDRESS> <RESOURCE_ID>

# AWS examples
terraform import aws_instance.web i-1234567890abcdef0
terraform import aws_s3_bucket.data my-bucket-name
terraform import aws_vpc.main vpc-0123456789abcdef0
terraform import aws_security_group.web sg-0123456789abcdef0
terraform import aws_db_instance.main my-db-identifier
terraform import aws_iam_role.app MyRoleName
terraform import aws_route53_zone.main Z1234567890ABC
terraform import aws_lambda_function.app my-function-name

# Azure examples
terraform import azurerm_resource_group.main /subscriptions/SUB_ID/resourceGroups/my-rg
terraform import azurerm_virtual_network.main /subscriptions/SUB_ID/resourceGroups/my-rg/providers/Microsoft.Network/virtualNetworks/my-vnet

# GCP examples
terraform import google_compute_instance.web projects/my-project/zones/us-central1-a/instances/my-instance
terraform import google_storage_bucket.data my-bucket-name

# Import into a module
terraform import module.vpc.aws_vpc.this vpc-0123456789abcdef0

# Import indexed resources
terraform import 'aws_instance.web[0]' i-1234567890abcdef0
terraform import 'aws_instance.web["web-1"]' i-1234567890abcdef0

# Import blocks (Terraform 1.5+, in-code):
# import {
#   to = aws_instance.web
#   id = "i-1234567890abcdef0"
# }

# Generate configuration for imported resources
terraform plan -generate-config-out=generated.tf
```

---

## Workspace Management

```bash
# Show current workspace
terraform workspace show

# List all workspaces (* marks current)
terraform workspace list

# Create a new workspace (and switch to it)
terraform workspace new dev
terraform workspace new staging
terraform workspace new prod

# Switch to a workspace
terraform workspace select dev
terraform workspace select prod

# Delete a workspace (must switch away first, must be empty)
terraform workspace select default
terraform workspace delete dev

# Force delete a workspace (even with resources -- DANGEROUS)
terraform workspace delete -force staging
```

---

## Output & Inspection

```bash
# Show all outputs
terraform output

# Show a specific output
terraform output vpc_id

# Get raw output value (no quotes, for scripting)
terraform output -raw load_balancer_dns

# Get output as JSON
terraform output -json

# Show a specific output as JSON
terraform output -json web_server_ips

# Graph dependencies (DOT format)
terraform graph
terraform graph | dot -Tpng > graph.png
terraform graph -type=plan | dot -Tsvg > plan-graph.svg

# List providers used
terraform providers

# Show provider requirements as a dependency tree
terraform providers mirror /path/to/mirror

# Show Terraform version
terraform version
terraform version -json
```

---

## Formatting & Validation

```bash
# Format all .tf files in current directory
terraform fmt

# Format recursively (all subdirectories)
terraform fmt -recursive

# Check formatting without changing files (for CI)
terraform fmt -check
terraform fmt -check -recursive

# Show which files would change
terraform fmt -diff

# Validate configuration syntax
terraform validate

# Validate as JSON (for automation)
terraform validate -json
```

---

## Provider Management

```bash
# List required providers and installed versions
terraform providers

# Lock provider versions (create/update .terraform.lock.hcl)
terraform providers lock

# Lock for specific platforms (for CI/CD or cross-platform teams)
terraform providers lock \
  -platform=linux_amd64 \
  -platform=darwin_amd64 \
  -platform=darwin_arm64

# Mirror providers to a local directory
terraform providers mirror /path/to/mirror

# Use a local mirror
terraform init -plugin-dir=/path/to/mirror

# Show provider schema (all resource types and attributes)
terraform providers schema -json
```

---

## Debugging & Logging

```bash
# Enable detailed logging
export TF_LOG=TRACE     # Most verbose
export TF_LOG=DEBUG
export TF_LOG=INFO
export TF_LOG=WARN
export TF_LOG=ERROR     # Least verbose

# Log to a file
export TF_LOG_PATH="terraform.log"

# Enable logging for specific components
export TF_LOG_CORE=TRACE      # Core Terraform logic
export TF_LOG_PROVIDER=TRACE  # Provider plugin communication

# Disable logging
unset TF_LOG
unset TF_LOG_PATH

# Run with crash log
# If Terraform crashes, it writes to crash.log automatically
```

---

## Environment Variables

```bash
# ─── Terraform Settings ───
export TF_LOG=DEBUG                    # Log level
export TF_LOG_PATH="./terraform.log"   # Log file path
export TF_INPUT=0                      # Disable interactive prompts
export TF_CLI_ARGS="-no-color"         # Default CLI arguments
export TF_CLI_ARGS_plan="-compact-warnings"  # Args for specific command
export TF_DATA_DIR=".terraform"        # Plugin/data directory
export TF_PLUGIN_CACHE_DIR="$HOME/.terraform.d/plugin-cache"  # Share plugins

# ─── Variable Values ───
export TF_VAR_region="us-east-1"
export TF_VAR_instance_type="t3.micro"
export TF_VAR_environment="production"
export TF_VAR_db_password="SuperSecret123!"

# ─── AWS Provider ───
export AWS_ACCESS_KEY_ID="AKIAIOSFODNN7EXAMPLE"
export AWS_SECRET_ACCESS_KEY="wJalrXUtnFEMI..."
export AWS_DEFAULT_REGION="us-east-1"
export AWS_PROFILE="production"

# ─── Azure Provider ───
export ARM_CLIENT_ID="00000000-0000-0000-0000-000000000000"
export ARM_CLIENT_SECRET="your-secret"
export ARM_SUBSCRIPTION_ID="00000000-0000-0000-0000-000000000000"
export ARM_TENANT_ID="00000000-0000-0000-0000-000000000000"

# ─── GCP Provider ───
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
export GOOGLE_PROJECT="my-project-id"
export GOOGLE_REGION="us-central1"

# ─── Terraform Cloud ───
export TF_TOKEN_app_terraform_io="your-api-token"
```

---

## Quick Reference Table

| Command | Description |
|---------|-------------|
| `terraform init` | Initialize working directory |
| `terraform init -upgrade` | Upgrade providers and modules |
| `terraform plan` | Preview changes |
| `terraform plan -out=tfplan` | Save plan to file |
| `terraform apply` | Apply changes |
| `terraform apply -auto-approve` | Apply without confirmation |
| `terraform apply tfplan` | Apply a saved plan |
| `terraform destroy` | Destroy all resources |
| `terraform destroy -target=X` | Destroy specific resource |
| `terraform fmt` | Format code |
| `terraform fmt -check` | Check formatting (CI) |
| `terraform validate` | Validate syntax |
| `terraform output` | Show outputs |
| `terraform output -raw X` | Get raw output value |
| `terraform show` | Show current state |
| `terraform state list` | List all resources |
| `terraform state show X` | Show resource details |
| `terraform state mv A B` | Rename/move resource |
| `terraform state rm X` | Remove from state |
| `terraform state pull` | Download state |
| `terraform import X ID` | Import existing resource |
| `terraform workspace list` | List workspaces |
| `terraform workspace new X` | Create workspace |
| `terraform workspace select X` | Switch workspace |
| `terraform workspace show` | Show current workspace |
| `terraform console` | Interactive expression eval |
| `terraform graph` | Dependency graph (DOT) |
| `terraform providers` | List providers |
| `terraform version` | Show version |
| `terraform force-unlock ID` | Force-unlock state |
| `terraform apply -replace=X` | Force recreate resource |

---

## Common Patterns

### Deploy to Specific Environment

```bash
terraform init -backend-config="environments/prod/backend.hcl"
terraform plan -var-file="environments/prod/terraform.tfvars" -out=tfplan
terraform apply tfplan
```

### CI/CD Pipeline Pattern

```bash
terraform init -input=false
terraform plan -input=false -out=tfplan
terraform apply -input=false tfplan
```

### Detect and Fix Drift

```bash
terraform plan -refresh-only
terraform apply -refresh-only  # Update state to match reality
terraform plan                  # See remaining differences
terraform apply                 # Apply your config over reality
```

### Safe Resource Replacement

```bash
terraform plan -replace=aws_instance.web  # Preview replacement
terraform apply -replace=aws_instance.web  # Execute replacement
```

### Move Resources Without Downtime

```bash
# In your .tf file, add:
# moved {
#   from = aws_instance.old_name
#   to   = aws_instance.new_name
# }
terraform plan   # Verifies move, no destroy/create
terraform apply  # Updates state
```

---

*Last updated: 2024 | Compatible with Terraform v1.5+*
