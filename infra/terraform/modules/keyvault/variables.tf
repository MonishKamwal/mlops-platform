variable "keyvault_name" {
  type        = string
  description = "Must be globally unique, 3-24 chars"
}

variable "resource_group_name" {
  type = string
}

variable "location" {
  type = string
}

variable "aks_kubelet_object_id" {
  type        = string
  default     = ""
  description = "Object ID of the AKS kubelet managed identity; empty string skips the policy"
}

variable "tags" {
  type    = map(string)
  default = {}
}
