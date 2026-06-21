environment              = "dev"
retention_days           = 7
log_retention_days       = 30
backup_schedule          = "cron(0 2 * * ? *)"
create_sample_instances  = false
log_bucket_force_destroy = true
dry_run                  = false
enable_notifications     = false
