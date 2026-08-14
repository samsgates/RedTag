provider "google" {
  project = var.project_id
  region  = var.region
}

locals {
  prefix = "redtag-${var.environment}"
  services = toset([
    "run.googleapis.com",
    "sqladmin.googleapis.com",
    "pubsub.googleapis.com",
    "storage.googleapis.com",
    "secretmanager.googleapis.com",
    "artifactregistry.googleapis.com",
    "aiplatform.googleapis.com",
    "identitytoolkit.googleapis.com",
    "modelarmor.googleapis.com",
    "cloudtrace.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com"
  ])
}

resource "google_project_service" "apis" {
  for_each           = local.services
  service            = each.value
  disable_on_destroy = false
}

resource "random_password" "db" {
  length  = 32
  special = false
}


resource "google_artifact_registry_repository" "redtag" {
  location      = var.region
  repository_id = "${local.prefix}-containers"
  description   = "RedTag production container images"
  format        = "DOCKER"
  depends_on    = [google_project_service.apis]
}

resource "google_service_account" "api" {
  account_id   = "${local.prefix}-api"
  display_name = "RedTag API"
  depends_on   = [google_project_service.apis]
}

resource "google_service_account" "worker" {
  account_id   = "${local.prefix}-worker"
  display_name = "RedTag outbox worker"
  depends_on   = [google_project_service.apis]
}

resource "google_service_account" "web" {
  account_id   = "${local.prefix}-web"
  display_name = "RedTag Web"
  depends_on   = [google_project_service.apis]
}

resource "google_storage_bucket" "evidence" {
  name                        = "${var.project_id}-${local.prefix}-evidence"
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = false
  versioning { enabled = true }
  lifecycle_rule {
    condition { age = 365 }
    action { type = "SetStorageClass" storage_class = "NEARLINE" }
  }
  depends_on = [google_project_service.apis]
}

resource "google_pubsub_topic" "domain" {
  name       = "${local.prefix}-domain-events"
  depends_on = [google_project_service.apis]
}

resource "google_pubsub_subscription" "domain_worker" {
  name                       = "${local.prefix}-domain-worker"
  topic                      = google_pubsub_topic.domain.name
  ack_deadline_seconds       = 60
  message_retention_duration = "604800s"
  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }
}

resource "google_sql_database_instance" "postgres" {
  name                = "${local.prefix}-postgres"
  database_version    = "POSTGRES_17"
  region              = var.region
  deletion_protection = true
  settings {
    tier              = var.database_tier
    availability_type = "REGIONAL"
    disk_type         = "PD_SSD"
    disk_autoresize   = true
    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = true
      transaction_log_retention_days = 7
    }
    insights_config {
      query_insights_enabled  = true
      record_application_tags = true
    }
    ip_configuration {
      ipv4_enabled = true
      require_ssl  = true
    }
  }
  depends_on = [google_project_service.apis]
}

resource "google_sql_database" "redtag" {
  name     = var.database_name
  instance = google_sql_database_instance.postgres.name
}

resource "google_sql_user" "redtag" {
  name     = var.database_user
  instance = google_sql_database_instance.postgres.name
  password = random_password.db.result
}

resource "google_secret_manager_secret" "database_url" {
  secret_id = "${local.prefix}-database-url"
  replication { auto {} }
}

resource "google_secret_manager_secret_version" "database_url" {
  secret = google_secret_manager_secret.database_url.id
  secret_data = "postgresql+psycopg://${var.database_user}:${random_password.db.result}@/${var.database_name}?host=/cloudsql/${google_sql_database_instance.postgres.connection_name}"
}

resource "google_project_iam_member" "api_cloudsql" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.api.email}"
}

resource "google_project_iam_member" "worker_cloudsql" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.worker.email}"
}

resource "google_secret_manager_secret_iam_member" "api_db_secret" {
  secret_id = google_secret_manager_secret.database_url.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.api.email}"
}

resource "google_secret_manager_secret_iam_member" "worker_db_secret" {
  secret_id = google_secret_manager_secret.database_url.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.worker.email}"
}

resource "google_cloud_run_v2_service" "api" {
  name     = "${local.prefix}-api"
  location = var.region
  deletion_protection = true
  template {
    service_account = google_service_account.api.email
    scaling { min_instance_count = 1 max_instance_count = 20 }
    volumes {
      name = "cloudsql"
      cloud_sql_instance { instances = [google_sql_database_instance.postgres.connection_name] }
    }
    containers {
      image = var.api_image
      ports { container_port = 8080 }
      resources { limits = { cpu = "2", memory = "2Gi" } }
      volume_mounts { name = "cloudsql" mount_path = "/cloudsql" }
      env { name = "APP_ENV" value = "production" }
      env { name = "AUTH_MODE" value = "oidc" }
      env { name = "JWT_ISSUER" value = var.jwt_issuer }
      env { name = "JWT_AUDIENCE" value = var.jwt_audience }
      env { name = "JWKS_URL" value = var.jwks_url }
      env { name = "CORS_ALLOW_ORIGINS" value = var.web_origin }
      env { name = "GOOGLE_CLOUD_PROJECT" value = var.project_id }
      env { name = "GOOGLE_CLOUD_LOCATION" value = var.region }
      env { name = "GCS_EVIDENCE_BUCKET" value = google_storage_bucket.evidence.name }
      env { name = "PUBSUB_TOPIC" value = google_pubsub_topic.domain.name }
      env { name = "PUBSUB_ENABLED" value = "true" }
      env { name = "REAL_AI_ENABLED" value = "true" }
      env { name = "MODEL_ARMOR_ENABLED" value = var.model_armor_template != "" ? "true" : "false" }
      env { name = "MODEL_ARMOR_LOCATION" value = var.model_armor_location }
      env { name = "MODEL_ARMOR_TEMPLATE" value = var.model_armor_template }
      env {
        name = "DATABASE_URL"
        value_source { secret_key_ref { secret = google_secret_manager_secret.database_url.secret_id version = "latest" } }
      }
    }
  }
  depends_on = [google_project_service.apis, google_secret_manager_secret_iam_member.api_db_secret]
}

resource "google_cloud_run_v2_service" "worker" {
  name     = "${local.prefix}-worker"
  location = var.region
  deletion_protection = true
  template {
    service_account = google_service_account.worker.email
    scaling { min_instance_count = 1 max_instance_count = 3 }
    volumes {
      name = "cloudsql"
      cloud_sql_instance { instances = [google_sql_database_instance.postgres.connection_name] }
    }
    containers {
      image = var.api_image
      command = ["uvicorn"]
      args = ["app.worker_service:app", "--host", "0.0.0.0", "--port", "8080"]
      ports { container_port = 8080 }
      resources {
        limits   = { cpu = "1", memory = "1Gi" }
        cpu_idle = false
      }
      volume_mounts { name = "cloudsql" mount_path = "/cloudsql" }
      env { name = "APP_ENV" value = "production" }
      env { name = "AUTH_MODE" value = "oidc" }
      env { name = "JWT_ISSUER" value = var.jwt_issuer }
      env { name = "JWT_AUDIENCE" value = var.jwt_audience }
      env { name = "JWKS_URL" value = var.jwks_url }
      env { name = "GOOGLE_CLOUD_PROJECT" value = var.project_id }
      env { name = "PUBSUB_TOPIC" value = google_pubsub_topic.domain.name }
      env { name = "PUBSUB_SUBSCRIPTION" value = google_pubsub_subscription.domain_worker.name }
      env { name = "PUBSUB_ENABLED" value = "true" }
      env {
        name = "DATABASE_URL"
        value_source { secret_key_ref { secret = google_secret_manager_secret.database_url.secret_id version = "latest" } }
      }
    }
  }
  depends_on = [google_project_service.apis, google_secret_manager_secret_iam_member.worker_db_secret]
}

resource "google_cloud_run_v2_service" "web" {
  name     = "${local.prefix}-web"
  location = var.region
  deletion_protection = true
  template {
    service_account = google_service_account.web.email
    scaling { min_instance_count = 0 max_instance_count = 20 }
    containers {
      image = var.web_image
      ports { container_port = 3000 }
      env { name = "REDTAG_API_URL" value = "${google_cloud_run_v2_service.api.uri}/api/v1" }
      env { name = "REDTAG_AUTH_MODE" value = "oidc" }
      env { name = "REDTAG_DEFAULT_TENANT_ID" value = var.default_tenant_id }
    }
  }
  depends_on = [google_project_service.apis]
}

resource "google_cloud_run_v2_service_iam_member" "web_public" {
  count    = var.allow_public_web ? 1 : 0
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.web.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_v2_service_iam_member" "api_public" {
  count    = var.allow_public_api ? 1 : 0
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.api.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_project_iam_member" "api_storage" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.api.email}"
}

resource "google_project_iam_member" "api_pubsub" {
  project = var.project_id
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${google_service_account.api.email}"
}

resource "google_project_iam_member" "worker_pubsub" {
  project = var.project_id
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${google_service_account.worker.email}"
}

resource "google_project_iam_member" "worker_pubsub_subscriber" {
  project = var.project_id
  role    = "roles/pubsub.subscriber"
  member  = "serviceAccount:${google_service_account.worker.email}"
}

resource "google_project_iam_member" "api_vertex" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.api.email}"
}

resource "google_cloud_run_v2_job" "migrate" {
  name     = "${local.prefix}-migrate"
  location = var.region
  template {
    template {
      service_account = google_service_account.api.email
      max_retries     = 1
      timeout         = "900s"
      volumes {
        name = "cloudsql"
        cloud_sql_instance { instances = [google_sql_database_instance.postgres.connection_name] }
      }
      containers {
        image   = var.api_image
        command = ["alembic"]
        args    = ["-c", "services/api/alembic.ini", "upgrade", "head"]
        volume_mounts { name = "cloudsql" mount_path = "/cloudsql" }
        env { name = "APP_ENV" value = "production" }
        env { name = "AUTH_MODE" value = "oidc" }
        env { name = "JWT_ISSUER" value = var.jwt_issuer }
        env { name = "JWT_AUDIENCE" value = var.jwt_audience }
        env { name = "JWKS_URL" value = var.jwks_url }
        env {
          name = "DATABASE_URL"
          value_source { secret_key_ref { secret = google_secret_manager_secret.database_url.secret_id version = "latest" } }
        }
      }
    }
  }
  depends_on = [google_secret_manager_secret_iam_member.api_db_secret, google_project_iam_member.api_cloudsql]
}

resource "google_project_iam_member" "api_model_armor" {
  count   = var.model_armor_template != "" ? 1 : 0
  project = var.project_id
  role    = "roles/modelarmor.user"
  member  = "serviceAccount:${google_service_account.api.email}"
}
