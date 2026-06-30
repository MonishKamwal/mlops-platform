# MLOps Platform — Project Plan

## Overview

Production-grade MLOps platform demonstrating end-to-end machine learning engineering: training pipelines, experiment tracking, containerized deployment on Kubernetes, model monitoring, and automated CI/CD. Built as a portfolio project with a live showcase site.

**Infrastructure:** AWS EC2 t2.micro + k3s (self-managed Kubernetes), Azure Blob for DVC remote  
**Strategy:** Ship end-to-end pipeline with a placeholder model first, then upgrade the model and connect to the portfolio site.

---

## Phased Roadmap

| Phase | Goal |
|---|---|
| **2 (current)** | End-to-end MLOps pipeline live with placeholder fraud detection model |
| **3** | Monitoring, observability, production deploy pipeline (Evidently, Prometheus, Grafana, canary) |
| **4** | Portfolio site at moish.github.io |
| **5** | Connect MLOps project to portfolio site — live endpoint demo, architecture page, embedded dashboards |
| **6** | Model upgrades + Models 2 & 3 (future consideration) |

---

## The Three Models

| # | Model | Domain | Framework | Dataset |
|---|-------|--------|-----------|---------|
| 1 | **Fraud Detection** | Tabular / Classification | XGBoost + scikit-learn | Kaggle Credit Card Fraud |
| 2 | **Sentiment Analysis** | NLP / Text Classification | DistilBERT (HuggingFace) | IMDB / Twitter dataset |
| 3 | **Demand Forecasting** | Time Series / Regression | LightGBM + Prophet | Open retail/energy dataset |

Model 1 is currently a placeholder — pipeline correctness is the goal, not model quality. Models 2 and 3 are future phases.

---

## Tech Stack

| Category | Tool | Rationale |
|---|---|---|
| Source control | GitHub (public monorepo) | Portfolio visibility, free Actions minutes |
| CI/CD | GitHub Actions | Industry standard, free for public repos |
| Experiment tracking | MLflow (self-hosted in k3s) | Open-source, shows infra ownership |
| Model registry | MLflow Model Registry | Co-located with tracking server |
| Data versioning | DVC + Azure Blob Storage | Industry standard, reproducibility |
| ML frameworks | scikit-learn, XGBoost, HuggingFace Transformers, LightGBM, Prophet | Breadth showcase |
| Model serving | FastAPI + Uvicorn | REST API, industry standard |
| Containerization | Docker + Docker Compose (local dev) | Consistent environments |
| Container registry | GitHub Container Registry (GHCR) | Free, integrated with Actions |
| Orchestration | k3s on AWS EC2 t2.micro | Self-managed Kubernetes, free tier eligible |
| Monitoring / Drift | Evidently AI | Open-source, purpose-built for ML drift |
| Metrics | Prometheus + Grafana | Industry standard observability |
| Logging | Grafana Loki | Lightweight, integrates with Grafana |
| Secrets | Kubernetes secrets + GitHub Actions secrets | No managed secret store needed |
| Portfolio site | GitHub Pages at moish.github.io | Free hosting, live model demos |

---

## Repository Structure

```
mlops-platform/
├── models/
│   ├── fraud-detection/
│   │   ├── data/               # DVC-tracked, gitignored
│   │   ├── notebooks/
│   │   ├── src/
│   │   │   ├── train.py
│   │   │   ├── evaluate.py
│   │   │   └── features.py
│   │   ├── tests/
│   │   ├── Makefile
│   │   └── Dockerfile
│   ├── sentiment-analysis/     # Future
│   └── demand-forecasting/     # Future
├── serving/
│   ├── api/                    # FastAPI app (all model routes)
│   ├── Dockerfile
│   └── k8s/                    # Deployment, Service, HPA, Ingress manifests
├── monitoring/
│   ├── evidently/              # Drift detection configs + reference datasets
│   ├── prometheus/             # prometheus.yml, alert rules
│   └── grafana/                # Dashboard JSON exports
├── infra/
│   └── scripts/                # vm-setup.sh (k3s install + swap), teardown helpers
├── .github/
│   └── workflows/
│       ├── ci.yml              # Lint, type-check, unit tests (every PR)
│       ├── train.yml           # Re-train on data/code change
│       ├── deploy-staging.yml  # develop → staging merge
│       ├── deploy-prod.yml     # staging → main merge (canary)
│       └── hotfix.yml          # Fast-path prod deploy + backmerge PR
├── docs/
│   ├── architecture/           # Diagrams (Mermaid / draw.io)
│   └── adr/                    # Architecture Decision Records
├── Makefile                    # Top-level dev commands
├── docker-compose.yml          # Local: api + mlflow + prometheus + grafana
└── PLAN.md
```

---

## Branch Strategy & CI/CD

```
feature/* ──► develop ──► staging ──► main (production)
                                          ▲
                                    hotfix/* (→ main, then backmerge to develop)
```

| Branch | k3s Namespace | Image Tag | Trigger |
|---|---|---|---|
| `feature/*` | none (CI only) | — | PR open / push |
| `develop` | `dev` (on-demand) | `dev-<sha>` | merge to develop |
| `staging` | `staging` | `staging-<sha>` | PR: develop → staging merged |
| `main` | `production` | `prod-<sha>` | PR: staging → main merged (canary) |
| `hotfix/*` | fast-path to production | `hotfix-<sha>` | merge to main + backmerge to develop |

**Branch protection (all long-lived branches):** no direct pushes, required status checks, PR-only merges.

### Pipeline Stages

**PR to `develop` (`ci.yml`):** Lint (ruff), type-check (mypy), unit tests (pytest), Docker build smoke test.

**develop → staging merged (`deploy-staging.yml`):**

1. Build + push to GHCR (`staging-<sha>`)
2. Integration tests (container health check)
3. Deploy to k3s `staging` namespace (via KUBECONFIG secret)
4. Smoke tests (latency + response shape)
5. Update MLflow model stage: `None → Staging`

**staging → main merged (`deploy-prod.yml`):**

1. Build + push to GHCR (`prod-<sha>`)
2. Canary deploy: 10% traffic
3. Monitor 10 min (error rate, latency, drift via Prometheus)
4. Auto-promote to 100% or auto-rollback
5. Update MLflow model stage: `Staging → Production`

**Hotfix (`hotfix.yml`):** Fast-path CI → immediate production deploy (no canary) → automated backmerge PR to `develop`.

---

## Model Monitoring & Auto-Rollback

- **Evidently AI** runs as a Kubernetes CronJob against incoming prediction logs
- Detects: data drift, prediction drift, feature distribution shift
- **Prometheus** scrapes FastAPI metrics, Evidently drift scores, periodic batch eval metrics
- **Grafana:** one dashboard per model + one system overview
- **Alertmanager** triggers auto-rollback workflow on:
  - Error rate > 5% for 5 minutes
  - Drift score exceeds configured threshold
  - Model accuracy drop > 10% from baseline

---

## Cost Profile

| Resource | SKU | Est. Cost/Month |
|---|---|---|
| AWS EC2 (k3s host) | t2.micro, free tier | $0 for 12 months, then ~$8.50 |
| Azure Blob Storage | LRS, ~10 GB (DVC remote) | ~$1 |
| AWS Elastic IP | Attached to running instance | $0 (free while attached) |
| Egress / misc | — | ~$1 |
| **Total** | | **~$2/month (free tier), ~$10/month after** |

---

## Portfolio Site (moish.github.io)

Separate repo: `moish.github.io` — GitHub Pages, static site.

| Page | Content |
|---|---|
| Home | Hero, live API health badge |
| Architecture | Interactive full-stack diagram |
| Models | Per-model card: metrics + live demo (calls FastAPI) |
| Monitoring | Embedded Grafana dashboards (public read-only) |
| CI/CD | Animated pipeline visualization, link to Actions runs |
| Behind the Scenes | ADRs and engineering decisions in plain English |

Design principle: every technical component has a plain-English tooltip for non-technical visitors.

---
### Phase 1 — Foundation (Weeks 1–3) ✓

- [x] GitHub repo, branch protection, repo structure scaffold
- [x] MLflow server deployed locally via Docker Compose
- [x] Docker Compose local dev stack (api + mlflow + prometheus + grafana)
- [x] DVC initialized, Azure Blob as remote

## Phase 2 — End-to-End Pipeline (Current)

All code is written. Remaining tasks are infrastructure wiring only.

- [x] Training script with MLflow tracking (params, metrics, artifacts)
- [x] DVC pipeline: data → features → train → evaluate
- [x] Model registered in MLflow Model Registry (placeholder — pipeline completeness is the goal)
- [x] FastAPI endpoint `/predict/fraud`
- [x] GitHub Actions CI (lint, test, build)
- [x] Kubernetes manifests (namespace, deployment, service, hpa, ingress)
- [x] GitHub Actions staging deploy workflow (5 jobs)
- [x] `learning.md` updated with AKS + Azure VM failures, infrastructure pivot decision
- [ ] Provision AWS EC2 t2.micro (Ubuntu 22.04, ports 22/80/443/6443 open)
- [ ] Add 1GB swap file on the VM
- [ ] Install k3s on the VM
- [ ] Export kubeconfig (substitute 127.0.0.1 → EC2 public IP)
- [ ] Update `deploy-staging.yml`: remove `azure/login` + `azure/aks-set-context` from `deploy` and `smoke-test` jobs; replace with KUBECONFIG setup step
- [ ] Set GitHub secrets: `KUBECONFIG`, `GHCR_PAT`, `MLFLOW_TRACKING_URI`, `FRAUD_MODEL_URI`, `MLFLOW_MODEL_VERSION`
- [ ] Merge `feat/deploy-aks-staging` → `staging` branch to trigger `deploy-staging.yml`
- [ ] Verify live `/predict/fraud` endpoint responds

## Phase 3 — Monitoring & Production Pipeline

- [ ] Evidently AI drift detection (k3s CronJob)
- [ ] Prometheus scraping FastAPI + Evidently metrics
- [ ] Grafana dashboards: per-model + system overview
- [ ] Alertmanager rules + auto-rollback workflow
- [ ] Production deploy pipeline with canary logic (`deploy-prod.yml`)
- [ ] Loki log aggregation

## Phase 4 — Portfolio Site (moish.github.io)

- [ ] Create `moish.github.io` repo, scaffold static site
- [ ] Architecture page with MLOps platform diagram
- [ ] Home page with live API health badge linked to staging endpoint
- [ ] Deploy via GitHub Pages

## Phase 5 — Connect MLOps to Portfolio

- [ ] Models page: live demo calling `/predict/fraud` endpoint
- [ ] CI/CD page: link to GitHub Actions run history
- [ ] Embedded Grafana dashboards (public read-only panels)

## Phase 6 — Model Upgrades + Models 2 & 3 (Future)

- [ ] Replace placeholder fraud detection model with a properly trained, documented version
- [ ] DistilBERT sentiment analysis: training pipeline, `/predict/sentiment` endpoint, staging deploy
- [ ] Demand forecasting: LightGBM/Prophet pipeline, `/predict/forecast` endpoint, staging deploy
- [ ] All three models live in staging

---

## Infrastructure History

| Decision | Reason |
|---|---|
| AKS abandoned | K8s version EOL, LTS-only patch available, VM family quota denied, quota increase denied |
| Azure VM abandoned | Standard_B2s unavailable in eastus; no alternatives available across all regions and sizes |
| Terraform dropped | Single VM doesn't need IaC; existing Terraform modules remain in git history as portfolio evidence |
| Azure Key Vault dropped | K8s secrets created directly in deploy job via `kubectl create secret --dry-run \| kubectl apply` |
| AWS EC2 t2.micro chosen | Free tier eligible (12 months), k3s runs on 1GB with swap, ~$8.50/month after free tier |
| DVC Azure Blob kept | Already working, no quota issues, ~$1/month |

---

## Decisions to Revisit

1. **Serving:** FastAPI is sufficient for 3 models; consider Ray Serve if concurrency becomes a concern.
2. **MLflow UI:** If self-hosted MLflow looks poor on the portfolio site, mirror runs to a free W&B account for embedded links.
3. **Model quality:** Placeholder fraud detection model will be upgraded in Phase 5 — prioritise pipeline correctness now.
