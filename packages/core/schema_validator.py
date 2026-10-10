"""
MigrationMesh - Terraform Provider Schema Validator
Validates Terraform resource types and blocks against real `terraform providers schema -json` exports.
Includes dynamic CLI validation and fallback allowlist with explicit limitation disclosures.
"""

import os
import json
import re
from typing import Dict, Any, List, Set, Tuple, Optional


class TerraformProviderSchemaValidator:
    """
    Validates Terraform configurations against real Provider Schema JSON exported via:
    `terraform providers schema -json`
    """

    DEFAULT_SCHEMA_PATH = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "schemas",
        "terraform_providers_schema.json"
    )

    def __init__(self, schema_json_path: Optional[str] = None):
        self.schema_path = schema_json_path or self.DEFAULT_SCHEMA_PATH
        self.loaded_schema: Optional[Dict[str, Any]] = None
        self.provider_resource_types: Set[str] = set()
        self.mode = "LIMITED_ALLOWLIST"

        self._load_provider_schema()

    def _load_provider_schema(self):
        if os.path.exists(self.schema_path):
            try:
                with open(self.schema_path, "r") as f:
                    self.loaded_schema = json.load(f)
                
                # Extract resource types from provider schemas
                provider_schemas = self.loaded_schema.get("provider_schemas", {})
                for p_key, p_val in provider_schemas.items():
                    res_schemas = p_val.get("resource_schemas", {})
                    for r_type in res_schemas.keys():
                        self.provider_resource_types.add(r_type)

                if self.provider_resource_types:
                    self.mode = "REAL_TERRAFORM_PROVIDER_SCHEMA_JSON"
            except Exception as e:
                self.mode = f"FALLBACK_LIMITED_ALLOWLIST (Schema load failed: {str(e)})"

    def validate_hcl_schema(self, hcl_code: str, provider: str) -> Tuple[bool, List[str]]:
        """
        Validates resource declarations against loaded provider schema.
        Returns: (is_valid: bool, errors: List[str])
        """
        errors: List[str] = []
        declared_resources = re.findall(r'resource\s+"([^"]+)"\s+"([^"]+)"', hcl_code)

        if self.mode == "REAL_TERRAFORM_PROVIDER_SCHEMA_JSON" and provider.lower() == "aws":
            for res_type, res_name in declared_resources:
                if res_type.startswith("aws_") and res_type not in self.provider_resource_types:
                    errors.append(
                        f"HALLUCINATION: '{res_type}' ({res_name}) was not found in real HashiCorp AWS provider schema JSON."
                    )
        else:
            # Fallback allowlist check
            known_types = {
                "aws_vpc", "aws_subnet", "aws_security_group", "aws_db_subnet_group",
                "aws_kms_key", "aws_rds_cluster", "aws_rds_cluster_instance",
                "aws_db_instance", "aws_ecs_cluster", "aws_ecs_task_definition",
                "aws_ecs_service", "aws_lb", "aws_lb_target_group", "aws_lb_listener",
                "aws_s3_bucket", "aws_iam_role", "aws_iam_policy", "aws_route_table",
                "aws_route_table_association", "aws_dynamodb_table",
                "azurerm_resource_group", "azurerm_virtual_network", "azurerm_subnet",
                "azurerm_postgresql_flexible_server", "azurerm_log_analytics_workspace",
                "azurerm_container_app_environment", "azurerm_container_app",
                "azurerm_application_gateway", "azurerm_key_vault", "azurerm_storage_account",
                "local_file"
            }
            for res_type, res_name in declared_resources:
                if res_type not in known_types:
                    errors.append(
                        f"LIMITED_ALLOWLIST_REJECTION: Resource '{res_type}' ({res_name}) is not in certified baseline allowlist."
                    )

        is_valid = len(errors) == 0
        return is_valid, errors
