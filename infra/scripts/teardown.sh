#!/usr/bin/env bash
# Destroys all resources in an environment. Use with caution.
set -euo pipefail

ENV=${1:-staging}
DIR="$(cd "$(dirname "$0")/../terraform/environments/$ENV" && pwd)"

echo "==> WARNING: This will destroy ALL resources in environment: $ENV"
read -r -p "Type the environment name to confirm: " CONFIRM

if [ "$CONFIRM" != "$ENV" ]; then
  echo "Aborted."
  exit 1
fi

cd "$DIR"
terraform destroy
