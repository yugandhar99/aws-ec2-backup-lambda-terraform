# Security Notes

This project is designed as a portfolio-ready AWS automation example. Before using it in production, review these items:

- Do not commit real `.env`, AWS keys, Terraform state files, or tfvars files containing secrets.
- Use an S3 remote backend with encryption and DynamoDB locking for team usage.
- Use GitHub OIDC to assume an AWS role instead of long-lived AWS access keys.
- Keep `create_sample_instances=false` unless you are running a controlled demo.
- Keep `log_bucket_force_destroy=false` in production.
- Review Lambda IAM permissions with your organization’s security team.
- Confirm snapshot retention aligns with internal compliance and cost policy.
- Enable notifications and CloudWatch alarms for production usage.
