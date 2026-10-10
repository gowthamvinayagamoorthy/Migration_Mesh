"""
MigrationMesh - OPA & Policy Evaluation MCP Server
Exposes policy checking tools to agents via Model Context Protocol (MCP).
"""

from typing import Dict, Any
from packages.core.schemas import IaCManifest, CloudProvider
from packages.policy_engine.evaluator import PolicyEngine


class OPAPolicyMCPServer:
    """
    Policy MCP Tool Provider:
    Exposes deterministic OPA/Rego rule evaluation to LLM agents.
    """

    def __init__(self):
        self.engine = PolicyEngine()

    def evaluate_hcl_policy(self, hcl_code: str, provider: str, stateful_resources: list) -> Dict[str, Any]:
        """Tool: Evaluates Terraform HCL against CIS benchmarks and least-privilege policies."""
        cloud_p = CloudProvider.AWS if provider.lower() == "aws" else CloudProvider.AZURE
        manifest = IaCManifest(
            provider=cloud_p,
            hcl_code=hcl_code,
            stateful_resources=stateful_resources,
            validation_status="valid"
        )
        result = self.engine.evaluate_manifest(manifest)
        return {
            "status": "success",
            "passed": result.passed,
            "total_rules": result.total_rules_checked,
            "violations": [v.model_dump() for v in result.violations]
        }
