# MigrationMesh Project Goal & Specifications

## ROLE
Principal Cloud Architect and Senior AI Engineer. Build **MigrationMesh**: an agentic AI orchestrator for cloud migration that is cloud-neutral, safe-by-design, and auditable.

## PROBLEM (Research-Backed)
Existing tools (AWS Transform, Azure Migrate, vendor agents) are biased toward their own cloud, have per-job limits, and need heavy human review. LLM agents are unreliable at sizing, data cutover, network/identity design and compliance. They hallucinate resources, produce non-deterministic plans, replace stateful resources destructively, over-inherit permissions, and leak topology via prompts. Evidence of net time saved is mixed.

## GOALS
1. **Cloud-neutral migration**: source (VMware / on-prem / AWS / Azure / GCP / Heroku) to any target, with a scored comparison of targets.
2. **Propose-approve-apply**: agents NEVER hold write credentials. Output is a diff, plan or report only. A deterministic pipeline applies approved changes.
3. **Shadow-run digital twin**: validate every plan in a sandbox, with auto-generated characterization tests for parity, before human approval.
4. **Safe cutover**: replication-lag monitoring, go/no-go scoring, rollback-first runbooks, deterministic one-click rollback.
5. **Immutable audit trail**: prompt, proposal, policy result, approver, applied diff, rollback, in a hash-chained log.
6. **Privacy**: redact secrets/identifiers before any LLM call; support self-hosted or local models for regulated environments.

## AGENTS (LangGraph supervisor + specialist workers, tools exposed via MCP)
- **Discovery Agent**: Ingest RVTools, CMDB, Terraform, repos, telemetry; build a dependency graph and inventory.
- **Strategy Agent**: 7R classification, wave planning, target scoring (cost, risk, lock-in, compliance); output includes confidence and open questions.
- **IaC Agent**: Generate Terraform/Kubernetes manifests using trusted modules; validate with terraform validate/plan; reject plans that destroy or replace stateful resources.
- **Policy Agent**: Evaluate plans against OPA/Rego policies (IAM least privilege, network exposure, encryption, residency).
- **Test Agent**: Generate characterization/parity tests from legacy behaviour.
- **Cutover Agent**: Build runbooks, monitor replication, compute go/no-go, execute only pre-approved steps.
- **FinOps/SRE Agent**: Rightsizing, drift detection, post-migration optimization.
- **Critic Agent**: Independently challenges every plan (hallucinated resources, deprecated APIs, missed dependencies) before it reaches a human.

## NON-NEGOTIABLE GUARDRAILS
- Read-only credentials for agents; just-in-time, scoped credentials only for the executor.
- Approval depth scales with blast radius (sandbox: auto; staging: 1 approver; prod: 2 approvers + change window).
- Plan-before-apply; block any destructive diff on stateful resources.
- Every agent output carries sources, assumptions and a confidence score. Low confidence forces human review.
- Budget, rate and step limits on all agent loops.

## TECH STACK
Python 3.12+, FastAPI, LangGraph, MCP servers, Temporal (durable workflows), Terraform + OPA, PostgreSQL (state + hash-chained audit), LocalStack / Azurite ephemeral sandboxes, React dashboard, OpenTelemetry, LiteLLM for model switching, Docker Compose.

## STUDY REFERENCES
awslabs migration-to-aws, Qovery/qovery-migration-ai-agent, konveyor/move2kube + Forklift + Konveyor AI, LukasNiessen/terrashark, pnnl/adept-agentic, github/awesome-copilot agents.

## DELIVERABLES
1. Architecture doc with component diagram and agent interaction flow.
2. Threat model (prompt injection, credential misuse, hallucinated destructive changes, data leakage) with mitigations.
3. Phased roadmap with milestones (P1 to P4).
4. Repo structure and an MVP slice (sample 3-tier app migrated to AWS and Azure).
5. Evaluation plan: benchmark against human baseline on plan accuracy, hallucination rate, destructive-diff catches, time to plan, review-time cost (Net saving = generation time - review - remediation).
6. Demo script and README explaining limitations honestly.
