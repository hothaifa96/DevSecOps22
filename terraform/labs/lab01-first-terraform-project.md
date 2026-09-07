# Lab 01: Your First Terraform Project

## Difficulty: Beginner

## Objectives

By the end of this lab, you will be able to:

- Install Terraform and verify the installation
- Understand the Terraform workflow: `init` → `plan` → `apply` → `destroy`
- Write a basic Terraform configuration using the `local` provider
- Create, inspect, and destroy local resources
- Understand Terraform state and its purpose

## Prerequisites

- A computer with macOS, Linux, or Windows
- Terminal/command-line access
- A text editor (VS Code recommended with the HashiCorp Terraform extension)
- No cloud account needed for this lab

## Estimated Time

45 minutes

---

## Part 1: Install Terraform

### Step 1.1: Download and Install Terraform

**macOS (using Homebrew):**

```bash
brew tap hashicorp/tap
brew install hashicorp/tap/terraform
```

**Linux (Ubuntu/Debian):**

```bash
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install terraform
```

**Windows (using Chocolatey):**

```powershell
choco install terraform
```

### Step 1.2: Verify the Installation

```bash
terraform version
```

**Expected Output:**

```
Terraform v1.x.x
on darwin_amd64
```

### Step 1.3: Enable Tab Completion (Optional)

```bash
terraform -install-autocomplete
```

Restart your shell after running this command.

---

## Part 2: Create Your First Terraform Configuration

### Step 2.1: Set Up the Project Directory

```bash
mkdir -p ~/terraform-labs/lab01
cd ~/terraform-labs/lab01
```

### Step 2.2: Create the Main Configuration File

Create a file named `main.tf`:

```hcl
# main.tf - My First Terraform Configuration

# Configure the Terraform settings
terraform {
  required_version = ">= 1.0.0"

  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.0"
    }
  }
}

# Create a local file
resource "local_file" "hello" {
  content  = "Hello, Terraform! Welcome to DevSecOps."
  filename = "${path.module}/hello.txt"
}
```

### Step 2.3: Understand the Configuration

Take a moment to understand what each block does:

| Block | Purpose |
|-------|---------|
| `terraform {}` | Specifies Terraform version and required providers |
| `required_providers` | Declares which providers this configuration needs |
| `resource` | Defines an infrastructure object to create |
| `local_file` | The resource type (provider: `local`, resource: `file`) |
| `"hello"` | The local name for this resource (used for references) |

---

## Part 3: The Terraform Workflow

### Step 3.1: Initialize the Project

```bash
terraform init
```

**Expected Output:**

```
Initializing the backend...

Initializing provider plugins...
- Finding hashicorp/local versions matching "~> 2.0"...
- Installing hashicorp/local v2.x.x...
- Installed hashicorp/local v2.x.x (signed by HashiCorp)

Terraform has been successfully initialized!
```

**What happened?**
- Terraform downloaded the `local` provider plugin
- A `.terraform` directory was created to store plugins
- A `.terraform.lock.hcl` file was created to lock provider versions

Examine the new files:

```bash
ls -la
ls -la .terraform/providers/
cat .terraform.lock.hcl
```

### Step 3.2: Format and Validate

```bash
# Auto-format your configuration files
terraform fmt

# Validate the configuration syntax
terraform validate
```

**Expected Output:**

```
Success! The configuration is valid.
```

### Step 3.3: Plan the Changes

```bash
terraform plan
```

**Expected Output:**

```
Terraform will perform the following actions:

  # local_file.hello will be created
  + resource "local_file" "hello" {
      + content              = "Hello, Terraform! Welcome to DevSecOps."
      + content_base64sha256 = (known after apply)
      + content_base64sha512 = (known after apply)
      + content_md5          = (known after apply)
      + content_sha1         = (known after apply)
      + content_sha256       = (known after apply)
      + content_sha512       = (known after apply)
      + directory_permission = "0777"
      + file_permission      = "0777"
      + filename             = "./hello.txt"
      + id                   = (known after apply)
    }

Plan: 1 to add, 0 to change, 0 to destroy.
```

> **Key Insight:** `terraform plan` shows what Terraform **will** do without making any changes. This is a critical safety feature — always review the plan before applying.

### Step 3.4: Apply the Changes

```bash
terraform apply
```

When prompted, type `yes` to confirm:

```
Do you want to perform these actions?
  Terraform will perform the following actions described above.
  Only 'yes' will be accepted to approve.

  Enter a value: yes
```

**Expected Output:**

```
local_file.hello: Creating...
local_file.hello: Creation complete after 0s [id=...]

Apply complete! Resources: 1 added, 0 changed, 0 destroyed.
```

### Step 3.5: Verify the Result

```bash
# Check that the file was created
cat hello.txt

# Examine the Terraform state
terraform show
```

**Expected Output of `cat hello.txt`:**

```
Hello, Terraform! Welcome to DevSecOps.
```

### Step 3.6: Examine the State File

```bash
cat terraform.tfstate
```

> **Important:** The state file tracks every resource Terraform manages. It maps your configuration to real-world resources. **Never edit this file manually.** In production, this file should be stored remotely and encrypted (covered in Lab 04).

---

## Part 4: Making Changes

### Step 4.1: Modify the Configuration

Update `main.tf` to change the file content and add a second resource:

```hcl
# main.tf - My First Terraform Configuration (Updated)

terraform {
  required_version = ">= 1.0.0"

  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.0"
    }
  }
}

# Create a greeting file
resource "local_file" "hello" {
  content  = "Hello, Terraform! Welcome to DevSecOps.\nModified on: ${timestamp()}"
  filename = "${path.module}/hello.txt"
}

# Create a configuration file in JSON format
resource "local_file" "config" {
  content = jsonencode({
    app_name    = "devsecops-lab"
    environment = "development"
    version     = "1.0.0"
    features = {
      logging    = true
      monitoring = true
    }
  })
  filename = "${path.module}/config.json"
}
```

### Step 4.2: Plan and Apply the Changes

```bash
terraform plan
```

Notice the output shows:
- `local_file.hello` will be **replaced** (the content changed)
- `local_file.config` will be **created** (it is new)

```bash
terraform apply -auto-approve
```

> **Note:** The `-auto-approve` flag skips the confirmation prompt. Use this only in labs and CI/CD pipelines — never for manual production changes.

### Step 4.3: Verify Both Files

```bash
cat hello.txt
cat config.json | python3 -m json.tool
```

---

## Part 5: Terraform State Commands

### Step 5.1: List Resources in State

```bash
terraform state list
```

**Expected Output:**

```
local_file.config
local_file.hello
```

### Step 5.2: Show a Specific Resource

```bash
terraform state show local_file.hello
```

### Step 5.3: View Outputs with `terraform show`

```bash
terraform show
```

---

## Part 6: Destroy the Infrastructure

### Step 6.1: Plan the Destruction

```bash
terraform plan -destroy
```

Review what will be destroyed.

### Step 6.2: Destroy All Resources

```bash
terraform destroy
```

Type `yes` when prompted.

**Expected Output:**

```
local_file.config: Destroying... [id=...]
local_file.config: Destruction complete after 0s
local_file.hello: Destroying... [id=...]
local_file.hello: Destruction complete after 0s

Destroy complete! Resources: 2 destroyed.
```

### Step 6.3: Verify the Cleanup

```bash
ls hello.txt config.json 2>/dev/null || echo "Files have been removed!"
```

---

## Expected Outcomes

After completing this lab, you should have:

- [x] Terraform installed and working on your system
- [x] Created a Terraform configuration from scratch
- [x] Executed the full workflow: `init` → `plan` → `apply` → `destroy`
- [x] Modified infrastructure and observed how Terraform handles updates
- [x] Examined the state file and used state commands
- [x] Understood the purpose of `.terraform/`, `.terraform.lock.hcl`, and `terraform.tfstate`

---

## Key Files to Understand

| File/Directory | Purpose |
|---|---|
| `main.tf` | Your main Terraform configuration |
| `.terraform/` | Provider plugins and modules (do not commit to Git) |
| `.terraform.lock.hcl` | Provider version lock file (commit to Git) |
| `terraform.tfstate` | Current state of your infrastructure |
| `terraform.tfstate.backup` | Previous state backup |

---

## Bonus Challenges

### Challenge 1: Add a `.gitignore` File

Create a `local_file` resource that generates a `.gitignore` suitable for Terraform projects. It should ignore `.terraform/`, `*.tfstate`, `*.tfstate.*`, and `*.tfvars`.

### Challenge 2: Use `local_sensitive_file`

Create a `local_sensitive_file` resource. How does Terraform treat it differently in the plan output? Why is this important for DevSecOps?

### Challenge 3: Multiple Files with `count`

Use the `count` meta-argument to create 5 numbered files (`file-0.txt`, `file-1.txt`, etc.) with a single resource block.

<details>
<summary>Hint</summary>

```hcl
resource "local_file" "numbered" {
  count    = 5
  content  = "This is file number ${count.index}"
  filename = "${path.module}/file-${count.index}.txt"
}
```

</details>

### Challenge 4: Explore the Provider Registry

Visit [registry.terraform.io](https://registry.terraform.io) and find the documentation for the `local` provider. What other resource types does it support besides `local_file`?

---

## Cleanup

Make sure you have destroyed all resources:

```bash
terraform destroy -auto-approve
cd ~
rm -rf ~/terraform-labs/lab01
```

---

## Next Lab

Proceed to [Lab 02: Provisioning an AWS EC2 Instance](lab02-aws-ec2-instance.md) to start working with cloud infrastructure.
