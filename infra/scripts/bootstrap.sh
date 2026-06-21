#!/usr/bin/env bash
# Run once to provision staging. Pass --env production to target prod.
set -euo pipefail

ENV=${1:-staging}
DIR="$(cd "$(dirname "$0")/../terraform/environments/$ENV" && pwd)"

echo "==> Initializing Terraform for environment: $ENV"
cd "$DIR"
terraform init
terraform plan -out=tfplan
echo ""
echo "==> Review the plan above, then run:"
echo "    terraform apply tfplan"
echo "    (from $DIR)"
