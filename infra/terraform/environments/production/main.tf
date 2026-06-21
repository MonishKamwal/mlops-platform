terraform {
  required_version = ">= 1.6"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.100"
    }
  }

  # backend "azurerm" {
  #   resource_group_name  = "mlops-tfstate-rg"
  #   storage_account_name = "<your-tfstate-storage-account>"
  #   container_name       = "tfstate"
  #   key                  = "production.terraform.tfstate"
  # }
}

provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy = false
    }
  }
  subscription_id = var.subscription_id
}

resource "azurerm_resource_group" "production" {
  name     = "mlops-production-rg"
  location = var.location
  tags     = local.tags
}

locals {
  tags = {
    environment = "production"
    project     = "mlops-platform"
    managed_by  = "terraform"
  }
}

module "aks" {
  source              = "../../modules/aks"
  cluster_name        = "mlops-prod-aks"
  location            = var.location
  resource_group_name = azurerm_resource_group.production.name
  tags                = local.tags
}

module "storage" {
  source               = "../../modules/storage"
  storage_account_name = var.storage_account_name
  location             = var.location
  resource_group_name  = azurerm_resource_group.production.name
  tags                 = local.tags
}

module "keyvault" {
  source                = "../../modules/keyvault"
  keyvault_name         = var.keyvault_name
  location              = var.location
  resource_group_name   = azurerm_resource_group.production.name
  aks_kubelet_object_id = module.aks.kubelet_identity_object_id
  tags                  = local.tags
}

resource "azurerm_key_vault_secret" "storage_key" {
  name         = "storage-account-key"
  value        = module.storage.primary_access_key
  key_vault_id = module.keyvault.keyvault_id

  depends_on = [module.keyvault]
}
