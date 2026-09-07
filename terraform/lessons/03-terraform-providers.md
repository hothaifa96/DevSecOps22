# Lesson 3: Terraform Providers

---

## Table of Contents

1. [What Are Providers?](#what-are-providers)
2. [Provider Configuration](#provider-configuration)
3. [AWS Provider](#aws-provider)
4. [Azure Provider](#azure-provider)
5. [GCP Provider](#gcp-provider)
6. [Provider Versioning](#provider-versioning)
7. [Multiple Providers and Aliases](#multiple-providers-and-aliases)
8. [Provider Authentication Best Practices](#provider-authentication-best-practices)
9. [Key Takeaways](#key-takeaways)

---

## What Are Providers?

Providers are **plugins** that Terraform uses to interact with external APIs. Every resource type in Terraform belongs to a provider. Without providers, Terraform cannot manage any infrastructure.

### How Providers Work

```
┌──────────────┐     ┌──────────────────┐     ┌─────────────┐     ┌────────────┐
│  Your .tf    │ --> │  Terraform Core  │ --> │  Provider   │ --> │  Cloud API │
│  Config      │     │  Engine          │     │  Plugin     │     │  (AWS/Az)  │
└──────────────┘     └──────────────────┘     └─────────────┘     └────────────┘
```

- **Terraform Core**: Reads your `.tf` files, builds a dependency graph, determines what needs to change
- **Provider Plugin**: Translates Terraform operations (create, read, update, delete) into API calls
- **Cloud API**: The actual service endpoint (AWS EC2 API, Azure Resource Manager, etc.)

### The Terraform Registry

Providers are published on the [Terraform Registry](https://registry.terraform.io/):

- **Official Providers**: Maintained by HashiCorp (e.g., `hashicorp/aws`)
- **Partner Providers**: Maintained by technology partners (e.g., `mongodb/mongodbatlas`)
- **Community Providers**: Maintained by the community

As of 2024, there are **3,800+** providers available on the registry.

### Provider Source Addresses

Every provider has a unique source address in the format:

```
<HOSTNAME>/<NAMESPACE>/<TYPE>
```

```hcl
# Full address
registry.terraform.io/hashicorp/aws

# Shorthand (registry.terraform.io is the default hostname)
hashicorp/aws
```

---

## Provider Configuration

### Basic Provider Block

```hcl
terraform {
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

The `terraform` block declares *which* providers are needed and their versions. The `provider` block *configures* the provider with settings like region and credentials.

### Required Providers Block

```hcl
terraform {
  required_providers {
    # Local name = configuration
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }

    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }

    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}
```

---

## AWS Provider

### Basic Configuration

```hcl
terraform {
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

### Authentication Methods (in order of precedence)

#### 1. Environment Variables (Recommended for CI/CD)

```bash
export AWS_ACCESS_KEY_ID="AKIAIOSFODNN7EXAMPLE"
export AWS_SECRET_ACCESS_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
export AWS_DEFAULT_REGION="us-east-1"

# For temporary credentials (STS)
export AWS_SESSION_TOKEN="FwoGZXIvYXdzE..."
```

#### 2. Shared Credentials File (~/.aws/credentials)

```ini
# ~/.aws/credentials
[default]
aws_access_key_id     = AKIAIOSFODNN7EXAMPLE
aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

[production]
aws_access_key_id     = AKIAI44QH8DHBEXAMPLE
aws_secret_access_key = je7MtGbClwBF/2Zp9Utk/h3yCo8nvbEXAMPLEKEY
```

```hcl
provider "aws" {
  region  = "us-east-1"
  profile = "production"  # Use named profile
}
```

#### 3. IAM Instance Profile / ECS Task Role (Recommended for AWS Workloads)

```hcl
# No credentials needed -- Terraform uses the instance/task role automatically
provider "aws" {
  region = "us-east-1"
}
```

#### 4. Assume Role

```hcl
provider "aws" {
  region = "us-east-1"

  assume_role {
    role_arn     = "arn:aws:iam::123456789012:role/TerraformRole"
    session_name = "terraform-session"
    external_id  = "my-external-id"
  }
}
```

### Common AWS Provider Arguments

```hcl
provider "aws" {
  region = "us-east-1"

  # Default tags applied to ALL resources
  default_tags {
    tags = {
      Environment = "Production"
      ManagedBy   = "Terraform"
      Project     = "MyApp"
    }
  }

  # Ignore specific tag changes (useful for auto-tagging)
  ignore_tags {
    key_prefixes = ["kubernetes.io/"]
  }

  # Custom endpoints (for LocalStack or testing)
  endpoints {
    s3  = "http://localhost:4566"
    ec2 = "http://localhost:4566"
  }
}
```

### AWS Provider Example: Complete VPC Setup

```hcl
provider "aws" {
  region = "us-east-1"

  default_tags {
    tags = {
      ManagedBy = "Terraform"
    }
  }
}

resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true

  tags = { Name = "main-vpc" }
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "us-east-1a"
  map_public_ip_on_launch = true

  tags = { Name = "public-subnet" }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = { Name = "main-igw" }
}
```

---

## Azure Provider

### Basic Configuration

```hcl
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}  # Required even if empty
}
```

> **Note**: The `features {}` block is **required** for the Azure provider, even if you leave it empty.

### Authentication Methods

#### 1. Azure CLI (Recommended for Local Development)

```bash
# Log in with Azure CLI
az login

# Set subscription
az account set --subscription="SUBSCRIPTION_ID"
```

```hcl
provider "azurerm" {
  features {}
  subscription_id = "00000000-0000-0000-0000-000000000000"
}
```

#### 2. Service Principal with Client Secret (Recommended for CI/CD)

```bash
export ARM_CLIENT_ID="00000000-0000-0000-0000-000000000000"
export ARM_CLIENT_SECRET="your-client-secret"
export ARM_SUBSCRIPTION_ID="00000000-0000-0000-0000-000000000000"
export ARM_TENANT_ID="00000000-0000-0000-0000-000000000000"
```

```hcl
provider "azurerm" {
  features {}
}
```

#### 3. Managed Identity (Recommended for Azure Workloads)

```hcl
provider "azurerm" {
  features {}
  use_msi = true
}
```

### Azure Provider Features Block

```hcl
provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = true
    }

    virtual_machine {
      delete_os_disk_on_deletion     = true
      graceful_shutdown               = false
      skip_shutdown_and_force_delete  = false
    }

    key_vault {
      purge_soft_delete_on_destroy    = true
      recover_soft_deleted_key_vaults = true
    }
  }
}
```

### Azure Provider Example: Resource Group and Storage

```hcl
provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "example" {
  name     = "rg-devsecops-dev"
  location = "East US"

  tags = {
    Environment = "Development"
    ManagedBy   = "Terraform"
  }
}

resource "azurerm_storage_account" "example" {
  name                     = "stdevsecopsdev001"
  resource_group_name      = azurerm_resource_group.example.name
  location                 = azurerm_resource_group.example.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  min_tls_version          = "TLS1_2"

  tags = azurerm_resource_group.example.tags
}
```

---

## GCP Provider

### Basic Configuration

```hcl
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = "my-gcp-project-id"
  region  = "us-central1"
  zone    = "us-central1-a"
}
```

### Authentication Methods

#### 1. Application Default Credentials (Recommended for Local Development)

```bash
gcloud auth application-default login
```

#### 2. Service Account Key File

```hcl
provider "google" {
  project     = "my-project"
  region      = "us-central1"
  credentials = file("service-account-key.json")
}
```

> **Security Warning**: Never commit service account keys to Git. Use environment variables instead.

#### 3. Environment Variable

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
export GOOGLE_PROJECT="my-project-id"
```

#### 4. Workload Identity (Recommended for GCP Workloads)

```hcl
# No credentials needed -- uses the attached service account
provider "google" {
  project = "my-project"
  region  = "us-central1"
}
```

### GCP Provider Example

```hcl
provider "google" {
  project = "my-devsecops-project"
  region  = "us-central1"
}

resource "google_compute_network" "vpc" {
  name                    = "devsecops-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "subnet" {
  name          = "devsecops-subnet"
  ip_cidr_range = "10.0.1.0/24"
  region        = "us-central1"
  network       = google_compute_network.vpc.id
}

resource "google_compute_instance" "web" {
  name         = "web-server"
  machine_type = "e2-micro"
  zone         = "us-central1-a"

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-11"
    }
  }

  network_interface {
    subnetwork = google_compute_subnetwork.subnet.id
    access_config {} # Assigns public IP
  }

  labels = {
    environment = "dev"
    managed_by  = "terraform"
  }
}
```

---

## Provider Versioning

### Why Version Pinning Matters

Providers are updated frequently. Without version pinning, a `terraform init` could download a newer version that introduces breaking changes.

### Version Constraint Syntax

```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"

      # Exact version
      version = "5.31.0"

      # Minimum version
      version = ">= 5.0"

      # Pessimistic constraint (recommended)
      version = "~> 5.0"     # >= 5.0.0, < 6.0.0
      version = "~> 5.31.0"  # >= 5.31.0, < 5.32.0

      # Range
      version = ">= 5.0, < 6.0"

      # Exclude specific version
      version = ">= 5.0, != 5.15.0"
    }
  }
}
```

### The Dependency Lock File

After `terraform init`, a `.terraform.lock.hcl` file is created:

```hcl
# .terraform.lock.hcl
provider "registry.terraform.io/hashicorp/aws" {
  version     = "5.31.0"
  constraints = "~> 5.0"
  hashes = [
    "h1:abc123...",
    "zh:def456...",
  ]
}
```

This file:
- **Locks** the exact provider version used
- **Records hashes** to verify provider integrity (security!)
- **Must be committed** to version control

```bash
# Update providers to latest versions within constraints
terraform init -upgrade
```

---

## Multiple Providers and Aliases

### Multi-Region Deployment

Use **provider aliases** to manage resources in multiple regions:

```hcl
# Default provider (us-east-1)
provider "aws" {
  region = "us-east-1"
}

# Aliased provider (us-west-2)
provider "aws" {
  alias  = "west"
  region = "us-west-2"
}

# Aliased provider (eu-west-1)
provider "aws" {
  alias  = "europe"
  region = "eu-west-1"
}

# Resource in default region (us-east-1)
resource "aws_instance" "east_server" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"
  tags = { Name = "east-server" }
}

# Resource in us-west-2
resource "aws_instance" "west_server" {
  provider      = aws.west
  ami           = "ami-0d74386b2ba5b1b28"
  instance_type = "t2.micro"
  tags = { Name = "west-server" }
}

# Resource in eu-west-1
resource "aws_instance" "europe_server" {
  provider      = aws.europe
  ami           = "ami-0d71ea30463e0ff8d"
  instance_type = "t2.micro"
  tags = { Name = "europe-server" }
}
```

### Multi-Cloud Deployment

You can use multiple cloud providers in a single configuration:

```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

provider "azurerm" {
  features {}
}

provider "google" {
  project = "my-project"
  region  = "us-central1"
}

# AWS S3 bucket
resource "aws_s3_bucket" "data" {
  bucket = "my-app-data-bucket"
}

# Azure Blob storage
resource "azurerm_storage_account" "data" {
  name                     = "myappdatastorage"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = "East US"
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

# GCP Cloud Storage bucket
resource "google_storage_bucket" "data" {
  name     = "my-app-data-bucket-gcp"
  location = "US"
}
```

### Multi-Account Deployment

```hcl
# Production AWS account
provider "aws" {
  alias  = "production"
  region = "us-east-1"

  assume_role {
    role_arn = "arn:aws:iam::111111111111:role/TerraformRole"
  }
}

# Staging AWS account
provider "aws" {
  alias  = "staging"
  region = "us-east-1"

  assume_role {
    role_arn = "arn:aws:iam::222222222222:role/TerraformRole"
  }
}

# Production VPC
resource "aws_vpc" "prod" {
  provider   = aws.production
  cidr_block = "10.0.0.0/16"
  tags       = { Name = "prod-vpc" }
}

# Staging VPC
resource "aws_vpc" "staging" {
  provider   = aws.staging
  cidr_block = "10.1.0.0/16"
  tags       = { Name = "staging-vpc" }
}
```

### Passing Providers to Modules

```hcl
module "vpc_east" {
  source = "./modules/vpc"

  providers = {
    aws = aws  # Default provider
  }

  cidr_block = "10.0.0.0/16"
}

module "vpc_west" {
  source = "./modules/vpc"

  providers = {
    aws = aws.west  # Aliased provider
  }

  cidr_block = "10.1.0.0/16"
}
```

---

## Provider Authentication Best Practices

### Do's

| Practice | Example |
|----------|---------|
| Use environment variables | `export AWS_ACCESS_KEY_ID=...` |
| Use IAM roles / Managed Identity | Instance profiles, Workload Identity |
| Use assume role for cross-account | `assume_role { role_arn = "..." }` |
| Use `aws-vault` or similar tools | `aws-vault exec prod -- terraform plan` |
| Store credentials in a secrets manager | HashiCorp Vault, AWS Secrets Manager |

### Don'ts

```hcl
# NEVER hardcode credentials in .tf files!
provider "aws" {
  region     = "us-east-1"
  access_key = "AKIAIOSFODNN7EXAMPLE"       # BAD!
  secret_key = "wJalrXUtnFEMI/K7MDENG..."   # BAD!
}
```

> **DevSecOps Rule**: Credentials should never appear in code, variable files committed to Git, or state files accessible to unauthorized users.

### Authentication Hierarchy for CI/CD

```
1. OIDC (GitHub Actions, GitLab CI) -- Best for CI/CD
2. IAM Roles (Instance Profile, ECS Task Role) -- Best for cloud workloads
3. Environment Variables -- Good for local/CI
4. Shared Credentials File -- Acceptable for local development
5. Hardcoded in .tf files -- NEVER DO THIS
```

---

## Key Takeaways

1. **Providers are the bridge** between Terraform and external APIs -- every resource belongs to a provider
2. **Always declare providers** in the `required_providers` block with version constraints
3. **Pin provider versions** using `~>` to avoid breaking changes
4. **Commit `.terraform.lock.hcl`** to version control for reproducible builds
5. **Use provider aliases** for multi-region or multi-account deployments
6. **Never hardcode credentials** -- use environment variables, IAM roles, or OIDC
7. **The Terraform Registry** has 3,800+ providers for almost any service you need

---

## What's Next?

In the next lesson, we will dive deep into Terraform resources -- the fundamental building blocks of your infrastructure.

[Previous Lesson: Terraform Basics](./02-terraform-basics.md) | [Next Lesson: Terraform Resources -->](./04-terraform-resources.md)
