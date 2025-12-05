# ECR Module Variables

variable "project_name" {
  description = "Project name for repository naming"
  type        = string
  default     = "vaspnestagent"
}

variable "image_tag_mutability" {
  description = "Image tag mutability setting"
  type        = string
  default     = "MUTABLE"
}

variable "scan_on_push" {
  description = "Enable image scanning on push"
  type        = bool
  default     = true
}

variable "image_count_to_keep" {
  description = "Number of tagged images to keep"
  type        = number
  default     = 10
}

variable "untagged_image_expiry_days" {
  description = "Days before untagged images expire"
  type        = number
  default     = 7
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
