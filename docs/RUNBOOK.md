# Operations Runbook

## Backup did not run

1. Check whether the EventBridge rule is enabled.
2. Review the latest Lambda execution in CloudWatch Logs.
3. Confirm the Lambda trigger permission exists.
4. Manually invoke Lambda with a test event if needed.

## No snapshots were created

1. Confirm EC2 instances have the correct backup tag, for example `Backup=true`.
2. Confirm instances are in the same AWS region as the Lambda function.
3. Check IAM permissions for `ec2:CreateSnapshot` and `ec2:CreateTags`.
4. Review the S3 backup report for skipped or failed volumes.

## Snapshot cleanup did not happen

1. Confirm snapshots have the `CreatedBy` tag matching this project/environment.
2. Confirm snapshots are completed, not pending.
3. Confirm `RETENTION_DAYS` is configured correctly.

## Emergency rollback

This project creates snapshots only. To recover, create an EBS volume from the snapshot and attach it to the required EC2 instance, or create an AMI/recovery instance based on your organization’s recovery procedure.
