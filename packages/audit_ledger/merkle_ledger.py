"""
MigrationMesh - Cryptographic Merkle Hash-Chained Audit Ledger
Append-only, tamper-evident record of prompts, proposals, policy verdicts,
critic attestations, human approvals, and execution receipts.
"""

import hashlib
import json
import datetime
from typing import List, Dict, Any, Optional
from packages.core.schemas import AuditBlock


class MerkleAuditLedger:
    """
    Immutable Hash-Chained Audit Ledger.
    Every event is linked to its predecessor via SHA-256 block hashing,
    enabling mathematical proof of non-tampering.
    """

    GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

    def __init__(self):
        self.chain: List[AuditBlock] = []
        self._initialize_genesis_block()

    def _calculate_digest(self, data: Any) -> str:
        """Calculates canonical SHA-256 hash of any Python data structure or string."""
        if isinstance(data, str):
            payload = data.encode('utf-8')
        else:
            payload = json.dumps(data, sort_keys=True, default=str).encode('utf-8')
        return hashlib.sha256(payload).hexdigest()

    def _initialize_genesis_block(self):
        genesis_time = "2026-01-01T00:00:00.000000+00:00"
        block_hash = self._compute_block_hash(
            index=0,
            timestamp=genesis_time,
            action_type="GENESIS",
            agent_name="SYSTEM",
            actor_id="ROOT",
            input_digest="0" * 64,
            output_digest="0" * 64,
            policy_digest="0" * 64,
            critic_digest="0" * 64,
            previous_hash=self.GENESIS_HASH
        )
        genesis_block = AuditBlock(
            block_index=0,
            timestamp=genesis_time,
            action_type="GENESIS",
            agent_name="SYSTEM",
            actor_id="ROOT",
            input_digest="0" * 64,
            output_digest="0" * 64,
            policy_digest="0" * 64,
            critic_digest="0" * 64,
            previous_block_hash=self.GENESIS_HASH,
            block_hash=block_hash,
            metadata={"description": "MigrationMesh Cryptographic Genesis Block"}
        )
        self.chain.append(genesis_block)

    def _compute_block_hash(
        self,
        index: int,
        timestamp: str,
        action_type: str,
        agent_name: str,
        actor_id: str,
        input_digest: str,
        output_digest: str,
        policy_digest: str,
        critic_digest: str,
        previous_hash: str
    ) -> str:
        raw_header = f"{index}|{timestamp}|{action_type}|{agent_name}|{actor_id}|{input_digest}|{output_digest}|{policy_digest}|{critic_digest}|{previous_hash}"
        return hashlib.sha256(raw_header.encode('utf-8')).hexdigest()

    def append_event(
        self,
        action_type: str,
        agent_name: str,
        actor_id: str,
        input_data: Any,
        output_data: Any,
        policy_result: Optional[Any] = None,
        critic_verdict: Optional[Any] = None,
        signature: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditBlock:
        """Appends a new immutable block to the cryptographic chain."""
        prev_block = self.chain[-1]
        new_index = len(self.chain)
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

        input_digest = self._calculate_digest(input_data)
        output_digest = self._calculate_digest(output_data)
        policy_digest = self._calculate_digest(policy_result) if policy_result else "0" * 64
        critic_digest = self._calculate_digest(critic_verdict) if critic_verdict else "0" * 64

        block_hash = self._compute_block_hash(
            index=new_index,
            timestamp=timestamp,
            action_type=action_type,
            agent_name=agent_name,
            actor_id=actor_id,
            input_digest=input_digest,
            output_digest=output_digest,
            policy_digest=policy_digest,
            critic_digest=critic_digest,
            previous_hash=prev_block.block_hash
        )

        block = AuditBlock(
            block_index=new_index,
            timestamp=timestamp,
            action_type=action_type,
            agent_name=agent_name,
            actor_id=actor_id,
            input_digest=input_digest,
            output_digest=output_digest,
            policy_digest=policy_digest,
            critic_digest=critic_digest,
            previous_block_hash=prev_block.block_hash,
            block_hash=block_hash,
            signature=signature,
            metadata=metadata or {}
        )

        self.chain.append(block)
        return block

    def verify_chain_integrity(self) -> Dict[str, Any]:
        """
        Cryptographically verifies the entire audit ledger from Genesis to Tip.
        Returns validation status and any detected tampering points.
        """
        if not self.chain:
            return {"valid": False, "error": "Empty chain"}

        for i in range(1, len(self.chain)):
            current = self.chain[i]
            prev = self.chain[i - 1]

            # 1. Verify previous hash pointer
            if current.previous_block_hash != prev.block_hash:
                return {
                    "valid": False,
                    "tamper_detected_at_block": i,
                    "reason": f"Broken hash pointer at block {i}: expected {prev.block_hash}, found {current.previous_block_hash}"
                }

            # 2. Recalculate block hash
            expected_hash = self._compute_block_hash(
                index=current.block_index,
                timestamp=current.timestamp,
                action_type=current.action_type,
                agent_name=current.agent_name,
                actor_id=current.actor_id,
                input_digest=current.input_digest,
                output_digest=current.output_digest,
                policy_digest=current.policy_digest,
                critic_digest=current.critic_digest,
                previous_hash=current.previous_block_hash
            )

            if current.block_hash != expected_hash:
                return {
                    "valid": False,
                    "tamper_detected_at_block": i,
                    "reason": f"Tampered block content at index {i}: expected {expected_hash}, stored {current.block_hash}"
                }

        return {
            "valid": True,
            "total_blocks": len(self.chain),
            "chain_tip_hash": self.chain[-1].block_hash,
            "verified_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }

    def compute_merkle_root(self) -> str:
        """Computes Merkle Root of all block hashes in the chain."""
        if not self.chain:
            return ""

        hashes = [b.block_hash for b in self.chain]
        while len(hashes) > 1:
            if len(hashes) % 2 != 0:
                hashes.append(hashes[-1])
            new_level = []
            for j in range(0, len(hashes), 2):
                combined = hashes[j] + hashes[j + 1]
                new_level.append(hashlib.sha256(combined.encode('utf-8')).hexdigest())
            hashes = new_level
        return hashes[0]
