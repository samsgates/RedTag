output "api_url" { value = google_cloud_run_v2_service.api.uri }
output "web_url" { value = google_cloud_run_v2_service.web.uri }
output "worker_url" { value = google_cloud_run_v2_service.worker.uri }
output "evidence_bucket" { value = google_storage_bucket.evidence.name }
output "pubsub_topic" { value = google_pubsub_topic.domain.name }
output "cloud_sql_instance" { value = google_sql_database_instance.postgres.connection_name }
output "database_url_secret" { value = google_secret_manager_secret.database_url.secret_id }
output "migration_job" { value = google_cloud_run_v2_job.migrate.name }

output "artifact_registry_repository" { value = google_artifact_registry_repository.redtag.name }
output "pubsub_subscription" { value = google_pubsub_subscription.domain_worker.name }
output "artifact_registry_uri" { value = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.redtag.repository_id}" }
