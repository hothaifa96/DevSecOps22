terraform {
  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "2.9.1"
    }
  }
}

provider "local" {}

resource "local_file" "demo_file"{
    filename = "/Users/hothaifa/workspace/DevSecOps-22/terraform/classcode/local-demo/demo.txt"
    content = "let have some pizza !!!!"
    file_permission = "0555"
    directory_permission = "0770"
}

resource "local_sensitive_file" "sensitive" {
    content  = "foo!"
    filename = "/Users/hothaifa/workspace/DevSecOps-22/terraform/classcode/local-demo/foo.ini"
}