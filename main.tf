### Optional demo EC2 instances ###
# This block is disabled by default to avoid creating compute resources by accident.
# Enable create_sample_instances=true only when you want to test the backup workflow.

data "aws_vpc" "default" {
  count   = var.create_sample_instances ? 1 : 0
  default = true
}

data "aws_subnets" "default" {
  count = var.create_sample_instances ? 1 : 0

  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default[0].id]
  }
}

resource "random_id" "bucket_suffix" {
  byte_length = 4
}

module "ec2_instance" {
  source  = "terraform-aws-modules/ec2-instance/aws"
  version = "~> 6.0"

  for_each = var.create_sample_instances ? {
    "backup-01" = var.backup_tag_value
    "backup-02" = var.backup_tag_value
    "no-backup" = "false"
  } : {}

  name          = "${local.project_name}-${var.environment}-${each.key}"
  instance_type = var.sample_instance_type
  subnet_id     = data.aws_subnets.default[0].ids[0]
  monitoring    = true

  tags = {
    (var.backup_tag_key) = each.value
    Purpose              = "backup-demo"
  }
}

### Log bucket ###
# S3 bucket for storing backup execution reports.
module "log_bucket" {
  source  = "terraform-aws-modules/s3-bucket/aws"
  version = "5.5.0"

  bucket        = lower("${local.project_name}-${var.environment}-${random_id.bucket_suffix.hex}-logs")
  force_destroy = var.log_bucket_force_destroy

  versioning = {
    enabled = true
  }

  server_side_encryption_configuration = {
    rule = {
      apply_server_side_encryption_by_default = {
        sse_algorithm = "AES256"
      }
    }
  }

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true

  lifecycle_rule = [
    {
      id      = "expire-backup-reports"
      enabled = true
      expiration = {
        days = var.log_retention_days
      }
      noncurrent_version_expiration = {
        noncurrent_days = 30
      }
    }
  ]
}

### Optional SNS notification ###
resource "aws_sns_topic" "backup_notifications" {
  count = var.enable_notifications ? 1 : 0
  name  = "${local.project_name}-${var.environment}-backup-notifications"

  tags = {
    Purpose = "ec2-backup-notifications"
  }
}

resource "aws_sns_topic_subscription" "backup_email" {
  count     = var.enable_notifications && var.notification_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.backup_notifications[0].arn
  protocol  = "email"
  endpoint  = var.notification_email
}

### Lambda ###
module "lambda_function" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "8.1.0"

  function_name = "${local.project_name}-backup-${var.environment}"
  source_path   = "${path.module}/lambda/lambda_function.py"
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.12"
  timeout       = var.lambda_timeout
  memory_size   = var.lambda_memory_size

  attach_policy_json = true
  policy_json = templatefile("${path.module}/templates/lambda_policy.json.tftpl", {
    log_bucket_arn = module.log_bucket.s3_bucket_arn
    sns_topic_arn  = var.enable_notifications ? aws_sns_topic.backup_notifications[0].arn : ""
  })

  allowed_triggers = {
    eventbridge = {
      service    = "events"
      source_arn = aws_cloudwatch_event_rule.ec2_backup_schedule.arn
    }
  }

  create_current_version_allowed_triggers = false
  artifacts_dir                           = "${path.root}/.terraform/lambda-builds/"

  environment_variables = {
    ENVIRONMENT      = var.environment
    LOG_BUCKET       = module.log_bucket.s3_bucket_id
    RETENTION_DAYS   = tostring(var.retention_days)
    BACKUP_TAG_KEY   = var.backup_tag_key
    BACKUP_TAG_VALUE = var.backup_tag_value
    CREATED_BY_TAG   = local.created_by_tag
    SNS_TOPIC_ARN    = var.enable_notifications ? aws_sns_topic.backup_notifications[0].arn : ""
    DRY_RUN          = tostring(var.dry_run)
  }
}

### EventBridge ###
resource "aws_cloudwatch_event_rule" "ec2_backup_schedule" {
  name                = "${local.project_name}-${var.environment}-backup-schedule"
  description         = "Scheduled EC2 EBS snapshot backup"
  schedule_expression = var.backup_schedule
  state               = var.backup_schedule_enabled ? "ENABLED" : "DISABLED"
}

resource "aws_cloudwatch_event_target" "ec2_backup_lambda" {
  rule      = aws_cloudwatch_event_rule.ec2_backup_schedule.name
  target_id = "ec2-backup-lambda"
  arn       = module.lambda_function.lambda_function_arn
}

### CloudWatch alarm for Lambda errors ###
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "${local.project_name}-${var.environment}-lambda-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Triggers when the EC2 backup Lambda reports errors."
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = module.lambda_function.lambda_function_name
  }

  alarm_actions = var.enable_notifications ? [aws_sns_topic.backup_notifications[0].arn] : []
}
