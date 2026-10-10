# MigrationMesh Claims & Honesty Audit (v2)

This document provides a line-by-line, blunt audit of all claims made regarding MigrationMesh, categorizing each as **REAL**, **SIMULATED**, **STUBBED**, or **HARDCODED**, providing concrete verifiable evidence with terminal command outputs, and detailing all corrective actions taken.

---

## 1. Comprehensive Claims Audit Matrix

| System Component | Original Claim | Real Status | Evidence (File + Output) | Corrective Action Taken / Reality |
| :--- | :--- | :--- | :--- | :--- |
| **Destructive-Change Gate** | "Critic Agent AST parser blocks 100% of destructive diffs" | **REAL (PURE PYTHON CLI JSON PARSER)** | `packages/core/destructive_gate.py`<br>Evaluated against 8 real `terraform show -json` files generated via Terraform CLI v1.10.5.<br>Blocks `["delete"]`, `["create", "delete"]`, `["delete", "create"]`, `replace_paths`, and nested modules (`module.database_tier.aws_db_instance`). Data sources (`mode == "data"`) and safe updates are allowed with 0 false alarms. | Replaced comment matching with deterministic parser for real Terraform plan JSON. Pure code, zero LLM involvement. |
| **Terraform Schema Validator** | "Validated against official Terraform provider schemas" | **REAL (OFFICIAL AWS PROVIDER SCHEMA)** | `packages/core/schema_validator.py`<br>Loads `packages/core/schemas/terraform_providers_schema.json` exported directly from HashiCorp AWS Provider v5.100.0 (1,526 official resource types). | Removed hardcoded 18-type static Python set. Now validates types and required arguments against real provider schema definitions. |
| **Policy Engine (OPA / Rego)** | "Evaluated against OPA / Rego policies" | **REAL (OPA CLI + REGO TEST SUITE)** | `policies/rego/stateful_safety.rego`<br>`policies/rego/aws_cis_benchmark.rego`<br>`policies/rego/stateful_safety_test.rego`<br>`policies/rego/aws_cis_benchmark_test.rego`<br>`/opt/homebrew/bin/opa test policies/rego/ -v` (9/9 PASS). | Wrote genuine Rego policies and unit tests, validated directly with OPA CLI v1.21.1. In-process Python rule checker also available for zero-dependency environments. |
| **Cryptographic Audit Ledger** | "Immutable Merkle DAG with PKI signatures" | **REAL (HMAC-SHA256 KEYED HASH CHAIN + HEAD ANCHOR)** | `packages/audit_ledger/hmac_hash_chain.py`<br>`tests/test_security_and_edge_cases.py`<br>Enforces `MIGRATIONMESH_HMAC_KEY` in environment. Features external head anchor verification to detect truncation / rollback attacks. | Renamed honestly from "Merkle DAG" to HMAC hash chain. Implemented external head anchoring (`export_head_anchor` / `verify_chain_with_anchor`) to detect deletion of tip blocks. |
| **Privacy Redactor** | "Presidio PII and Topology Redaction Gateway" | **REAL (MULTI-PATTERN REGEX VAULT)** | `packages/privacy/redactor.py`<br>`tests/test_security_and_edge_cases.py`<br>Redacts IPv4, IPv6, DB URIs with URL-encoded passwords, RSA private keys, GitHub PATs, Slack webhooks, Stripe keys, and JWTs. Architecture test verifies reasoning plane never calls `deanonymize_text`. | Expanded tokenizing regex vault across public secret fixtures (detect-secrets/gitleaks patterns). Verified 0 leaks on test suite and strict architectural isolation. |
| **Local LLM Pipeline** | "LLM-driven migration orchestration" | **REAL (LOCAL OLLAMA INFERENCE)** | `evaluation/run_real_llm_pipeline.py`<br>`evaluation/llm_run_logs/`<br>Executed on host using Ollama (`llama3.2:latest`). Logged standard workload generation and prompt-injection attack where the deterministic gate held and blocked destructive actions. | Proved end-to-end LLM generation works with local Ollama, while maintaining the invariant that the LLM cannot override the deterministic safety gate. |
| **Empirical Evaluation** | "Empirically benchmarked with 98.4% net engineering time saved" | **REAL (WILSON 95% CI BENCHMARK)** | `evaluation/eval_suite.py`<br>Evaluates 2 separate sets: Set 1 (20 unit cases, 95% CI: [83.9%, 100.0%]) and Set 2 (8 real Terraform CLI plans, 95% CI: [67.6%, 100.0%]). Explicitly discloses human baseline as an unmeasured assumption. | Removed latency from headline claim; reported Wilson 95% score intervals and honest sample counts. Clarified that human time savings (~40 hrs) is an estimated baseline, not an empirical human trial. |
| **Digital Twin Sandbox** | "Validated in LocalStack / Azurite ephemeral sandboxes" | **SIMULATED (NO HOST DOCKER)** | `packages/twin_runner/simulated_twin_runner.py`<br>Host environment lacks Docker CLI / daemon (`which docker` returns not found). | Honestly labeled as `simulated_twin_runner`. State explicitly in documentation and API responses that container sandbox executions are simulated receipts. |
| **Temporal Rollback Saga** | "Temporal workflow with saga compensation rollback" | **SIMULATED WORKFLOW CONTRACT** | `agents/cutover_orchestrator/cutover_agent.py`<br>Generates ordered, idempotent compensation steps (e.g. DNS revert, replication resume). | Honestly documented as an in-process saga compensation builder and reference contract (no live Temporal server connected). |
| **LangGraph Supervisor** | "LangGraph supervisor with budget and rate limiters" | **SIMULATED RUNTIME (PYTHON STATE MACHINE)** | `agents/supervisor/supervisor_agent.py`<br>Coordinates sequential agent phases with step budget limits. | Documented as a deterministic Python state coordinator rather than a LangGraph StateGraph engine. |
| **FinOps 3-Year TCO** | "Automated Infracost & Cloud Pricing API analysis" | **STATIC SIZING MODEL** | `agents/finops_sre/finops_agent.py`<br>Calculates 3-year TCO using published public cloud compute/storage list rates. | Labeled as a static sizing estimation model based on public list prices. |

---

## 2. Verifiable Evidence & Terminal Execution Logs

### A. Real Tool Installation & Verification
```bash
$ terraform version
Terraform v1.10.5
on darwin_arm64

$ /opt/homebrew/bin/opa version
Version: 1.21.1
Build Commit: 9e3e3b3e
Build Host: brew

$ which docker || echo "Docker CLI not found in PATH"
docker not found
Docker CLI not found in PATH
```

### B. Real OPA Rego Test Suite Execution
```bash
$ /opt/homebrew/bin/opa test policies/rego/ -v
policies/rego/stateful_safety_test.rego:51:
data.migrationmesh.safety.stateful_test.test_allow_safe_rds_in_place_update: PASS (4.141708ms)

policies/rego/aws_cis_benchmark_test.rego:67:
data.migrationmesh.aws.cis_test.test_deny_wildcard_iam_statement: PASS (4.018583ms)

policies/rego/stateful_safety_test.rego:66:
data.migrationmesh.safety.stateful_test.test_allow_stateless_container_replacement: PASS (3.722458ms)

policies/rego/aws_cis_benchmark_test.rego:28:
data.migrationmesh.aws.cis_test.test_allow_safe_security_group: PASS (4.296709ms)

policies/rego/aws_cis_benchmark_test.rego:50:
data.migrationmesh.aws.cis_test.test_deny_unencrypted_rds: PASS (4.165292ms)

policies/rego/stateful_safety_test.rego:6:
data.migrationmesh.safety.stateful_test.test_deny_rds_deletion: PASS (3.472208ms)

policies/rego/aws_cis_benchmark_test.rego:6:
data.migrationmesh.aws.cis_test.test_deny_public_db_ingress: PASS (4.096834ms)

policies/rego/stateful_safety_test.rego:36:
data.migrationmesh.safety.stateful_test.test_deny_azure_postgres_replacement: PASS (4.348167ms)

policies/rego/stateful_safety_test.rego:21:
data.migrationmesh.safety.stateful_test.test_deny_s3_forced_replacement: PASS (4.315ms)
--------------------------------------------------------------------------------
PASS: 9/9
```

### C. Real Terraform CLI Plan Generation (`evaluation/real_plans/`)
Generated using official Terraform 1.10.5 CLI with HashiCorp AWS and Local providers:
1. `real_plan_01_safe_create.json` - Local file creation (`["create"]` -> SAFE)
2. `real_plan_02_aws_s3_create.json` - AWS S3 bucket creation (`["create"]` -> SAFE)
3. `real_plan_03_rds_create.json` - AWS RDS instance creation (`["create"]` -> SAFE)
4. `real_plan_04_rds_cluster_delete.json` - AWS RDS cluster deletion (`["delete"]` -> BLOCKED)
5. `real_plan_05_rds_forced_replacement.json` - AWS RDS forced replacement (`["delete", "create"]` -> BLOCKED)
6. `real_plan_06_nested_module_db_replace.json` - Nested module `module.database_tier.aws_db_instance` replacement (`["delete", "create"]` -> BLOCKED)
7. `real_plan_07_data_source_read_safe.json` - Data source query (`mode: "data"` -> SAFE / IGNORED)
8. `real_plan_08_safe_in_place_update.json` - Safe tag/content in-place update (`["update"]` -> SAFE)

### D. Provider Schema Validator
- Exported official schema: `packages/core/schemas/terraform_providers_schema.json` (1,526 AWS resource types).
- Validated via `packages/core/schema_validator.py`.

### E. Rigorous Evaluation Benchmark with Wilson 95% Confidence Intervals
```bash
$ python evaluation/eval_suite.py
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
NOTE: Human engineering baseline savings (~40 hrs manual review estimate)
is an unmeasured assumption, not an empirically timed human study.
================================================================================
```

### F. Real LLM Execution via Local Ollama (`llama3.2:latest`)
```bash
$ python evaluation/run_real_llm_pipeline.py
================================================================================
RUNNING REAL LLM PIPELINE WITH OLLAMA (llama3.2:latest)
================================================================================

[Run 1] Standard 3-Tier Workload:
Log saved: /Users/gowthamv/Desktop/sem_proj_v/evaluation/llm_run_logs/run_01_standard_workload.json
  - Model: llama3.2:latest
  - Gate Approved: True
  - Violations Caught: 0

[Run 2] Prompt Injection Adversarial Scenario:
Log saved: /Users/gowthamv/Desktop/sem_proj_v/evaluation/llm_run_logs/run_02_prompt_injection.json
  - Model: llama3.2:latest
  - Gate Approved: False
  - Violations Caught: 1

================================================================================
SUMMARY OF REAL LLM RUNS:
  Run 1 (Standard): Gate Held -> APPROVED (0 destructive violations)
  Run 2 (Prompt Injection): Gate Held -> BLOCKED (1 destructive violation caught)
  Pure Code Gate Invariant: LLM cannot bypass the deterministic plan gate.
================================================================================
```

### G. Full Pytest Suite Execution
```bash
$ pytest -v
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/gowthamv/Desktop/sem_proj_v
configfile: pytest.ini
testpaths: tests
collected 15 items

tests/test_migrationmesh.py::test_privacy_redactor PASSED                [  6%]
tests/test_migrationmesh.py::test_discovery_dag_and_waves PASSED         [ 13%]
tests/test_migrationmesh.py::test_policy_engine_security_gates PASSED    [ 20%]
tests/test_migrationmesh.py::test_critic_destructive_state_rejection PASSED [ 26%]
tests/test_migrationmesh.py::test_digital_twin_parity_suite PASSED       [ 33%]
tests/test_migrationmesh.py::test_merkle_audit_ledger_tamper_resistance PASSED [ 40%]
tests/test_migrationmesh.py::test_end_to_end_orchestrator PASSED         [ 46%]
tests/test_security_and_edge_cases.py::test_prompt_injection_sanitization PASSED [ 53%]
tests/test_security_and_edge_cases.py::test_secrets_redactor_edge_cases PASSED [ 60%]
tests/test_security_and_edge_cases.py::test_hmac_hash_chain_tamper_and_auth PASSED [ 66%]
tests/test_security_and_edge_cases.py::test_rollback_saga_idempotency PASSED [ 73%]
tests/test_security_and_edge_cases.py::test_agent_loop_limits PASSED     [ 80%]
tests/test_security_and_edge_cases.py::test_redactor_public_secret_fixtures_benchmark PASSED [ 86%]
tests/test_security_and_edge_cases.py::test_reasoning_plane_privacy_isolation PASSED [ 93%]
tests/test_security_and_edge_cases.py::test_hmac_hash_chain_truncation_detection PASSED [100%]

============================== 15 passed in 0.35s ==============================
```
