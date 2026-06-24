# MLOps Platform — Project Plan

## Overview

Production-grade MLOps platform built on Azure demonstrating end-to-end machine learning engineering: training, experiment tracking, containerized deployment on Kubernetes, model monitoring, and automated rollback. Built as a portfolio project for technical and non-technical audiences via a showcase site at monish.io.

**Timeline:** 3–4 months (16 weeks)
**Infrastructure:** Azure Student tier (~$100 credit), cost-guarded

---

## The Three Models

| # | Model | Domain | Framework | Dataset |
|---|-------|--------|-----------|---------|
| 1 | **Fraud Detection** | Tabular / Classification | XGBoost + scikit-learn | Kaggle Credit Card Fraud |
| 2 | **Sentiment Analysis** | NLP / Text Classification | DistilBERT (HuggingFace) | IMDB / Twitter dataset |
| 3 | **Demand Forecasting** | Time Series / Regression | LightGBM + Prophet | Open retail/energy dataset |

Each model has its own training script, evaluation script, DVC-tracked data, Dockerfile, and MLflow experiment namespace.

---

## Tech Stack

| Category | Tool | Rationale |
|---|---|---|
| Source control | GitHub (public monorepo) | Portfolio visibility, free Actions minutes |
| CI/CD | GitHub Actions | Industry standard, free for public repos |
| Experiment tracking | MLflow (self-hosted in AKS) | Open-source, shows infra ownership |
| Model registry | MLflow Model Registry | Co-located with tracking server |
| Data versioning | DVC + Azure Blob Storage | Industry standard, reproducibility |
| ML frameworks | scikit-learn, XGBoost, HuggingFace Transformers, LightGBM, Prophet | Breadth showcase |
| Model serving | FastAPI + Uvicorn | REST API, industry standard |
| Containerization | Docker + Docker Compose (local dev) | Consistent environments |
| Container registry | GitHub Container Registry (GHCR) | Free, integrated with Actions |
| Orchestration | AKS — 1-node Standard_B2s, cost-guarded | Real Kubernetes |
| IaC | Terraform (Azure provider) | Transferable, employer-recognizable |
| Monitoring / Drift | Evidently AI | Open-source, purpose-built for ML drift |
| Metrics | Prometheus + Grafana | Industry standard observability |
| Logging | Grafana Loki | Lightweight, integrates with Grafana |
| Secrets | Azure Key Vault | Azure-native, security awareness |
| Portfolio site | Next.js on Vercel + monish.io | Free hosting, live model demos |

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
│   ├── sentiment-analysis/     # Same structure
│   └── demand-forecasting/     # Same structure
├── serving/
│   ├── api/                    # FastAPI app (all 3 model routes)
│   ├── Dockerfile
│   └── k8s/                    # Deployment, Service, HPA, Ingress manifests
├── monitoring/
│   ├── evidently/              # Drift detection configs + reference datasets
│   ├── prometheus/             # prometheus.yml, alert rules
│   └── grafana/                # Dashboard JSON exports
├── infra/
│   ├── terraform/
│   │   ├── modules/            # aks, keyvault, storage (reusable)
│   │   └── environments/
│   │       ├── staging/
│   │       └── production/
│   └── scripts/                # bootstrap, teardown helpers
├── .github/
│   └── workflows/
│       ├── ci.yml              # Lint, type-check, unit tests (every PR)
│       ├── train.yml           # Re-train on data/code change
│       ├── deploy-dev.yml      # On-demand deploy to dev namespace
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

| Branch | AKS Namespace | Image Tag | Trigger |
|---|---|---|---|
| `feature/*` | none (CI only) | — | PR open / push |
| `develop` | `dev` (on-demand) | `dev-<sha>` | merge to develop |
| `staging` | `staging` | `staging-<sha>` | PR: develop → staging merged |
| `main` | `production` | `prod-<sha>` | PR: staging → main merged (canary) |
| `hotfix/*` | fast-path to production | `hotfix-<sha>` | merge to main + backmerge to develop |

**Branch protection (all long-lived branches):** no direct pushes, required status checks, PR-only merges.

**Hotfix rule:** Every hotfix merged to `main` must be backmerged to `develop`. A GitHub Actions step automatically opens the backmerge PR and fails loudly on conflicts.

### Pipeline Stages

**PR to `develop` (`ci.yml`):** Lint (ruff), type-check (mypy), unit tests (pytest), Docker build smoke test.

**Merge to `develop` (`deploy-dev.yml`, on-demand):** Build + push to GHCR (`dev-<sha>`), deploy to AKS `dev` namespace.

**develop → staging merged (`deploy-staging.yml`):**
1. Build + push to GHCR (`staging-<sha>`)
2. Integration tests
3. Deploy to AKS `staging` namespace
4. Model validation smoke tests (latency, accuracy threshold)
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

## Azure Cost Management

| Resource | SKU | Est. Cost/Month |
|---|---|---|
| AKS node pool | 1× Standard_B2s (auto-scale to 0 at night) | ~$30 |
| Azure Blob Storage | LRS, ~10 GB | ~$1 |
| Azure Key Vault | Standard | ~$0.50 |
| Public IP + Load Balancer | Basic | ~$4 |
| Egress / misc | — | ~$5 |
| **Total** | | **~$40–45/month** |

- Azure budget alerts at $50 (warning) and $80 (stop email)
- AKS scales to 0 nightly via scheduled GitHub Action
- GHCR instead of ACR (saves ~$5/month)
- MLflow runs inside AKS (no separate VM cost)

---

## Portfolio Showcase Site (monish.io)

Separate repo: `mlops-portfolio-site` — Next.js on Vercel, custom domain.

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

## Phased Timeline

### Phase 1 — Foundation (Weeks 1–3) ✓
- [x] GitHub repo, branch protection, repo structure scaffold
- [x] Terraform: AKS (1 node), Azure Blob Storage, Key Vault — config written + plan validated; `apply` deferred to save costs until Phase 2
- [x] MLflow server deployed locally via Docker Compose; AKS deployment deferred to Phase 2 (requires `terraform apply`)
- [x] Docker Compose local dev stack (api + mlflow + prometheus + grafana)
- [x] DVC initialized, Azure Blob as remote

### Phase 2 — Model 1: Fraud Detection (Weeks 4–5)
- [ ] Training script with MLflow tracking (params, metrics, artifacts)
- [ ] DVC pipeline: data → features → train → evaluate
- [ ] Model registered in MLflow Model Registry
- [ ] FastAPI endpoint `/predict/fraud`
- [ ] GitHub Actions CI (lint, test, build)
- [ ] Deploy to AKS staging

### Phase 3 — Model 2: Sentiment Analysis (Weeks 6–7)
- [ ] DistilBERT fine-tuning script with MLflow
- [ ] FastAPI endpoint `/predict/sentiment`
- [ ] Deploy to AKS staging alongside Model 1
- [ ] Full CI/CD pipeline for Model 2

### Phase 4 — Model 3: Demand Forecasting (Weeks 8–9)
- [ ] LightGBM/Prophet training pipeline
- [ ] FastAPI endpoint `/predict/forecast`
- [ ] All three models live in staging
- [ ] Production deploy pipeline with canary logic

### Phase 5 — Monitoring & Observability (Weeks 10–11)
- [ ] Evidently AI drift detection (AKS CronJob)
- [ ] Prometheus scraping FastAPI + Evidently metrics
- [ ] Grafana dashboards: per-model + system overview
- [ ] Alertmanager rules + auto-rollback workflow
- [ ] Loki log aggregation

### Phase 6 — Portfolio Site (Weeks 12–13)
- [ ] Next.js site scaffold, Vercel deployment
- [ ] Architecture diagram, live model demos, embedded Grafana panels
- [ ] monish.io domain configured on Vercel

### Phase 7 — Polish & Documentation (Weeks 14–16)
- [ ] ADRs for key decisions
- [ ] README with architecture overview and quickstart
- [ ] Demo videos / GIFs for GitHub README
- [ ] Cost audit, security review
- [ ] Blog-style writeups for "Behind the Scenes" page

---

## Verification Checklist

- [x] `make dev` brings up full local stack (Docker Compose)
- [ ] `terraform plan` on staging environment shows no drift
- [ ] Feature branch push triggers CI (lint + tests)
- [ ] Merge to `develop` builds image; dev endpoint returns predictions
- [ ] develop → staging PR triggers staging deploy and model validation
- [ ] staging → main PR triggers canary deploy; Grafana shows traffic split
- [ ] Manually shifted dataset triggers Evidently alert → auto-rollback
- [ ] monish.io/models returns live predictions from production API

---

## Decisions to Revisit

1. **Serving:** FastAPI is sufficient for 3 models; consider Ray Serve if concurrency becomes a concern.
2. **AKS fallback:** If Azure credits run low, pivot to Azure Container Apps for Model 3.
3. **MLflow UI:** If self-hosted MLflow looks poor on the portfolio site, mirror runs to a free W&B account for embedded links.
