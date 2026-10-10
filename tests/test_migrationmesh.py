"""
MigrationMesh - Unit & Integration Test Suite
Validates safety gates, privacy redaction, policy engine, digital twin,
merkle ledger tamper resistance, and multi-cloud orchestration.
"""

import pytest
from packages.privacy.redactor import PrivacyRedactor
from packages.policy_engine.evaluator import PolicyEngine
from packages.audit_ledger.merkle_ledger import MerkleAuditLedger
from packages.twin_runner.sandbox_manager import DigitalTwinSandboxManager
from packages.core.schemas import CloudProvider, IaCManifest, CanonicalInventory, SourceResource, ResourceType
from agents.discovery.discovery_agent import DiscoveryAgent
from agents.strategy.strategy_agent import StrategyAgent
from agents.iac_generator.iac_agent import IaCGeneratorAgent
from agents.critic.critic_agent import CriticAgent
from agents.cutover_orchestrator.cutover_agent import CutoverAgent
from agents.supervisor.supervisor_agent import MigrationMeshSupervisor


def test_privacy_redactor():
    redactor = PrivacyRedactor()
    raw_prompt = "Connect to db at 192.168.1.104 with password=SecretPassword123! using AKIAIOSFODNN7EXAMPLE"
    redacted, count = redactor.redact_text(raw_prompt)

    assert "192.168.1.104" not in redacted
    assert "SecretPassword123!" not in redacted
    assert "AKIAIOSFODNN7EXAMPLE" not in redacted
    assert "<IP_NODE_" in redacted
    assert "<SECRET_TOKEN_" in redacted
    assert "<AWS_KEY_" in redacted

    restored = redactor.deanonymize_text(redacted)
    assert restored == raw_prompt


def test_discovery_dag_and_waves():
    redactor = PrivacyRedactor()
    agent = DiscoveryAgent(redactor)

    inv = CanonicalInventory(
        app_id="test-app",
        app_name="Test App",
        resources=[
            SourceResource(id="web", name="Web", resource_type=ResourceType.VIRTUAL_MACHINE, dependencies=["api"]),
            SourceResource(id="api", name="API", resource_type=ResourceType.VIRTUAL_MACHINE, dependencies=["db"]),
            SourceResource(id="db", name="DB", resource_type=ResourceType.DATABASE, is_stateful=True, dependencies=[])
        ]
    )

    dag_info = agent.build_dependency_dag(inv)
    assert dag_info["is_valid_dag"] is True
    assert dag_info["detected_cycles"] == []
    assert len(dag_info["migration_waves"]) == 3
    # Wave 0 must be DB, Wave 1 must be API, Wave 2 must be Web
    assert dag_info["migration_waves"][0] == ["db"]
    assert dag_info["migration_waves"][1] == ["api"]
    assert dag_info["migration_waves"][2] == ["web"]


def test_policy_engine_security_gates():
    engine = PolicyEngine()

    bad_hcl = """
    resource "aws_security_group" "db_sg" {
      ingress {
        from_port = 5432
        to_port = 5432
        protocol = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
      }
    }
    resource "aws_iam_policy" "wildcard" {
      policy = jsonencode({ Action = "*" })
    }
    """

    manifest = IaCManifest(
        provider=CloudProvider.AWS,
        hcl_code=bad_hcl,
        validation_status="valid"
    )

    result = engine.evaluate_manifest(manifest)
    assert result.passed is False
    assert any(v.rule_id == "CIS-SEC-002" for v in result.violations)
    assert any(v.rule_id == "CIS-IAM-003" for v in result.violations)


def test_critic_destructive_state_rejection():
    critic = CriticAgent()

    mutated_hcl = """
    resource "aws_rds_cluster" "aurora_postgres" {
      cluster_identifier = "production-db"
      # DESTROY: aws_rds_cluster.aurora_postgres
    }
    """

    manifest = IaCManifest(
        provider=CloudProvider.AWS,
        hcl_code=mutated_hcl,
        stateful_resources=["aws_rds_cluster.aurora_postgres"],
        validation_status="valid"
    )

    verdict = critic.evaluate_plan(manifest)
    assert verdict.approved is False
    assert len(verdict.detected_destructive_changes) > 0
    assert verdict.confidence_score < 0.90


def test_digital_twin_parity_suite():
    manager = DigitalTwinSandboxManager()
    manifest = IaCManifest(
        provider=CloudProvider.AWS,
        hcl_code="resource 'aws_vpc' 'mesh' {}",
        validation_status="valid"
    )

    receipt = manager.provision_shadow_twin(manifest)
    assert receipt.provisioned_successfully is True
    assert receipt.parity_pass_percentage == 100.0
    assert receipt.parity_tests_passed == receipt.parity_tests_total
    assert len(receipt.test_results) >= 5


def test_merkle_audit_ledger_tamper_resistance():
    ledger = MerkleAuditLedger()

    # Append events
    b1 = ledger.append_event("DISCOVERY", "DiscoveryAgent", "SYSTEM", "input1", "output1")
    b2 = ledger.append_event("STRATEGY", "StrategyAgent", "SYSTEM", "input2", "output2")

    # Initial check must be valid
    initial_check = ledger.verify_chain_integrity()
    assert initial_check["valid"] is True
    assert initial_check["total_blocks"] == 3  # Genesis + 2 events

    # Intentionally tamper with block 1 output digest
    ledger.chain[1].output_digest = "tampered_digest_value_1234567890"

    # Integrity verification must fail and identify exact block
    tampered_check = ledger.verify_chain_integrity()
    assert tampered_check["valid"] is False
    assert tampered_check["tamper_detected_at_block"] == 1


def test_end_to_end_orchestrator():
    supervisor = MigrationMeshSupervisor()

    sample_config = {
        "app_id": "app-test-e2e",
        "app_name": "Test Payment Gateway",
        "resources": [
            {
                "id": "vm-web",
                "name": "nginx-web",
                "resource_type": "virtual_machine",
                "cpu_cores": 2,
                "ram_gb": 4.0,
                "storage_gb": 40.0,
                "open_ports": [80, 443],
                "dependencies": ["vm-db"],
                "is_stateful": False
            },
            {
                "id": "vm-db",
                "name": "postgres-db",
                "resource_type": "database",
                "cpu_cores": 4,
                "ram_gb": 16.0,
                "storage_gb": 200.0,
                "open_ports": [5432],
                "dependencies": [],
                "is_stateful": True
            }
        ]
    }

    # Run for AWS
    res_aws = supervisor.run_end_to_end_migration(sample_config, selected_target=CloudProvider.AWS)
    assert res_aws["target_cloud"] == "aws"
    assert res_aws["policy_result"]["passed"] is True
    assert res_aws["critic_verdict"]["approved"] is True
    assert res_aws["twin_receipt"]["parity_pass_percentage"] == 100.0
    assert res_aws["cutover_runbook"]["go_no_go_verdict"] == "GO"
    assert res_aws["audit_ledger"]["chain_valid"] is True

    # Run for Azure
    res_azure = supervisor.run_end_to_end_migration(sample_config, selected_target=CloudProvider.AZURE)
    assert res_azure["target_cloud"] == "azure"
    assert res_azure["policy_result"]["passed"] is True
    assert res_azure["critic_verdict"]["approved"] is True
    assert res_azure["twin_receipt"]["parity_pass_percentage"] == 100.0
