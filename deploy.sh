#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="$ROOT_DIR/terraform"

run_tests=true

for arg in "$@"; do
  case "$arg" in
    --skip-tests)
      run_tests=false
      ;;
    -h|--help)
      cat <<'EOF'
Usage: ./deploy.sh [--skip-tests]

Runs the standard deployment flow for api-news:
1. Run API tests
2. Build Cloud Functions source package
3. Run terraform plan
4. Run terraform apply
5. Print deployed function URL

Options:
  --skip-tests    Skip pytest before deploy
  -h, --help      Show this help message
EOF
      exit 0
      ;;
    *)
      echo "Unknown argument: $arg" >&2
      echo "Use --help to see available options." >&2
      exit 1
      ;;
  esac
done

if [[ ! -d "$TERRAFORM_DIR" ]]; then
  echo "Terraform directory not found: $TERRAFORM_DIR" >&2
  exit 1
fi

if [[ ! -f "$TERRAFORM_DIR/terraform.tfvars" ]]; then
  echo "Missing terraform/terraform.tfvars. Create it before deploying." >&2
  exit 1
fi

if ! command -v make >/dev/null 2>&1; then
  echo "make is required to run deploy.sh" >&2
  exit 1
fi

if ! command -v terraform >/dev/null 2>&1; then
  echo "terraform is required to run deploy.sh" >&2
  exit 1
fi

cd "$ROOT_DIR"

if [[ "$run_tests" == true ]]; then
  echo "==> Running tests"
  make test
fi

echo "==> Building Cloud Functions package"
make build-cf

echo "==> Planning Terraform deployment"
make terraform-plan

echo "==> Applying Terraform plan"
make terraform-apply

echo "==> Deployment finished"
echo "Function URL: $(cd "$TERRAFORM_DIR" && terraform output -raw function_uri)"