run "validate_default_configuration" {
  command = plan

  assert {
    condition     = local.project_name == var.project_name
    error_message = "Project name local should come from var.project_name."
  }

  assert {
    condition     = var.retention_days >= 1
    error_message = "Retention days must be positive."
  }

  assert {
    condition     = var.create_sample_instances == false
    error_message = "Sample EC2 instances should be disabled by default."
  }
}
