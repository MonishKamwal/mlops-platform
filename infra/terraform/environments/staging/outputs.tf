output "aks_cluster_name" {
  value = module.aks.cluster_name
}

output "storage_account_name" {
  value = module.storage.storage_account_name
}

output "keyvault_uri" {
  value = module.keyvault.keyvault_uri
}

output "kube_config" {
  value     = module.aks.kube_config
  sensitive = true
}
