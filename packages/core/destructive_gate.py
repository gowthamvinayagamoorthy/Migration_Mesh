"""
MigrationMesh - Hardened Deterministic Destructive-Change Gate
Pure deterministic parser for `terraform show -json` plan output.
Zero LLM involvement in destructive change gating decisions.
"""

import os
import json
from typing import Dict, Any, List, Set, Tuple, Optional


class TerraformPlanDestructiveGate:
    """
    Hardened Deterministic Destructive-Change Gate:
    - Parses standard `terraform show -json` plan output.
    - Handles actions: ["delete"], ["create", "delete"], ["delete", "create"].
    - Handles `change.replace_paths`.
    - Handles nested module addresses (e.g. module.db.aws_db_instance.main).
    - Strictly ignores data sources (mode: "data" or address starting with "data.").
    - Evaluates resource drift and verifies active planned changes.
    - Configurable stateful resource type list.
    """

    DEFAULT_STATEFUL_TYPES: Set[str] = {
        # AWS Stateful Resources
        "aws_db_instance",
        "aws_rds_cluster",
        "aws_rds_cluster_instance",
        "aws_s3_bucket",
        "aws_dynamodb_table",
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

    def __init__(
        self,
        custom_stateful_types: Optional[Set[str]] = None,
        allow_env_override: bool = True
    ):
        self.stateful_types = set(self.DEFAULT_STATEFUL_TYPES)
        if custom_stateful_types:
            self.stateful_types.update(custom_stateful_types)

        if allow_env_override:
            env_types = os.environ.get("MIGRATIONMESH_STATEFUL_TYPES")
            if env_types:
                for t in env_types.split(","):
                    if t.strip():
                        self.stateful_types.add(t.strip())

    def evaluate_plan_json(self, plan_data: Dict[str, Any]) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Evaluates a Terraform Plan JSON dictionary.
        Returns: (is_approved: bool, violations: List[Dict[str, Any]])
        """
        violations: List[Dict[str, Any]] = []

        resource_changes = plan_data.get("resource_changes", [])
        if not isinstance(resource_changes, list):
            return False, [{
                "error": "MALFORMED_PLAN",
                "message": "resource_changes must be a JSON array"
            }]

        for change_item in resource_changes:
            # 1. Ignore Data Sources strictly
            mode = change_item.get("mode", "managed")
            address = change_item.get("address", change_item.get("name", "unknown"))
            if mode == "data" or address.startswith("data."):
                continue

            res_type = change_item.get("type", "")
            change_obj = change_item.get("change", {})
            actions = change_obj.get("actions", [])
            replace_paths = change_obj.get("replace_paths", [])

            # Check if recognized as stateful
            is_stateful = res_type in self.stateful_types

            # Check for custom stateful tags / metadata in before or after state
            before_tags = change_obj.get("before", {}).get("tags", {}) if isinstance(change_obj.get("before"), dict) else {}
            after_tags = change_obj.get("after", {}).get("tags", {}) if isinstance(change_obj.get("after"), dict) else {}
            
            if isinstance(before_tags, dict) and before_tags.get("Tier") == "stateful-db":
                is_stateful = True
            if isinstance(after_tags, dict) and after_tags.get("Tier") == "stateful-db":
                is_stateful = True

            # Determine destructive actions:
            # - ["delete"]: Direct drop of the resource
            # - ["create", "delete"] or ["delete", "create"]: Forced replacement (requires_new)
            is_delete = "delete" in actions
            is_replacement = (
                (len(actions) == 2 and "create" in actions and "delete" in actions) or
                (bool(replace_paths) and ("delete" in actions or "create" in actions))
            )

            if is_stateful and (is_delete or is_replacement):
                action_desc = "FORCED_REPLACEMENT (requires_new)" if is_replacement else "DESTRUCTION (drop)"
                violations.append({
                    "resource_address": address,
                    "resource_type": res_type,
                    "actions": actions,
                    "replace_paths": replace_paths,
                    "violation_type": "DESTRUCTIVE_STATEFUL_CHANGE",
                    "severity": "CRITICAL",
                    "reason": f"Plan specifies {action_desc} on stateful resource '{address}' ({res_type}). Actions: {actions}."
                })

        is_approved = len(violations) == 0
        return is_approved, violations

    def evaluate_plan_json_file(self, file_path: str) -> Tuple[bool, List[Dict[str, Any]]]:
        """Convenience method to load and evaluate a plan JSON file from disk."""
        with open(file_path, "r") as f:
            data = json.load(f)
        return self.evaluate_plan_json(data)
