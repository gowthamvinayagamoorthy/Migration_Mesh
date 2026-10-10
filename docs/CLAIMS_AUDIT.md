# MigrationMesh Claims & Honesty Audit

This document provides a line-by-line, blunt audit of all claims made in previous iterations of MigrationMesh, categorizing each as **REAL**, **SIMULATED**, **STUBBED**, or **HARDCODED**, providing concrete evidence, and detailing the exact corrective actions taken.

---

## 1. Comprehensive Claims Audit Matrix

| System Component | Previous Claim | Real Status | Evidence (File + Output) | Required Fix / Real Implementation |
| :--- | :--- | :--- | :--- | :--- |
| **Destructive-Change Gate** | "Critic Agent AST parser blocks 100% of destructive diffs" | **HARDCODED / STRING MATCH** | Looked for `# DESTROY:` string comments in `agents/critic/critic_agent.py`<br>`# DESTROY: {stateful_res} in hcl` | Implement a pure deterministic Python parser for real `terraform show -json` plan JSON format (`resource_changes[].change.actions`). Test with real plan JSON structures (both destructive and safe plans to test false-positives). Pure code, zero LLM. |
| **Hallucination Detection** | "Validated against official Terraform provider schemas" | **HARDCODED LIST** | `critic_agent.py` had a static Python `set` of 18 AWS and 10 Azure resource type strings.<br>`VALID_AWS_RESOURCES = {"aws_vpc", ...}` | Parse structured Terraform provider schema registry JSON and validate resource types and attributes. |
| **Policy Engine (OPA / Rego)** | "Evaluated against OPA / Rego policies" | **SIMULATED (PYTHON REGEX)** | `packages/policy_engine/evaluator.py` used regex matching in Python.<br>`re.search(r'cidr_blocks...', hcl)`<br>OPA CLI was not installed or invoked. | Rename module to `python_policy_checker`. Provide real `.rego` policy files in `policies/rego/`. Honestly document that rule evaluation runs in-process via Python AST/structure checks. |
| **Cryptographic Audit Ledger** | "Immutable Merkle DAG with PKI signatures" | **SIMULATED (HASH CHAIN)** | `packages/audit_ledger/merkle_ledger.py` was a simple SHA-256 hash list with a naive Merkle root calculation and optional unsigned string field. | Rename honestly to `hmac_hash_chain`. Enforce real HMAC-SHA256 cryptographic signatures using a mandatory secret key from `MIGRATIONMESH_HMAC_KEY` (fail if missing). |
| **Digital Twin Sandbox** | "Validated in LocalStack / Azurite ephemeral sandboxes" | **SIMULATED** | `packages/twin_runner/sandbox_manager.py` returned hardcoded dictionary payloads with a `time.sleep(1.25)` delay. Docker was not running on host. | Rename to `simulated_twin_runner`. State explicitly in README and UI that sandbox receipts are simulated assertions due to missing local Docker runtime. |
| **Temporal Rollback Saga** | "Temporal workflow with saga compensation rollback" | **SIMULATED / STUB** | `apps/api/main.py` returned hardcoded mock JSON with a 1.8s synthetic latency. No Temporal server existed. | Rename to `simulated_saga_rollback_runner`. Document as a workflow reference contract. |
| **LangGraph Supervisor** | "LangGraph supervisor with budget and rate limiters" | **SIMULATED** | `agents/supervisor/supervisor_agent.py` was a synchronous Python class executing sequential agent methods without LangGraph StateGraph runtime. | Document orchestrator honestly as a deterministic Python state coordinator with modular agent dispatch. |
| **FinOps 3-Year TCO** | "Automated Infracost & Cloud Pricing API analysis" | **HARDCODED FORMULA** | `agents/finops_sre/finops_agent.py` used static linear multiplication formulas (`cpu * 18.0 + ram * 4.5`). | Label as a static sizing estimation model based on published public cloud list prices. |
| **Privacy Redactor** | "Presidio PII and Topology Redaction Gateway" | **REAL (REGEX-BASED)** | `packages/privacy/redactor.py` successfully tokenized IPv4 and standard DB passwords, but missed IPv6 and base64 tokens. | Expand regex tokenization to cover IPv6, base64 keys, and URL-encoded credentials. Add adversarial test suite. |
| **Empirical Benchmarks (98.4% Saved)** | "Empirically benchmarked with 98.4% net engineering time saved" | **SIMULATED BENCHMARK** | `evaluation/eval_suite.py` evaluated 25 synthetic instances in a CPU loop; 40-hour human baseline was an unverified assumption. | Rebuild evaluation harness to evaluate a real, held-out set of 20 independent Terraform Plan JSON cases, reporting True Positives, False Positives, False Negatives, Precision, Recall, and real elapsed timers. |

---

## 2. Real vs Simulated Inventory Summary

```
+---------------------------------------------------------------------------------------------------+
| COMPONENT                  | IMPLEMENTATION REALITY                                               |
+----------------------------+----------------------------------------------------------------------+
| Destructive-Change Gate    | REAL: Pure deterministic JSON parser for `terraform show -json`      |
| Hallucination Detector     | REAL: Terraform Provider Schema JSON validation                      |
| Policy Engine              | REAL (Python Rule Checker) + Real `.rego` files for OPA CLI reference|
| Audit Ledger               | REAL: HMAC-SHA256 Keyed Hash Chain (enforces secret key in env)      |
| Privacy Redactor           | REAL: Bidirectional Tokenizing Regex Vault (IPv4, IPv6, Secrets)      |
| Evaluation Suite           | REAL: Held-out test set reporting FP, FN, Precision, and Recall      |
+----------------------------+----------------------------------------------------------------------+
| Digital Twin Sandbox       | SIMULATED: Emulated container execution receipt (no host Docker)     |
| Temporal Workflow          | SIMULATED: In-process compensation step builder (no live Temporal)   |
| Cloud Pricing FinOps       | STATIC MODEL: Formulaic estimation from public list prices           |
+---------------------------------------------------------------------------------------------------+
```
