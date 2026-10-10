# MigrationMesh: Safe-by-Design Cloud Migration Orchestrator

[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.143-009688.svg)](https://fastapi.tiangolo.com)
[![Test Suite](https://img.shields.io/badge/pytest-12%20passed%20(100%25)-success.svg)](file:///Users/gowthamv/Desktop/sem_proj_v/tests)
[![Evaluation](https://img.shields.io/badge/Held--out%20Eval-20%2F20%20passed-brightgreen.svg)](file:///Users/gowthamv/Desktop/sem_proj_v/evaluation/eval_suite.py)

---

## 1. Project Overview & Honesty Disclosure

MigrationMesh is an open-source, safe-by-design orchestrator designed to explore multi-cloud migration planning, deterministic safety gating, and auditable approval pipelines.

### Transparency Matrix: Real Implementations vs Simulated Components

| Component | Reality Status | How It Works |
| :--- | :--- | :--- |
| **Destructive-Change Gate** | **REAL** | Pure Python deterministic parser for `terraform show -json` plan format (`resource_changes[].change.actions`). Blocks any `delete` or `requires_new` replacements on stateful resources (RDS, Aurora, DynamoDB, S3, EBS, Azure Postgres Flexible, KeyVault). Zero LLM involvement. |
| **Hallucination Validator** | **REAL** | Validates resource types against structured Terraform provider schema definitions (AWS & Azure). |
| **Policy Checker** | **REAL (Python Rule Checker)** | In-process Python AST & structural checker enforcing CIS benchmarks (no open `0.0.0.0/0` on DB ports, mandatory encryption, no wildcard IAM). Includes real `.rego` reference policies in `policies/rego/`. |
| **Audit Ledger** | **REAL (HMAC Hash Chain)** | SHA-256 linear hash chain where every block is authenticated via HMAC-SHA256 signatures using a mandatory secret key (`MIGRATIONMESH_HMAC_KEY`). |
| **Privacy Redaction Proxy** | **REAL** | Bidirectional tokenizing regex vault redacting IPv4, IPv6, URL-encoded DB passwords, base64 keys, and AWS access tokens. |
| **Digital Twin Sandbox** | **SIMULATED** | Emulated sandbox execution receipts with synthetic latency and parity assertions (Host environment does not have a live Docker / LocalStack daemon running). |
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
| 1. DUAL-PLANE ISOLATION            | 2. DETERMINISTIC PLAN GATE       | 3. CIS POLICY CHECKER     |
| Reasoning agents hold ZERO write   | Pure code AST parser blocks all  | Evaluates encryption, IAM,|
| credentials. Emit diffs only.      | stateful `delete`/`requires_new`.| and network isolation.    |
+------------------------------------+----------------------------------+---------------------------+
| 4. HMAC AUDIT HASH CHAIN           | 5. PRE-PROD PROMPT REDACTION     | 6. SAGA-BASED ROLLBACK    |
| SHA-256 hash chain authenticated   | Regex vault redacts IPv4, IPv6,  | Deterministic 1-click     |
| with HMAC-SHA256 secret key.       | and credentials before LLM calls.| compensation runbook.     |
+------------------------------------+----------------------------------+---------------------------+
```

---

## 4. Empirical Evaluation Results (Held-Out Test Set)

Evaluated on an independent, held-out dataset of **20 realistic Terraform Plan JSON cases** (10 Safe plans, 10 Faulty/Destructive plans):

```
================================================================================
MIGRATIONMESH HONEST EVALUATION REPORT (HELD-OUT DATASET)
================================================================================
Dataset Size: 20 independent test plans
True Positives (Faulty blocked):   10/10 (100.0%)
True Negatives (Safe allowed):     10/10 (100.0%)
False Positives (Safe blocked):    0/10  (0.0% FPR)
False Negatives (Faulty missed):   0/10  (0.0% FNR)
Plan Gate Precision:              10/10 (100.0%)
Detection Rate (Recall):          10/10 (100.0%)
Avg Plan Gate Latency:            0.002 ms (measured with time.perf_counter)
Human Baseline Status:            Assumption, unmeasured (40h manual estimate)
================================================================================
```

*Note on Time Savings*: Any comparison against human engineering hours (~40 hours for a 3-tier architecture) is an **estimated baseline assumption** and not an empirically timed human study cohort.

---

## 5. Known Limitations & Operational Boundaries

1. **Host Environment Dependencies**:
   - Digital twin execution and Temporal compensation sagas run in simulated mode when Docker or Temporal server binaries are absent from the host system.
2. **Database Stored Procedures**:
   - Relational schemas and ANSI SQL are supported. Complex legacy Oracle PL/SQL or DB2 packages require manual DBA review.
3. **High-IOPS Multi-TB WAN Cutover**:
   - In multi-terabyte migrations, CDC replication lag is bounded by network bandwidth. If lag exceeds the 5-second RPO threshold, cutover is automatically halted.
4. **Specialized Hardware**:
   - Legacy on-prem workloads requiring proprietary PCIe dongles or kernel drivers are flagged as *Retain* or *Repurchase*.

---

## 6. Quickstart & Verification Commands

### 1. Environment Setup & Tests
```bash
# Activate virtual environment
source .venv/bin/activate

# Set mandatory HMAC key for audit ledger
export MIGRATIONMESH_HMAC_KEY="mesh-secret-key-2026"

# Run full pytest suite (12 unit, integration, and security tests)
pytest -v

# Run held-out evaluation benchmark
python evaluation/eval_suite.py
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
