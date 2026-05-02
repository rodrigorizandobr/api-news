variable "project_id" {
  description = "Google Cloud project id"
  type        = string
}

variable "manage_project_services" {
  description = "Whether Terraform should enable required Google APIs for the project"
  type        = bool
  default     = true
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "function_name" {
  description = "Cloud Function name"
  type        = string
  default     = "api-news"
}

variable "source_bucket_name" {
  description = "Optional bucket name for source code"
  type        = string
  default     = null
}

variable "create_firestore_database" {
  description = "Create the default Firestore database if it does not exist yet"
  type        = bool
  default     = true
}

variable "firestore_location" {
  description = "Firestore database location for the default database"
  type        = string
  default     = "nam5"
}

variable "firestore_cache_collection" {
  description = "Firestore collection used for persistent cache entries"
  type        = string
  default     = "api_news"
}

variable "bucket_prefix" {
  description = "Prefix for source bucket when source_bucket_name is null"
  type        = string
  default     = "api-news-src"
}

variable "public_invoker" {
  description = "Whether to allow public (unauthenticated) invocation of the function"
  type        = bool
  default     = false
}

# Authentication Configuration
variable "auth_jwt_secret" {
  description = "JWT secret for bearer token authentication (minimum 32 characters)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "auth_jwt_expiry_hours" {
  description = "JWT token expiry in hours"
  type        = number
  default     = 24
}

variable "allow_unauthenticated" {
  description = "Allow public HTTP access"
  type        = bool
  default     = true
}

variable "max_instance_count" {
  description = "Maximum function instances"
  type        = number
  default     = 1
}

variable "gnews_api_key" {
  description = "GNews API key for news search"
  type        = string
  default     = ""
  sensitive   = true
}

variable "bigquery_max_bytes_billed" {
  description = "Hard cap for bytes billed per BigQuery query job"
  type        = number
  default     = 175921860444
}

variable "enable_project_budget_guardrail" {
  description = "Create a monthly Cloud Billing budget guardrail for the project"
  type        = bool
  default     = true
}

variable "billing_account_id" {
  description = "Billing account id in format XXXXXX-XXXXXX-XXXXXX"
  type        = string
  default     = ""
}

variable "project_monthly_budget_usd" {
  description = "Monthly budget limit in USD"
  type        = number
  default     = 1
}

variable "project_budget_currency" {
  description = "Budget currency code supported by the linked billing account"
  type        = string
  default     = "BRL"
}
