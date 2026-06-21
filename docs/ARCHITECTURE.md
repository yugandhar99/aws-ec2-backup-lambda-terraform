# Architecture

```text
Tagged EC2 instances
        |
        |  Backup=true
        v
EventBridge schedule ---> AWS Lambda ---> EBS Snapshots
                           |      |
                           |      +--> Deletes old automated snapshots
                           |
                           +--> S3 JSON backup reports
                           |
                           +--> Optional SNS email notification
                           |
                           +--> CloudWatch logs and Lambda error alarm
```

## Flow

1. Platform team tags EC2 instances with `Backup=true`.
2. EventBridge invokes the Lambda function on the configured schedule.
3. Lambda discovers matching non-terminated EC2 instances.
4. Lambda creates EBS snapshots for attached EBS volumes.
5. Lambda tags snapshots with `CreatedBy`, `CreatedOn`, `InstanceId`, `VolumeId`, `Environment`, and `RetentionDays`.
6. Lambda deletes completed automated snapshots older than the retention window.
7. A JSON execution report is stored in S3 for audit and troubleshooting.
8. Optional SNS notifications and CloudWatch alarms improve operational visibility.

## Why this design is useful

This design is serverless, low-maintenance, auditable, and easy to extend to multi-account or multi-region backup automation.
