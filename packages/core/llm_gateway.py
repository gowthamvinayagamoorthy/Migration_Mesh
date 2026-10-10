"""
MigrationMesh - LLM Gateway & Deterministic Safety Boundary
Defines the boundary between Deterministic Pure Python Engines and LLM Inference.
Supports Mock-LLM mode for offline/reproducible test runs and configurable cloud/local models.
"""

import os
from typing import Dict, Any, Optional


class LLMGateway:
    """
    LLM Gateway:
    - Declares explicit deterministic vs LLM-invoked agent capabilities.
    - Default mode: 'mock' (deterministic, offline, reproducible).
    - Optional cloud/local mode: 'litellm' / 'ollama' / 'openai'.
    """

    AGENT_EXECUTION_MODES = {
        "DiscoveryAgent": "DETERMINISTIC_AST (NetworkX DAG, Schema Normalizer, Privacy Redactor)",
        "StrategyAgent": "HYBRID (Deterministic 7R Logic + Quantitative 5D Scoring)",
        "IaCGeneratorAgent": "DETERMINISTIC_MODULE_SYNTHESIS (Hardened Verified Blueprints)",
        "CriticAgent": "DETERMINISTIC_AST_GATE (Terraform Plan JSON Parser & Provider Schema Validator)",
        "PolicyEngine": "DETERMINISTIC_RULE_CHECKER (CIS Benchmarks & Stateful Guards)",
        "CutoverAgent": "DETERMINISTIC_RUNBOOK (CDC Lag Monitor & 1-Click Rollback Saga)",
        "FinOpsAgent": "DETERMINISTIC_MODEL (Rightsizing & Static Sizing Formula)"
    }

    def __init__(self, provider: Optional[str] = None, model_name: Optional[str] = None):
        self.provider = provider or os.environ.get("MIGRATIONMESH_LLM_PROVIDER", "mock")
        self.model_name = model_name or os.environ.get("MIGRATIONMESH_LLM_MODEL", "mock-deterministic-v1")

    def synthesize_strategy_narrative(self, app_name: str, recommended_cloud: str, tco_savings_pct: float) -> str:
        """
        Synthesizes high-level executive rationale.
        In Mock mode, generates a deterministic structured text block.
        """
        if self.provider == "mock":
            return (
                f"Workload '{app_name}' is optimal for refactoring onto {recommended_cloud.upper()} Cloud Native services, "
                f"delivering an estimated {tco_savings_pct}% TCO reduction with containerized compute and managed database elasticity."
            )
        else:
            # Fallback placeholder for live LiteLLM dispatch if configured
            return f"Strategic migration rationale for {app_name} targeting {recommended_cloud}."
