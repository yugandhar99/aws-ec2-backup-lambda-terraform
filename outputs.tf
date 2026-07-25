output "lambda_function_name" {
  description = "Name of the backup Lambda function."
  value       = module.lambda_function.lambda_function_name
}

output "lambda_function_arn" {
  description = "ARN of the backup Lambda function."
  value       = module.lambda_function.lambda_function_arn
}

output "log_bucket_name" {
  description = "S3 bucket storing backup execution reports."
  value       = module.log_bucket.s3_bucket_id
}

output "backup_schedule" {
  description = "EventBridge schedule expression."
  value       = var.backup_schedule
}

output "notification_topic_arn" {
  description = "SNS topic ARN when notifications are enabled."
  value       = var.enable_notifications ? aws_sns_topic.backup_notifications[0].arn : null
}
