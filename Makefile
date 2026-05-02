PYTHON ?= python3
API_DIR ?= api
VENV_DIR ?= $(API_DIR)/.venv

PROJECT_ID ?= ht-dev
FIRESTORE_EMULATOR_HOST ?= 127.0.0.1:8088

.PHONY: help venv install dev test firestore-emulator build-cf terraform-plan terraform-apply

help:
	@echo "Targets:"
	@echo "  make dev                - Run API locally with Firestore emulator env vars"
	@echo "  make install            - Create venv and install API dependencies"
	@echo "  make test               - Run API tests"
	@echo "  make firestore-emulator - Start local Firestore emulator"
	@echo "  make build-cf           - Build Cloud Functions source package"
	@echo "  make terraform-plan     - Run terraform plan for deployment"
	@echo "  make terraform-apply    - Deploy to Google Cloud via Terraform"

venv:
	$(PYTHON) -m venv $(VENV_DIR)

install: venv
	cd $(API_DIR) && .venv/bin/pip install -r requirements.txt

dev: install
	cd $(API_DIR) && GOOGLE_CLOUD_PROJECT=$(PROJECT_ID) FIRESTORE_EMULATOR_HOST=$(FIRESTORE_EMULATOR_HOST) .venv/bin/uvicorn app.api:app --reload --port 8080

test: install
	cd $(API_DIR) && .venv/bin/python -m pytest -q

firestore-emulator:
	gcloud emulators firestore start --host-port=$(FIRESTORE_EMULATOR_HOST)

build-cf:
	cd $(API_DIR) && zip -r ../terraform/function-source.zip . \
		--exclude ".venv/*" ".pytest_cache/*" "tests/*" "*.egg-info/*" "__pycache__/*" ".git/*"
	@echo "✓ Cloud Functions source package created: terraform/function-source.zip"

terraform-plan:
	cd terraform && terraform plan -out=tfplan

terraform-apply:
	cd terraform && terraform apply tfplan
	@echo "✓ Deployment complete. Use terraform output to get function URL."
