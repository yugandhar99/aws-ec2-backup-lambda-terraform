"""
AWS Lambda function for automated EC2 EBS snapshot backups.

The function discovers EC2 instances by tag, creates snapshots for attached EBS
volumes, stores an execution report in S3, and deletes old snapshots based on a
retention period. Optional SNS notification support is included for operational
visibility.
"""

from __future__ import annotations

import datetime as dt
import json
import os
from typing import Any, Dict, Iterable, List, Optional, Tuple

import boto3
from botocore.exceptions import ClientError


def _env_int(name: str, default: int) -> int:
    value = os.environ.get(name, str(default)).strip()
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"Environment variable {name} must be an integer") from exc
    if parsed < 1:
        raise ValueError(f"Environment variable {name} must be greater than zero")
    return parsed


REGION = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")
RETENTION_DAYS = _env_int("RETENTION_DAYS", 7)
LOG_BUCKET = os.environ.get("LOG_BUCKET", "")
BACKUP_TAG_KEY = os.environ.get("BACKUP_TAG_KEY", "Backup")
BACKUP_TAG_VALUE = os.environ.get("BACKUP_TAG_VALUE", "true")
CREATED_BY_TAG = os.environ.get("CREATED_BY_TAG", "automated-ec2-backup")
ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")
SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN", "")
DRY_RUN = os.environ.get("DRY_RUN", "false").lower() == "true"


def _client(service: str):
    if REGION:
        return boto3.client(service, region_name=REGION)
    return boto3.client(service)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Create snapshots, clean old snapshots, write report, and optionally notify."""
    ec2 = _client("ec2")
    s3 = _client("s3")
    sns = _client("sns") if SNS_TOPIC_ARN else None

    started_at = dt.datetime.now(dt.timezone.utc)
    report: Dict[str, Any] = {
        "status": "started",
        "environment": ENVIRONMENT,
        "started_at": started_at.isoformat(),
        "backup_tag": {"key": BACKUP_TAG_KEY, "value": BACKUP_TAG_VALUE},
        "retention_days": RETENTION_DAYS,
        "dry_run": DRY_RUN,
        "snapshots_created": [],
        "snapshots_deleted": [],
        "errors": [],
    }

    try:
        report["snapshots_created"] = create_backups(ec2)
        report["snapshots_deleted"] = cleanup_old_snapshots(ec2)

        backup_failures = [item for item in report["snapshots_created"] if item.get("snapshot_id") == "failed"]
        cleanup_failures = [item for item in report["snapshots_deleted"] if item.get("status") == "failed"]
        if backup_failures or cleanup_failures:
            report["errors"].extend(backup_failures + cleanup_failures)

        report["status"] = "success" if not report["errors"] else "completed_with_errors"
    except Exception as exc:  # Keep the Lambda failed for alerting, but persist report first.
        report["status"] = "failed"
        report["errors"].append(str(exc))
        raise
    finally:
        finished_at = dt.datetime.now(dt.timezone.utc)
        report["finished_at"] = finished_at.isoformat()
        report["duration_seconds"] = round((finished_at - started_at).total_seconds(), 2)
        save_report_to_s3(s3, report)
        publish_notification(sns, report)

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": "EC2 backup workflow completed",
                "created": len(report["snapshots_created"]),
                "deleted": len(report["snapshots_deleted"]),
                "status": report["status"],
            }
        ),
    }


def create_backups(ec2) -> List[Dict[str, str]]:
    """Find tagged EC2 instances and create snapshots for attached EBS volumes."""
    created: List[Dict[str, str]] = []
    instances = list(find_backup_instances(ec2))

    for instance in instances:
        instance_id = instance["InstanceId"]
        instance_name = get_tag_value(instance.get("Tags", []), "Name", instance_id)

        for mapping in instance.get("BlockDeviceMappings", []):
            ebs = mapping.get("Ebs")
            if not ebs:
                continue

            volume_id = ebs["VolumeId"]
            created_on = dt.date.today().isoformat()
            tags = [
                {"Key": "Name", "Value": f"backup-{instance_name}-{volume_id}-{created_on}"[:255]},
                {"Key": "InstanceId", "Value": instance_id},
                {"Key": "InstanceName", "Value": instance_name},
                {"Key": "VolumeId", "Value": volume_id},
                {"Key": "CreatedBy", "Value": CREATED_BY_TAG},
                {"Key": "CreatedOn", "Value": created_on},
                {"Key": "Environment", "Value": ENVIRONMENT},
                {"Key": "RetentionDays", "Value": str(RETENTION_DAYS)},
            ]

            if DRY_RUN:
                created.append({"instance_id": instance_id, "volume_id": volume_id, "snapshot_id": "dry-run"})
                continue

            try:
                response = ec2.create_snapshot(
                    VolumeId=volume_id,
                    Description=f"Automated backup of {instance_id} volume {volume_id}",
                    TagSpecifications=[{"ResourceType": "snapshot", "Tags": tags}],
                )
                created.append(
                    {
                        "instance_id": instance_id,
                        "instance_name": instance_name,
                        "volume_id": volume_id,
                        "snapshot_id": response["SnapshotId"],
                    }
                )
            except ClientError as exc:
                # Continue backing up other volumes and include failure in the report.
                created.append(
                    {
                        "instance_id": instance_id,
                        "volume_id": volume_id,
                        "snapshot_id": "failed",
                        "error": str(exc),
                    }
                )

    return created


def find_backup_instances(ec2) -> Iterable[Dict[str, Any]]:
    """Return non-terminated instances where the configured backup tag matches."""
    paginator = ec2.get_paginator("describe_instances")
    pages = paginator.paginate(
        Filters=[
            {"Name": f"tag:{BACKUP_TAG_KEY}", "Values": [BACKUP_TAG_VALUE]},
            {"Name": "instance-state-name", "Values": ["pending", "running", "stopping", "stopped"]},
        ]
    )
    for page in pages:
        for reservation in page.get("Reservations", []):
            yield from reservation.get("Instances", [])


def cleanup_old_snapshots(ec2) -> List[Dict[str, str]]:
    """Delete completed snapshots created by this automation and older than retention."""
    deleted: List[Dict[str, str]] = []
    cutoff_date = dt.date.today() - dt.timedelta(days=RETENTION_DAYS)

    paginator = ec2.get_paginator("describe_snapshots")
    pages = paginator.paginate(
        OwnerIds=["self"],
        Filters=[
            {"Name": "tag:CreatedBy", "Values": [CREATED_BY_TAG]},
            {"Name": "status", "Values": ["completed"]},
        ],
    )

    for page in pages:
        for snapshot in page.get("Snapshots", []):
            created_on = get_snapshot_created_on(snapshot)
            if created_on and created_on < cutoff_date:
                snapshot_id = snapshot["SnapshotId"]
                if DRY_RUN:
                    deleted.append({"snapshot_id": snapshot_id, "created_on": str(created_on), "status": "dry-run"})
                    continue
                try:
                    ec2.delete_snapshot(SnapshotId=snapshot_id)
                    deleted.append({"snapshot_id": snapshot_id, "created_on": str(created_on), "status": "deleted"})
                except ClientError as exc:
                    deleted.append({"snapshot_id": snapshot_id, "created_on": str(created_on), "status": "failed", "error": str(exc)})

    return deleted


def get_snapshot_created_on(snapshot: Dict[str, Any]) -> Optional[dt.date]:
    created_on_tag = get_tag_value(snapshot.get("Tags", []), "CreatedOn")
    if created_on_tag:
        try:
            return dt.datetime.strptime(created_on_tag, "%Y-%m-%d").date()
        except ValueError:
            return None

    start_time = snapshot.get("StartTime")
    if isinstance(start_time, dt.datetime):
        return start_time.date()
    return None


def get_tag_value(tags: List[Dict[str, str]], key: str, default: Optional[str] = None) -> Optional[str]:
    for tag in tags:
        if tag.get("Key") == key:
            return tag.get("Value")
    return default


def save_report_to_s3(s3, report: Dict[str, Any]) -> None:
    """Store a JSON report in S3 for audit and troubleshooting."""
    if not LOG_BUCKET:
        print(json.dumps(report, default=str))
        return

    timestamp = report["started_at"].replace(":", "-")
    date_prefix = report["started_at"][:10]
    key = f"backup-reports/{ENVIRONMENT}/{date_prefix}/ec2-backup-{timestamp}.json"

    s3.put_object(
        Bucket=LOG_BUCKET,
        Key=key,
        Body=json.dumps(report, indent=2, default=str).encode("utf-8"),
        ContentType="application/json",
        ServerSideEncryption="AES256",
    )


def publish_notification(sns, report: Dict[str, Any]) -> None:
    """Send a compact backup summary to SNS when a topic is configured."""
    if not sns or not SNS_TOPIC_ARN:
        return

    subject = f"EC2 Backup {report['status']} - {ENVIRONMENT}"
    message = (
        f"EC2 backup status: {report['status']}\n"
        f"Environment: {ENVIRONMENT}\n"
        f"Created snapshots: {len(report.get('snapshots_created', []))}\n"
        f"Deleted snapshots: {len(report.get('snapshots_deleted', []))}\n"
        f"Duration seconds: {report.get('duration_seconds')}\n"
    )
    sns.publish(TopicArn=SNS_TOPIC_ARN, Subject=subject[:100], Message=message)
