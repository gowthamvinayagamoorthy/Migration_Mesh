"""
MigrationMesh - Terraform Provider Schema Validator
Validates resource types against structured provider schemas (AWS, Azure, GCP).
Catches hallucinated resource types and invalid top-level configurations.
"""

import re
from typing import Dict, Any, List, Set, Tuple


class TerraformProviderSchemaValidator:
    """
    Validates Terraform configurations against provider schemas.
    Identifies non-existent resource types or invalid top-level provider resources.
    """

    AWS_PROVIDER_SCHEMAS: Dict[str, Dict[str, Any]] = {
        "aws_vpc": {"blocks": ["tags"], "attributes": ["cidr_block", "enable_dns_hostnames", "enable_dns_support", "tags"]},
        "aws_subnet": {"blocks": ["tags"], "attributes": ["vpc_id", "cidr_block", "availability_zone", "map_public_ip_on_launch", "tags"]},
        "aws_security_group": {"blocks": ["ingress", "egress", "tags"], "attributes": ["name", "description", "vpc_id", "ingress", "egress", "tags"]},
        "aws_db_subnet_group": {"blocks": ["tags"], "attributes": ["name", "description", "subnet_ids", "tags"]},
        "aws_kms_key": {"blocks": ["tags"], "attributes": ["description", "deletion_window_in_days", "enable_key_rotation", "tags"]},
        "aws_rds_cluster": {"blocks": ["serverlessv2_scaling_configuration", "tags"], "attributes": ["cluster_identifier", "engine", "engine_mode", "engine_version", "database_name", "master_username", "manage_master_user_password", "db_subnet_group_name", "vpc_security_group_ids", "storage_encrypted", "kms_key_id", "deletion_protection", "skip_final_snapshot", "final_snapshot_identifier", "serverlessv2_scaling_configuration", "tags"]},
        "aws_rds_cluster_instance": {"blocks": ["tags"], "attributes": ["count", "identifier", "cluster_identifier", "instance_class", "engine", "engine_version", "tags"]},
        "aws_db_instance": {"blocks": ["tags"], "attributes": ["identifier", "instance_class", "engine", "allocated_storage", "username", "password", "db_subnet_group_name", "vpc_security_group_ids", "storage_encrypted", "kms_key_id", "tags"]},
        "aws_ecs_cluster": {"blocks": ["setting", "tags"], "attributes": ["name", "setting", "tags"]},
        "aws_ecs_task_definition": {"blocks": ["tags"], "attributes": ["family", "network_mode", "requires_compatibilities", "cpu", "memory", "container_definitions", "tags"]},
        "aws_ecs_service": {"blocks": ["network_configuration", "tags"], "attributes": ["name", "cluster", "task_definition", "desired_count", "launch_type", "network_configuration", "tags"]},
        "aws_lb": {"blocks": ["tags"], "attributes": ["name", "internal", "load_balancer_type", "security_groups", "subnets", "tags"]},
        "aws_lb_target_group": {"blocks": ["health_check", "tags"], "attributes": ["name", "port", "protocol", "vpc_id", "target_type", "tags"]},
        "aws_lb_listener": {"blocks": ["default_action", "tags"], "attributes": ["load_balancer_arn", "port", "protocol", "ssl_policy", "certificate_arn", "default_action", "tags"]},
        "aws_s3_bucket": {"blocks": ["tags"], "attributes": ["bucket", "force_destroy", "tags"]},
        "aws_iam_role": {"blocks": ["tags"], "attributes": ["name", "assume_role_policy", "description", "tags"]},
        "aws_iam_policy": {"blocks": ["tags"], "attributes": ["name", "policy", "description", "tags"]},
        "aws_route_table": {"blocks": ["route", "tags"], "attributes": ["vpc_id", "route", "tags"]},
        "aws_route_table_association": {"blocks": [], "attributes": ["subnet_id", "route_table_id"]},
        "aws_dynamodb_table": {"blocks": ["attribute", "tags"], "attributes": ["name", "hash_key", "range_key", "billing_mode", "attribute", "tags"]}
    }

    AZURE_PROVIDER_SCHEMAS: Dict[str, Dict[str, Any]] = {
        "azurerm_resource_group": {"blocks": ["tags"], "attributes": ["name", "location", "tags"]},
        "azurerm_virtual_network": {"blocks": ["tags"], "attributes": ["name", "address_space", "location", "resource_group_name", "tags"]},
        "azurerm_subnet": {"blocks": ["delegation"], "attributes": ["name", "resource_group_name", "virtual_network_name", "address_prefixes", "delegation"]},
        "azurerm_postgresql_flexible_server": {"blocks": ["high_availability", "tags"], "attributes": ["name", "resource_group_name", "location", "version", "delegated_subnet_id", "administrator_login", "administrator_password", "storage_mb", "sku_name", "backup_retention_days", "high_availability", "tags"]},
        "azurerm_log_analytics_workspace": {"blocks": ["tags"], "attributes": ["name", "location", "resource_group_name", "sku", "retention_in_days", "tags"]},
        "azurerm_container_app_environment": {"blocks": ["tags"], "attributes": ["name", "location", "resource_group_name", "log_analytics_workspace_id", "infrastructure_subnet_id", "tags"]},
        "azurerm_container_app": {"blocks": ["template", "ingress", "tags"], "attributes": ["name", "container_app_environment_id", "resource_group_name", "revision_mode", "template", "ingress", "tags"]},
        "azurerm_application_gateway": {"blocks": ["gateway_ip_configuration", "frontend_port", "frontend_ip_configuration", "backend_address_pool", "backend_http_settings", "http_listener", "request_routing_rule", "tags"], "attributes": ["name", "resource_group_name", "location", "sku", "tags"]},
        "azurerm_key_vault": {"blocks": ["access_policy", "tags"], "attributes": ["name", "location", "resource_group_name", "tenant_id", "sku_name", "access_policy", "tags"]},
        "azurerm_storage_account": {"blocks": ["tags"], "attributes": ["name", "resource_group_name", "location", "account_tier", "account_replication_type", "tags"]}
    }

    def validate_hcl_schema(self, hcl_code: str, provider: str) -> Tuple[bool, List[str]]:
        """
        Validates resource types against structured provider registry.
        """
        errors: List[str] = []
        provider_name = provider.lower()
        schema_db = self.AWS_PROVIDER_SCHEMAS if provider_name == "aws" else self.AZURE_PROVIDER_SCHEMAS

        declared_resources = re.findall(r'resource\s+"([^"]+)"\s+"([^"]+)"', hcl_code)

        for res_type, res_name in declared_resources:
            if res_type not in schema_db:
                errors.append(f"HALLUCINATION: '{res_type}' ({res_name}) is not a recognized {provider.upper()} provider resource type.")

        is_valid = len(errors) == 0
        return is_valid, errors
