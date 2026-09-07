# Lab 02: Provisioning an AWS EC2 Instance

## Difficulty: Beginner–Intermediate

## Objectives

By the end of this lab, you will be able to:

- Configure the AWS provider in Terraform
- Define and use input variables for flexible configurations
- Provision a VPC, security group, key pair, and EC2 instance
- Use Terraform outputs to display useful information
- SSH into your provisioned instance
- Clean up cloud resources to avoid unnecessary costs

## Prerequisites

- Completed [Lab 01](lab01-first-terraform-project.md)
- An AWS account (Free Tier eligible)
- AWS CLI installed and configured (`aws configure`)
- An SSH key pair generated on your local machine
- Basic understanding of AWS networking concepts (VPC, subnets, security groups)

## Estimated Time

60 minutes

---

## Part 1: Set Up AWS Credentials

### Step 1.1: Verify AWS CLI Configuration

```bash
aws sts get-caller-identity
```

**Expected Output:**

```json
{
    "UserId": "AIDAXXXXXXXXXXXXXXXXX",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/your-username"
}
```

If this fails, configure your credentials:

```bash
aws configure
```

> **DevSecOps Note:** Never hardcode AWS credentials in Terraform files. Use environment variables, AWS CLI profiles, or IAM roles. We will use the default credentials chain here.

### Step 1.2: Generate an SSH Key Pair (If Needed)

```bash
ssh-keygen -t ed25519 -f ~/.ssh/terraform-lab -N ""
```

This creates:
- `~/.ssh/terraform-lab` (private key)
- `~/.ssh/terraform-lab.pub` (public key)

---

## Part 2: Create the Terraform Configuration

### Step 2.1: Set Up the Project Directory

```bash
mkdir -p ~/terraform-labs/lab02
cd ~/terraform-labs/lab02
```

### Step 2.2: Create the Provider Configuration

Create `providers.tf`:

```hcl
# providers.tf

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

  default_tags {
    tags = {
      Project     = "DevSecOps-Lab02"
      Environment = "lab"
      ManagedBy   = "terraform"
    }
  }
}
```

### Step 2.3: Define Input Variables

Create `variables.tf`:

```hcl
# variables.tf

variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t2.micro"
}

variable "instance_name" {
  description = "Name tag for the EC2 instance"
  type        = string
  default     = "devsecops-lab02"
}

variable "ssh_public_key_path" {
  description = "Path to the SSH public key file"
  type        = string
  default     = "~/.ssh/terraform-lab.pub"
}

variable "allowed_ssh_cidr" {
  description = "CIDR block allowed to SSH into the instance"
  type        = string
  default     = "0.0.0.0/0" # Restrict this in production!
}
```

### Step 2.4: Add a Data Source for the AMI

Create `data.tf`:

```hcl
# data.tf

# Dynamically fetch the latest Amazon Linux 2023 AMI
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

# Get the default VPC
data "aws_vpc" "default" {
  default = true
}

# Get a subnet in the default VPC
data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}
```

### Step 2.5: Create the Main Resources

Create `main.tf`:

```hcl
# main.tf

# Upload the SSH public key to AWS
resource "aws_key_pair" "lab" {
  key_name   = "${var.instance_name}-key"
  public_key = file(var.ssh_public_key_path)

  tags = {
    Name = "${var.instance_name}-key"
  }
}

# Create a security group
resource "aws_security_group" "lab" {
  name        = "${var.instance_name}-sg"
  description = "Security group for DevSecOps Lab 02"
  vpc_id      = data.aws_vpc.default.id

  # SSH access
  ingress {
    description = "SSH from allowed CIDR"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.allowed_ssh_cidr]
  }

  # HTTP access
  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # All outbound traffic
  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.instance_name}-sg"
  }
}

# Launch the EC2 instance
resource "aws_instance" "lab" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = var.instance_type
  key_name               = aws_key_pair.lab.key_name
  vpc_security_group_ids = [aws_security_group.lab.id]
  subnet_id              = data.aws_subnets.default.ids[0]

  # Enable detailed monitoring (DevSecOps best practice)
  monitoring = true

  # Add a simple user_data script
  user_data = <<-EOF
    #!/bin/bash
    yum update -y
    yum install -y httpd
    systemctl start httpd
    systemctl enable httpd
    echo "<h1>Hello from Terraform - DevSecOps Lab 02</h1>" > /var/www/html/index.html
    echo "<p>Instance ID: $(curl -s http://169.254.169.254/latest/meta-data/instance-id)</p>" >> /var/www/html/index.html
  EOF

  root_block_device {
    volume_size = 8
    volume_type = "gp3"
    encrypted   = true # DevSecOps: Always encrypt volumes

    tags = {
      Name = "${var.instance_name}-root-volume"
    }
  }

  metadata_options {
    http_tokens   = "required" # DevSecOps: Enforce IMDSv2
    http_endpoint = "enabled"
  }

  tags = {
    Name = var.instance_name
  }
}
```

### Step 2.6: Define Outputs

Create `outputs.tf`:

```hcl
# outputs.tf

output "instance_id" {
  description = "The ID of the EC2 instance"
  value       = aws_instance.lab.id
}

output "instance_public_ip" {
  description = "The public IP address of the EC2 instance"
  value       = aws_instance.lab.public_ip
}

output "instance_public_dns" {
  description = "The public DNS name of the EC2 instance"
  value       = aws_instance.lab.public_dns
}

output "security_group_id" {
  description = "The ID of the security group"
  value       = aws_security_group.lab.id
}

output "ami_id" {
  description = "The AMI ID used for the instance"
  value       = data.aws_ami.amazon_linux.id
}

output "ssh_command" {
  description = "Command to SSH into the instance"
  value       = "ssh -i ~/.ssh/terraform-lab ec2-user@${aws_instance.lab.public_ip}"
}

output "web_url" {
  description = "URL to access the web server"
  value       = "http://${aws_instance.lab.public_dns}"
}
```

---

## Part 3: Deploy the Infrastructure

### Step 3.1: Initialize the Project

```bash
terraform init
```

### Step 3.2: Review the Plan

```bash
terraform plan
```

Carefully review the plan output. You should see:
- 1 `aws_key_pair` to be created
- 1 `aws_security_group` to be created (with 2 ingress and 1 egress rules)
- 1 `aws_instance` to be created

### Step 3.3: Apply the Configuration

```bash
terraform apply
```

Type `yes` when prompted. This will take 1–2 minutes.

**Expected Output (end of apply):**

```
Apply complete! Resources: 3 added, 0 changed, 0 destroyed.

Outputs:

ami_id = "ami-0abcdef1234567890"
instance_id = "i-0abcdef1234567890"
instance_public_dns = "ec2-XX-XX-XX-XX.compute-1.amazonaws.com"
instance_public_ip = "XX.XX.XX.XX"
security_group_id = "sg-0abcdef1234567890"
ssh_command = "ssh -i ~/.ssh/terraform-lab ec2-user@XX.XX.XX.XX"
web_url = "http://ec2-XX-XX-XX-XX.compute-1.amazonaws.com"
```

### Step 3.4: Access Your Instance

**SSH into the instance:**

```bash
# Use the ssh_command output
$(terraform output -raw ssh_command)
```

**View the web page:**

Open the `web_url` output in your browser, or:

```bash
curl $(terraform output -raw web_url)
```

---

## Part 4: Inspect and Modify

### Step 4.1: View Outputs

```bash
terraform output
terraform output -json
terraform output -raw instance_public_ip
```

### Step 4.2: Inspect State

```bash
terraform state list
terraform state show aws_instance.lab
```

### Step 4.3: Make a Change

Modify the instance name in `main.tf` by adding a tag:

```hcl
  tags = {
    Name        = var.instance_name
    LastUpdated = timestamp()
  }
```

Then plan and apply:

```bash
terraform plan
terraform apply -auto-approve
```

> **Observe:** Notice how Terraform performs an **in-place update** for tag changes (no instance replacement needed).

### Step 4.4: View in AWS Console

Log into the AWS Management Console and navigate to:
- **EC2 → Instances** — find your instance
- **EC2 → Security Groups** — find your security group
- **EC2 → Key Pairs** — find your key pair

Compare what you see in the console with the Terraform state.

---

## Part 5: Clean Up

### Step 5.1: Destroy All Resources

```bash
terraform destroy
```

Type `yes` when prompted.

**Expected Output:**

```
aws_instance.lab: Destroying... [id=i-0abcdef1234567890]
aws_instance.lab: Still destroying... [id=i-0abcdef1234567890, 10s elapsed]
aws_instance.lab: Destruction complete after 30s
aws_security_group.lab: Destroying... [id=sg-0abcdef1234567890]
aws_security_group.lab: Destruction complete after 1s
aws_key_pair.lab: Destroying... [id=devsecops-lab02-key]
aws_key_pair.lab: Destruction complete after 0s

Destroy complete! Resources: 3 destroyed.
```

### Step 5.2: Verify Cleanup

```bash
aws ec2 describe-instances --filters "Name=tag:Name,Values=devsecops-lab02" \
  --query "Reservations[].Instances[].State.Name" --output text
```

The instance should show `terminated` or return no results.

---

## Expected Outcomes

After completing this lab, you should have:

- [x] Configured the AWS provider with best practices (default tags, no hardcoded creds)
- [x] Used a data source to dynamically fetch the latest AMI
- [x] Provisioned a security group with appropriate rules
- [x] Launched an EC2 instance with encrypted volumes and IMDSv2
- [x] Used variables to make the configuration flexible
- [x] Defined outputs to display useful deployment information
- [x] Successfully SSHed into and accessed the web server on the instance
- [x] Destroyed all resources cleanly

---

## DevSecOps Best Practices Highlighted

| Practice | Implementation |
|---|---|
| No hardcoded credentials | Used AWS CLI default credential chain |
| Encrypted storage | `encrypted = true` on root volume |
| IMDSv2 enforced | `http_tokens = "required"` in metadata options |
| Least privilege networking | Security group with specific port rules |
| Resource tagging | Consistent tags via `default_tags` and resource-level tags |
| Infrastructure as Code | All resources defined in version-controlled `.tf` files |

---

## Bonus Challenges

### Challenge 1: Restrict SSH Access

Find your current public IP and restrict SSH access to only your IP address:

```bash
MY_IP=$(curl -s https://checkip.amazonaws.com)
echo $MY_IP
```

Update `terraform.tfvars`:

```hcl
allowed_ssh_cidr = "YOUR_IP/32"
```

### Challenge 2: Add an Elastic IP

Add an `aws_eip` resource and associate it with your instance so the public IP persists across stop/start cycles.

<details>
<summary>Hint</summary>

```hcl
resource "aws_eip" "lab" {
  instance = aws_instance.lab.id
  domain   = "vpc"

  tags = {
    Name = "${var.instance_name}-eip"
  }
}
```

</details>

### Challenge 3: Add a Second Instance

Create a second EC2 instance in a different availability zone using the same security group and key pair. Output both IP addresses.

### Challenge 4: Use `terraform.tfvars`

Create a `terraform.tfvars` file to override the default variable values:

```hcl
aws_region    = "us-west-2"
instance_type = "t3.micro"
instance_name = "my-devsecops-instance"
```

Re-run `terraform plan` and observe the changes.

---

## Cleanup

```bash
terraform destroy -auto-approve
cd ~
rm -rf ~/terraform-labs/lab02
```

---

## Next Lab

Proceed to [Lab 03: Variables and Outputs Deep Dive](lab03-variables-and-outputs.md) to master Terraform's type system and data flow.
