# Secrets Module Variables

variable "nest_client_id" {
  description = "Google Nest OAuth client ID"
  type        = string
  sensitive   = true
}

variable "nest_client_secret" {
  description = "Google Nest OAuth client secret"
  type        = string
  sensitive   = true
}

variable "nest_refresh_token" {
  description = "Google Nest OAuth refresh token"
  type        = string
  sensitive   = true
}

variable "nest_project_id" {
  description = "Google Nest project ID"
  type        = string
  sensitive   = true
}

variable "google_voice_credentials" {
  description = "Google Voice API credentials"
  type        = string
  sensitive   = true
}

variable "google_voice_phone_number" {
  description = "Google Voice phone number for notifications (480-442-0574)"
  type        = string
  sensitive   = true
  default     = "480-442-0574"
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
