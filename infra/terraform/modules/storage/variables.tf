variable "storage_account_name" {
  type        = string
  description = "Must be globally unique, 3-24 lowercase alphanumeric chars"
}

variable "resource_group_name" {
  type = string
}

variable "location" {
  type = string
}

variable "tags" {
  type    = map(string)
  default = {}
}
