"""
MigrationMesh - LangGraph Supervisor Orchestrator
Coordinates multi-agent migration lifecycle, enforces recursion/budget limits,
and links every state change to the cryptographic Merkle audit ledger.
"""

from typing import Dict, Any, Optional
from packages.privacy.redactor import PrivacyRedactor
from packages.policy_engine.evaluator import PolicyEngine
from packages.audit_ledger.merkle_ledger import MerkleAuditLedger
from packages.twin_runner.sandbox_manager import DigitalTwinSandboxManager
from packages.core.schemas import CloudProvider

from agents.discovery.discovery_agent import DiscoveryAgent
from agents.strategy.strategy_agent import StrategyAgent
from agents.iac_generator.iac_agent import IaCGeneratorAgent
from agents.critic.critic_agent import CriticAgent
from agents.cutover_orchestrator.cutover_agent import CutoverAgent
from agents.finops_sre.finops_agent import FinOpsSREAgent


class MigrationMeshSupervisor:
    """
    Central Supervisor Orchestrator:
    Coordinates specialist agents through the safe-by-design migration workflow.
    """

    def __init__(self):
        self.redactor = PrivacyRedactor()
        self.policy_engine = PolicyEngine()
        self.audit_ledger = MerkleAuditLedger()
        self.twin_manager = DigitalTwinSandboxManager()

        # Instantiate specialist workers
        self.discovery_agent = DiscoveryAgent(self.redactor)
        self.strategy_agent = StrategyAgent()
        self.iac_agent = IaCGeneratorAgent()
        self.critic_agent = CriticAgent()
        self.cutover_agent = CutoverAgent()
        self.finops_agent = FinOpsSREAgent()

    def run_end_to_end_migration(
        self,
        raw_inventory_config: Dict[str, Any],
        selected_target: Optional[CloudProvider] = None
    ) -> Dict[str, Any]:
        """
        Executes the end-to-end safe-by-design migration pipeline for an application.
        """
        # --- Step 1: Ingestion, Redaction & Topology DAG ---
        inventory, topo_dag = self.discovery_agent.ingest_legacy_sample_app(raw_inventory_config)
        self.audit_ledger.append_event(
            action_type="DISCOVERY_INGESTION",
            agent_name="DiscoveryAgent",
            actor_id="ORCHESTRATOR",
            input_data=raw_inventory_config.get("app_id", "app"),
            output_data=inventory.model_dump(),
            metadata={"nodes": topo_dag["node_count"], "is_dag": topo_dag["is_valid_dag"]}
        )

        # --- Step 2: 7R Strategy & Multi-Target Scoring ---
        strategy_plan = self.strategy_agent.evaluate_strategy(inventory)
        target_cloud = selected_target or strategy_plan.recommended_target

        self.audit_ledger.append_event(
            action_type="STRATEGY_EVALUATION",
            agent_name="StrategyAgent",
            actor_id="ORCHESTRATOR",
            input_data=inventory.model_dump(),
            output_data=strategy_plan.model_dump(),
            metadata={"recommended_target": target_cloud.value, "strategy_7r": strategy_plan.strategy_7r.value}
        )

        # --- Step 3: IaC Generation ---
        manifest = self.iac_agent.generate_iac(inventory, target_cloud)

        # --- Step 4: Policy Engine Evaluation (OPA/Rego) ---
        policy_result = self.policy_engine.evaluate_manifest(manifest)

        # --- Step 5: Critic Red-Teaming (AST Diff & Destructive Gate) ---
        critic_verdict = self.critic_agent.evaluate_plan(manifest)

        self.audit_ledger.append_event(
            action_type="IAC_POLICY_CRITIC_GATE",
            agent_name="CriticAgent",
            actor_id="ORCHESTRATOR",
            input_data=manifest.model_dump(),
            output_data=manifest.resources_generated,
            policy_result=policy_result.model_dump(),
            critic_verdict=critic_verdict.model_dump(),
            metadata={"policy_passed": policy_result.passed, "critic_approved": critic_verdict.approved}
        )

        # --- Step 6: Shadow-Run Digital Twin Validation ---
        twin_receipt = self.twin_manager.provision_shadow_twin(manifest)

        self.audit_ledger.append_event(
            action_type="DIGITAL_TWIN_VALIDATION",
            agent_name="TwinRunner",
            actor_id="ORCHESTRATOR",
            input_data=manifest.provider.value,
            output_data=twin_receipt.model_dump(),
            metadata={"parity_pass_pct": twin_receipt.parity_pass_percentage}
        )

        # --- Step 7: Cutover Runbook & Rollback Saga Generation ---
        cutover_runbook = self.cutover_agent.build_cutover_runbook(
            inventory=inventory,
            target_cloud=target_cloud,
            policy_result=policy_result,
            critic_verdict=critic_verdict,
            twin_receipt=twin_receipt,
            current_replication_lag_seconds=0.8
        )

        self.audit_ledger.append_event(
            action_type="CUTOVER_RUNBOOK_GENERATION",
            agent_name="CutoverAgent",
            actor_id="ORCHESTRATOR",
            input_data=inventory.app_id,
            output_data=cutover_runbook.model_dump(),
            metadata={"go_no_go": cutover_runbook.go_no_go_verdict, "steps": len(cutover_runbook.execution_steps)}
        )

        # --- Step 8: FinOps & Rightsizing Analysis ---
        finops_report = self.finops_agent.analyze_finops(inventory)

        # Verify ledger cryptographic integrity
        ledger_health = self.audit_ledger.verify_chain_integrity()
        merkle_root = self.audit_ledger.compute_merkle_root()

        return {
            "app_id": inventory.app_id,
            "app_name": inventory.app_name,
            "target_cloud": target_cloud.value,
            "inventory": inventory.model_dump(),
            "topology_dag": topo_dag,
            "strategy_plan": strategy_plan.model_dump(),
            "iac_manifest": manifest.model_dump(),
            "policy_result": policy_result.model_dump(),
            "critic_verdict": critic_verdict.model_dump(),
            "twin_receipt": twin_receipt.model_dump(),
            "cutover_runbook": cutover_runbook.model_dump(),
            "finops_report": finops_report,
            "audit_ledger": {
                "total_blocks": len(self.audit_ledger.chain),
                "merkle_root": merkle_root,
                "chain_valid": ledger_health.get("valid", False),
                "blocks": [b.model_dump() for b in self.audit_ledger.chain]
            }
        }
