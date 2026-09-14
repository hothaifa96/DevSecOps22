variable "aws_region" {
  type    = list(string)
  default = ["us-east-1", "eu-west-1"]
}

variable "default_ami" {
  type    = string
  default = "ami-06468be052a4195a6"
}

variable "type" {
  type    = string
  default = "t3.micro"
}

variable "vpc_cidr" {
  type    = string
  default = "10.0.0.0/16" # 10.0.0.0 -> 10.0.255.255
}

variable "public_subnet_cidr" {
  type    = string
  default = "10.0.1.0/24"
}
variable "private_subnet_cidr" {
  type    = string
  default = "10.0.2.0/24"
}

variable "az" {
  type    = string
  default = "eu-west-1a"
}