output "storage_account_name" {
  value = azurerm_storage_account.this.name
}

output "storage_account_id" {
  value = azurerm_storage_account.this.id
}

output "primary_access_key" {
  value     = azurerm_storage_account.this.primary_access_key
  sensitive = true
}

output "dvc_container_name" {
  value = azurerm_storage_container.dvc.name
}

output "mlflow_container_name" {
  value = azurerm_storage_container.mlflow.name
}
