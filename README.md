# MigrationMesh: Safe-by-Design Cloud Migration Orchestrator

[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.143-009688.svg)](https://fastapi.tiangolo.com)
[![Pytest Suite](https://img.shields.io/badge/pytest-15%20passed%20(100%25)-success.svg)](file:///Users/gowthamv/Desktop/sem_proj_v/tests)
[![OPA Rego Tests](https://img.shields.io/badge/OPA%20Tests-9%2F9%20passed-brightgreen.svg)](file:///Users/gowthamv/Desktop/sem_proj_v/policies/rego)
[![Real Terraform Plans](https://img.shields.io/badge/Real%20Terraform%20Plans-8%2F8%20verified-success.svg)](file:///Users/gowthamv/Desktop/sem_proj_v/evaluation/real_plans)

---

## 1. Project Overview & Honesty Disclosure

MigrationMesh is an open-source, safe-by-design orchestrator designed for multi-cloud migration planning, deterministic safety gating, and auditable approval pipelines.

### Transparency Matrix: Real Implementations vs Simulated Components

| Component | Reality Status | Implementation Details |
| :--- | :--- | :--- |
| **Destructive-Change Gate** | **REAL** | Pure Python deterministic parser for `terraform show -json` plan format. Evaluated against 8 real Terraform CLI plans (`evaluation/real_plans/`). Blocks any delete or forced replacement actions (`["delete"]`, `["create", "delete"]`, `["delete", "create"]`, and `replace_paths`) on stateful resources (RDS, Aurora, DynamoDB, S3, EBS, Azure Postgres Flexible, KeyVault). Zero LLM involvement in gating decisions. |
| **Provider Schema Validator** | **REAL** | Validates resource types and configurations against official HashiCorp AWS Provider v5.100.0 schema definitions (`1,526` official types in `packages/core/schemas/terraform_providers_schema.json`). |
| **Policy Engine (OPA / Rego)** | **REAL** | Rego policies in `policies/rego/` verified with official OPA CLI (`opa test policies/rego/ -v` -> 9/9 PASS). Also includes in-process Python rule checker for zero-dependency environments. |
| **Audit Ledger** | **REAL** | SHA-256 linear hash chain where every block is authenticated via HMAC-SHA256 signatures using a mandatory secret key (`MIGRATIONMESH_HMAC_KEY`). Includes external head anchoring (`export_head_anchor` / `verify_chain_with_anchor`) to detect tip truncation and rollback attacks. |
| **Privacy Redaction Proxy** | **REAL** | Bidirectional tokenizing regex vault redacting IPv4, IPv6, URL-encoded DB passwords, RSA private keys, GitHub PATs, Slack webhooks, Stripe keys, and JWTs. Architecture tests enforce that reasoning plane agents never call `deanonymize_text`. |
| **Local LLM Pipeline** | **REAL** | Runs end-to-end multi-agent migration planning with local Ollama (`llama3.2:latest`). Verified under prompt-injection attacks: even if the LLM is instructed to drop safety checks, the deterministic gate blocks the plan. |
| **Digital Twin Sandbox** | **SIMULATED** | Emulated sandbox execution receipts with synthetic latency and parity assertions (host environment does not have a live Docker / LocalStack daemon). |
| **Temporal Rollback Saga** | **SIMULATED** | In-memory compensation step runner and reference contract (not connected to a live Temporal cluster). |
| **FinOps 3-Year TCO** | **STATIC MODEL** | Deterministic sizing cost model based on published public cloud list prices. |

---

## 2. Prior Art & Related Work

| System / Tool | Strengths | Known Limitations | What MigrationMesh Adds |
| :--- | :--- | :--- | :--- |
| **`awslabs/migration-to-aws`** | Enterprise inventory questionnaires, server normalization. | AWS-only bias; opaque sizing heuristics; mixes write actions with discovery. | Cloud-neutral multi-target scoring comparing AWS, Azure, GCP, and Kubernetes simultaneously. |
| **`Qovery/qovery-migration-ai-agent`** | Automated containerization of repos (Procfiles, Dockerfiles). | Lacks stateful resource destruction protection; direct cloud API mutations. | Pure code deterministic plan gate blocking stateful destruction before any human review. |
| **`konveyor/move2kube` + `Forklift`** | Deterministic AST-based source translation to Kubernetes CRDs. | Strict Kubernetes / OpenShift bias; steep operational complexity for standard PaaS targets. | Flexible multi-target architecture supporting IaaS, CaaS (ECS/ACA), and managed PaaS. |
| **`LukasNiessen/terrashark`** | Deep graph and AST visualization of Terraform plan JSON. | Manual post-hoc inspection tool without automated blocking or remediation loops. | Automated programmatic gate integrated directly into the orchestrator pipeline. |
| **Vendor Tools (AWS Transform, Azure Migrate)** | Deep proprietary integrations for their own respective clouds. | Extreme vendor lock-in; per-job limits; opaque heuristic formulas. | Unbiased 5-dimensional quantitative decision matrix (Cost, Lock-in, Risk, Compliance, Complexity). |

---

## 3. System Architecture & Safety Invariants

```
+---------------------------------------------------------------------------------------------------+
|                                    MIGRATIONMESH SAFETY INVARIANTS                                |
+------------------------------------+----------------------------------+---------------------------+
| 1. DUAL-PLANE ISOLATION            | 2. DETERMINISTIC PLAN GATE       | 3. OPA / CIS BENCHMARKS   |
| Reasoning agents hold ZERO write   | Pure code parser blocks all      | Rego & Python checkers    |
| credentials. Emit diffs only.      | stateful deletions & replacements| enforce CIS benchmarks.   |
+------------------------------------+----------------------------------+---------------------------+
| 4. HMAC AUDIT HASH CHAIN           | 5. PRE-PROD PROMPT REDACTION     | 6. SAGA-BASED ROLLBACK    |
| SHA-256 hash chain with HMAC key   | Regex vault redacts IPv4, IPv6,  | Deterministic 1-click     |
| and external head anchor store.    | and credentials before LLM calls.| compensation runbook.     |
+------------------------------------+----------------------------------+---------------------------+
```

---

## 4. Empirical Evaluation Results

Evaluated on two distinct sets with **Wilson 95% Confidence Intervals**:

```
================================================================================
MIGRATIONMESH RIGOROUS EVALUATION REPORT
================================================================================
SET 1: Unit Cases (Handwritten) (N=20)
  - Accuracy:               20/20 (100.0%, 95% CI: [83.9%, 100.0%])
  - Detection Rate:         10/10 (100.0%, 95% CI: [72.2%, 100.0%])
  - False Positive Rate:    0/10 (0.0%)
  - False Negative Rate:    0/10 (0.0%)
--------------------------------------------------------------------------------
SET 2: Real Terraform CLI Plans (`terraform show -json`) (N=8)
  - Accuracy:               8/8 (100.0%, 95% CI: [67.6%, 100.0%])
  - Detection Rate:         3/3 (100.0%, 95% CI: [43.9%, 100.0%])
  - False Positive Rate:    0/5 (0.0%)
  - False Negative Rate:    0/3 (0.0%)
================================================================================
```

*Disclosure on Baseline*: Any comparison against human engineering hours (~40 hours for a 3-tier architecture) is an **estimated baseline assumption** and not an empirically timed human trial cohort.

---

## 5. Quickstart & Verification Commands

### 1. Environment Setup & Tests
```bash
# Activate virtual environment
source .venv/bin/activate

# Set mandatory HMAC key for audit ledger
export MIGRATIONMESH_HMAC_KEY="mesh-secret-key-2026"

# Run full pytest suite (15 unit, integration, and security tests)
pytest -v

# Run OPA Rego policy test suite
opa test policies/rego/ -v

# Run evaluation benchmark with Wilson 95% CIs
python evaluation/eval_suite.py

# Run real LLM pipeline with Ollama
python evaluation/run_real_llm_pipeline.py
```

### 2. Launch FastAPI Backend & Dashboard
```bash
# Terminal 1: Launch FastAPI backend server
uvicorn apps.api.main:app --host 0.0.0.0 --port 8000

# Terminal 2: Launch React dashboard
cd apps/dashboard
npm run dev
```

Visit **`http://localhost:5173`** to access the MigrationMesh console.

---

## 6. License

MigrationMesh is licensed under the [Apache License 2.0](LICENSE).
