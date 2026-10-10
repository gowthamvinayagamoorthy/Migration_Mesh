package migrationmesh.safety.stateful

default allow = false

# Mesh Safety Rule: Deny deletion or replacement of stateful resources
stateful_types = [
    "aws_rds_cluster",
    "aws_rds_cluster_instance",
    "aws_db_instance",
    "aws_dynamodb_table",
    "aws_s3_bucket",
    "aws_ebs_volume",
    "azurerm_postgresql_flexible_server",
    "azurerm_storage_account",
    "google_sql_database_instance"
]

deny[msg] {
    some i
    input.resource_changes[i].type == stateful_types[_]
    actions := input.resource_changes[i].change.actions
    actions[_] == "delete"
    msg := sprintf("MESH-SAFE-001 Violation: Plan specifies destructive drop/replacement action %v on stateful resource '%v'.", [actions, input.resource_changes[i].address])
}

allow {
    count(deny) == 0
}
