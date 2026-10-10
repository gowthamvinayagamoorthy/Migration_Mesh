"""
MigrationMesh - Core Canonical Schemas
Standardized data contracts for multi-cloud, safe-by-design agent orchestration.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import datetime


class Strategy7R(str, Enum):
    REHOST = "Rehost (Lift & Shift)"
    REPLATFORM = "Replatform (Lift & Reshape)"
    REFACTOR = "Refactor (Cloud Native / Containerize)"
    REPURCHASE = "Repurchase (Drop & Shop / SaaS)"
    RETAIN = "Retain (Keep On-Prem / As-Is)"
    RETIRE = "Retire (Decommission)"
    RELOCATE = "Relocate (Hypervisor Level)"


class CloudProvider(str, Enum):
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    KUBERNETES = "kubernetes"
    ON_PREM = "on_prem"


class ResourceType(str, Enum):
    VIRTUAL_MACHINE = "virtual_machine"
    DATABASE = "database"
    OBJECT_STORAGE = "object_storage"
    BLOCK_STORAGE = "block_storage"
    LOAD_BALANCER = "load_balancer"
    CONTAINER = "container"
    NETWORK_VPC = "network_vpc"
    SECURITY_GROUP = "security_group"


class SourceResource(BaseModel):
    id: str
    name: str
    resource_type: ResourceType
    os: Optional[str] = None
    cpu_cores: int = 2
    ram_gb: float = 4.0
    storage_gb: float = 50.0
    ip_addresses: List[str] = Field(default_factory=list)
    tags: Dict[str, str] = Field(default_factory=dict)
    open_ports: List[int] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list, description="IDs of dependent resources")
    is_stateful: bool = False
    data_volume_gb: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CanonicalInventory(BaseModel):
    app_id: str
    app_name: str
    source_platform: str = "vmware_onprem"
    resources: List[SourceResource]
    network_flows: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())


class TargetCloudScore(BaseModel):
    provider: CloudProvider
    target_architecture_summary: str
    three_year_tco_usd: float
    vendor_lockin_score: float = Field(..., ge=0.0, le=100.0, description="0=Pure Open/Zero lock-in, 100=Max lock-in")
    migration_risk_score: float = Field(..., ge=0.0, le=100.0, description="0=Trivial/Zero risk, 100=Critical risk")
    compliance_score: float = Field(..., ge=0.0, le=100.0, description="0-100% compliance fit")
    operational_complexity_score: float = Field(..., ge=0.0, le=100.0)
    overall_fit_score: float = Field(..., ge=0.0, le=100.0)
    pros: List[str] = Field(default_factory=list)
    cons: List[str] = Field(default_factory=list)
    recommended_services: Dict[str, str] = Field(default_factory=dict)


class MigrationStrategyPlan(BaseModel):
    app_id: str
    strategy_7r: Strategy7R
    rationale: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    target_scores: List[TargetCloudScore]
    recommended_target: CloudProvider
    wave_number: int = 1
    open_questions: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)


class IaCManifest(BaseModel):
    provider: CloudProvider
    hcl_code: str
    kubernetes_yaml: Optional[str] = None
    resources_generated: List[str] = Field(default_factory=list)
    stateful_resources: List[str] = Field(default_factory=list)
    validation_status: str = "valid"
    validation_errors: List[str] = Field(default_factory=list)


class PolicyViolation(BaseModel):
    rule_id: str
    severity: str = "CRITICAL"  # CRITICAL, HIGH, MEDIUM, LOW
    description: str
    resource_id: str
    remediation_suggestion: str


class PolicyEvaluationResult(BaseModel):
    passed: bool
    total_rules_checked: int
    violations: List[PolicyViolation] = Field(default_factory=list)
    attestation_timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())


class CriticVerdict(BaseModel):
    approved: bool
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    detected_destructive_changes: List[str] = Field(default_factory=list)
    detected_hallucinations: List[str] = Field(default_factory=list)
    missed_dependencies: List[str] = Field(default_factory=list)
    security_concerns: List[str] = Field(default_factory=list)
    critic_notes: str


class ParityTestResult(BaseModel):
    test_name: str
    category: str  # http_endpoint, database_schema, row_count, latency
    passed: bool
    legacy_output: Any
    twin_output: Any
    latency_ms_legacy: float = 0.0
    latency_ms_twin: float = 0.0
    details: str = ""


class DigitalTwinExecutionReceipt(BaseModel):
    twin_id: str
    target_cloud: CloudProvider
    sandbox_runtime: str = "localstack_azurite_docker"
    provisioned_successfully: bool
    provision_duration_seconds: float
    parity_tests_passed: int
    parity_tests_total: int
    parity_pass_percentage: float
    test_results: List[ParityTestResult] = Field(default_factory=list)
    twin_logs_snippet: str = ""


class CutoverRunbook(BaseModel):
    app_id: str
    target_cloud: CloudProvider
    replication_lag_seconds: float
    max_tolerable_rpo_seconds: float = 5.0
    go_no_go_verdict: str  # GO, NO_GO
    go_no_go_confidence: float
    pre_flight_checks: List[Dict[str, Any]]
    execution_steps: List[Dict[str, Any]]
    rollback_steps: List[Dict[str, Any]]
    estimated_downtime_minutes: float = 0.0


class AuditBlock(BaseModel):
    block_index: int
    timestamp: str
    action_type: str
    agent_name: str
    actor_id: str
    input_digest: str
    output_digest: str
    policy_digest: str
    critic_digest: str
    previous_block_hash: str
    block_hash: str
    signature: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
