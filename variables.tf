variable "project_name" {
  description = "Project name used for AWS resource names and tags."
  type        = string
  default     = "ec2-auto-backup"

  validation {
    condition     = can(regex("^[a-z0-9-]{3,32}$", var.project_name))
    error_message = "project_name must be 3-32 characters and contain only lowercase letters, numbers, and hyphens."
  }
}

variable "environment" {
  description = "Environment name."
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "test", "stage", "prod"], var.environment)
    error_message = "environment must be one of dev, test, stage, or prod."
  }
}

variable "aws_region" {
  description = "AWS region."
  type        = string
  default     = "us-west-2"
}

variable "backup_schedule" {
  description = "EventBridge cron/rate expression for backup execution."
  type        = string
  default     = "cron(0 2 * * ? *)"
}

variable "backup_schedule_enabled" {
  description = "Enable or disable the EventBridge backup schedule."
  type        = bool
  default     = true
}

variable "retention_days" {
  description = "Number of days to retain automated snapshots."
  type        = number
  default     = 7

  validation {
    condition     = var.retention_days >= 1 && var.retention_days <= 365
    error_message = "retention_days must be between 1 and 365."
  }
}

variable "log_retention_days" {
  description = "Number of days to retain backup reports in S3."
  type        = number
  default     = 90
}

variable "backup_tag_key" {
  description = "EC2 tag key used to select instances for backup."
  type        = string
  default     = "Backup"
}

variable "backup_tag_value" {
  description = "EC2 tag value used to select instances for backup."
  type        = string
  default     = "true"
}

variable "lambda_timeout" {
  description = "Lambda timeout in seconds."
  type        = number
  default     = 300
}

variable "lambda_memory_size" {
  description = "Lambda memory size in MB."
  type        = number
  default     = 256
}

variable "enable_notifications" {
  description = "Create SNS topic and send backup/alarm notifications."
  type        = bool
  default     = false
}

variable "notification_email" {
  description = "Optional email endpoint for SNS notifications. Requires enable_notifications=true."
  type        = string
  default     = ""
}

variable "create_sample_instances" {
  description = "Create sample EC2 instances for demo/testing. Keep false for real environments."
  type        = bool
  default     = false
}

variable "sample_instance_type" {
  description = "Instance type for optional demo EC2 instances."
  type        = string
  default     = "t3.micro"
}

variable "log_bucket_force_destroy" {
  description = "Allow Terraform destroy to remove the S3 report bucket even when it contains objects. Use carefully."
  type        = bool
  default     = false
}

variable "dry_run" {
  description = "When true, Lambda reports intended backup/delete actions without creating or deleting snapshots."
  type        = bool
  default     = false
}
