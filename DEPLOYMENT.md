# Deployment Guide - api-news

## Prerequisites

- Google Cloud Project (set up at https://console.cloud.google.com)
- `gcloud` CLI installed and authenticated
- `terraform` >= 1.5.0
- Python 3.12+
- `make` installed

## Local Development

### 1. Setup Virtual Environment

```bash
make install
```

### 2. Run Tests

```bash
make test
```

All 12 tests should pass. Expected output:
- `test_health_returns_ok` ✓
- `test_news_rejects_empty_keywords` ✓
- `test_news_query_params_are_forwarded` ✓
- `test_date_query_param_is_forwarded` ✓
- `test_date_and_range_are_mutually_exclusive` ✓
- `test_date_filter_is_required` ✓
- `test_cache_works` ✓
- `test_historical_date_uses_cache_on_second_call` ✓
- `test_current_date_does_not_cache` ✓
- `test_stale_cache_fallback_on_upstream_error` ✓
- `test_empty_payload_when_upstream_fails_without_stale` ✓
- `test_cache_write_failure_does_not_fail_response` ✓

### 3. Run Locally Against Emulator

```bash
# Terminal 1: Start Firestore emulator
make firestore-emulator

# Terminal 2: Run API
make dev
```

API will be available at `http://localhost:8080`

Test endpoint:
```bash
curl -X GET "http://localhost:8080/news?q=bitcoin&date=2024-01-01" \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>"
```

## Cloud Deployment

### 1. Prepare Configuration

Copy and update `terraform/terraform.tfvars.example`:

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars`:
- Set `project_id` to your GCP project
- Configure `auth_jwt_secret` (minimum 32 chars)
- Set `auth_jwt_expiry_hours` as needed
- Set `allow_unauthenticated = true` for public access (or false for authenticated)

Optional environment-specific local files (ignored by git):

```bash
cp environments/dev.tfvars.example environments/dev.tfvars.local
cp environments/prd.tfvars.example environments/prd.tfvars.local
```

If using environment file, run Terraform with `-var-file`:

```bash
terraform plan -var-file=environments/dev.tfvars.local -out=tfplan
terraform apply tfplan
```

### 2. Build Cloud Functions Package

```bash
make build-cf
```

This creates `terraform/function-source.zip` with:
- `app/` directory (FastAPI code)
- `requirements.txt` (production dependencies)
- `main.py` (Cloud Functions entry point)

Excludes:
- `.venv/` directories
- `tests/` and test dependencies
- `__pycache__/` and other build artifacts

### 3. Plan Deployment

```bash
make terraform-plan
```

Review the output to understand what will be created:
- Cloud Function (`api-news`)
- Firestore database (if not exists)
- Service account and IAM roles
- Storage bucket for source code
- Cloud Run integration

### 4. Deploy to Google Cloud

```bash
make terraform-apply
```

This will:
1. Create/update all GCP resources
2. Deploy Cloud Function
3. Output function URL and details

### 5. Get Function URL

After successful deployment:

```bash
cd terraform
terraform output function_uri
```

### 6. Test Deployed Function

```bash
FUNCTION_URL=$(cd terraform && terraform output -raw function_uri)

curl -X GET "${FUNCTION_URL}/news?q=bitcoin&date=2024-01-01" \
  -H "Authorization: Bearer <YOUR_AUTH_TOKEN>"
```

## API Endpoints

### GET /news

Query the provider through the stable API contract with date filters.

**Parameters:**
- `q` (required): Comma-separated keywords
- `date` (required): Specific date in YYYY-MM-DD format

**Constraints:**
- `date` is mandatory
- The API converts `date` into the full UTC day window (`00:00:00Z` to `23:59:59Z`)

**Examples:**

```bash
# Specific date
curl "${FUNCTION_URL}/news?q=bitcoin&date=2024-01-01"

# Multi-keyword query
curl "${FUNCTION_URL}/news?q=crypto,market&date=2024-01-15"
```

### GET /health

Health check endpoint.

```bash
curl "${FUNCTION_URL}/health"
# {"status":"ok"}
```

## Cache Strategy

- **Historical data** (before today): Permanently cached in Firestore
- **Current/future data**: Not cached (always fresh)
- **Cache hits**: Returned with `"cache_hit": true`
- **Stale fallback**: If upstream unavailable, returns cached data if available

## Authentication

Configure in `terraform.tfvars`:

```hcl
auth_jwt_secret       = "your-min-32-character-secret-key"
auth_jwt_expiry_hours = 24
```

Generate token:

```bash
python api/generate_token.py --secret "your-min-32-character-secret-key" --expiry-hours 24
```

Use:

```bash
curl -H "Authorization: Bearer <token>" "/news?q=bitcoin&date=2026-04-09&language=en&country=US"
```

## Troubleshooting

### Cloud Function fails to deploy

Check Terraform output for details:
```bash
cd terraform
terraform show
```

### Function returns 401/403

Verify authentication configuration and credentials:
```bash
# Check deployed configuration
gcloud functions describe api-news --region us-central1
```

### Cache is not working

Check Firestore connection:
```bash
# Enable Firestore emulator locally
FIRESTORE_EMULATOR_HOST=127.0.0.1:8088 make dev
```

### High costs?

Monitor Cloud Function usage:
```bash
# Check function metrics
gcloud functions describe api-news --region us-central1 --gen2
```

Adjust `max_instance_count` in `terraform.tfvars` to control scaling.

## Cleanup

To destroy all GCP resources:

```bash
cd terraform
terraform destroy
```

This will delete:
- Cloud Function
- Firestore database
- Storage buckets
- Service accounts
- All related resources

**⚠️ Warning:** Firestore has `prevent_destroy = true` - you may need to manually delete the database in the GCP console.

## Cost Estimation

Typical monthly costs (April 2026):

- **Cloud Function**: $0.40/million invocations → ~$4/month (100K calls)
- **Firestore**: Read/write ops → ~$0.06/100K ops → $5-10/month
- **Storage**: ~$0.02/month for source code bucket
- **Egress**: ~$0.12/GB → varies

**Total**: $10-20/month for moderate usage

## Support & Documentation

- [Google Cloud Functions Documentation](https://cloud.google.com/functions/docs)
- [Firestore Documentation](https://cloud.google.com/firestore/docs)
- [Terraform Google Provider](https://registry.terraform.io/providers/hashicorp/google/latest)
- [GDELT Project](https://www.gdeltproject.org/)
