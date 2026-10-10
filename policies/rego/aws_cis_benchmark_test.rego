package migrationmesh.aws.cis_test

import rego.v1
import data.migrationmesh.aws.cis

test_deny_public_db_ingress if {
    input_data := {
        "resource_changes": [
            {
                "type": "aws_security_group",
                "address": "aws_security_group.db_sg",
                "change": {
                    "after": {
                        "ingress": [
                            {
                                "to_port": 5432,
                                "cidr_blocks": ["0.0.0.0/0"]
                            }
                        ]
                    }
                }
            }
        ]
    }
    count(cis.deny) > 0 with input as input_data
}

test_allow_safe_security_group if {
    input_data := {
        "resource_changes": [
            {
                "type": "aws_security_group",
                "address": "aws_security_group.app_sg",
                "change": {
                    "after": {
                        "ingress": [
                            {
                                "to_port": 443,
                                "cidr_blocks": ["10.100.0.0/16"]
                            }
                        ]
                    }
                }
            }
        ]
    }
    cis.allow with input as input_data
}

test_deny_unencrypted_rds if {
    input_data := {
        "resource_changes": [
            {
                "type": "aws_rds_cluster",
                "address": "aws_rds_cluster.aurora",
                "change": {
                    "after": {
                        "storage_encrypted": false
                    }
                }
            }
        ]
    }
    count(cis.deny) > 0 with input as input_data
}

test_deny_wildcard_iam_statement if {
    input_data := {
        "resource_changes": [
            {
                "type": "aws_iam_policy",
                "address": "aws_iam_policy.admin",
                "change": {
                    "after": {
                        "policy": {
                            "Statement": [
                                {
                                    "Action": "*"
                                }
                            ]
                        }
                    }
                }
            }
        ]
    }
    count(cis.deny) > 0 with input as input_data
}
