# Pre-Deployment Checklist

Use this checklist before deploying to production.

## Code Quality

- [ ] All unit tests passing: `make test` (12/12 ✓)
- [ ] No lint/type errors: `cd api && python -m pylint app/` (if configured)
- [ ] All changes committed to git
- [ ] No hardcoded secrets in code
- [ ] `.env.example` updated with all variables

## Configuration

- [ ] `terraform/terraform.tfvars` created and populated
- [ ] GCP Project ID is correct
- [ ] Authentication mode selected and credentials configured
- [ ] Firestore database location appropriate for users
- [ ] Cloud Function memory/timeout settings reviewed
- [ ] Max instance count set appropriately

## Security

- [ ] Service account has minimal required permissions
- [ ] Firestore database has appropriate access rules
- [ ] Never committed secrets to git (check `.gitignore`)
- [ ] JWT secret (if used) is strong (32+ chars)
- [ ] API Key (if used) is strong and rotated regularly
- [ ] `allow_unauthenticated = false` for production
- [ ] Cloud Function ingress restricted if needed

## Google Cloud Setup

- [ ] GCP Project created
- [ ] Billing enabled
- [ ] Required APIs enabled:
  - [ ] Cloud Functions
  - [ ] Cloud Build
  - [ ] Firestore
  - [ ] Cloud Storage
  - [ ] Cloud Run (for Cloud Functions v2)
- [ ] Service account created and permissions set
- [ ] gcloud CLI authenticated: `gcloud auth login`

## Local Validation

- [ ] Local tests pass against emulator
- [ ] Can generate JWT tokens: `cd api && python generate_token.py`
- [ ] Health endpoint responds: `curl http://localhost:8080/health`
- [ ] News endpoint returns data: `curl "http://localhost:8080/news?q=test&date=2024-01-01"`
- [ ] Cache works: repeat queries show `cache_hit: true`

## Deployment

- [ ] Run: `make build-cf`
  - [ ] Verify `terraform/function-source.zip` created
  - [ ] Zip includes `app/`, `main.py`, `requirements.txt`
  - [ ] Zip excludes `.venv/`, `tests/`, `__pycache__/`
- [ ] Run: `make terraform-plan`
  - [ ] Review changes carefully
  - [ ] No errors in plan output
- [ ] Run: `make terraform-apply`
  - [ ] All resources created successfully
  - [ ] Function URI displayed in output
  - [ ] Firestore database provisioned
  - [ ] Service account configured

## Post-Deployment

- [ ] Cloud Function deployed successfully (no errors in logs)
- [ ] Verify deployment: `gcloud functions describe api-news --region us-central1 --gen2`
- [ ] Get function URL: `cd terraform && terraform output function_uri`
- [ ] Test health endpoint via curl (or use included test script)
- [ ] Test news endpoint: `curl "${FUNCTION_URL}/news?q=bitcoin&date=2024-01-15"`
- [ ] Integration tests pass: `python api/tests/test_cloud_function.py ${FUNCTION_URL}`
- [ ] Monitor function in [Cloud Console](https://console.cloud.google.com/functions)

## Performance & Monitoring

- [ ] First cold start latency acceptable (~5-10 seconds)
- [ ] Subsequent invocations fast (<1 second)
- [ ] No unusual error rates
- [ ] Firestore reads/writes as expected
- [ ] Function logs visible and cleanup enabled

## Rollback Plan

- [ ] Know how to revert: `cd terraform && terraform destroy`
- [ ] Backup important data before destroy
- [ ] Document any manual fixes applied
- [ ] Firestore has `prevent_destroy = true` - requires manual deletion

## Documentation

- [ ] README.md updated with function URL
- [ ] DEPLOYMENT.md reflects actual setup
- [ ] Team members informed of new endpoint
- [ ] API documentation shared
- [ ] On-call runbook prepared

## Cost Monitoring

- [ ] Set up billing alert: [GCP Billing](https://console.cloud.google.com/billing)
- [ ] Review estimated costs vs budget
- [ ] Monitor actual usage after deployment
- [ ] Set up regular cost reports

## Signoff

- [ ] Code reviewer: _________________ Date: _______
- [ ] Ops/DevOps: _________________ Date: _______
- [ ] Product/PM: _________________ Date: _______

---

## Emergency Contacts

- GCP Support: https://cloud.google.com/support
- Terraform Issues: https://github.com/hashicorp/terraform-provider-google
- GDELT Status: https://www.gdeltproject.org/

## Rollback Instructions

If deployment fails or unexpected issues occur:

```bash
# Immediate rollback
cd terraform
terraform destroy -auto-approve

# This will delete:
# - Cloud Function
# - Storage bucket
# - Service account
# - IAM roles

# Firestore must be deleted manually if needed
```

## Troubleshooting

### Function fails to deploy
```bash
# Check error
cd terraform
terraform apply

# View Cloud Build logs
gcloud builds log --region=us-central1
```

### Authentication failures
```bash
# Test JWT generation
cd api
python generate_token.py

# The output token can be used for testing
```

### No cache hits
```bash
# Verify Firestore is working
gcloud firestore collections list --project hyper-trader-492500

# Check cache collection
gcloud firestore documents list api_news --project hyper-trader-492500
```

### High costs
- Reduce `max_instance_count` in terraform.tfvars
- Implement more aggressive rate limiting
- Cache more aggressively for frequently queried data
