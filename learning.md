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

---

## Phase 2 — Model Training, Serving, and Staging Deploy

### DVC + Azure Blob Storage

**What we did:**
- Ran `dvc init` to add DVC tracking to the repo
- Added an Azure Blob remote: `dvc remote add -d azblob azure://dvc/` pointed at storage account `mlopsmonishstg`
- Set up `data/raw/` and `data/processed/` directory scaffolding for all three models, tracked by DVC, ignored by git

**What I learned:**

**What DVC actually does**
- DVC separates large data files from git: it stores the file in a remote (Azure Blob here), and commits only a tiny `.dvc` pointer file that contains the file's MD5 hash
- `dvc push` uploads the data to the remote; `dvc pull` downloads it — the same mental model as `git push / pull`
- The pointer file IS committed to git, so the full history of which data version corresponded to which code is tracked

**DVC remotes on Azure**
- The `azure://` protocol uses the Azure SDK under the hood — it needs either a connection string or environment variables (`AZURE_STORAGE_ACCOUNT` + `AZURE_STORAGE_KEY`) to authenticate
- The remote name (`-d` flag sets it as default) is stored in `.dvc/config`, which IS committed so teammates get the same remote automatically

**`.gitkeep` pattern**
- Git cannot track empty directories; `.gitkeep` is a zero-byte file added purely so the directory structure is committed
- Once real files (or `.dvc` pointer files) are added, `.gitkeep` can be removed — but leaving it causes no harm

---

### Fraud Detection DVC Pipeline

**What we did:**
- Defined a three-stage DVC pipeline in `models/fraud-detection/dvc.yaml`: `featurize → train → evaluate`
- Each stage declares its `cmd`, `deps` (inputs), and `outs` (outputs/cache)
- The pipeline produces a trained XGBoost model logged to MLflow and registered as `fraud-detection`

**What I learned:**

**DVC pipeline stages vs. plain scripts**
- A plain script has no memory: running `python train.py` twice reruns everything even if nothing changed
- A DVC stage is a mini-Makefile entry: DVC hashes all `deps`, and if they haven't changed since the last run it skips the stage (shows "cached")
- `dvc repro` walks the DAG and only reruns stages whose deps changed — this is the core efficiency win

**`dvc.lock`**
- After a successful pipeline run, DVC writes `dvc.lock` with the exact hashes of every dep and output
- Commit this file — it's the reproducibility record; anyone can `dvc repro` and DVC will tell them which stages are stale

**MLflow experiment tracking inside a DVC stage**
- The train stage logs params (`mlflow.log_param`), metrics (`mlflow.log_metric`), and the model artifact (`mlflow.xgboost.log_model`) during `dvc repro`
- DVC tracks *file-level* reproducibility (did inputs change?); MLflow tracks *experiment-level* metadata (what hyperparams gave what metrics?)
- They complement each other: DVC tells you "this model artifact was built from this data"; MLflow tells you "this run got 0.91 AUC with these params"

**Model registration in MLflow**
- `mlflow.register_model(model_uri, name)` pushes a model artifact into the Model Registry under a named entry
- A registered model has versions (1, 2, 3…) and lifecycle stages: `None → Staging → Production → Archived`
- `mlflow.xgboost.load_model("models:/fraud-detection/Staging")` lets the serving layer always load whatever is currently promoted to Staging without hardcoding a path

---

### GitHub Actions CI

**What we did:**
- Added `.github/workflows/ci.yml` with two jobs: `lint-and-test` and `docker-build-check`
- `lint-and-test`: runs ruff, mypy, and pytest on every PR targeting `develop`, `staging`, or `main`
- `docker-build-check`: uses `git diff` against the base branch to detect which model/serving directories changed, then only builds the Docker images for those paths

**What I learned:**

**Path-filtered builds in GitHub Actions**
- `git diff --name-only origin/${{ github.base_ref }}...HEAD` lists every file changed on the branch vs. the PR target
- Piping that through `grep -q "^serving/"` returns exit code 0 (true) if any serving file changed, 1 otherwise
- Storing the result in a step output (`echo "serving=true" >> $GITHUB_OUTPUT`) and reading it with `if: steps.changes.outputs.serving == 'true'` skips the Docker build entirely when unrelated code changed
- This keeps CI fast: a docs-only change doesn't build four Docker images

**`GITHUB_OUTPUT` vs. `set-output`**
- The old pattern `echo "::set-output name=key::value"` is deprecated
- The current pattern is `echo "key=value" >> "$GITHUB_OUTPUT"` — appending to the file path stored in the `$GITHUB_OUTPUT` env var
- GitHub Actions reads this file after each step and makes the values available as `steps.<id>.outputs.<key>`

**`job.outputs` for cross-job values**
- Values computed in one job (like an image tag) are passed to downstream jobs via `outputs:` at the job level and `needs.<job>.outputs.<key>` in the consumer
- This is necessary because each job runs in a fresh VM — there is no shared memory between jobs

**`--dry-run=client -o yaml | kubectl apply -f -`**
- This is the idiomatic pattern for "create if missing, update if exists" for Kubernetes secrets
- `--dry-run=client` generates the YAML that *would* be applied without hitting the cluster
- Piping that to `kubectl apply -f -` applies it — if the secret already exists, it patches; if not, it creates
- Plain `kubectl create secret` fails if the secret already exists, making it unusable in a CD pipeline without a pre-check

---

### FastAPI Fraud Serving Endpoint

**What we did:**
- Added `serving/api/routers/fraud.py` with a `POST /predict/fraud` endpoint
- The model is loaded lazily from the URI in `$FRAUD_MODEL_URI` on first request
- Returns `{ fraud_probability: float, is_fraud: bool }` with a 503 if no model is configured

**What I learned:**

**Lazy loading models in FastAPI**
- Loading a large model at import time blocks the entire FastAPI startup — every cold start pays the full load cost even for endpoints that may not be called
- The module-level `_model = None` + `get_model()` pattern loads once on the first actual request, then caches in the module global for the lifetime of the process
- The tradeoff: the first request to that endpoint is slow (model load); all subsequent requests are fast

**`mlflow.xgboost.load_model(uri)`**
- This is the MLflow-flavored loader — it knows how to reconstruct an XGBoost model from a logged artifact
- URI formats: `runs:/<run_id>/model` (specific run), `models:/fraud-detection/Staging` (registry alias), or a local path
- At serving time the `Staging` alias is most useful: you can promote a new model version in MLflow without redeploying the service

**Pydantic v2 `BaseModel`**
- Field types are enforced at the Python type level — `list[float]` rejects strings automatically, returning a 422 with a clear validation error message
- No need for manual input validation in the route handler

---

### Kubernetes Manifests for AKS Staging

**What we did:**
- Wrote five manifests in `serving/k8s/`: `namespace.yaml`, `deployment.yaml`, `service.yaml`, `hpa.yaml`, `ingress.yaml`
- The Deployment uses `IMAGE_PLACEHOLDER` as the image tag — CI substitutes the real tag with `sed` before applying

**What I learned:**

**`IMAGE_PLACEHOLDER` + `sed` pattern**
- Kubernetes manifests need a concrete image tag at apply time, but the tag isn't known at commit time (it's derived from the git SHA in CI)
- The pattern: write `IMAGE_PLACEHOLDER` in the committed manifest, then in CI run `sed "s|IMAGE_PLACEHOLDER|ghcr.io/org/repo:staging-$SHA|g" deployment.yaml | kubectl apply -f -`
- The pipe means the original file is never modified on disk — the substituted YAML is piped directly to kubectl's stdin
- Alternative tools that handle this more formally: `kustomize` (patches overlays per environment), `helm` (values files), `envsubst` (substitutes `${VAR}` syntax)

**Kubernetes probes: readiness vs. liveness**
- `readinessProbe`: "is this pod ready to receive traffic?" — a failing pod is removed from the Service endpoints (no 503s to users)
- `livenessProbe`: "is this pod stuck/crashed?" — a failing pod is restarted by kubelet
- `initialDelaySeconds` on liveness should be longer than on readiness: you want to stop traffic first, wait for the app to boot, *then* decide if it needs a restart
- Both probe the same `/health` endpoint here; the difference is just timing and consequence

**HPA (HorizontalPodAutoscaler)**
- HPA watches a deployment and adjusts replica count based on metrics (CPU here)
- `autoscaling/v2` (current API) supports multiple metric types; `autoscaling/v1` only supported CPU
- `averageUtilization: 70` means: if average CPU across all pods exceeds 70% of their `requests.cpu`, scale up
- HPA requires `resources.requests.cpu` to be set on the container — without it, HPA cannot compute utilization and stays inactive

**ClusterIP vs. LoadBalancer vs. Ingress**
- `ClusterIP`: accessible only inside the cluster — used here because Ingress handles external traffic
- `LoadBalancer`: provisions a cloud load balancer per service (costs money, one IP per service)
- `Ingress`: a single entry point that routes to many services by path/host — one cloud load balancer shared across all services; the nginx ingress controller runs inside the cluster and reads Ingress resources

---

### GitHub Actions Staging Deploy Workflow

**What we did:**
- Completed `.github/workflows/deploy-staging.yml` with five sequential jobs: `build-push → integration-test → deploy → smoke-test → promote-model`
- Each job must pass before the next runs (`needs:` dependency chain)

**What I learned:**

**GHCR (GitHub Container Registry)**
- Images are pushed to `ghcr.io/<owner>/<repo>:<tag>`; the `GITHUB_TOKEN` has `packages: write` permission by default on the same repo, so no extra secret is needed for push
- For AKS to *pull* the image at runtime (outside the Action run), the `GITHUB_TOKEN` is expired — you need a long-lived PAT with `read:packages` scope, stored as a secret and installed as an `imagePullSecret` in Kubernetes
- `docker/login-action@v3` handles the `docker login ghcr.io` plumbing; `docker/build-push-action@v5` builds and pushes in one step using BuildKit

**`azure/login@v2` + `azure/aks-set-context@v3`**
- `AZURE_CREDENTIALS` is the JSON blob from `az ad sp create-for-rbac --sdk-auth` — it contains `clientId`, `clientSecret`, `tenantId`, and `subscriptionId`
- `azure/login` uses these to authenticate the runner's `az` CLI session
- `azure/aks-set-context` then calls `az aks get-credentials` behind the scenes, writing a `~/.kube/config` entry that subsequent `kubectl` commands in the same job use automatically

**`kubectl port-forward` in CI for smoke tests**
- The smoke-test job runs on a GitHub-hosted runner (not inside the cluster), so it can't reach cluster-internal services directly
- `kubectl port-forward svc/fraud-serving 8080:80 -n staging &` opens a tunnel from the runner's port 8080 to the service — no Ingress or public IP needed
- The `&` backgrounds the process; `PF_PID=$!` captures its PID so `trap "kill $PF_PID" EXIT` cleans it up when the step finishes
- `sleep 5` gives the tunnel a moment to establish before sending requests

**MLflow model stage transitions**
- `client.transition_model_version_stage(name, version, stage, archive_existing_versions=True)` is the programmatic equivalent of clicking "Transition to Staging" in the MLflow UI
- `archive_existing_versions=True` automatically moves any *other* version that was in `Staging` to `Archived` — ensures only one version holds the stage at a time
- This is the last step in the pipeline: code is deployed, smoke tests passed, so the model that's live in AKS is officially the Staging model

---

### Infrastructure Pivot: AKS → Azure VM + k3s

**What happened:**

The original plan used Azure Kubernetes Service (AKS) — a managed Kubernetes offering — provisioned via Terraform. Three consecutive `terraform apply` attempts failed before the cluster ever started:

1. **K8s version EOL** — `1.29` was specified in the Terraform module; Azure had already removed it from eastus. Fixed by bumping to `1.32`.
2. **LTS-only patch** — Azure resolved `1.32` to patch `1.32.11`, which requires the paid Premium/LTS tier on free subscriptions. Fixed by bumping to `1.33`.
3. **VM family quota** — `Standard_B2s` is not available on free Azure subscriptions; switched to `Standard_D2s_v7`. The subscription had 0 vCPU quota for the `StandardDsv7Family` in eastus. Submitted a quota increase request via Azure Portal — **denied**. Changed region to `westus2` and restarted the destroy/apply cycle; Terraform hung for >6 minutes on Key Vault soft-delete.

At this point three hours had been spent on infra that had not yet run a single container.

**Decision process:**

The core goal was a live, publicly accessible endpoint to demonstrate on a portfolio website — not a managed control plane. The question became: is AKS *necessary* for that goal, or just the first approach we tried?

Kubernetes itself is open-source software. AKS, GKE, and EKS are managed wrappers around it — they run the control plane on your behalf and charge for that convenience plus the underlying VMs. A free Azure subscription imposes per-family vCPU quotas specifically on the *VM pool* used by managed services. A plain Azure VM does not hit those same quota gates.

Alternatives evaluated:

| Option | Cost | Complexity | Public URL |
|---|---|---|---|
| AKS (original) | Free tier VM quota → blocked | Terraform managed | Yes (LoadBalancer) |
| Oracle Cloud Free Tier + k3s | Always free | Manual VM setup | Yes (public IP) |
| Hetzner Cloud VM + k3s | ~€4/month | Manual VM setup | Yes |
| Azure VM + k3s | Pay-as-you-go (~$0.10/hr B2s) | Stays in Azure | Yes |

**Decision: Azure VM + k3s.**

Rationale:
- The rest of the stack (DVC, MLflow, Azure Blob for DVC remote, GitHub Actions) is already on Azure. Keeping the VM in Azure avoids cross-cloud credential management.
- An Azure VM does not have the same K8s-specific version and VM family quota restrictions as AKS — you install whatever Linux distribution and k3s version you want.
- k3s is CNCF-certified Kubernetes — all existing manifests in `serving/k8s/` work without modification.
- Cost is predictable and comparable to AKS: a `Standard_B2s` VM (~$0.05/hr) running k3s is cheaper than the minimum AKS node pool because there is no managed control plane markup.
- Stays in the portfolio story: "provisioned and managed a Kubernetes cluster on Azure infrastructure."

**Architectural shifts:**

*What is removed:*
- `infra/terraform/modules/aks/` — the AKS-specific Terraform module
- `infra/terraform/modules/keyvault/` — Key Vault was only needed to pass secrets into AKS pods; k3s pods read secrets from Kubernetes secrets directly (already the pattern in the deploy workflow)
- `azure/login@v2` + `azure/aks-set-context@v3` steps in the deploy workflow
- `AZURE_CREDENTIALS` GitHub secret (the Service Principal JSON blob)

*What is added:*
- `infra/terraform/modules/vm/` — Terraform module to provision an Azure Linux VM (Ubuntu, Standard_B2s), open ports 22/80/443, attach a public IP
- k3s installed on that VM via a cloud-init script or post-provision remote-exec provisioner
- `KUBECONFIG` GitHub secret — the `/etc/rancher/k3s/k3s.yaml` file content from the VM, with the server IP substituted; used by the deploy workflow to authenticate kubectl
- SSH key pair — private key stored as a GitHub secret for any remote-exec steps; public key embedded in the VM

*What is unchanged:*
- All 5 Kubernetes manifests (`namespace.yaml`, `deployment.yaml`, `service.yaml`, `hpa.yaml`, `ingress.yaml`)
- The 5-job deploy workflow structure and every job except the `deploy` job's cluster-auth steps
- `GHCR_PAT` secret for image pull at runtime
- `MLFLOW_TRACKING_URI` and `FRAUD_MODEL_URI` secrets used to create the `mlflow-secrets` K8s secret in the deploy job
- DVC pipeline, MLflow tracking, GitHub Actions CI — no changes

**What I learned:**

**Managed K8s vs. self-managed K8s**
- Managed services (AKS/GKE/EKS) run the Kubernetes control plane (API server, etcd, scheduler, controller-manager) on your behalf. You pay for the convenience and get SLA guarantees on the control plane.
- k3s packages the entire control plane into a single ~70 MB binary. On a VM, `curl -sfL https://get.k3s.io | sh -` installs a production-grade, CNCF-conformant cluster in under 60 seconds.
- The worker nodes and pods are identical between managed and self-managed — the same Docker images, the same YAML manifests, the same `kubectl` commands. The only difference is who manages the control plane process.

**Why free-tier subscriptions impose stricter limits on managed K8s than on plain VMs**
- Azure free subscriptions have per-VM-family vCPU quotas. AKS node pools count against these quotas *and* additionally restrict which K8s versions and VM families are supported for the managed offering.
- A plain Linux VM only hits the vCPU quota — the same `Standard_B2s` that was rejected as an AKS node pool is available as a standalone VM on the same subscription.

**Key Vault soft-delete behaviour**
- Azure Key Vault has a soft-delete protection enabled by default (and mandatory since 2021). When Terraform destroys a Key Vault, Azure moves it to a "soft-deleted" state and holds it for 7–90 days before purging.
- `purge_soft_delete_on_destroy = true` in the Terraform provider block tells it to also call the purge API — but Azure enforces a delay before the purge API accepts the call, causing Terraform to poll and appear stuck.
- If this happens: cancel Terraform, go to Portal → Key Vaults → Manage deleted vaults → Purge manually. The resource group and other resources can be deleted independently.

**kubeconfig as a CI secret**
- k3s writes its kubeconfig to `/etc/rancher/k3s/k3s.yaml` on the server with `server: https://127.0.0.1:6443`. To use it from GitHub Actions, substitute the loopback address with the VM's public IP and store the whole file as a secret.
- The deploy job writes it to `~/.kube/config` and all subsequent `kubectl` commands in the job authenticate automatically — the same end state as `azure/aks-set-context@v3` but without any Azure-specific action.

<!-- Add new entries below as the project progresses -->
