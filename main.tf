variable "project" {}
variable "region" { default = "us-central1" }
provider "google" { project = var.project  region = var.region }

resource "google_project_service" "apis" {
  for_each = toset(["run.googleapis.com","documentai.googleapis.com","aiplatform.googleapis.com",
                    "pubsub.googleapis.com","cloudtasks.googleapis.com","secretmanager.googleapis.com","artifactregistry.googleapis.com"])
  service = each.key
}
resource "google_storage_bucket" "uploads" { name = "${var.project}-contract-uploads" location = var.region uniform_bucket_level_access = true }
resource "google_pubsub_topic" "contract_events" { name = "contract-events" }
resource "google_cloud_tasks_queue" "sla" { name = "dept-sla" location = var.region }
resource "google_service_account" "api" { account_id = "contractflow-api" }
resource "google_project_iam_member" "roles" {
  for_each = toset(["roles/documentai.apiUser","roles/aiplatform.user","roles/pubsub.publisher","roles/storage.objectAdmin"])
  project = var.project  role = each.key  member = "serviceAccount:${google_service_account.api.email}"
}
resource "google_cloud_run_v2_service" "api" {
  name = "contractflow-api" location = var.region
  template {
    service_account = google_service_account.api.email
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project}/contractflow/api:latest"
      env { name = "LOCAL_MODE" value = "false" }
      env { name = "GCP_PROJECT" value = var.project }
    }
    scaling { min_instance_count = 0 }
  }
}
# Cloud SQL (Postgres + pgvector) and Identity Platform omitted from this skeleton; add per README roadmap.
