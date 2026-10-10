"""
MigrationMesh - Deterministic Destructive-Change Gate
Pure deterministic parser for `terraform show -json` plan output.
Zero LLM involvement in destructive change gating decisions.
"""

import json
from typing import Dict, Any, List, Set, Tuple


class TerraformPlanDestructiveGate:
    """
    Parses standard Terraform Plan JSON format (`terraform show -json plan.tfplan`)
    and enforces a zero-tolerance blocker against any delete or replace actions
    on stateful cloud infrastructure.
    """

    # Comprehensive registry of stateful cloud resource types across AWS, Azure, GCP, and Kubernetes
    STATEFUL_RESOURCE_TYPES: Set[str] = {
        # AWS Stateful Resources
        "aws_rds_cluster",
        "aws_rds_cluster_instance",
        "aws_db_instance",
        "aws_dynamodb_table",
        "aws_s3_bucket",
        "aws_ebs_volume",
        "aws_efs_file_system",
        "aws_opensearch_domain",
        "aws_elasticsearch_domain",
        "aws_msk_cluster",
        "aws_kms_key",
        "aws_redshift_cluster",
        "aws_elasticache_cluster",
        "aws_elasticache_replication_group",

        # Azure Stateful Resources
        "azurerm_postgresql_flexible_server",
        "azurerm_postgresql_server",
        "azurerm_mssql_server",
        "azurerm_mssql_database",
        "azurerm_cosmosdb_account",
        "azurerm_storage_account",
        "azurerm_storage_container",
        "azurerm_managed_disk",
        "azurerm_key_vault",
        "azurerm_redis_cache",

        # GCP Stateful Resources
        "google_sql_database_instance",
        "google_storage_bucket",
        "google_bigtable_instance",
        "google_spanner_instance",
        "google_kms_crypto_key",

        # Kubernetes Stateful Resources
        "kubernetes_persistent_volume",
        "kubernetes_persistent_volume_claim",
        "kubernetes_stateful_set"
    }

    def evaluate_plan_json(self, plan_data: Dict[str, Any]) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Evaluates a Terraform Plan JSON dictionary.
        Returns:
            (is_approved: bool, violations: List[Dict[str, Any]])
        """
        violations: List[Dict[str, Any]] = []

        resource_changes = plan_data.get("resource_changes", [])
        if not isinstance(resource_changes, list):
            return False, [{
                "error": "MALFORMED_PLAN",
                "message": "resource_changes must be a JSON array"
            }]

        for change_item in resource_changes:
            res_type = change_item.get("type", "")
            res_address = change_item.get("address", change_item.get("name", "unknown"))
            change_obj = change_item.get("change", {})
            actions = change_obj.get("actions", [])

            # Check if this resource is recognized as stateful
            is_stateful = res_type in self.STATEFUL_RESOURCE_TYPES

            # Check for custom stateful tags or metadata
            before_tags = change_obj.get("before", {}).get("tags", {}) if isinstance(change_obj.get("before"), dict) else {}
            after_tags = change_obj.get("after", {}).get("tags", {}) if isinstance(change_obj.get("after"), dict) else {}
            
            if isinstance(before_tags, dict) and before_tags.get("Tier") == "stateful-db":
                is_stateful = True
            if isinstance(after_tags, dict) and after_tags.get("Tier") == "stateful-db":
                is_stateful = True

            # Determine if action is destructive:
            # - ["delete"]: Direct drop of the resource
            # - ["create", "delete"] or ["delete", "create"]: Forced replacement (requires_new)
            is_delete = "delete" in actions
            is_replacement = len(actions) == 2 and "create" in actions and "delete" in actions

            if is_stateful and (is_delete or is_replacement):
                action_desc = "FORCED_REPLACEMENT (requires_new)" if is_replacement else "DESTRUCTION (drop)"
                violations.append({
                    "resource_address": res_address,
                    "resource_type": res_type,
                    "actions": actions,
                    "violation_type": "DESTRUCTIVE_STATEFUL_CHANGE",
                    "severity": "CRITICAL",
                    "reason": f"Plan specifies {action_desc} on stateful resource '{res_address}' ({res_type})."
                })

        is_approved = len(violations) == 0
        return is_approved, violations

    def evaluate_plan_json_string(self, plan_json_str: str) -> Tuple[bool, List[Dict[str, Any]]]:
        """Convenience method to parse and evaluate raw JSON string."""
        try:
            data = json.loads(plan_json_str)
            return self.evaluate_plan_json(data)
        except json.JSONDecodeError as e:
            return False, [{
                "error": "INVALID_JSON",
                "message": f"Failed to parse Terraform Plan JSON: {str(e)}"
            }]
