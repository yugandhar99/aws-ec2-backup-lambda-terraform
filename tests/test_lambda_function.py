import datetime as dt
import importlib
import os
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest


class FakePaginator:
    def __init__(self, pages):
        self.pages = pages

    def paginate(self, **kwargs):
        return self.pages


@pytest.fixture()
def lambda_module(monkeypatch):
    monkeypatch.setenv("RETENTION_DAYS", "7")
    monkeypatch.setenv("LOG_BUCKET", "backup-log-bucket")
    monkeypatch.setenv("BACKUP_TAG_KEY", "Backup")
    monkeypatch.setenv("BACKUP_TAG_VALUE", "true")
    monkeypatch.setenv("CREATED_BY_TAG", "unit-test-backup")
    monkeypatch.setenv("ENVIRONMENT", "test")

    fake_boto3 = MagicMock()
    fake_botocore = MagicMock()
    fake_botocore.exceptions.ClientError = Exception
    monkeypatch.setitem(sys.modules, "boto3", fake_boto3)
    monkeypatch.setitem(sys.modules, "botocore", fake_botocore)
    monkeypatch.setitem(sys.modules, "botocore.exceptions", fake_botocore.exceptions)

    sys.modules.pop("lambda.lambda_function", None)
    return importlib.import_module("lambda.lambda_function")


def test_create_backups_creates_snapshot(lambda_module):
    ec2 = MagicMock()
    ec2.get_paginator.return_value = FakePaginator(
        [
            {
                "Reservations": [
                    {
                        "Instances": [
                            {
                                "InstanceId": "i-1234567890",
                                "Tags": [{"Key": "Name", "Value": "app-server"}],
                                "BlockDeviceMappings": [{"Ebs": {"VolumeId": "vol-123"}}],
                            }
                        ]
                    }
                ]
            }
        ]
    )
    ec2.create_snapshot.return_value = {"SnapshotId": "snap-123"}

    result = lambda_module.create_backups(ec2)

    assert result[0]["snapshot_id"] == "snap-123"
    ec2.create_snapshot.assert_called_once()


def test_cleanup_deletes_old_snapshot(lambda_module):
    ec2 = MagicMock()
    old_date = dt.date.today() - dt.timedelta(days=10)
    ec2.get_paginator.return_value = FakePaginator(
        [
            {
                "Snapshots": [
                    {
                        "SnapshotId": "snap-old",
                        "Tags": [{"Key": "CreatedOn", "Value": old_date.isoformat()}],
                    }
                ]
            }
        ]
    )

    result = lambda_module.cleanup_old_snapshots(ec2)

    assert result[0]["snapshot_id"] == "snap-old"
    assert result[0]["status"] == "deleted"
    ec2.delete_snapshot.assert_called_once_with(SnapshotId="snap-old")


def test_save_report_to_s3(lambda_module):
    s3 = MagicMock()
    report = {
        "started_at": "2026-01-01T00:00:00+00:00",
        "status": "success",
        "snapshots_created": [],
        "snapshots_deleted": [],
    }

    lambda_module.save_report_to_s3(s3, report)

    args = s3.put_object.call_args.kwargs
    assert args["Bucket"] == "backup-log-bucket"
    assert args["ContentType"] == "application/json"
