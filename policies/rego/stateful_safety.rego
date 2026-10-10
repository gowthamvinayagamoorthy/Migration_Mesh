package migrationmesh.safety.stateful

import rego.v1

default allow := false

stateful_types := [
    "aws_rds_cluster",
    "aws_rds_cluster_instance",
    "aws_db_instance",
    "aws_dynamodb_table",
    "aws_s3_bucket",
    "aws_ebs_volume",
    "aws_efs_file_system",
    "azurerm_postgresql_flexible_server",
    "azurerm_storage_account",
    "azurerm_managed_disk",
    "google_sql_database_instance",
    "google_storage_bucket",
    "kubernetes_persistent_volume_claim"
]

deny contains msg if {
    some res in input.resource_changes
    res.type in stateful_types
    some action in res.change.actions
    action == "delete"
    msg := sprintf("MESH-SAFE-001 Violation: Plan specifies destructive drop/replacement action on stateful resource '%v'.", [res.address])
}

allow if {
    count(deny) == 0
}
