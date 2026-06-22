data "azurerm_client_config" "current" {}

resource "azurerm_key_vault" "this" {
  name                = var.keyvault_name
  location            = var.location
  resource_group_name = var.resource_group_name
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = "standard"

  # Prevent accidental deletion
  soft_delete_retention_days = 7
  purge_protection_enabled   = false

  tags = var.tags
}

# Give the deploying identity (you, via az login) full access
resource "azurerm_key_vault_access_policy" "deployer" {
  key_vault_id = azurerm_key_vault.this.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = data.azurerm_client_config.current.object_id

  secret_permissions = [
    "Get", "List", "Set", "Delete", "Purge"
  ]
}

# Give AKS kubelet identity read access to pull secrets at runtime
resource "azurerm_key_vault_access_policy" "aks_kubelet" {
  key_vault_id = azurerm_key_vault.this.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = var.aks_kubelet_object_id

  secret_permissions = ["Get", "List"]
}
