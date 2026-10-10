package migrationmesh.aws.cis

import rego.v1

default allow := false

# CIS Rule 1: Deny unrestricted public database ingress
deny contains msg if {
    some res in input.resource_changes
    res.type == "aws_security_group"
    some ingress in res.change.after.ingress
    ingress.to_port == 5432
    some cidr in ingress.cidr_blocks
    cidr == "0.0.0.0/0"
    msg := sprintf("CIS-SEC-002 Violation: Security group '%v' allows unrestricted 0.0.0.0/0 ingress on PostgreSQL port 5432.", [res.address])
}

# CIS Rule 2: Deny unencrypted database storage
deny contains msg if {
    some res in input.resource_changes
    res.type in ["aws_rds_cluster", "aws_db_instance"]
    res.change.after.storage_encrypted == false
    msg := sprintf("CIS-AWS-001 Violation: Database '%v' does not have storage encryption enabled.", [res.address])
}

# CIS Rule 3: Deny wildcard IAM policies
deny contains msg if {
    some res in input.resource_changes
    res.type in ["aws_iam_policy", "aws_iam_role_policy"]
    some statement in res.change.after.policy.Statement
    statement.Action == "*"
    msg := sprintf("CIS-IAM-003 Violation: IAM policy '%v' grants wildcard Action: '*'.", [res.address])
}

# CIS Rule 4: Deny public IP on private compute tasks
deny contains msg if {
    some res in input.resource_changes
    res.type == "aws_ecs_service"
    res.change.after.network_configuration.assign_public_ip == true
    msg := sprintf("CIS-NET-004 Violation: ECS service '%v' has assign_public_ip enabled.", [res.address])
}

allow if {
    count(deny) == 0
}
