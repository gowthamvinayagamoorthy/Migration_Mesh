"""
MigrationMesh - Discovery Agent
Ingests legacy infrastructure metadata (RVTools, CMDB, Docker Compose, VM specs),
normalizes into canonical inventory schemas, and computes dependency graphs with cycle detection.
"""

import networkx as nx
from typing import Dict, Any, List, Tuple
from packages.core.schemas import (
    CanonicalInventory,
    SourceResource,
    ResourceType
)
from packages.privacy.redactor import PrivacyRedactor


class DiscoveryAgent:
    """
    Discovery Agent:
    - Normalizes multi-source infrastructure inventory.
    - Sanitizes sensitive IPs and credentials before downstream processing.
    - Builds NetworkX dependency DAG and identifies critical migration wave paths.
    """

    def __init__(self, redactor: PrivacyRedactor):
        self.redactor = redactor

    def ingest_legacy_sample_app(self, raw_config: Dict[str, Any]) -> Tuple[CanonicalInventory, Dict[str, Any]]:
        """
        Ingests the legacy 3-tier sample app and returns a sanitized canonical inventory
        along with topological dependency analysis.
        """
        # Redact raw input dictionary
        sanitized_config, redactions = self.redactor.redact_dict(raw_config)

        resources: List[SourceResource] = []
        for r_data in sanitized_config.get("resources", []):
            res = SourceResource(
                id=r_data["id"],
                name=r_data["name"],
                resource_type=ResourceType(r_data.get("resource_type", "virtual_machine")),
                os=r_data.get("os", "Ubuntu 22.04 LTS"),
                cpu_cores=r_data.get("cpu_cores", 2),
                ram_gb=r_data.get("ram_gb", 4.0),
                storage_gb=r_data.get("storage_gb", 50.0),
                ip_addresses=r_data.get("ip_addresses", []),
                tags=r_data.get("tags", {}),
                open_ports=r_data.get("open_ports", []),
                dependencies=r_data.get("dependencies", []),
                is_stateful=r_data.get("is_stateful", False),
                data_volume_gb=r_data.get("data_volume_gb", 0.0),
                metadata=r_data.get("metadata", {})
            )
            resources.append(res)

        inventory = CanonicalInventory(
            app_id=sanitized_config.get("app_id", "app-sample-3tier"),
            app_name=sanitized_config.get("app_name", "Enterprise Payment & Customer Portal"),
            source_platform=sanitized_config.get("source_platform", "vmware_onprem_vcenter"),
            resources=resources,
            network_flows=sanitized_config.get("network_flows", [])
        )

        topo_analysis = self.build_dependency_dag(inventory)
        return inventory, topo_analysis

    def build_dependency_dag(self, inventory: CanonicalInventory) -> Dict[str, Any]:
        """Builds a Directed Acyclic Graph (DAG) and computes wave sequencing & stateful nodes."""
        graph = nx.DiGraph()

        for res in inventory.resources:
            graph.add_node(
                res.id,
                name=res.name,
                type=res.resource_type.value,
                is_stateful=res.is_stateful,
                ports=res.open_ports
            )

        for res in inventory.resources:
            for dep_id in res.dependencies:
                if graph.has_node(dep_id):
                    # Edge from dependency to consumer (dependency must be migrated/ready first)
                    graph.add_edge(dep_id, res.id)

        # Check for circular dependencies
        is_dag = nx.is_directed_acyclic_graph(graph)
        cycles = list(nx.simple_cycles(graph)) if not is_dag else []

        # Topological sorting for wave ordering
        if is_dag:
            waves = []
            temp_graph = graph.copy()
            while temp_graph.nodes():
                # Zero in-degree nodes have no pending dependencies in current wave
                zero_in = [n for n, d in temp_graph.in_degree() if d == 0]
                if not zero_in:
                    break
                waves.append(zero_in)
                temp_graph.remove_nodes_from(zero_in)
        else:
            waves = [[r.id for r in inventory.resources]]

        stateful_nodes = [r.id for r in inventory.resources if r.is_stateful]

        return {
            "is_valid_dag": is_dag,
            "detected_cycles": cycles,
            "node_count": len(inventory.resources),
            "edge_count": graph.number_of_edges(),
            "migration_waves": waves,
            "stateful_resources": stateful_nodes,
            "critical_path_length": len(waves)
        }
