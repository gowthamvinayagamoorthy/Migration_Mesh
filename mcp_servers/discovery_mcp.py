"""
MigrationMesh - Read-Only Discovery MCP Server
Exposes secure, read-only tools to agents via the Model Context Protocol (MCP).
"""

import json
from typing import Dict, Any


class DiscoveryMCPServer:
    """
    Discovery MCP Tool Provider:
    Ensures agents have read-only access to CMDB, VMware, and network inventories.
    Mutating methods do not exist on this server.
    """

    def __init__(self, sample_config_path: str = "sample_apps/legacy_3tier_app/config.json"):
        self.sample_config_path = sample_config_path

    def inspect_inventory(self, app_id: str) -> Dict[str, Any]:
        """Tool: Reads legacy infrastructure inventory for a specified application ID."""
        try:
            with open(self.sample_config_path, "r") as f:
                data = json.load(f)
            return {"status": "success", "data": data}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_network_topology(self, app_id: str) -> Dict[str, Any]:
        """Tool: Retrieves network flow tables and security group mappings."""
        inv = self.inspect_inventory(app_id)
        if inv["status"] == "success":
            return {"status": "success", "network_flows": inv["data"].get("network_flows", [])}
        return inv

    def list_stateful_resources(self, app_id: str) -> Dict[str, Any]:
        """Tool: Returns IDs of all database and persistent storage nodes."""
        inv = self.inspect_inventory(app_id)
        if inv["status"] == "success":
            stateful = [r for r in inv["data"].get("resources", []) if r.get("is_stateful")]
            return {"status": "success", "stateful_resources": stateful}
        return inv
