# Lesson 4: Terraform Resources

---

## Table of Contents

1. [What Are Resources?](#what-are-resources)
2. [Resource Block Syntax](#resource-block-syntax)
3. [Resource Arguments](#resource-arguments)
4. [Meta-Arguments](#meta-arguments)
5. [Resource Dependencies](#resource-dependencies)
6. [Resource Addressing](#resource-addressing)
7. [Data Sources](#data-sources)
8. [Key Takeaways](#key-takeaways)

---

## What Are Resources?

**Resources** are the most important element in Terraform. Each resource block describes one or more infrastructure objects, such as:

- A virtual machine (`aws_instance`)
- A virtual network (`aws_vpc`, `azurerm_virtual_network`)
- A DNS record (`aws_route53_record`)
- A database instance (`aws_db_instance`)
- A Kubernetes deployment (`kubernetes_deployment`)

Resources are the things Terraform **creates, reads, updates, and deletes** (CRUD operations) to match your desired configuration.

---

## Resource Block Syntax

### Basic Structure

```hcl
resource "<PROVIDER>_<TYPE>" "<LOCAL_NAME>" {
  <ARGUMENT> = <VALUE>

  <NESTED_BLOCK> {
    <ARGUMENT> = <VALUE>
  }
}
```

- **`<PROVIDER>_<TYPE>`**: The resource type (e.g., `aws_instance`, `azurerm_resource_group`)
- **`<LOCAL_NAME>`**: A unique name within your configuration (used to reference this resource)
- **Arguments**: Configuration for the resource
- **Nested Blocks**: Sub-configurations (like `ingress` rules in a security group)

### Example: AWS EC2 Instance

```hcl
resource "aws_instance" "web_server" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.micro"
  subnet_id     = aws_subnet.public.id

  root_block_device {
    volume_size = 20
    volume_type = "gp3"
    encrypted   = true
  }

  tags = {
    Name        = "web-server"
    Environment = "production"
    ManagedBy   = "terraform"
  }
}
```

### Example: Azure Virtual Machine

```hcl
resource "azurerm_linux_virtual_machine" "web" {
  name                = "web-vm"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  size                = "Standard_B1s"
  admin_username      = "adminuser"

  network_interface_ids = [
    azurerm_network_interface.web.id,
  ]

  admin_ssh_key {
    username   = "adminuser"
    public_key = file("~/.ssh/id_rsa.pub")
  }

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts"
    version   = "latest"
  }
}
```

---

## Resource Arguments

Resources have two types of arguments:

### Required Arguments

These must be specified -- Terraform will error without them:

```hcl
resource "aws_instance" "example" {
  ami           = "ami-0c55b159cbfafe1f0"  # Required
  instance_type = "t3.micro"                # Required
}
```

### Optional Arguments

These have defaults and can be omitted:

```hcl
resource "aws_instance" "example" {
  ami                         = "ami-0c55b159cbfafe1f0"
  instance_type               = "t3.micro"
  associate_public_ip_address = true           # Optional (default: depends on subnet)
  monitoring                  = true           # Optional (default: false)
  disable_api_termination     = false          # Optional (default: false)
}
```

### Computed Attributes

Some attributes are not set by you -- they are computed by the provider after creation:

```hcl
resource "aws_instance" "example" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.micro"
}

# These attributes are available AFTER creation:
# aws_instance.example.id            -> "i-1234567890abcdef0"
# aws_instance.example.public_ip     -> "54.123.45.67"
# aws_instance.example.arn           -> "arn:aws:ec2:us-east-1:123456789:instance/i-123..."
# aws_instance.example.private_dns   -> "ip-10-0-1-23.ec2.internal"
```

---

## Meta-Arguments

Meta-arguments are special arguments available on **every** resource type. They change how Terraform handles the resource rather than configuring the resource itself.

### 1. `count` -- Create Multiple Identical Resources

```hcl
resource "aws_instance" "web" {
  count = 3

  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.micro"

  tags = {
    Name = "web-server-${count.index}"  # web-server-0, web-server-1, web-server-2
  }
}

# Reference individual instances:
# aws_instance.web[0].public_ip
# aws_instance.web[1].public_ip
# aws_instance.web[2].public_ip

# Reference all instances:
# aws_instance.web[*].public_ip  -> ["54.1.2.3", "54.4.5.6", "54.7.8.9"]
```

**Conditional resource creation with `count`:**

```hcl
variable "create_monitoring" {
  type    = bool
  default = true
}

resource "aws_cloudwatch_metric_alarm" "high_cpu" {
  count = var.create_monitoring ? 1 : 0  # Create only if monitoring is enabled

  alarm_name          = "high-cpu-alarm"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = "120"
  statistic           = "Average"
  threshold           = "80"
}
```

> **Caveat with `count`**: Resources are identified by index. If you remove an item from the middle of the list, all subsequent resources are renumbered and may be destroyed/recreated.

### 2. `for_each` -- Create Multiple Resources from a Map or Set

`for_each` is generally preferred over `count` because resources are identified by key, not index.

**With a set of strings:**

```hcl
resource "aws_iam_user" "developers" {
  for_each = toset(["alice", "bob", "charlie"])

  name = each.value

  tags = {
    Team = "Development"
  }
}

# Reference:
# aws_iam_user.developers["alice"].arn
# aws_iam_user.developers["bob"].arn
```

**With a map:**

```hcl
variable "instances" {
  default = {
    web = {
      instance_type = "t3.micro"
      ami           = "ami-0c55b159cbfafe1f0"
    }
    api = {
      instance_type = "t3.small"
      ami           = "ami-0c55b159cbfafe1f0"
    }
    worker = {
      instance_type = "t3.medium"
      ami           = "ami-0c55b159cbfafe1f0"
    }
  }
}

resource "aws_instance" "servers" {
  for_each = var.instances

  ami           = each.value.ami
  instance_type = each.value.instance_type

  tags = {
    Name = "${each.key}-server"  # web-server, api-server, worker-server
    Role = each.key
  }
}

# Reference:
# aws_instance.servers["web"].public_ip
# aws_instance.servers["api"].public_ip
```

**Why `for_each` is safer than `count`:**

```hcl
# With count: removing "bob" shifts charlie's index, causing recreation
# count = ["alice", "bob", "charlie"]
#   [0] = alice, [1] = bob, [2] = charlie
# Remove bob:
#   [0] = alice, [1] = charlie  <- charlie was [2], now recreated as [1]

# With for_each: removing "bob" only affects bob
# for_each = {"alice", "bob", "charlie"}
# Remove bob: only bob is destroyed, alice and charlie are untouched
```

### 3. `depends_on` -- Explicit Dependencies

Terraform automatically detects dependencies through resource references. Use `depends_on` only when there are hidden dependencies that Terraform cannot detect.

```hcl
resource "aws_iam_role" "app" {
  name = "app-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "app" {
  name = "app-policy"
  role = aws_iam_role.app.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action   = ["s3:GetObject"]
      Effect   = "Allow"
      Resource = "${aws_s3_bucket.data.arn}/*"
    }]
  })
}

resource "aws_instance" "app" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.micro"

  iam_instance_profile = aws_iam_instance_profile.app.name

  # Terraform can't know the instance needs the POLICY (not just the role)
  # to function properly at boot time
  depends_on = [aws_iam_role_policy.app]
}
```

> **Best Practice**: Avoid `depends_on` when possible. Let Terraform infer dependencies from references. Use `depends_on` only for side-effect dependencies that are not visible in the configuration.

### 4. `lifecycle` -- Control Resource Behavior

The `lifecycle` block customizes how Terraform handles resource creation, updates, and deletion.

#### `create_before_destroy`

```hcl
resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.micro"

  lifecycle {
    create_before_destroy = true  # Create new instance before destroying old one
  }
}
```

This is crucial for zero-downtime deployments. Normally Terraform destroys the old resource first, then creates the new one. This reverses that order.

#### `prevent_destroy`

```hcl
resource "aws_db_instance" "production" {
  identifier     = "prod-database"
  engine         = "postgres"
  engine_version = "15.4"
  instance_class = "db.r5.large"

  lifecycle {
    prevent_destroy = true  # Terraform will error if this resource would be destroyed
  }
}
```

This is a safety net for critical resources like production databases. Terraform will raise an error if any operation would destroy the resource.

#### `ignore_changes`

```hcl
resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.micro"

  tags = {
    Name = "web-server"
  }

  lifecycle {
    # Ignore changes to tags made outside Terraform (e.g., by auto-scaling)
    ignore_changes = [tags, ami]
  }
}
```

Use this when external processes modify resource attributes and you do not want Terraform to revert those changes.

#### `replace_triggered_by`

```hcl
resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.micro"
}

resource "aws_instance" "app" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.micro"

  lifecycle {
    # Recreate this instance whenever the web instance changes
    replace_triggered_by = [aws_instance.web.id]
  }
}
```

#### `precondition` and `postcondition`

```hcl
resource "aws_instance" "web" {
  ami           = var.ami_id
  instance_type = var.instance_type

  lifecycle {
    precondition {
      condition     = contains(["t3.micro", "t3.small", "t3.medium"], var.instance_type)
      error_message = "Instance type must be t3.micro, t3.small, or t3.medium."
    }

    postcondition {
      condition     = self.public_ip != ""
      error_message = "The instance must have a public IP address."
    }
  }
}
```

---

## Resource Dependencies

### Implicit Dependencies (Automatic)

Terraform automatically creates dependencies when one resource references another:

```hcl
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}

# Terraform knows this subnet depends on the VPC because of the reference
resource "aws_subnet" "public" {
  vpc_id     = aws_vpc.main.id   # <-- implicit dependency
  cidr_block = "10.0.1.0/24"
}

# Terraform knows this instance depends on the subnet
resource "aws_instance" "web" {
  subnet_id = aws_subnet.public.id   # <-- implicit dependency
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.micro"
}
```

Terraform builds a **dependency graph** and creates resources in the correct order:
```
VPC → Subnet → Instance
```

### Viewing the Dependency Graph

```bash
# Generate a visual dependency graph (DOT format)
terraform graph | dot -Tpng > graph.png

# Or view in text format
terraform graph
```

---

## Resource Addressing

Every resource has a unique address used to reference it in configurations, commands, and state operations.

### Address Format

```
<RESOURCE_TYPE>.<LOCAL_NAME>
<RESOURCE_TYPE>.<LOCAL_NAME>[<INDEX_OR_KEY>]
module.<MODULE_NAME>.<RESOURCE_TYPE>.<LOCAL_NAME>
```

### Examples

```hcl
# Simple resource
resource "aws_instance" "web" { ... }
# Address: aws_instance.web

# Resource with count
resource "aws_instance" "web" {
  count = 3
  ...
}
# Addresses: aws_instance.web[0], aws_instance.web[1], aws_instance.web[2]

# Resource with for_each
resource "aws_instance" "web" {
  for_each = toset(["a", "b", "c"])
  ...
}
# Addresses: aws_instance.web["a"], aws_instance.web["b"], aws_instance.web["c"]

# Resource inside a module
module "vpc" {
  source = "./modules/vpc"
}
# Address: module.vpc.aws_vpc.main
```

### Using Addresses in Commands

```bash
# Target a specific resource
terraform plan -target=aws_instance.web
terraform apply -target=aws_instance.web

# Destroy a specific resource
terraform destroy -target=aws_instance.web[0]

# Show a specific resource in state
terraform state show aws_instance.web

# Remove a resource from state (without destroying it)
terraform state rm aws_instance.web

# Move/rename a resource in state
terraform state mv aws_instance.web aws_instance.app_server

# Import an existing resource into state
terraform import aws_instance.web i-1234567890abcdef0
```

---

## Data Sources

Data sources allow you to **read** information from existing resources that are not managed by your Terraform configuration.

### Syntax

```hcl
data "<PROVIDER>_<TYPE>" "<LOCAL_NAME>" {
  # Query arguments (filters)
}
```

### Example: Look Up an AMI

```hcl
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]  # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_instance" "web" {
  ami           = data.aws_ami.ubuntu.id  # Use the looked-up AMI
  instance_type = "t3.micro"
}
```

### Example: Look Up an Existing VPC

```hcl
data "aws_vpc" "existing" {
  filter {
    name   = "tag:Name"
    values = ["production-vpc"]
  }
}

resource "aws_subnet" "new" {
  vpc_id     = data.aws_vpc.existing.id
  cidr_block = "10.0.99.0/24"
}
```

### Example: Look Up Current AWS Account Info

```hcl
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

output "account_id" {
  value = data.aws_caller_identity.current.account_id
}

output "current_region" {
  value = data.aws_region.current.name
}
```

### Example: Read a File

```hcl
data "local_file" "config" {
  filename = "${path.module}/config.json"
}

output "config_content" {
  value = data.local_file.config.content
}
```

### Resource vs. Data Source

| Feature | Resource | Data Source |
|---------|----------|-------------|
| **Keyword** | `resource` | `data` |
| **Purpose** | Create/manage infrastructure | Read existing infrastructure |
| **CRUD** | Create, Read, Update, Delete | Read only |
| **State** | Tracked in state | Cached in state (read-only) |
| **Reference** | `aws_instance.web.id` | `data.aws_ami.ubuntu.id` |

---

## Practical Example: Complete Web Application Infrastructure

```hcl
# ──────────────────────────────────────────────
# Data Sources
# ──────────────────────────────────────────────

data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}

data "aws_availability_zones" "available" {
  state = "available"
}

# ──────────────────────────────────────────────
# Networking
# ──────────────────────────────────────────────

resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = { Name = "main-vpc" }
}

resource "aws_subnet" "public" {
  count = 2

  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.${count.index + 1}.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "public-subnet-${count.index + 1}"
  }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  tags   = { Name = "main-igw" }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = { Name = "public-rt" }
}

resource "aws_route_table_association" "public" {
  count          = 2
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# ──────────────────────────────────────────────
# Security
# ──────────────────────────────────────────────

resource "aws_security_group" "web" {
  name        = "web-sg"
  description = "Security group for web servers"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow HTTP"
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow HTTPS"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound"
  }

  tags = { Name = "web-sg" }

  lifecycle {
    create_before_destroy = true
  }
}

# ──────────────────────────────────────────────
# Compute
# ──────────────────────────────────────────────

resource "aws_instance" "web" {
  for_each = {
    web-1 = aws_subnet.public[0].id
    web-2 = aws_subnet.public[1].id
  }

  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = "t3.micro"
  subnet_id              = each.value
  vpc_security_group_ids = [aws_security_group.web.id]

  user_data = <<-EOF
    #!/bin/bash
    yum update -y
    yum install -y httpd
    systemctl start httpd
    echo "<h1>Hello from ${each.key}</h1>" > /var/www/html/index.html
  EOF

  tags = {
    Name = each.key
    Role = "web"
  }

  lifecycle {
    create_before_destroy = true

    postcondition {
      condition     = self.instance_state == "running"
      error_message = "Instance ${each.key} is not in running state."
    }
  }
}

# ──────────────────────────────────────────────
# Outputs
# ──────────────────────────────────────────────

output "web_server_ips" {
  value = { for k, v in aws_instance.web : k => v.public_ip }
}
```

---

## Key Takeaways

1. **Resources are the core of Terraform** -- they represent the infrastructure objects you create and manage
2. **Resource names must be unique** within a given type in your configuration
3. **Use `for_each` over `count`** when resources have meaningful identifiers (prevents index-shifting issues)
4. **`lifecycle` blocks** give you fine-grained control over how resources are created, updated, and destroyed
5. **`prevent_destroy`** is essential for protecting critical resources like databases
6. **Data sources** let you read information from existing resources without managing them
7. **Implicit dependencies** (through references) are preferred over explicit `depends_on`
8. **Resource addresses** are used in commands, state operations, and cross-resource references

---

## What's Next?

In the next lesson, we will explore Terraform variables -- how to parameterize your configurations and make them reusable.

[Previous Lesson: Terraform Providers](./03-terraform-providers.md) | [Next Lesson: Terraform Variables -->](./05-terraform-variables.md)
