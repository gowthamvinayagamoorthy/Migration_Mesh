package migrationmesh.safety.stateful_test

import rego.v1
import data.migrationmesh.safety.stateful

test_deny_rds_deletion if {
    input_data := {
        "resource_changes": [
            {
                "type": "aws_rds_cluster",
                "address": "aws_rds_cluster.prod_db",
                "change": {
                    "actions": ["delete"]
                }
            }
        ]
    }
    count(stateful.deny) > 0 with input as input_data
}

test_deny_s3_forced_replacement if {
    input_data := {
        "resource_changes": [
            {
                "type": "aws_s3_bucket",
                "address": "aws_s3_bucket.user_data",
                "change": {
                    "actions": ["create", "delete"]
                }
            }
        ]
    }
    count(stateful.deny) > 0 with input as input_data
}

test_deny_azure_postgres_replacement if {
    input_data := {
        "resource_changes": [
            {
                "type": "azurerm_postgresql_flexible_server",
                "address": "azurerm_postgresql_flexible_server.db",
                "change": {
                    "actions": ["delete", "create"]
                }
            }
        ]
    }
    count(stateful.deny) > 0 with input as input_data
}

test_allow_safe_rds_in_place_update if {
    input_data := {
        "resource_changes": [
            {
                "type": "aws_rds_cluster",
                "address": "aws_rds_cluster.prod_db",
                "change": {
                    "actions": ["update"]
                }
            }
        ]
    }
    stateful.allow with input as input_data
}

test_allow_stateless_container_replacement if {
    input_data := {
        "resource_changes": [
            {
                "type": "aws_ecs_task_definition",
                "address": "aws_ecs_task_definition.api",
                "change": {
                    "actions": ["create", "delete"]
                }
            }
        ]
    }
    stateful.allow with input as input_data
}
