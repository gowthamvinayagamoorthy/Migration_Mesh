"""
MigrationMesh - Audit Ledger Compatibility Wrapper
"""

import os
from packages.audit_ledger.hmac_hash_chain import HMACHashChain


class MerkleAuditLedger(HMACHashChain):
    """
    Backward-compatible wrapper for HMACHashChain.
    Defaults to environment key or fallback local key for tests.
    """

    def __init__(self, secret_key: str = None):
        key = secret_key or os.environ.get("MIGRATIONMESH_HMAC_KEY", "migrationmesh-default-hmac-key-2026")
        super().__init__(secret_key=key)

    def compute_merkle_root(self) -> str:
        """Computes chain tip digest for compatibility."""
        return self.chain[-1].block_hash if self.chain else ""
