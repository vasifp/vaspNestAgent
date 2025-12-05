# Terraform Backend Configuration
# Requirements: 8.3

# Uncomment and configure for remote state storage
# terraform {
#   backend "s3" {
#     bucket         = "vaspnestagent-terraform-state"
#     key            = "terraform.tfstate"
#     region         = "us-east-1"
#     encrypt        = true
#     dynamodb_table = "vaspnestagent-terraform-locks"
#   }
# }

# S3 bucket for Terraform state (create separately or use existing)
# resource "aws_s3_bucket" "terraform_state" {
#   bucket = "vaspnestagent-terraform-state"
#
#   lifecycle {
#     prevent_destroy = true
#   }
#
#   tags = {
#     Name    = "vaspNestAgent Terraform State"
#     Project = "vaspNestAgent"
#   }
# }

# resource "aws_s3_bucket_versioning" "terraform_state" {
#   bucket = aws_s3_bucket.terraform_state.id
#   versioning_configuration {
#     status = "Enabled"
#   }
# }

# resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
#   bucket = aws_s3_bucket.terraform_state.id
#
#   rule {
#     apply_server_side_encryption_by_default {
#       sse_algorithm = "aws:kms"
#     }
#   }
# }

# DynamoDB table for state locking
# resource "aws_dynamodb_table" "terraform_locks" {
#   name         = "vaspnestagent-terraform-locks"
#   billing_mode = "PAY_PER_REQUEST"
#   hash_key     = "LockID"
#
#   attribute {
#     name = "LockID"
#     type = "S"
#   }
#
#   tags = {
#     Name    = "vaspNestAgent Terraform Locks"
#     Project = "vaspNestAgent"
#   }
# }
