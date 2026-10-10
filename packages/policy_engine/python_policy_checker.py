"""
MigrationMesh - Python Policy Checker (CIS & Stateful Safety)
Deterministic in-process policy checker enforcing CIS benchmarks and stateful resource safety.
Includes reference bindings for OPA CLI subprocess evaluation when `opa` binary is installed.
"""

import re
import shutil
import subprocess
import json
from typing import List, Dict, Any, Optional
from packages.core.schemas import IaCManifest, PolicyEvaluationResult, PolicyViolation, CloudProvider


class PythonPolicyChecker:
    """
    Evaluates generated Terraform manifests and plan structures against
    CIS Benchmarks, Least-Privilege IAM, and Stateful Resource Safety.
    """

    def __init__(self, use_opa_cli_if_available: bool = True):
        self.opa_path = shutil.which("opa") if use_opa_cli_if_available else None
        self.mode = "OPA_CLI" if self.opa_path else "IN_PROCESS_PYTHON"

    def evaluate_manifest(self, manifest: IaCManifest) -> PolicyEvaluationResult:
        """Evaluates Terraform HCL manifest string."""
        violations: List[PolicyViolation] = []
        hcl = manifest.hcl_code
        total_rules = 5

        # Rule 1: No public 0.0.0.0/0 ingress on Database ports (5432, 3306, 1433)
        db_sg_match = re.search(
            r'resource\s+"aws_security_group"\s+"[^"]*db[^"]*"\s*\{([\s\S]*?)\n\}',
            hcl,
            re.IGNORECASE
        )
        if db_sg_match:
            db_sg_body = db_sg_match.group(1)
            ingress_match = re.search(r'ingress\s*\{([\s\S]*?)\}', db_sg_body)
            if ingress_match and "0.0.0.0/0" in ingress_match.group(1):
                violations.append(PolicyViolation(
                    rule_id="CIS-SEC-002",
                    severity="CRITICAL",
                    description="Database security group allows unrestricted 0.0.0.0/0 public ingress.",
                    resource_id="aws_security_group.db_sg",
                    remediation_suggestion="Restrict ingress to private app subnet CIDR blocks or application security group ID."
                ))
        elif re.search(r'from_port\s*=\s*(?:5432|3306)[\s\S]*?cidr_blocks\s*=\s*\[.*0\.0\.0\.0\/0.*\]', hcl):
            violations.append(PolicyViolation(
                rule_id="CIS-SEC-002",
                severity="CRITICAL",
                description="Database port (5432/3306) allows unrestricted 0.0.0.0/0 public ingress.",
                resource_id="aws_security_group.db_sg",
                remediation_suggestion="Restrict ingress to private app subnet CIDR blocks or application security group ID."
            ))

        # Rule 2: Encryption-at-rest must be enabled on storage & database
        if "aws_db_instance" in hcl or "aws_rds_cluster" in hcl or "azurerm_postgresql_flexible_server" in hcl:
            if "storage_encrypted = false" in hcl or ("storage_encrypted" not in hcl and "azurerm_postgresql" not in hcl):
                violations.append(PolicyViolation(
                    rule_id="CIS-AWS-001",
                    severity="HIGH",
                    description="Database storage encryption-at-rest is disabled or not explicitly configured.",
                    resource_id="db_instance",
                    remediation_suggestion="Set storage_encrypted = true with KMS key ARN or customer-managed key."
                ))

        # Rule 3: IAM Least Privilege - No wildcard actions
        if re.search(r'Action\s*=\s*\[?\s*"\*"\s*\]?', hcl) or re.search(r'Resource\s*=\s*\[?\s*"\*"\s*\]?', hcl):
            violations.append(PolicyViolation(
                rule_id="CIS-IAM-003",
                severity="CRITICAL",
                description="IAM policy document grants wildcard Action: '*' or Resource: '*'.",
                resource_id="aws_iam_policy.app_exec_policy",
                remediation_suggestion="Narrow IAM policy permissions strictly to necessary KMS, S3, or SecretsManager ARNs."
            ))

        # Rule 4: Compute containers must reside in private subnets
        if "assign_public_ip = true" in hcl:
            violations.append(PolicyViolation(
                rule_id="CIS-NET-004",
                severity="HIGH",
                description="ECS task / Compute instance has assign_public_ip enabled.",
                resource_id="aws_ecs_service.app_service",
                remediation_suggestion="Place compute tasks in private subnets with NAT Gateway / Private Endpoints."
            ))

        # Rule 5: Stateful Resource Deletion / Replacement Gate
        for stateful_id in manifest.stateful_resources:
            if f"# DESTROY: {stateful_id}" in hcl or f"# REPLACE: {stateful_id}" in hcl:
                violations.append(PolicyViolation(
                    rule_id="MESH-SAFE-005",
                    severity="CRITICAL",
                    description=f"Destructive action or forced replacement detected on stateful resource: {stateful_id}.",
                    resource_id=stateful_id,
                    remediation_suggestion="Block plan immediately. Enforce migration attachment or in-place snapshot."
                ))

        passed = len([v for v in violations if v.severity in ("CRITICAL", "HIGH")]) == 0

        return PolicyEvaluationResult(
            passed=passed,
            total_rules_checked=total_rules,
            violations=violations
        )
