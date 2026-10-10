"""
MigrationMesh - Digital Twin Sandbox MCP Server
Exposes ephemeral sandbox execution tools to agents via Model Context Protocol (MCP).
"""

from typing import Dict, Any
from packages.core.schemas import IaCManifest, CloudProvider
from packages.twin_runner.sandbox_manager import DigitalTwinSandboxManager


class SandboxMCPServer:
    """
    Sandbox MCP Tool Provider:
    Provisions ephemeral digital twins and runs characterization assertions.
    """

    def __init__(self):
        self.manager = DigitalTwinSandboxManager()

    def run_twin_characterization(self, hcl_code: str, provider: str) -> Dict[str, Any]:
        """Tool: Provisions ephemeral LocalStack/Azurite container and executes parity suite."""
        cloud_p = CloudProvider.AWS if provider.lower() == "aws" else CloudProvider.AZURE
        manifest = IaCManifest(
            provider=cloud_p,
            hcl_code=hcl_code,
            validation_status="valid"
        )
        receipt = self.manager.provision_shadow_twin(manifest)
        return {
            "status": "success",
            "receipt": receipt.model_dump()
        }
