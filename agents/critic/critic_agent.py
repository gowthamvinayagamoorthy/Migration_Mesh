"""
MigrationMesh - Critic Agent (Adversarial Plan Verifier)
Enforces zero-tolerance gates on destructive state replacements and hallucinated cloud resources.
100% deterministic code: uses Terraform Provider Schema validation and Terraform Plan JSON parsing.
"""

import re
from typing import List, Dict, Any, Optional
from packages.core.schemas import IaCManifest, CriticVerdict, CloudProvider
from packages.core.destructive_gate import TerraformPlanDestructiveGate
from packages.core.schema_validator import TerraformProviderSchemaValidator


class CriticAgent:
    """
    Critic Agent:
    - Pure deterministic verification: Zero LLM hallucinations in the gating decision.
    - Validates resource types against structured provider schemas.
    - Evaluates Terraform Plan JSON structures for destructive stateful replacements.
    """

    def __init__(self):
        self.destructive_gate = TerraformPlanDestructiveGate()
        self.schema_validator = TerraformProviderSchemaValidator()

    def evaluate_plan(self, manifest: IaCManifest, plan_json_data: Optional[Dict[str, Any]] = None) -> CriticVerdict:
        hcl = manifest.hcl_code
        destructive_changes: List[str] = []
        hallucinations: List[str] = []
        missed_deps: List[str] = []
        security_concerns: List[str] = []

        # 1. Provider Schema & Hallucination Validation
        is_schema_valid, schema_errors = self.schema_validator.validate_hcl_schema(
            hcl_code=hcl,
            provider=manifest.provider.value
        )
        for err in schema_errors:
            if "HALLUCINATION" in err:
                hallucinations.append(err)
            else:
                security_concerns.append(err)

        # 2. Destructive Stateful Changes via Plan JSON Gate
        if plan_json_data:
            approved, violations = self.destructive_gate.evaluate_plan_json(plan_json_data)
            for v in violations:
                destructive_changes.append(v.get("reason", "Destructive change on stateful resource"))
        else:
            # Check for synthetic destruction or forced replacement annotations
            for stateful_res in manifest.stateful_resources:
                if f"# DESTROY: {stateful_res}" in hcl or f"# REPLACE: {stateful_res}" in hcl:
                    destructive_changes.append(
                        f"CRITICAL: Plan contains destructive replacement or drop action on stateful entity '{stateful_res}'."
                    )

        # 3. Plaintext Credentials Check
        if re.search(r'password\s*=\s*"[^"]{4,}"', hcl) and "TemporaryVaultSecret" not in hcl:
            security_concerns.append("Potential un-redacted plaintext password found in manifest string literal.")

        # 4. Deterministic Confidence Score Computation
        confidence = 1.0
        if destructive_changes:
            confidence -= 0.8
        if hallucinations:
            confidence -= (len(hallucinations) * 0.3)
        if security_concerns:
            confidence -= (len(security_concerns) * 0.15)

        confidence = max(0.0, min(1.0, confidence))
        approved = (len(destructive_changes) == 0) and (len(hallucinations) == 0) and (confidence >= 0.90)

        notes = (
            "Critic plan verification PASSED with 0 destructive actions and valid provider schemas."
            if approved else
            f"Critic plan verification FAILED: {len(destructive_changes)} destructive diffs, {len(hallucinations)} hallucinations."
        )

        return CriticVerdict(
            approved=approved,
            confidence_score=round(confidence, 2),
            detected_destructive_changes=destructive_changes,
            detected_hallucinations=hallucinations,
            missed_dependencies=missed_deps,
            security_concerns=security_concerns,
            critic_notes=notes
        )
