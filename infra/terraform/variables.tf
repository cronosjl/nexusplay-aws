variable "region" {
  description = "AWS Region"
  default     = "us-east-1"
}

variable "project" {
  description = "Project name"
  default     = "nexusplay"
}

variable "environment" {
  description = "Environment (dev/test/prod)"
  default     = "prod"
}

variable "aws_access_key" {
  description = "AWS Access Key"
  sensitive   = true
}

variable "aws_secret_key" {
  description = "AWS Secret Key"
  sensitive   = true
}
