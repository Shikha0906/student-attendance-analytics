terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    azure = {
      source  = "hashicorp/azuread"
      version = "~> 2.0"
    }
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}

# AWS S3 Backend Configuration for Attendance Data
# Uncomment and configure if using remote state
#
# backend "s3" {
#   bucket = "attendance-analytics-terraform-state"
#   key    = "student-attendance/terraform.tfstate"
#   region = "us-east-1"
# }

# Provider: AWS
provider "aws" {
  region = var.aws_region
}

# Provider: Azure
provider "azuread" {
  tenant_id = var.azure_tenant_id
  client_id = var.azure_client_id
}

# Provider: Google Cloud
provider "google" {
  project = var.gcp_project
  region  = var.gcp_region
}

# Input Variables
variable "aws_region" {
  description = "AWS region for resources"
  default     = "us-east-1"
}

variable "azure_tenant_id" {
  description = "Azure Active Directory tenant ID"
}

variable "azure_client_id" {
  description = "Azure client ID for authentication"
}

variable "gcp_project" {
  description = "Google Cloud project ID"
}

variable "gcp_region" {
  description = "Google Cloud region"
  default     = "us-central1"
}

# Output Values
output "aws_bucket_name" {
  description = "AWS S3 bucket name for attendance data"
  value       = aws.s3_attendance_bucket.bucket_id
}

output "azure_container_name" {
  description = "Azure Blob container name for attendance data"
  value       = azurerm_storage_container.attendance.container_name
}

output "gcp_bucket_name" {
  description = "GCP Cloud Storage bucket name for attendance data"
  value       = google_storage_bucket.attendance.name
}