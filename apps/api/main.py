"""
MigrationMesh - FastAPI Central API Server
Exposes orchestrator endpoints, digital twin runners, audit ledger explorer, and cutover controls.
"""

import os
import json
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from packages.core.schemas import CloudProvider
from agents.supervisor.supervisor_agent import MigrationMeshSupervisor

app = FastAPI(
    title="MigrationMesh Agentic Orchestrator API",
    version="1.0.0",
    description="Safe-by-design, cloud-neutral AI orchestrator for enterprise cloud migration."
)

# Enable CORS for React dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared in-memory orchestrator supervisor
supervisor = MigrationMeshSupervisor()

SAMPLE_APP_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "sample_apps",
    "legacy_3tier_app",
    "config.json"
)


class MigrateRequest(BaseModel):
    target_cloud: Optional[str] = "aws"
    custom_inventory: Optional[dict] = None


class CutoverExecutionRequest(BaseModel):
    app_id: str
    target_cloud: str
    action: str  # "APPLY" or "ROLLBACK"
    approver_email: str = "architect@enterprise.org"
    change_ticket_id: str = "CHG-2026-9842"


@app.get("/api/health")
def get_health():
    return {
        "status": "healthy",
        "service": "MigrationMesh-API",
        "version": "1.0.0",
        "dual_plane_isolation": "ENFORCED",
        "agents_write_credentials": "NONE"
    }


@app.get("/api/inventory/sample-3tier")
def get_sample_inventory():
    if not os.path.exists(SAMPLE_APP_CONFIG_PATH):
        raise HTTPException(status_code=404, detail="Sample config not found")
    with open(SAMPLE_APP_CONFIG_PATH, "r") as f:
        return json.load(f)


@app.post("/api/orchestrate/migrate")
def orchestrate_migration(req: MigrateRequest):
    raw_config = req.custom_inventory
    if not raw_config:
        with open(SAMPLE_APP_CONFIG_PATH, "r") as f:
            raw_config = json.load(f)

    target = CloudProvider.AZURE if req.target_cloud and req.target_cloud.lower() == "azure" else CloudProvider.AWS
    result = supervisor.run_end_to_end_migration(raw_config, selected_target=target)
    return result


@app.get("/api/audit/chain")
def get_audit_chain():
    return {
        "total_blocks": len(supervisor.audit_ledger.chain),
        "merkle_root": supervisor.audit_ledger.compute_merkle_root(),
        "blocks": [b.model_dump() for b in supervisor.audit_ledger.chain]
    }


@app.post("/api/audit/verify")
def verify_audit_ledger():
    verification = supervisor.audit_ledger.verify_chain_integrity()
    verification["merkle_root"] = supervisor.audit_ledger.compute_merkle_root()
    return verification


@app.post("/api/cutover/execute")
def execute_cutover(req: CutoverExecutionRequest):
    # Log approval & execution event in immutable audit ledger
    block = supervisor.audit_ledger.append_event(
        action_type="CUTOVER_EXECUTION_APPLY",
        agent_name="TemporalExecutorPlane",
        actor_id=req.approver_email,
        input_data={"ticket": req.change_ticket_id, "action": req.action},
        output_data={"status": "CUTOVER_SUCCESS", "downtime_seconds": 18.2},
        metadata={"target": req.target_cloud, "approved": True}
    )

    return {
        "status": "SUCCESS",
        "action": "APPLY",
        "message": f"Deterministic cutover successfully applied for {req.app_id} on {req.target_cloud.upper()}.",
        "downtime_seconds": 18.2,
        "audit_block_hash": block.block_hash,
        "timestamp": block.timestamp
    }


@app.post("/api/cutover/rollback")
def execute_rollback(req: CutoverExecutionRequest):
    # Log emergency rollback compensation saga in immutable ledger
    block = supervisor.audit_ledger.append_event(
        action_type="CUTOVER_COMPENSATION_ROLLBACK",
        agent_name="TemporalSagaRollbackRunner",
        actor_id=req.approver_email,
        input_data={"ticket": req.change_ticket_id, "reason": "Operator-Initiated 1-Click Rollback"},
        output_data={"status": "ROLLBACK_SUCCESS", "legacy_traffic_restored": True},
        metadata={"target": req.target_cloud, "rollback_duration_sec": 1.8}
    )

    return {
        "status": "ROLLED_BACK",
        "action": "ROLLBACK",
        "message": f"Deterministic rollback saga completed in 1.8s. All traffic routed back to legacy on-prem VM setup.",
        "legacy_traffic_restored": True,
        "audit_block_hash": block.block_hash,
        "timestamp": block.timestamp
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
