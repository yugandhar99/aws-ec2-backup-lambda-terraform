# Optional GenAI Enhancement

This project includes a practical GenAI-style operations helper:

```bash
python scripts/genai_backup_summary.py docs/sample-backup-report.json --output reports/backup-summary.md
```

By default, the script runs offline and produces a deterministic backup risk summary. This keeps the project safe for GitHub and easy to test.

## Optional Amazon Bedrock mode

For a real AWS environment, you can enable Bedrock-based summarization:

```bash
export USE_BEDROCK=true
export AWS_REGION=us-east-1
export BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
python scripts/genai_backup_summary.py docs/sample-backup-report.json
```

## How to explain this in interviews

The GenAI enhancement is not replacing the backup workflow. It improves operational visibility by converting raw backup reports into a readable summary with status, risk level, and recommended action. This is similar to how teams use AI for release summaries, incident summaries, and security scan explanations.
