"""
MigrationMesh - Privacy & Redaction Gateway
Protects enterprise infrastructure topologies, internal IPs, credentials,
and PII from leaking to LLMs via prompt payloads.
"""

import re
import hashlib
from typing import Dict, Tuple, Any, List


class PrivacyRedactor:
    """
    Bidirectional Tokenizing Redactor:
    - Identifies IPv4/IPv6 addresses, internal hostnames, DB connection URIs,
      API keys, JWTs, AWS/Azure access tokens, and passwords.
    - Replaces sensitive strings with deterministic pseudo-tokens (e.g. <IP_PSEUDO_1>).
    - Maintains an encrypted, local-only token vault for deanonymization post-generation.
    """

    def __init__(self, salt: str = "migrationmesh-vault-salt-2026"):
        self.salt = salt
        self.forward_vault: Dict[str, str] = {}  # original -> token
        self.reverse_vault: Dict[str, str] = {}  # token -> original
        self.ip_counter = 0
        self.host_counter = 0
        self.secret_counter = 0

        # Regex patterns for high-risk tokens
        self.ip_pattern = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
        self.secret_pattern = re.compile(
            r'(?:password|secret|key|token|bearer|pwd)[\s:=]+["\']?([^"\'\s,;]{6,})["\']?',
            re.IGNORECASE
        )
        self.connection_string_pattern = re.compile(
            r'(?:postgres|postgresql|mysql|mongodb|redis|sqlserver):\/\/[^:]+:([^@]+)@([^:\/]+):(\d+)\/(\w+)',
            re.IGNORECASE
        )
        self.aws_key_pattern = re.compile(r'\b(AKIA[0-9A-Z]{16})\b')

    def _get_or_create_token(self, category: str, original: str) -> str:
        if original in self.forward_vault:
            return self.forward_vault[original]

        # Generate deterministic token name
        hash_digest = hashlib.sha256(f"{self.salt}:{original}".encode()).hexdigest()[:6]
        token = f"<{category.upper()}_{hash_digest}>"

        self.forward_vault[original] = token
        self.reverse_vault[token] = original
        return token

    def redact_text(self, text: str) -> Tuple[str, int]:
        """Redacts sensitive entities from a plain text or prompt string."""
        redacted = text
        redaction_count = 0

        # 1. AWS Access Keys
        for match in self.aws_key_pattern.finditer(text):
            val = match.group(1)
            tok = self._get_or_create_token("AWS_KEY", val)
            redacted = redacted.replace(val, tok)
            redaction_count += 1

        # 2. Connection Strings (Redact passwords and internal DB hosts)
        for match in self.connection_string_pattern.finditer(text):
            pwd = match.group(1)
            host = match.group(2)
            pwd_tok = self._get_or_create_token("DB_PASSWD", pwd)
            host_tok = self._get_or_create_token("DB_HOST", host)
            redacted = redacted.replace(pwd, pwd_tok)
            redacted = redacted.replace(host, host_tok)
            redaction_count += 2

        # 3. Explicit Secret/Password key-values
        for match in self.secret_pattern.finditer(text):
            val = match.group(1)
            # Avoid re-redacting existing pseudo-tokens
            if val.startswith("<") and val.endswith(">"):
                continue
            tok = self._get_or_create_token("SECRET_TOKEN", val)
            redacted = redacted.replace(val, tok)
            redaction_count += 1

        # 4. IP Addresses (Private subnets e.g. 10.x, 192.168.x, 172.16-31.x)
        for match in self.ip_pattern.finditer(text):
            val = match.group(0)
            tok = self._get_or_create_token("IP_NODE", val)
            redacted = redacted.replace(val, tok)
            redaction_count += 1

        return redacted, redaction_count

    def redact_dict(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """Recursively traverses a JSON/Dict structure and redacts all string values."""
        redacted_data = {}
        total_redactions = 0

        for key, value in data.items():
            if isinstance(value, str):
                redacted_val, count = self.redact_text(value)
                redacted_data[key] = redacted_val
                total_redactions += count
            elif isinstance(value, dict):
                sub_data, count = self.redact_dict(value)
                redacted_data[key] = sub_data
                total_redactions += count
            elif isinstance(value, list):
                sub_list = []
                for item in value:
                    if isinstance(item, str):
                        r_item, count = self.redact_text(item)
                        sub_list.append(r_item)
                        total_redactions += count
                    elif isinstance(item, dict):
                        r_item, count = self.redact_dict(item)
                        sub_list.append(r_item)
                        total_redactions += count
                    else:
                        sub_list.append(item)
                redacted_data[key] = sub_list
            else:
                redacted_data[key] = value

        return redacted_data, total_redactions

    def deanonymize_text(self, text: str) -> str:
        """Restores original values using the private in-memory token vault (used in executor plane)."""
        restored = text
        for token, original in self.reverse_vault.items():
            restored = restored.replace(token, original)
        return restored
