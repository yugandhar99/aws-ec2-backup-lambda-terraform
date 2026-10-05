# Optional remote backend example.
# For a real team project, create the backend bucket/table first and then uncomment this block.
#
# terraform {
#   backend "s3" {
#     bucket         = "your-terraform-state-bucket"
#     key            = "aws-ec2-backup-lambda/terraform.tfstate"
#     region         = "us-west-2"
#     dynamodb_table = "terraform-state-locks"
#     encrypt        = true
#   }
# }
