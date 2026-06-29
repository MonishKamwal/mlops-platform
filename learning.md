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

### Local Dev Stack (Docker Compose)

**What we did:**
- Completed the local dev stack: FastAPI API + MLflow + Prometheus + Grafana, all wired together via Docker Compose
- Added healthchecks, a named bridge network, persistent volumes, and Grafana auto-provisioning
- Added graceful 503 handling in the API routers for when no models are registered yet

**What I learned:**

**Docker Compose `depends_on` with healthchecks**
- Plain `depends_on: [mlflow]` only waits for the container to *start*, not for the service inside it to be *ready*
- `depends_on: mlflow: condition: service_healthy` waits until the container's healthcheck passes — meaning the MLflow HTTP server is actually accepting requests
- The healthcheck is defined on the target service (`mlflow`), not the dependent one
- `start_period` gives the container grace time before failures start counting against `retries`

**MLflow healthcheck endpoint**
- MLflow exposes `/health` at the root (`http://localhost:5000/health`) — returns 200 OK when ready
- The mlflow Docker image does **not** include `curl` — a healthcheck using `curl -sf` will always fail silently, making the container permanently unhealthy
- Use Python's stdlib instead: `python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')"` — Python is guaranteed to be in any Python-based image

**macOS port 5000 conflict**
- macOS Monterey and later reserves port 5000 for AirPlay Receiver (process: ControlCenter)
- Running `lsof -ti :5000` reveals the PID; it's a system process so killing it is not a fix
- Solution: make host ports configurable via `.env` using `${VAR:-default}` syntax in docker-compose.yml, then set `MLFLOW_PORT=5001` locally
- The internal Docker network port (container-to-container) is unaffected — the API still reaches MLflow at `http://mlflow:5000` over the bridge network

**Grafana auto-provisioning**
- Grafana reads provisioning configs from `/etc/grafana/provisioning/` on startup
- Two sub-directories matter: `datasources/` (connects Grafana to Prometheus) and `dashboards/` (tells Grafana where to load dashboard JSON files from)
- Dashboard JSON files go in a separate volume-mounted directory (`/var/lib/grafana/dashboards`)
- This means Grafana starts pre-configured — no manual "Add data source" step needed

**Prometheus persistent storage**
- By default, Prometheus writes TSDB data to an ephemeral container layer — wiped on `docker compose down`
- Mounting a named volume to `/prometheus` and passing `--storage.tsdb.path=/prometheus` makes metrics survive restarts
- `--web.enable-lifecycle` adds a `/-/reload` endpoint so you can hot-reload prometheus.yml without restarting the container

**Environment variable defaults in Compose**
- `${VAR:-}` in docker-compose.yml means: use `$VAR` from the environment (or `.env` file) if set, otherwise default to empty string
- This lets the API container start cleanly even when model URIs aren't configured yet
- Without the default, Docker Compose would warn about an unset variable but still start — but the Python code would crash at runtime with a `KeyError`

**Lazy model loading + graceful degradation**
- Models are loaded the first time a prediction endpoint is called (not at startup) — this is intentional
- Before Phase 2, no models are registered in MLflow, so returning HTTP 503 with a clear message is cleaner than a 500 crash
- Pattern: `os.environ.get("KEY")` + `raise HTTPException(503, ...)` if empty, instead of `os.environ["KEY"]` which raises `KeyError`
- The `/health` endpoint always returns 200 regardless — Prometheus can scrape metrics and the stack is usable even without models

<!-- Add new entries below as the project progresses -->
