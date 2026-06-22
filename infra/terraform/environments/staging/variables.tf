variable "subscription_id" {
  type        = string
  description = "Azure subscription ID"
}

variable "location" {
  type    = string
  default = "eastus"
}

variable "storage_account_name" {
  type        = string
  description = "Globally unique, 3-24 lowercase alphanumeric — e.g. mlopsmonishstg"
}

variable "keyvault_name" {
  type        = string
  description = "Globally unique, 3-24 chars — e.g. mlops-monish-kv-stg"
}
