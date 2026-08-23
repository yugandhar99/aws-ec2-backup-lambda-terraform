locals {
  project_name   = var.project_name
  created_by_tag = "${var.project_name}-${var.environment}"
}
