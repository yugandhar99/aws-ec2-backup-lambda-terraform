# Portfolio Notes

## Project Summary

Built a serverless AWS EC2 backup automation platform using Lambda, EventBridge, Terraform, S3, SNS, and CloudWatch. The solution discovers tagged EC2 instances, creates EBS snapshots, applies retention-based cleanup, stores JSON audit reports in S3, and supports optional AI-assisted backup summaries.

## Resume Bullet

Built an AWS serverless EC2 backup automation solution using Terraform, Lambda, EventBridge, S3, SNS, and CloudWatch to create scheduled EBS snapshots, enforce retention cleanup, store audit reports, and support AI-assisted backup summaries for operational review.

## Interview Explanation

I built this project to automate EC2 backup operations without using manual scripts or servers. The design uses EventBridge to trigger a Lambda function on a schedule. Lambda finds EC2 instances with a backup tag, snapshots attached EBS volumes, tags snapshots for tracking, deletes old snapshots based on retention, and writes a JSON report to S3.

I enhanced it with production-style practices such as Terraform variable validation, optional SNS notifications, CloudWatch error alarms, S3 encryption and lifecycle retention, safer `.gitignore`, GitHub Actions validation, Python unit tests, and an optional GenAI-style backup summary script. This shows not only AWS automation, but also DevOps, IaC, security, reliability, and modern operations visibility.

## Best GitHub Description

Serverless AWS EC2 backup automation using Terraform, Lambda, EventBridge, S3, SNS, CloudWatch, GitHub Actions, and optional GenAI backup summaries.
