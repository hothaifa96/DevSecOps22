#!/bin/bash
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"

REGION=$(terraform -chdir="$DIR" output -raw update_kubeconfig_command | awk '{print $5}')
CLUSTER_NAME=$(terraform -chdir="$DIR" output -raw cluster_name)

aws eks update-kubeconfig --region "$REGION" --name "$CLUSTER_NAME"

kubectl get nodes
