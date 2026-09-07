# Lesson 8: Terraform Expressions and Functions

---

## Table of Contents

1. [Expressions Overview](#expressions-overview)
2. [String Functions](#string-functions)
3. [Numeric Functions](#numeric-functions)
4. [Collection Functions](#collection-functions)
5. [Encoding Functions](#encoding-functions)
6. [Filesystem Functions](#filesystem-functions)
7. [Type Conversion Functions](#type-conversion-functions)
8. [Conditional Expressions](#conditional-expressions)
9. [For Expressions](#for-expressions)
10. [Splat Expressions](#splat-expressions)
11. [Dynamic Blocks](#dynamic-blocks)
12. [Key Takeaways](#key-takeaways)

---

## Expressions Overview

Expressions in Terraform are used to compute values. They can reference variables, resource attributes, call functions, and use operators.

### Types of Expressions

```hcl
# Literal values
name = "web-server"
count = 3
enabled = true

# References
vpc_id = aws_vpc.main.id
region = var.region
prefix = local.name_prefix

# Function calls
upper_name = upper(var.name)
cidr = cidrsubnet(var.vpc_cidr, 8, 1)

# Operators
total = var.base_count * 2
is_prod = var.environment == "prod"

# Conditional
size = var.environment == "prod" ? "large" : "small"

# Template (interpolation)
greeting = "Hello, ${var.name}!"
```

### The Terraform Console

Use the `terraform console` command to experiment with expressions interactively:

```bash
$ terraform console

> upper("hello")
"HELLO"

> length(["a", "b", "c"])
3

> cidrsubnet("10.0.0.0/16", 8, 1)
"10.0.1.0/24"

> max(5, 12, 9)
12

> exit
```

---

## String Functions

### `format` -- Format Strings (like printf)

```hcl
# format(spec, values...)
format("Hello, %s!", "World")           # "Hello, World!"
format("Instance %d of %d", 1, 3)      # "Instance 1 of 3"
format("CPU: %.1f%%", 85.678)           # "CPU: 85.7%"
format("%-20s %s", "Name:", "web-01")   # "Name:                web-01"

# Real-world usage
locals {
  instance_name = format("%s-%s-%02d", var.project, var.environment, count.index + 1)
  # Result: "myapp-prod-01", "myapp-prod-02", etc.
}
```

### `formatlist` -- Format Each Item in a List

```hcl
formatlist("Hello, %s!", ["Alice", "Bob", "Charlie"])
# ["Hello, Alice!", "Hello, Bob!", "Hello, Charlie!"]

formatlist("%s:%s", ["web", "api", "db"], ["80", "8080", "5432"])
# ["web:80", "api:8080", "db:5432"]
```

### `join` and `split`

```hcl
# join(separator, list)
join(", ", ["a", "b", "c"])    # "a, b, c"
join("-", ["web", "prod", "01"])  # "web-prod-01"

# split(separator, string)
split(",", "a,b,c")     # ["a", "b", "c"]
split("/", "10.0.0.0/16")  # ["10.0.0.0", "16"]
```

### `upper`, `lower`, `title`

```hcl
upper("hello world")    # "HELLO WORLD"
lower("HELLO WORLD")    # "hello world"
title("hello world")    # "Hello World"
```

### `trimspace`, `trim`, `trimprefix`, `trimsuffix`

```hcl
trimspace("  hello  ")          # "hello"
trim("?!hello!?", "?!")         # "hello"
trimprefix("helloworld", "hello")  # "world"
trimsuffix("helloworld", "world")  # "hello"
```

### `replace`

```hcl
replace("hello world", "world", "terraform")  # "hello terraform"
replace("hello-world-foo", "-", "_")           # "hello_world_foo"

# With regex (wrap pattern in forward slashes)
replace("hello 123 world", "/[0-9]+/", "NUM")  # "hello NUM world"
```

### `regex` and `regexall`

```hcl
# regex(pattern, string) -- returns first match
regex("[a-z]+", "1234abcd5678")          # "abcd"
regex("^(?:(?P<scheme>[^:/?#]+):)?", "https://example.com")
# { "scheme" = "https" }

# regexall(pattern, string) -- returns all matches
regexall("[a-z]+", "1234abcd5678efgh")   # ["abcd", "efgh"]

# Use can() to test if regex matches
can(regex("^t[23]\\.", var.instance_type))  # true/false
```

### `substr`

```hcl
substr("hello world", 0, 5)   # "hello"
substr("hello world", 6, -1)  # "world" (-1 = rest of string)
```

### `startswith` and `endswith`

```hcl
startswith("hello world", "hello")  # true
endswith("myfile.tf", ".tf")        # true
```

---

## Numeric Functions

```hcl
# Absolute value
abs(-42)        # 42

# Ceiling and floor
ceil(4.1)       # 5
floor(4.9)      # 4

# Min and max
min(1, 5, 3)    # 1
max(1, 5, 3)    # 5

# Logarithm
log(100, 10)    # 2 (log base 10 of 100)

# Power
pow(2, 8)       # 256

# Sign
signum(-5)      # -1
signum(0)       # 0
signum(5)       # 1

# Parse a number from a string
parseint("FF", 16)  # 255
parseint("100", 2)  # 4
```

### Real-World Numeric Examples

```hcl
# Calculate number of subnets needed
locals {
  subnet_bits    = ceil(log(var.subnet_count, 2))
  subnets = [
    for i in range(var.subnet_count) :
    cidrsubnet(var.vpc_cidr, local.subnet_bits, i)
  ]
}

# Determine instance count based on environment
locals {
  instance_count = max(var.min_instances, var.environment == "prod" ? 3 : 1)
}
```

---

## Collection Functions

### `length` -- Count Items

```hcl
length(["a", "b", "c"])               # 3
length({ name = "Alice", age = 30 })  # 2
length("hello")                        # 5
```

### `lookup` -- Map Lookup with Default

```hcl
variable "instance_types" {
  default = {
    dev  = "t3.micro"
    prod = "t3.large"
  }
}

# lookup(map, key, default)
lookup(var.instance_types, "dev", "t3.micro")      # "t3.micro"
lookup(var.instance_types, "staging", "t3.small")   # "t3.small" (default)
```

### `merge` -- Merge Maps

```hcl
merge(
  { Name = "web-server" },
  { Environment = "prod" },
  { ManagedBy = "Terraform" }
)
# { Name = "web-server", Environment = "prod", ManagedBy = "Terraform" }

# Later maps override earlier ones
merge(
  { Name = "old-name", Environment = "dev" },
  { Name = "new-name" }
)
# { Name = "new-name", Environment = "dev" }

# Real-world: merge common tags with resource-specific tags
locals {
  common_tags = {
    Project     = var.project
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

resource "aws_instance" "web" {
  tags = merge(local.common_tags, {
    Name = "web-server"
    Role = "frontend"
  })
}
```

### `concat` -- Combine Lists

```hcl
concat(["a", "b"], ["c", "d"])           # ["a", "b", "c", "d"]
concat(var.public_subnets, var.private_subnets)  # Combined subnet list
```

### `flatten` -- Flatten Nested Lists

```hcl
flatten([["a", "b"], ["c"], ["d", "e"]])  # ["a", "b", "c", "d", "e"]

# Real-world: flatten subnet configs
locals {
  all_subnets = flatten([
    for env in ["dev", "prod"] : [
      for az in ["a", "b"] : {
        name = "${env}-${az}"
        env  = env
        az   = az
      }
    ]
  ])
  # Result: [{name="dev-a", ...}, {name="dev-b", ...}, {name="prod-a", ...}, {name="prod-b", ...}]
}
```

### `distinct` -- Remove Duplicates

```hcl
distinct(["a", "b", "a", "c", "b"])  # ["a", "b", "c"]
```

### `contains` -- Check for Element

```hcl
contains(["dev", "staging", "prod"], "prod")   # true
contains(["dev", "staging", "prod"], "test")   # false
```

### `element` -- Index with Wrapping

```hcl
element(["a", "b", "c"], 0)   # "a"
element(["a", "b", "c"], 3)   # "a" (wraps around!)
element(["a", "b", "c"], 4)   # "b"

# Useful for distributing across AZs
element(var.availability_zones, count.index)
```

### `index` -- Find Position

```hcl
index(["a", "b", "c"], "b")  # 1
```

### `slice` -- Subset of a List

```hcl
slice(["a", "b", "c", "d", "e"], 1, 3)  # ["b", "c"]
```

### `range` -- Generate Number Sequences

```hcl
range(3)          # [0, 1, 2]
range(1, 4)       # [1, 2, 3]
range(0, 10, 2)   # [0, 2, 4, 6, 8]
```

### `zipmap` -- Create Map from Two Lists

```hcl
zipmap(
  ["name", "environment", "team"],
  ["web-server", "prod", "devops"]
)
# { name = "web-server", environment = "prod", team = "devops" }

# Real-world: map AZ names to subnet IDs
zipmap(
  data.aws_availability_zones.available.names,
  aws_subnet.public[*].id
)
# { "us-east-1a" = "subnet-abc", "us-east-1b" = "subnet-def" }
```

### `keys` and `values`

```hcl
keys({ name = "web", env = "prod" })    # ["env", "name"] (alphabetical)
values({ name = "web", env = "prod" })  # ["prod", "web"] (matches key order)
```

### `toset`, `tolist`, `tomap`

```hcl
toset(["a", "b", "a", "c"])    # toset(["a", "b", "c"]) -- unique, unordered
tolist(toset(["c", "a", "b"])) # ["a", "b", "c"]
```

---

## Encoding Functions

### `jsonencode` and `jsondecode`

```hcl
# Encode HCL to JSON
jsonencode({
  Version = "2012-10-17"
  Statement = [{
    Effect   = "Allow"
    Action   = ["s3:GetObject"]
    Resource = "arn:aws:s3:::my-bucket/*"
  }]
})
# '{"Statement":[{"Action":["s3:GetObject"],"Effect":"Allow","Resource":"arn:aws:s3:::my-bucket/*"}],"Version":"2012-10-17"}'

# Real-world: IAM policy
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

# Decode JSON to HCL
jsondecode("{\"name\": \"web\", \"port\": 80}")
# { name = "web", port = 80 }
```

### `yamlencode` and `yamldecode`

```hcl
yamlencode({
  apiVersion = "v1"
  kind       = "ConfigMap"
  metadata = {
    name = "my-config"
  }
  data = {
    key1 = "value1"
    key2 = "value2"
  }
})

# Decode YAML
yamldecode(file("${path.module}/config.yaml"))
```

### `base64encode` and `base64decode`

```hcl
base64encode("Hello, World!")   # "SGVsbG8sIFdvcmxkIQ=="
base64decode("SGVsbG8sIFdvcmxkIQ==")  # "Hello, World!"

# Real-world: EC2 user data
resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.micro"
  user_data_base64 = base64encode(templatefile("${path.module}/userdata.sh", {
    environment = var.environment
  }))
}
```

### `csvdecode`

```hcl
# Parse a CSV string
csvdecode("name,port,protocol\nweb,80,tcp\napi,8080,tcp")
# [
#   { name = "web", port = "80", protocol = "tcp" },
#   { name = "api", port = "8080", protocol = "tcp" }
# ]

# Real-world: Load configs from a CSV file
locals {
  servers = csvdecode(file("${path.module}/servers.csv"))
}

resource "aws_instance" "servers" {
  for_each = { for s in local.servers : s.name => s }

  ami           = each.value.ami
  instance_type = each.value.instance_type
  tags = {
    Name = each.key
  }
}
```

---

## Filesystem Functions

### `file` -- Read a File

```hcl
# Read file contents as a string
resource "aws_instance" "web" {
  user_data = file("${path.module}/scripts/setup.sh")
}

resource "aws_iam_role" "app" {
  assume_role_policy = file("${path.module}/policies/assume-role.json")
}
```

### `filebase64` -- Read File as Base64

```hcl
resource "aws_instance" "web" {
  user_data_base64 = filebase64("${path.module}/scripts/setup.sh")
}
```

### `templatefile` -- Render a Template File

```hcl
# templates/userdata.sh.tpl
#!/bin/bash
echo "Deploying to ${environment}"
echo "Server name: ${server_name}"
echo "Port: ${port}"

%{ for pkg in packages ~}
apt-get install -y ${pkg}
%{ endfor ~}
```

```hcl
# main.tf
resource "aws_instance" "web" {
  user_data = templatefile("${path.module}/templates/userdata.sh.tpl", {
    environment = var.environment
    server_name = "web-01"
    port        = 80
    packages    = ["nginx", "curl", "jq"]
  })
}
```

### `fileexists`

```hcl
# Check if a file exists before reading it
locals {
  custom_policy = fileexists("${path.module}/custom-policy.json") ? file("${path.module}/custom-policy.json") : null
}
```

### `fileset` -- Find Files Matching a Pattern

```hcl
# Find all .json policy files
fileset(path.module, "policies/*.json")
# ["policies/s3-read.json", "policies/ec2-admin.json"]

# Upload all HTML files to S3
resource "aws_s3_object" "website" {
  for_each = fileset("${path.module}/website", "**/*.html")

  bucket = aws_s3_bucket.website.id
  key    = each.value
  source = "${path.module}/website/${each.value}"
}
```

### Path References

```hcl
path.module   # Directory of the current module
path.root     # Directory of the root module
path.cwd      # Current working directory
```

---

## Type Conversion Functions

```hcl
# Convert to string
tostring(42)        # "42"
tostring(true)      # "true"

# Convert to number
tonumber("42")      # 42
tonumber("3.14")    # 3.14

# Convert to bool
tobool("true")      # true
tobool("false")     # false

# Convert collections
tolist(toset(["c", "a", "b"]))   # ["a", "b", "c"]
toset(["a", "b", "a"])            # toset(["a", "b"])
tomap({ name = "web" })           # { "name" = "web" }

# Try -- return first successful expression
try(var.custom_value, "default_value")
try(yamldecode(var.config), {})

# Can -- test if an expression is valid
can(regex("^t[23]", var.instance_type))  # true or false (no error)
can(tonumber("abc"))                       # false
```

---

## Conditional Expressions

### Ternary Operator

```hcl
# condition ? true_value : false_value
instance_type = var.environment == "prod" ? "t3.large" : "t3.micro"
```

### Common Patterns

```hcl
# Conditional resource creation
resource "aws_cloudwatch_metric_alarm" "cpu" {
  count = var.enable_monitoring ? 1 : 0
  # ...
}

# Conditional value
locals {
  db_class = var.environment == "prod" ? "db.r5.large" : (
    var.environment == "staging" ? "db.r5.medium" : "db.t3.micro"
  )
}

# Conditional list inclusion
locals {
  security_groups = compact([
    aws_security_group.web.id,
    var.enable_ssh ? aws_security_group.ssh[0].id : "",
  ])
  # compact() removes empty strings
}

# Conditional map merge
tags = merge(
  local.common_tags,
  var.environment == "prod" ? { "Backup" = "daily" } : {},
)
```

### Null Coalescing with `coalesce`

```hcl
# Returns first non-null, non-empty value
coalesce(var.custom_name, var.default_name, "unnamed")

# For lists
coalescelist(var.custom_subnets, var.default_subnets, ["10.0.1.0/24"])
```

---

## For Expressions

`for` expressions transform and filter collections.

### Transform a List

```hcl
# Transform list elements
[for s in ["hello", "world"] : upper(s)]
# ["HELLO", "WORLD"]

# With index
[for i, s in ["hello", "world"] : "${i}: ${s}"]
# ["0: hello", "1: world"]

# Filter
[for s in var.names : upper(s) if length(s) > 3]
```

### Transform a Map

```hcl
# Map values
{ for k, v in var.tags : k => upper(v) }
# { Name = "WEB-SERVER", Env = "PROD" }

# Transform a list into a map
{ for s in var.servers : s.name => s.ip }
# { "web-1" = "10.0.1.5", "web-2" = "10.0.1.6" }
```

### Grouping with `...`

```hcl
variable "users" {
  default = [
    { name = "alice", role = "admin" },
    { name = "bob", role = "developer" },
    { name = "charlie", role = "admin" },
    { name = "diana", role = "developer" },
  ]
}

locals {
  users_by_role = {
    for user in var.users : user.role => user.name...
  }
  # {
  #   admin     = ["alice", "charlie"]
  #   developer = ["bob", "diana"]
  # }
}
```

### Real-World For Expression Examples

```hcl
# Create a map of subnet IDs by AZ
locals {
  subnet_by_az = {
    for subnet in aws_subnet.public :
    subnet.availability_zone => subnet.id
  }
}

# Filter instances that have a public IP
locals {
  public_instances = {
    for k, v in aws_instance.web :
    k => v.public_ip
    if v.public_ip != ""
  }
}

# Generate CIDR blocks for subnets
locals {
  subnet_cidrs = [
    for i in range(var.subnet_count) :
    cidrsubnet(var.vpc_cidr, 8, i)
  ]
  # ["10.0.0.0/24", "10.0.1.0/24", "10.0.2.0/24", ...]
}

# Flatten nested structure for for_each
locals {
  user_roles = flatten([
    for user, roles in var.user_role_assignments : [
      for role in roles : {
        user = user
        role = role
      }
    ]
  ])

  user_role_map = {
    for ur in local.user_roles : "${ur.user}-${ur.role}" => ur
  }
}

resource "aws_iam_user_policy_attachment" "assignments" {
  for_each = local.user_role_map

  user       = each.value.user
  policy_arn = each.value.role
}
```

---

## Splat Expressions

Splat expressions are shorthand for extracting attributes from lists of objects.

### Full Splat (`[*]`)

```hcl
# These are equivalent:
aws_instance.web[*].public_ip
[for instance in aws_instance.web : instance.public_ip]

# Nested splat
aws_instance.web[*].root_block_device[0].volume_id
```

### With Count

```hcl
resource "aws_instance" "web" {
  count         = 3
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.micro"
}

output "all_ips" {
  value = aws_instance.web[*].public_ip
  # ["54.1.2.3", "54.4.5.6", "54.7.8.9"]
}

output "all_ids" {
  value = aws_instance.web[*].id
  # ["i-abc123", "i-def456", "i-ghi789"]
}
```

### With For Each (Use `values()`)

```hcl
resource "aws_instance" "web" {
  for_each      = toset(["web-1", "web-2", "web-3"])
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.micro"
}

# for_each resources are maps, not lists -- use values()
output "all_ips" {
  value = values(aws_instance.web)[*].public_ip
}

# Or use a for expression
output "all_ips_map" {
  value = { for k, v in aws_instance.web : k => v.public_ip }
}
```

---

## Dynamic Blocks

Dynamic blocks generate repeated nested blocks programmatically, replacing the need for copy-pasting similar block configurations.

### Problem: Repeated Blocks

```hcl
# Without dynamic blocks -- lots of repetition
resource "aws_security_group" "web" {
  name   = "web-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]
  }
}
```

### Solution: Dynamic Block

```hcl
variable "ingress_rules" {
  type = list(object({
    port        = number
    protocol    = string
    cidr_blocks = list(string)
    description = string
  }))

  default = [
    { port = 80,   protocol = "tcp", cidr_blocks = ["0.0.0.0/0"],  description = "HTTP" },
    { port = 443,  protocol = "tcp", cidr_blocks = ["0.0.0.0/0"],  description = "HTTPS" },
    { port = 8080, protocol = "tcp", cidr_blocks = ["10.0.0.0/8"], description = "App" },
  ]
}

resource "aws_security_group" "web" {
  name   = "web-sg"
  vpc_id = aws_vpc.main.id

  dynamic "ingress" {
    for_each = var.ingress_rules

    content {
      from_port   = ingress.value.port
      to_port     = ingress.value.port
      protocol    = ingress.value.protocol
      cidr_blocks = ingress.value.cidr_blocks
      description = ingress.value.description
    }
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
```

### Dynamic Block Syntax

```hcl
dynamic "<BLOCK_NAME>" {
  for_each = <COLLECTION>

  # Optional: change the iterator name (default is the block name)
  iterator = <CUSTOM_NAME>

  content {
    # Use <BLOCK_NAME>.value or <CUSTOM_NAME>.value
    <ARGUMENT> = <BLOCK_NAME>.value.<ATTRIBUTE>
  }
}
```

### Nested Dynamic Blocks

```hcl
variable "load_balancer_rules" {
  default = {
    http = {
      port     = 80
      protocol = "HTTP"
      actions = [
        { type = "redirect", redirect_port = "443" }
      ]
    }
    https = {
      port     = 443
      protocol = "HTTPS"
      actions = [
        { type = "forward", target_group = "web-tg" }
      ]
    }
  }
}

resource "aws_lb_listener" "this" {
  for_each = var.load_balancer_rules

  load_balancer_arn = aws_lb.main.arn
  port              = each.value.port
  protocol          = each.value.protocol

  dynamic "default_action" {
    for_each = each.value.actions

    content {
      type = default_action.value.type

      dynamic "redirect" {
        for_each = default_action.value.type == "redirect" ? [1] : []

        content {
          port        = default_action.value.redirect_port
          protocol    = "HTTPS"
          status_code = "HTTP_301"
        }
      }
    }
  }
}
```

### Real-World Dynamic Block: Azure Network Security Group

```hcl
variable "nsg_rules" {
  default = [
    {
      name                       = "allow-http"
      priority                   = 100
      direction                  = "Inbound"
      access                     = "Allow"
      protocol                   = "Tcp"
      source_port_range          = "*"
      destination_port_range     = "80"
      source_address_prefix      = "*"
      destination_address_prefix = "*"
    },
    {
      name                       = "allow-https"
      priority                   = 110
      direction                  = "Inbound"
      access                     = "Allow"
      protocol                   = "Tcp"
      source_port_range          = "*"
      destination_port_range     = "443"
      source_address_prefix      = "*"
      destination_address_prefix = "*"
    }
  ]
}

resource "azurerm_network_security_group" "web" {
  name                = "web-nsg"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  dynamic "security_rule" {
    for_each = var.nsg_rules

    content {
      name                       = security_rule.value.name
      priority                   = security_rule.value.priority
      direction                  = security_rule.value.direction
      access                     = security_rule.value.access
      protocol                   = security_rule.value.protocol
      source_port_range          = security_rule.value.source_port_range
      destination_port_range     = security_rule.value.destination_port_range
      source_address_prefix      = security_rule.value.source_address_prefix
      destination_address_prefix = security_rule.value.destination_address_prefix
    }
  }
}
```

> **Best Practice**: Use dynamic blocks sparingly. Overuse makes code harder to read. If you only have 2-3 blocks, writing them out explicitly is often clearer.

---

## Key Takeaways

1. **Use `terraform console`** to experiment with expressions and functions interactively
2. **String functions** (`format`, `join`, `replace`, `regex`) are essential for naming and templating
3. **Collection functions** (`merge`, `flatten`, `lookup`, `zipmap`) help transform data structures
4. **`jsonencode`** is critical for IAM policies and JSON configuration
5. **`templatefile`** renders templates with variables -- use it for user data scripts and configs
6. **For expressions** are Terraform's map/filter/reduce -- use them to transform collections
7. **Splat expressions** (`[*]`) are shorthand for extracting a single attribute from a list
8. **Dynamic blocks** eliminate repetitive nested block configurations
9. **Conditional expressions** (`? :`) enable environment-specific logic and optional resources
10. **`try()` and `can()`** handle errors gracefully -- use them in validations and fallback logic

---

## What's Next?

In the next lesson, we will explore Terraform workspaces -- how to manage multiple environments with the same configuration.

[Previous Lesson: Terraform Modules](./07-terraform-modules.md) | [Next Lesson: Terraform Workspaces -->](./09-terraform-workspaces.md)
