"""
MigrationMesh - HMAC-Signed Cryptographic Hash Chain
Append-only, tamper-evident audit ledger with HMAC-SHA256 signatures per block.
Enforces secret key authentication from environment variables.
"""

import os
import hmac
import hashlib
import json
import datetime
from typing import List, Dict, Any, Optional
from packages.core.schemas import AuditBlock


class HMACHashChain:
    """
    Cryptographic HMAC-Signed Hash Chain.
    Every event is hash-chained to its predecessor via SHA-256 and authenticated
    with an HMAC-SHA256 signature using a mandatory secret key.
    """

    GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = secret_key or os.environ.get("MIGRATIONMESH_HMAC_KEY")
        if not self.secret_key:
            raise ValueError(
                "MIGRATIONMESH_HMAC_KEY environment variable is required for cryptographic HMAC signing. "
                "Set MIGRATIONMESH_HMAC_KEY in your environment or pass secret_key to the constructor."
            )
        self.chain: List[AuditBlock] = []
        self._initialize_genesis_block()

    def _calculate_digest(self, data: Any) -> str:
        """Calculates canonical SHA-256 hash of any Python data structure or string."""
        if isinstance(data, str):
            payload = data.encode('utf-8')
        else:
            payload = json.dumps(data, sort_keys=True, default=str).encode('utf-8')
        return hashlib.sha256(payload).hexdigest()

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

    def _compute_hmac_signature(self, block_hash: str, key: Optional[str] = None) -> str:
        signing_key = (key or self.secret_key).encode('utf-8')
        return hmac.new(signing_key, block_hash.encode('utf-8'), hashlib.sha256).hexdigest()

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
        signature = self._compute_hmac_signature(block_hash)

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
            signature=signature,
            metadata={"description": "MigrationMesh Cryptographic Genesis Block"}
        )
        self.chain.append(genesis_block)

    def append_event(
        self,
        action_type: str,
        agent_name: str,
        actor_id: str,
        input_data: Any,
        output_data: Any,
        policy_result: Optional[Any] = None,
        critic_verdict: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditBlock:
        """Appends a new HMAC-signed block to the cryptographic chain."""
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

        signature = self._compute_hmac_signature(block_hash)

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

    def verify_chain_integrity(self, verification_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Cryptographically verifies the entire hash chain from Genesis to Tip.
        Validates hash pointers, block digests, and HMAC signatures.
        """
        key = verification_key or self.secret_key
        if not key:
            return {"valid": False, "error": "Verification key required"}

        if not self.chain:
            return {"valid": False, "error": "Empty chain"}

        for i in range(len(self.chain)):
            current = self.chain[i]

            # 1. Verify previous hash pointer (except genesis)
            if i > 0:
                prev = self.chain[i - 1]
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

            # 3. Verify HMAC signature with secret key
            expected_sig = self._compute_hmac_signature(current.block_hash, key)
            if not hmac.compare_digest(current.signature or "", expected_sig):
                return {
                    "valid": False,
                    "tamper_detected_at_block": i,
                    "reason": f"Invalid HMAC signature at block {i}. Authentication failed."
                }

        return {
            "valid": True,
            "total_blocks": len(self.chain),
            "chain_tip_hash": self.chain[-1].block_hash,
            "chain_tip_signature": self.chain[-1].signature,
            "verified_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }

    def export_head_anchor(self) -> Dict[str, Any]:
        """
        Exports an external anchor for the current tip of the hash chain.
        This anchor can be stored in an external immutable witness/store to detect truncation attacks.
        """
        tip = self.chain[-1]
        return {
            "head_sequence_number": tip.block_index,
            "head_hash": tip.block_hash,
            "head_signature": tip.signature,
            "anchored_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }

    def verify_chain_with_anchor(self, anchor: Dict[str, Any], verification_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Cryptographically verifies the ledger against an external head anchor.
        Detects if trailing blocks have been removed (truncation attacks) or altered (forking).
        """
        # First verify intrinsic integrity
        base_verification = self.verify_chain_integrity(verification_key)
        if not base_verification["valid"]:
            return base_verification

        anchor_seq = anchor.get("head_sequence_number")
        anchor_hash = anchor.get("head_hash")
        anchor_sig = anchor.get("head_signature")

        if anchor_seq is None or not anchor_hash:
            return {
                "valid": False,
                "error": "Invalid external anchor structure: missing head_sequence_number or head_hash"
            }

        # 1. Truncation detection: local chain has fewer blocks than the anchored state
        if len(self.chain) <= anchor_seq:
            return {
                "valid": False,
                "tamper_type": "TRUNCATION_ATTACK",
                "reason": (
                    f"Ledger truncation detected! External anchor expects at least {anchor_seq + 1} blocks "
                    f"(sequence index {anchor_seq}), but local ledger only contains {len(self.chain)} blocks."
                ),
                "expected_sequence": anchor_seq,
                "actual_count": len(self.chain)
            }

        # 2. Historical block mismatch at the anchored sequence
        anchored_block = self.chain[anchor_seq]
        if anchored_block.block_hash != anchor_hash:
            return {
                "valid": False,
                "tamper_type": "ANCHOR_HASH_MISMATCH",
                "reason": (
                    f"External anchor hash mismatch at block index {anchor_seq}! "
                    f"Expected {anchor_hash}, found {anchored_block.block_hash}."
                ),
                "expected_hash": anchor_hash,
                "actual_hash": anchored_block.block_hash
            }

        if anchor_sig and anchored_block.signature != anchor_sig:
            return {
                "valid": False,
                "tamper_type": "ANCHOR_SIGNATURE_MISMATCH",
                "reason": f"External anchor signature mismatch at block index {anchor_seq}."
            }

        return {
            "valid": True,
            "anchor_verified": True,
            "anchored_sequence": anchor_seq,
            "anchored_hash": anchor_hash,
            "current_total_blocks": len(self.chain),
            "verified_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }

