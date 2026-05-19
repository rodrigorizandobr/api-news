terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.25"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.5"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

data "google_project" "current" {
  project_id = var.project_id
}

resource "google_project_service" "required_apis" {
  for_each = var.manage_project_services ? toset([
    "cloudfunctions.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
    "firebase.googleapis.com",
    "firestore.googleapis.com",
    "run.googleapis.com",
    "eventarc.googleapis.com",
    "storage.googleapis.com",
    "billingbudgets.googleapis.com",
  ]) : toset([])

  project = var.project_id
  service = each.value
}

resource "random_id" "source_bucket_suffix" {
  byte_length = 4
}

locals {
  api_source_bucket_name = coalesce(var.source_bucket_name, "${var.bucket_prefix}-${random_id.source_bucket_suffix.hex}")
}

resource "google_storage_bucket" "api_source_bucket" {
  name                        = local.api_source_bucket_name
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = true
}

data "archive_file" "api_source_archive" {
  type        = "zip"
  source_dir  = "${path.module}/../api"
  output_path = "${path.module}/function-source.zip"
}

resource "google_storage_bucket_object" "api_source_object" {
  name   = "function-source-${data.archive_file.api_source_archive.output_sha}.zip"
  bucket = google_storage_bucket.api_source_bucket.name
  source = data.archive_file.api_source_archive.output_path
}

resource "google_firestore_database" "api_news_cache_database" {
  count = var.create_firestore_database ? 1 : 0

  project                     = var.project_id
  name                        = "(default)"
  location_id                 = var.firestore_location
  type                        = "FIRESTORE_NATIVE"
  concurrency_mode            = "OPTIMISTIC"
  app_engine_integration_mode = "DISABLED"

  lifecycle {
    prevent_destroy = true
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_service_account" "api_news_runtime" {
  account_id   = "api-news-runtime"
  display_name = "api-news runtime"
}

resource "google_project_iam_member" "api_news_firestore_user" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.api_news_runtime.email}"
}

resource "google_project_iam_member" "api_news_bigquery_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.api_news_runtime.email}"
}

resource "google_project_iam_member" "api_news_bigquery_data_viewer" {
  project = var.project_id
  role    = "roles/bigquery.dataViewer"
  member  = "serviceAccount:${google_service_account.api_news_runtime.email}"
}

resource "google_project_iam_member" "api_news_bigquery_resource_viewer" {
  project = var.project_id
  role    = "roles/bigquery.resourceViewer"
  member  = "serviceAccount:${google_service_account.api_news_runtime.email}"
}

resource "google_cloudfunctions2_function" "api_news_function" {
  name        = var.function_name
  location    = var.region
  description = "FastAPI GNews search with Firestore cache"

  build_config {
    runtime     = "python312"
    entry_point = "handler"

    source {
      storage_source {
        bucket = google_storage_bucket.api_source_bucket.name
        object = google_storage_bucket_object.api_source_object.name
      }
    }
  }

  service_config {
    max_instance_count               = var.max_instance_count
    min_instance_count               = 0
    available_memory                 = "256M"
    timeout_seconds                  = 60
    max_instance_request_concurrency = 1
    ingress_settings                 = "ALLOW_ALL"
    all_traffic_on_latest_revision   = true
    service_account_email            = google_service_account.api_news_runtime.email

    environment_variables = merge(
      {
        FIRESTORE_CACHE_COLLECTION = var.firestore_cache_collection
        AUTH_JWT_EXPIRY_HOURS      = tostring(var.auth_jwt_expiry_hours)
        BIGQUERY_MAX_BYTES_BILLED  = tostring(var.bigquery_max_bytes_billed)
        BIGQUERY_SOURCE_PROJECT    = "gdelt-bq"
        BIGQUERY_DATASET           = "gdeltv2"
        BIGQUERY_TABLE             = "gkg_partitioned"
        BIGQUERY_LOCATION          = "US"
      },
      var.gnews_api_key != "" ? {
        GNEWS_API_KEY = var.gnews_api_key
      } : {},
      var.auth_jwt_secret != "" ? {
        AUTH_JWT_SECRET = var.auth_jwt_secret
      } : {},
    )
  }

  depends_on = [
    google_project_service.required_apis,
    google_project_iam_member.api_news_firestore_user,
    google_project_iam_member.api_news_bigquery_job_user,
    google_project_iam_member.api_news_bigquery_data_viewer,
    google_project_iam_member.api_news_bigquery_resource_viewer,
    google_firestore_database.api_news_cache_database,
  ]
}

resource "google_billing_budget" "project_monthly_guardrail" {
  count = var.enable_project_budget_guardrail ? 1 : 0

  billing_account = var.billing_account_id
  display_name    = "api-news-monthly-guardrail-usd-${var.project_monthly_budget_usd}"

  budget_filter {
    projects = ["projects/${data.google_project.current.number}"]
  }

  amount {
    specified_amount {
      currency_code = var.project_budget_currency
      units         = tostring(var.project_monthly_budget_usd)
    }
  }

  threshold_rules {
    threshold_percent = 0.5
  }

  threshold_rules {
    threshold_percent = 0.9
  }

  threshold_rules {
    threshold_percent = 1.0
  }

  lifecycle {
    precondition {
      condition     = length(trimspace(var.billing_account_id)) > 0
      error_message = "billing_account_id must be set when enable_project_budget_guardrail is true."
    }
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_cloud_run_service_iam_member" "api_news_public_invoker" {
  count = var.allow_unauthenticated ? 1 : 0

  location = google_cloudfunctions2_function.api_news_function.location
  service  = google_cloudfunctions2_function.api_news_function.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
