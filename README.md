# AWS EC2 Backup Automation with Lambda and Terraform

Serverless EC2 EBS snapshot backup automation built with **AWS Lambda, EventBridge, Terraform, S3, SNS, CloudWatch, GitHub Actions, and optional GenAI backup summaries**.

This project is designed as a DevOps / Cloud Engineering portfolio project. It demonstrates how to automate backup operations, apply infrastructure as code, add basic security controls, validate changes through CI, and improve operational visibility.

## Project Overview

The solution automatically finds EC2 instances tagged for backup, creates EBS snapshots, tags those snapshots for audit and cleanup, deletes old snapshots based on a retention policy, and stores a JSON backup report in S3.

```text
EC2 instances tagged Backup=true
        |
        v
EventBridge schedule -> Lambda -> EBS snapshots
                          |
                          +-> S3 backup reports
                          +-> Snapshot retention cleanup
                          +-> Optional SNS notifications
                          +-> CloudWatch error alarm
                          +-> Optional GenAI backup summary
```

## Features

- Scheduled EC2 EBS snapshot backups using EventBridge
- Tag-based instance discovery using `Backup=true`
- Snapshot tagging for audit, cleanup, and traceability
- Retention-based automated snapshot cleanup
- S3 JSON backup reports with server-side encryption
- Optional SNS email notifications
- CloudWatch alarm for Lambda failures
- Terraform-based infrastructure provisioning
- Safer defaults: sample EC2 instances disabled by default
- GitHub Actions validation for Terraform and Python code
- Python unit tests for Lambda backup logic
- Optional GenAI-style backup risk summary script

## Technology Stack

| Area | Tools |
|---|---|
| Cloud | AWS Lambda, EC2, EBS Snapshots, S3, EventBridge, SNS, CloudWatch |
| IaC | Terraform, TFLint, Checkov |
| Runtime | Python 3.12 |
| CI/CD | GitHub Actions |
| Security | IAM least privilege pattern, S3 encryption, public access block, state/secrets protection |
| AI Enhancement | Optional Amazon Bedrock-ready backup summary helper |

## Repository Structure

```text
.
├── .github/workflows/              # GitHub Actions validation and optional drift workflow
├── docs/                           # Architecture, runbook, screenshots, GenAI notes
├── envs/                           # Environment-specific tfvars
├── lambda/                         # Python Lambda backup function
├── scripts/                        # Optional AI backup summary helper
├── templates/                      # IAM policy template
├── tests/                          # Terraform and Python tests
├── main.tf                         # AWS infrastructure
├── variables.tf                    # Terraform variables and validation
├── outputs.tf                      # Terraform outputs
├── versions.tf                     # Providers and versions
└── README.md
```

## How It Works

1. Add the tag `Backup=true` to EC2 instances that should be backed up.
2. EventBridge invokes the Lambda function on the configured schedule.
3. Lambda discovers tagged non-terminated EC2 instances.
4. Lambda creates snapshots for attached EBS volumes.
5. Lambda tags snapshots with instance ID, volume ID, creation date, environment, and retention metadata.
6. Lambda deletes completed automated snapshots older than the configured retention period.
7. Lambda stores a JSON report in S3.
8. Optional SNS and CloudWatch alarms improve visibility.

## Prerequisites

- AWS CLI configured locally
- Terraform 1.6+
- Python 3.12+
- An AWS account with permission to create Lambda, IAM, S3, EventBridge, SNS, CloudWatch, and EC2 snapshot resources

## Configure

Update `envs/dev.tfvars` or create your own tfvars file:

```hcl
environment              = "dev"
retention_days           = 7
log_retention_days       = 30
backup_schedule          = "cron(0 2 * * ? *)"
create_sample_instances  = false
log_bucket_force_destroy = true
enable_notifications     = false
```

To select instances for backup, tag them like this:

```text
Key: Backup
Value: true
```

## Deploy

```bash
terraform init
terraform fmt -recursive
terraform validate
terraform plan -var-file=envs/dev.tfvars
terraform apply -var-file=envs/dev.tfvars
```

## Test Lambda Logic Locally

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
pytest
```

## Optional GenAI Backup Summary

Generate an operations-style backup summary from a backup report:

```bash
python scripts/genai_backup_summary.py docs/sample-backup-report.json --output reports/backup-summary.md
```

For real AWS usage, the script can optionally call Amazon Bedrock when `USE_BEDROCK=true`. See [docs/GENAI_ENHANCEMENT.md](docs/GENAI_ENHANCEMENT.md).

## GitHub Actions

The project includes CI validation for:

- Terraform formatting
- Terraform validation
- TFLint
- Checkov IaC security scan
- Python syntax check
- Python unit tests

The validation workflow does not require AWS credentials. A separate drift workflow is included as a manual workflow for real AWS environments.

## Important Safety Notes

- Terraform state files were removed and are ignored.
- Real AWS keys should never be committed.
- Sample EC2 instances are disabled by default.
- Use a remote backend for team or production usage.
- Keep `log_bucket_force_destroy=false` for production.
- Review snapshot costs before enabling frequent schedules or long retention.

## Cleanup

```bash
terraform destroy -var-file=envs/dev.tfvars
```

Be careful: destroying resources may remove AWS infrastructure created by this project. Snapshot deletion depends on the resources and settings in your environment.

## Future Improvements

- Multi-region backup execution
- Cross-account backup using AWS Organizations and STS AssumeRole
- AWS Backup integration comparison
- Backup success/failure dashboard in CloudWatch
- Slack or Teams notification integration
- Bedrock-powered daily backup summary from S3 reports
- Automated recovery validation workflow

## Resume Bullet

Built a serverless AWS EC2 backup automation solution using Terraform, Lambda, EventBridge, S3, SNS, and CloudWatch to create scheduled EBS snapshots, enforce retention cleanup, store audit reports, and support AI-assisted backup summaries for operational review.

---

<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=0:0F2027,50:2C5364,100:00C9FF&height=120&section=footer&text=Let's%20Connect&fontColor=ffffff&fontSize=32&fontAlignY=70" />
</p>

<h2 align="center">🤝 Connect With Me</h2>

<p align="center">
  <em>
    Thanks for visiting this project! I’m continuously building hands-on DevOps, Cloud, Automation, and AI-enabled engineering projects to improve real-world deployment, monitoring, and infrastructure skills.
  </em>
</p>

<p align="center">
  <img src="https://readme-typing-svg.herokuapp.com?font=Fira+Code&size=22&duration=2500&pause=800&color=00C9FF&center=true&vCenter=true&width=650&lines=DevOps+%7C+Cloud+%7C+Automation;CI%2FCD+%7C+Docker+%7C+Kubernetes+%7C+Terraform;Building+real-world+projects+one+commit+at+a+time" alt="Typing SVG" />
</p>

<p align="center">
  <a href="https://github.com/yugandhar99" target="_blank" rel="noopener noreferrer">
    <img src="https://img.shields.io/badge/GitHub-Follow-181717?style=flat&logo=github&logoColor=white" alt="GitHub" />
  </a>
  <a href="https://www.linkedin.com/in/yugandhar-devops" target="_blank" rel="noopener noreferrer">
    <img src="https://img.shields.io/badge/LinkedIn-Connect-0A66C2?style=flat&logo=linkedin&logoColor=white" alt="LinkedIn" />
  </a>
  <a href="https://yugandhar-portfolio-psi.vercel.app/" target="_blank" rel="noopener noreferrer">
    <img src="https://img.shields.io/badge/Portfolio-View%20My%20Work-FF5722?style=flat&logo=vercel&logoColor=white" alt="Portfolio" />
  </a>
  <a href="mailto:yugandharethamukkala1999@gmail.com">
    <img src="https://img.shields.io/badge/Email-Contact%20Me-D14836?style=flat&logo=gmail&logoColor=white" alt="Email" />
  </a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Focus-DevOps%20Engineering-blue?style=flat-square" />
  <img src="https://img.shields.io/badge/Cloud-AWS%20%7C%20Azure%20%7C%20GCP-orange?style=flat-square" />
  <img src="https://img.shields.io/badge/IaC-Terraform-purple?style=flat-square" />
  <img src="https://img.shields.io/badge/Containers-Docker%20%7C%20Kubernetes-2496ED?style=flat-square" />
</p>

---

<p align="center">
  ⭐ If this project added value, feel free to star the repository and connect with me!
</p>

<p align="center">
  <strong>Built with ❤️ using modern DevOps practices</strong>
</p>
