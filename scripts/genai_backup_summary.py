#!/usr/bin/env python3
"""
Optional GenAI-style backup operations summary generator.

This script reads an EC2 backup JSON report and creates an executive-friendly
summary. By default it works offline with deterministic logic. If you configure
Amazon Bedrock credentials and set USE_BEDROCK=true, it can call Bedrock to
produce a richer AI-assisted summary.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict


def offline_summary(report: Dict[str, Any]) -> str:
    created = report.get("snapshots_created", [])
    deleted = report.get("snapshots_deleted", [])
    failed_created = [item for item in created if item.get("snapshot_id") == "failed"]
    failed_deleted = [item for item in deleted if item.get("status") == "failed"]
    status = report.get("status", "unknown")
    environment = report.get("environment", "unknown")

    risk = "Low"
    if failed_created or failed_deleted or status == "failed":
        risk = "High"
    elif status == "completed_with_errors":
        risk = "Medium"

    return f"""# AI-Assisted EC2 Backup Summary

Environment: {environment}
Status: {status}
Risk Level: {risk}

Summary:
- Snapshots created: {len(created)}
- Snapshots deleted by retention policy: {len(deleted)}
- Snapshot creation failures: {len(failed_created)}
- Snapshot cleanup failures: {len(failed_deleted)}

Recommended action:
{recommendation(risk)}
"""


def recommendation(risk: str) -> str:
    if risk == "High":
        return "Review the failed snapshot entries immediately, validate IAM permissions, and confirm affected EC2 volumes are protected by another recovery option."
    if risk == "Medium":
        return "Review the backup report and verify that all critical EC2 volumes have recent successful snapshots."
    return "No urgent action required. Continue monitoring CloudWatch alarms and backup reports."


def bedrock_summary(report: Dict[str, Any]) -> str:
    import boto3

    model_id = os.environ.get("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")
    client = boto3.client("bedrock-runtime", region_name=os.environ.get("AWS_REGION", "us-east-1"))
    prompt = (
        "Summarize this EC2 backup report for a DevOps release/operations audience. "
        "Include status, risk level, and recommended action. Keep it concise.\n\n"
        f"Report JSON:\n{json.dumps(report, indent=2, default=str)}"
    )
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 500,
        "messages": [{"role": "user", "content": prompt}],
    }
    response = client.invoke_model(modelId=model_id, body=json.dumps(body))
    response_body = json.loads(response["body"].read())
    return response_body["content"][0]["text"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate an EC2 backup operations summary.")
    parser.add_argument("report", type=Path, help="Path to backup report JSON file")
    parser.add_argument("--output", type=Path, default=Path("reports/backup-summary.md"))
    args = parser.parse_args()

    report = json.loads(args.report.read_text())
    use_bedrock = os.environ.get("USE_BEDROCK", "false").lower() == "true"
    summary = bedrock_summary(report) if use_bedrock else offline_summary(report)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(summary)
    print(f"Summary written to {args.output}")


if __name__ == "__main__":
    main()
