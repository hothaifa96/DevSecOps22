# Lesson 2: Terraform Basics

---

## Table of Contents

1. [Installing Terraform](#installing-terraform)
2. [HCL Syntax Fundamentals](#hcl-syntax-fundamentals)
3. [Your First Terraform Configuration](#your-first-terraform-configuration)
4. [The Core Workflow: init, plan, apply, destroy](#the-core-workflow)
5. [Understanding Providers](#understanding-providers)
6. [State Overview](#state-overview)
7. [Key Takeaways](#key-takeaways)

---

## Installing Terraform

### macOS

```bash
# Using Homebrew (recommended)
brew tap hashicorp/tap
brew install hashicorp/tap/terraform

# Verify installation
terraform -version
# Terraform v1.7.x
```

### Linux (Ubuntu/Debian)

```bash
# Add HashiCorp GPG key and repository
wget -O- https://apt.releases.hashicorp.com/gpg | \
  sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg

echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] \
  https://apt.releases.hashicorp.com $(lsb_release -cs) main" | \
  sudo tee /etc/apt/sources.list.d/hashicorp.list

sudo apt update && sudo apt install terraform
```

### Linux (CentOS/RHEL)

```bash
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://rpm.releases.hashicorp.com/RHEL/hashicorp.repo
sudo yum -y install terraform
```

### Windows

```powershell
# Using Chocolatey
choco install terraform

# Using Scoop
scoop install terraform
```

### Manual Installation (Any OS)

1. Download the binary from [terraform.io/downloads](https://www.terraform.io/downloads)
2. Unzip the archive
3. Move the `terraform` binary to a directory in your `PATH`

```bash
# Example on Linux/macOS
unzip terraform_1.7.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/
terraform -version
```

### Enable Tab Completion (Optional)

```bash
# Bash
terraform -install-autocomplete

# Restart your shell or source your profile
source ~/.bashrc
```

---

## HCL Syntax Fundamentals

Terraform uses **HashiCorp Configuration Language (HCL)** -- a declarative language designed to be both human-readable and machine-parseable.

### Basic Structure

```hcl
# This is a comment

# Block type with labels
<BLOCK_TYPE> "<LABEL_1>" "<LABEL_2>" {
  # Arguments
  <ARGUMENT_NAME> = <ARGUMENT_VALUE>

  # Nested block
  <NESTED_BLOCK> {
    <ARGUMENT_NAME> = <ARGUMENT_VALUE>
  }
}
```

### Data Types

```hcl
# String
name = "web-server"

# Number
instance_count = 3

# Boolean
enable_monitoring = true

# List (ordered collection)
availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]

# Map (key-value pairs)
tags = {
  Name        = "WebServer"
  Environment = "Production"
  Team        = "DevOps"
}

# Null
optional_value = null
```

### String Interpolation and Heredocs

```hcl
# String interpolation
name = "server-${var.environment}-${count.index}"

# Heredoc for multi-line strings
user_data = <<-EOF
  #!/bin/bash
  echo "Hello from ${var.environment}"
  apt-get update
  apt-get install -y nginx
EOF
```

### References and Expressions

```hcl
# Reference another resource's attribute
subnet_id = aws_subnet.main.id

# Reference a variable
instance_type = var.instance_type

# Reference a local value
ami = local.ubuntu_ami

# Conditional expression
instance_type = var.environment == "prod" ? "t3.large" : "t3.micro"
```

### Comments

```hcl
# Single-line comment (hash)

// Single-line comment (double slash)

/*
Multi-line
comment
block
*/
```

---

## Your First Terraform Configuration

Let's create a complete, working example. We will use the `local` provider (no cloud account needed) to create a file on your machine.

### Step 1: Create a Project Directory

```bash
mkdir my-first-terraform && cd my-first-terraform
```

### Step 2: Write the Configuration

Create a file named `main.tf`:

```hcl
# main.tf

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
  filename = "${path.module}/hello.txt"
  content  = "Hello, Terraform! Welcome to Infrastructure as Code."
}

# Output the file path
output "file_path" {
  value       = local_file.hello.filename
  description = "The path of the created file"
}
```

### Step 3: Follow the Core Workflow

See the next section for detailed commands.

---

## The Core Workflow

Terraform follows a four-step core workflow:

```
Write → Init → Plan → Apply
                        ↓
                     Destroy (when done)
```

### 1. `terraform init` -- Initialize the Working Directory

This is always the **first command** you run. It:

- Downloads required provider plugins
- Initializes the backend (where state is stored)
- Downloads modules referenced in the configuration

```bash
$ terraform init

Initializing the backend...

Initializing provider plugins...
- Finding hashicorp/local versions matching "~> 2.0"...
- Installing hashicorp/local v2.5.1...
- Installed hashicorp/local v2.5.1 (signed by HashiCorp)

Terraform has been successfully initialized!
```

**Key files created by `init`:**

```
my-first-terraform/
├── main.tf                    # Your configuration
├── .terraform/                # Provider plugins (DO NOT commit to Git)
│   └── providers/
│       └── registry.terraform.io/
│           └── hashicorp/local/...
└── .terraform.lock.hcl        # Dependency lock file (DO commit to Git)
```

> **Important**: Add `.terraform/` to your `.gitignore`. Always commit `.terraform.lock.hcl`.

### 2. `terraform plan` -- Preview Changes

This command creates an execution plan showing what Terraform *will* do without making any changes:

```bash
$ terraform plan

Terraform will perform the following actions:

  # local_file.hello will be created
  + resource "local_file" "hello" {
      + content              = "Hello, Terraform! Welcome to Infrastructure as Code."
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

Changes to Outputs:
  + file_path = "./hello.txt"
```

**Reading the plan output:**
- `+` (green) = Resource will be **created**
- `-` (red) = Resource will be **destroyed**
- `~` (yellow) = Resource will be **updated in-place**
- `-/+` (red/green) = Resource will be **destroyed and recreated**

**Save a plan to a file:**

```bash
# Save the plan
terraform plan -out=tfplan

# Apply the saved plan (skips confirmation)
terraform apply tfplan
```

### 3. `terraform apply` -- Apply Changes

This command executes the plan and creates/modifies/destroys infrastructure:

```bash
$ terraform apply

Terraform will perform the following actions:

  # local_file.hello will be created
  + resource "local_file" "hello" {
      + content  = "Hello, Terraform! Welcome to Infrastructure as Code."
      + filename = "./hello.txt"
      ...
    }

Plan: 1 to add, 0 to change, 0 to destroy.

Do you want to perform these actions?
  Terraform will perform the actions described above.
  Only 'yes' will be accepted to approve.

  Enter a value: yes

local_file.hello: Creating...
local_file.hello: Creation complete after 0s [id=abc123...]

Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

Outputs:

file_path = "./hello.txt"
```

**Auto-approve (for CI/CD pipelines -- use with caution):**

```bash
terraform apply -auto-approve
```

**Key files after `apply`:**

```
my-first-terraform/
├── main.tf
├── .terraform/
├── .terraform.lock.hcl
├── terraform.tfstate          # State file (tracks what was created)
└── hello.txt                  # The resource we created!
```

### 4. `terraform destroy` -- Tear Down Infrastructure

This command removes all resources managed by the configuration:

```bash
$ terraform destroy

Terraform will perform the following actions:

  # local_file.hello will be destroyed
  - resource "local_file" "hello" {
      - content  = "Hello, Terraform! Welcome to Infrastructure as Code." -> null
      - filename = "./hello.txt" -> null
      ...
    }

Plan: 0 to add, 0 to change, 1 to destroy.

Do you want to perform these actions?
  Enter a value: yes

local_file.hello: Destroying... [id=abc123...]
local_file.hello: Destruction complete after 0s

Destroy complete! Resources: 1 destroyed.
```

### Other Useful Commands

```bash
# Validate configuration syntax
terraform validate

# Format code to canonical style
terraform fmt

# Show current state
terraform show

# List resources in state
terraform state list

# View output values
terraform output
```

---

## Understanding Providers

**Providers** are plugins that allow Terraform to interact with APIs of cloud platforms, SaaS tools, and other services.

### How Providers Work

```
Your .tf Code  →  Terraform Core  →  Provider Plugin  →  API  →  Cloud Resource
                   (engine)          (e.g., AWS)         (EC2)   (running server)
```

### Provider Configuration

```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"     # Provider source address
      version = "~> 5.0"            # Version constraint
    }
  }
}

# Configure the AWS provider
provider "aws" {
  region = "us-east-1"
}
```

### Common Providers

| Provider | Source | Purpose |
|----------|--------|---------|
| AWS | `hashicorp/aws` | Amazon Web Services |
| Azure | `hashicorp/azurerm` | Microsoft Azure |
| GCP | `hashicorp/google` | Google Cloud Platform |
| Kubernetes | `hashicorp/kubernetes` | Kubernetes clusters |
| Docker | `kreuzwerker/docker` | Docker containers |
| GitHub | `integrations/github` | GitHub repos, teams |
| Helm | `hashicorp/helm` | Helm charts |
| Cloudflare | `cloudflare/cloudflare` | Cloudflare DNS/CDN |

### Provider Version Constraints

```hcl
version = "5.0.0"    # Exactly version 5.0.0
version = ">= 5.0"   # Version 5.0 or newer
version = "~> 5.0"   # Any 5.x version (>= 5.0, < 6.0) -- RECOMMENDED
version = ">= 5.0, < 6.0"  # Between 5.0 and 6.0
```

> **Best Practice**: Always pin provider versions using `~>` to avoid unexpected breaking changes.

---

## State Overview

Terraform **state** is a JSON file that maps your configuration to real-world resources. It is how Terraform knows what it has already created.

### What State Tracks

```json
{
  "version": 4,
  "terraform_version": "1.7.0",
  "resources": [
    {
      "type": "local_file",
      "name": "hello",
      "instances": [
        {
          "attributes": {
            "content": "Hello, Terraform!",
            "filename": "./hello.txt",
            "id": "abc123..."
          }
        }
      ]
    }
  ]
}
```

### Why State Exists

1. **Mapping to Real Resources**: Links `aws_instance.web` in your code to `i-1234567890abcdef0` in AWS
2. **Performance**: Caches resource attributes so Terraform does not need to query every API on every run
3. **Dependency Tracking**: Knows the order to create/destroy resources
4. **Drift Detection**: Compares desired state (code) with actual state (state file) to determine changes

### State File Warnings

> **CRITICAL SECURITY WARNING**: The state file may contain sensitive data (passwords, API keys, private IPs). Treat it as a secret!

- **Never** commit `terraform.tfstate` to Git
- Store state remotely (S3, Azure Blob, GCS) with encryption
- Enable state locking to prevent concurrent modifications
- Restrict access to the state file

Add to `.gitignore`:

```gitignore
# Terraform
*.tfstate
*.tfstate.*
.terraform/
*.tfvars       # May contain secrets
!example.tfvars
```

---

## Putting It All Together: A Real-World AWS Example

```hcl
# main.tf -- Deploy a simple web server on AWS

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
  region = "us-east-1"
}

# Find the latest Amazon Linux 2 AMI
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}

# Create a security group allowing HTTP traffic
resource "aws_security_group" "web" {
  name        = "web-server-sg"
  description = "Allow HTTP inbound traffic"

  ingress {
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
    Name = "web-server-sg"
  }
}

# Create an EC2 instance
resource "aws_instance" "web" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = "t2.micro"
  vpc_security_group_ids = [aws_security_group.web.id]

  user_data = <<-EOF
    #!/bin/bash
    yum update -y
    yum install -y httpd
    systemctl start httpd
    systemctl enable httpd
    echo "<h1>Hello from Terraform!</h1>" > /var/www/html/index.html
  EOF

  tags = {
    Name        = "web-server"
    Environment = "dev"
    ManagedBy   = "Terraform"
  }
}

# Output the public IP
output "web_server_ip" {
  value       = aws_instance.web.public_ip
  description = "The public IP of the web server"
}
```

---

## Key Takeaways

1. **Install Terraform** from HashiCorp's official sources and verify with `terraform -version`
2. **HCL syntax** uses blocks, arguments, and expressions -- it is designed to be human-readable
3. **The core workflow** is: `init` (setup) -> `plan` (preview) -> `apply` (execute) -> `destroy` (cleanup)
4. **Always run `plan` before `apply`** to review what will change
5. **Providers** are plugins that connect Terraform to cloud APIs -- always pin their versions
6. **State** is critical -- it maps your code to real resources. Protect it like a secret
7. **Use `.gitignore`** to exclude `.terraform/`, `*.tfstate`, and sensitive variable files

---

## What's Next?

In the next lesson, we will take a deep dive into Terraform providers -- how to configure them, use multiple providers, and work with provider aliases.

[Previous Lesson: Introduction to IaC](./01-introduction-to-iac.md) | [Next Lesson: Terraform Providers -->](./03-terraform-providers.md)
