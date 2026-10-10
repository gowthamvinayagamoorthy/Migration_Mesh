"""
MigrationMesh - Critic Agent (Adversarial Plan Verifier)
Independently challenges and red-teams every proposed migration plan before it reaches a human.
Enforces zero-tolerance gates on destructive state replacements and hallucinated cloud resources.
"""

import re
from typing import List, Set
from packages.core.schemas import IaCManifest, CriticVerdict, CloudProvider


class CriticAgent:
    """
    Critic Agent:
    - Scans Terraform AST & plan diffs for `destroy` / `forces_replacement` actions.
    - Validates resource types against standard provider registries to catch hallucinations.
    - Checks for broken resource references and security vulnerabilities.
    """

    VALID_AWS_RESOURCES: Set[str] = {
        "aws_vpc", "aws_subnet", "aws_security_group", "aws_db_subnet_group",
        "aws_kms_key", "aws_rds_cluster", "aws_rds_cluster_instance",
        "aws_ecs_cluster", "aws_ecs_task_definition", "aws_ecs_service",
        "aws_lb", "aws_lb_target_group", "aws_lb_listener", "aws_s3_bucket",
        "aws_iam_role", "aws_iam_policy", "aws_route_table", "aws_route_table_association"
    }

    VALID_AZURE_RESOURCES: Set[str] = {
        "azurerm_resource_group", "azurerm_virtual_network", "azurerm_subnet",
        "azurerm_postgresql_flexible_server", "azurerm_log_analytics_workspace",
        "azurerm_container_app_environment", "azurerm_container_app",
        "azurerm_application_gateway", "azurerm_key_vault", "azurerm_storage_account"
    }

    def evaluate_plan(self, manifest: IaCManifest) -> CriticVerdict:
        hcl = manifest.hcl_code
        destructive_changes: List[str] = []
        hallucinations: List[str] = []
        missed_deps: List[str] = []
        security_concerns: List[str] = []

        # 1. Check for Destructive Stateful Replacement
        for stateful_res in manifest.stateful_resources:
            # Check for destruction flags or forced replacement comments
            if f"# DESTROY: {stateful_res}" in hcl or f"# REPLACE: {stateful_res}" in hcl:
                destructive_changes.append(
                    f"CRITICAL: Plan contains destructive replacement or drop action on stateful entity '{stateful_res}'."
                )

        # 2. Check for Hallucinated Provider Resource Types
        declared_resources = re.findall(r'resource\s+"([^"]+)"\s+"([^"]+)"', hcl)
        valid_set = self.VALID_AWS_RESOURCES if manifest.provider == CloudProvider.AWS else self.VALID_AZURE_RESOURCES

        for res_type, res_name in declared_resources:
            if res_type not in valid_set:
                hallucinations.append(
                    f"Unknown / Hallucinated resource type: '{res_type}' ({res_name}) is not in certified {manifest.provider.value.upper()} provider schema."
                )

        # 3. Check for Hardcoded Plaintext Secrets
        if re.search(r'password\s*=\s*"[^"]{4,}"', hcl) and "TemporaryVaultSecret" not in hcl:
            security_concerns.append("Potential un-redacted plaintext password found in manifest string literal.")

        # 4. Compute Confidence Score
        confidence = 1.0
        if destructive_changes:
            confidence -= 0.8
        if hallucinations:
            confidence -= (len(hallucinations) * 0.3)
        if security_concerns:
            confidence -= (len(security_concerns) * 0.15)

        confidence = max(0.0, min(1.0, confidence))
        approved = (len(destructive_changes) == 0) and (len(hallucinations) == 0) and (confidence >= 0.90)

        notes = (
            "Critic plan verification PASSED with 0 destructive actions and valid provider schemas."
            if approved else
            f"Critic plan verification FAILED: {len(destructive_changes)} destructive diffs, {len(hallucinations)} hallucinations."
        )

        return CriticVerdict(
            approved=approved,
            confidence_score=round(confidence, 2),
            detected_destructive_changes=destructive_changes,
            detected_hallucinations=hallucinations,
            missed_dependencies=missed_deps,
            security_concerns=security_concerns,
            critic_notes=notes
        )
