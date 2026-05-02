output "function_uri" {
  description = "Public URI for the function"
  value       = google_cloudfunctions2_function.api_news_function.service_config[0].uri
}

output "source_bucket" {
  description = "Bucket used to store zipped source"
  value       = google_storage_bucket.api_source_bucket.name
}

output "runtime_service_account" {
  description = "Service account used by the Cloud Function runtime"
  value       = google_service_account.api_news_runtime.email
}
