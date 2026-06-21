# Project Walkthrough: Serverless EC2 Backup Automation

This walkthrough explains the AWS EC2 backup automation project from a practical DevOps perspective.

## Problem

Manual EC2/EBS backups are easy to miss, difficult to audit, and inconsistent across environments. A small team may start with manual snapshots, but that approach does not scale well when more servers and environments are added.

## Solution

This project uses AWS-native serverless services to automate backup operations:

- EventBridge triggers the backup workflow on a schedule.
- Lambda discovers EC2 instances using a backup tag.
- Lambda creates EBS snapshots and adds tracking tags.
- Lambda deletes old snapshots based on retention.
- S3 stores JSON backup reports for audit.
- SNS and CloudWatch alarms provide optional operational visibility.
- Terraform provisions the complete infrastructure.

## Backup Selection

Only instances with this tag are backed up:

```text
Backup=true
```

This makes the solution flexible because teams can onboard or remove servers from backup scope by changing tags instead of editing code.

## Retention Cleanup

Snapshots created by this automation receive tags such as:

```text
CreatedBy=ec2-auto-backup-dev
CreatedOn=2026-01-01
RetentionDays=7
```

The cleanup logic uses these tags to safely delete only snapshots created by this system.

## Operational Reporting

Each run writes a JSON report to S3. The report includes created snapshots, deleted snapshots, failed operations, status, duration, environment, and retention settings.

## GenAI Enhancement

The `scripts/genai_backup_summary.py` helper can convert a raw backup report into a readable operations summary. This is useful for daily backup review, release handoff, or incident follow-up notes.

## Portfolio Value

This project demonstrates practical skills in:

- AWS automation
- Terraform infrastructure as code
- Lambda/Python scripting
- Event-driven operations
- Backup and retention design
- IAM and security-minded configuration
- CI validation with GitHub Actions
- AI-assisted operations reporting
