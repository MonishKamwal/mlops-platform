# MLOps Platform — Learning Journal

## How to use this file
Each entry records what was done, what was learned, and any concepts that clicked or were confusing. Updated as the project progresses.

---

## Phase 1 — Foundation

### Terraform & Azure Infrastructure

**What we did:**
- Set up Terraform module structure: `modules/aks`, `modules/storage`, `modules/keyvault`
- Configured the staging environment (`infra/terraform/environments/staging/`)
- Filled in `terraform.tfvars` with subscription ID, location, storage account name, and Key Vault name

**What I learned:**

**`terraform init`**
- Initializes a Terraform working directory
- Downloads the provider plugin declared in `main.tf` (in our case `hashicorp/azurerm`) into a local `.terraform/` folder
- Also creates `.terraform.lock.hcl` to pin the exact provider version
- Safe to run multiple times — it never touches Azure
- `2>&1` in shell commands redirects stderr to stdout so all output appears together

**`terraform plan`**
- Read-only preview: calls the Azure API and compares your config against current Azure state
- Shows exactly what would be created, changed, or destroyed
- Nothing is created in Azure — it is purely a diff

**`terraform apply`**
- Actually provisions resources in Azure (costs money)
- Always run `plan` first to review before applying

**Where things live:**
- `.terraform/` — provider binaries cached locally, re-downloadable anytime, gitignored
- `terraform.tfstate` — tracks what Terraform created in Azure; critical file, must not be lost
- Azure — where the actual infrastructure runs (AKS, Storage, Key Vault)
- GitHub — all code and configs; the source of truth

**The bootstrap problem (remote state):**
- Terraform state should be stored remotely (Azure Blob) so it isn't tied to your laptop
- But you need a storage account to store state — and Terraform creates the storage account
- Solution: two-phase approach
  - Phase A: manually create a dedicated tfstate storage account via Azure CLI
  - Phase B: run `terraform init` / `plan` / `apply` for the main infra
  - Phase C: uncomment the backend block in `main.tf`, run `terraform init -migrate-state` to move local state to Azure Blob

**Key insight:** Your laptop is just the control plane — not where the project runs. If you wipe your laptop, you only need `git clone` + `az login` + `terraform init` to be back in control, as long as state is stored remotely.

---

<!-- Add new entries below as the project progresses -->
