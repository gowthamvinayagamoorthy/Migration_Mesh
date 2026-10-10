package migrationmesh.aws.cis

default allow = false

# CIS Rule 1: Deny unrestricted public database ingress
deny[msg] {
    some i
    input.resource_changes[i].type == "aws_security_group"
    ingress := input.resource_changes[i].change.after.ingress[_]
    ingress.to_port == 5432
    ingress.cidr_blocks[_] == "0.0.0.0/0"
    msg := sprintf("CIS-SEC-002 Violation: Security group '%v' allows unrestricted 0.0.0.0/0 ingress on PostgreSQL port 5432.", [input.resource_changes[i].address])
}

# CIS Rule 2: Deny unencrypted database storage
deny[msg] {
    some i
    input.resource_changes[i].type in ["aws_rds_cluster", "aws_db_instance"]
    input.resource_changes[i].change.after.storage_encrypted == false
    msg := sprintf("CIS-AWS-001 Violation: Database '%v' does not have storage encryption enabled.", [input.resource_changes[i].address])
}

# CIS Rule 3: Deny wildcard IAM policies
deny[msg] {
    some i
    input.resource_changes[i].type in ["aws_iam_policy", "aws_iam_role_policy"]
    statement := input.resource_changes[i].change.after.policy.Statement[_]
    statement.Action == "*"
    msg := sprintf("CIS-IAM-003 Violation: IAM policy '%v' grants wildcard Action: '*'.", [input.resource_changes[i].address])
}

# CIS Rule 4: Deny public IP on private compute tasks
deny[msg] {
    some i
    input.resource_changes[i].type == "aws_ecs_service"
    input.resource_changes[i].change.after.network_configuration.assign_public_ip == true
    msg := sprintf("CIS-NET-004 Violation: ECS service '%v' has assign_public_ip enabled.", [input.resource_changes[i].address])
}

allow {
    count(deny) == 0
}
