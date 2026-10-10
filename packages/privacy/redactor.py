"""
MigrationMesh - Privacy & Redaction Gateway
Protects enterprise infrastructure topologies, internal IPv4/IPv6 addresses, credentials,
and PII from leaking to LLMs via prompt payloads.
"""

import re
import hashlib
import ipaddress
from typing import Dict, Tuple, Any, List


class PrivacyRedactor:
    """
    Bidirectional Tokenizing Redactor:
    - Redacts IPv4, IPv6, DB connection URIs (with URL-encoded passwords),
      Base64 tokens, AWS/Azure access keys, and bearer tokens.
    - Replaces sensitive strings with deterministic pseudo-tokens (e.g. <IP_NODE_...>, <SECRET_TOKEN_...>).
    - Maintains a local-only token vault for deanonymization in the execution plane.
    """

    def __init__(self, salt: str = "migrationmesh-vault-salt-2026"):
        self.salt = salt
        self.forward_vault: Dict[str, str] = {}  # original -> token
        self.reverse_vault: Dict[str, str] = {}  # token -> original

        self.aws_key_pattern = re.compile(r'\b(AKIA[0-9A-Z]{16})\b')
        self.connection_string_pattern = re.compile(
            r'(?:postgres|postgresql|mysql|mongodb|redis|sqlserver):\/\/[^:]+:([^@]+)@([^:\/]+):(\d+)\/(\w+)',
            re.IGNORECASE
        )
        self.base64_secret_pattern = re.compile(
            r'(?<![A-Za-z0-9+/_-])[A-Za-z0-9+/_-]{28,}={0,2}(?![A-Za-z0-9+/_-])'
        )
        self.secret_pattern = re.compile(
            r'(?:password|secret|key|token|bearer|pwd)[\s:=]+["\']?([^"\'\s,;]{6,})["\']?',
            re.IGNORECASE
        )
        self.ipv4_pattern = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')

    def _get_or_create_token(self, category: str, original: str) -> str:
        if original in self.forward_vault:
            return self.forward_vault[original]

        hash_digest = hashlib.sha256(f"{self.salt}:{original}".encode()).hexdigest()[:6]
        token = f"<{category.upper()}_{hash_digest}>"

        self.forward_vault[original] = token
        self.reverse_vault[token] = original
        return token

    def redact_text(self, text: str) -> Tuple[str, int]:
        """Redacts sensitive entities from plain text or prompt strings."""
        redacted = text
        redaction_count = 0

        # 1. AWS Access Keys
        for match in self.aws_key_pattern.finditer(text):
            val = match.group(1)
            tok = self._get_or_create_token("AWS_KEY", val)
            redacted = redacted.replace(val, tok)
            redaction_count += 1

        # 2. Connection Strings (Redact passwords and internal hosts)
        for match in self.connection_string_pattern.finditer(text):
            pwd = match.group(1)
            host = match.group(2)
            pwd_tok = self._get_or_create_token("DB_PASSWD", pwd)
            host_tok = self._get_or_create_token("DB_HOST", host)
            redacted = redacted.replace(pwd, pwd_tok)
            redacted = redacted.replace(host, host_tok)
            redaction_count += 2

        # 3. IPv6 Addresses via ipaddress validation
        for candidate in set(re.findall(r'[\w:]+', redacted)):
            if ":" in candidate and len(candidate) >= 4 and not candidate.startswith("<"):
                try:
                    ip = ipaddress.ip_address(candidate)
                    if isinstance(ip, ipaddress.IPv6Address):
                        tok = self._get_or_create_token("IPV6_NODE", candidate)
                        redacted = redacted.replace(candidate, tok)
                        redaction_count += 1
                except ValueError:
                    pass

        # 4. High-Entropy Base64 / JWT tokens (Run before generic keyword matching)
        for match in self.base64_secret_pattern.finditer(redacted):
            val = match.group(0)
            if not val.startswith("<") and not val.endswith(">"):
                tok = self._get_or_create_token("BASE64_KEY", val)
                redacted = redacted.replace(val, tok)
                redaction_count += 1

        # 5. Explicit Secret/Password key-values
        for match in self.secret_pattern.finditer(redacted):
            val = match.group(1)
            if val.startswith("<") and val.endswith(">"):
                continue
            tok = self._get_or_create_token("SECRET_TOKEN", val)
            redacted = redacted.replace(val, tok)
            redaction_count += 1

        # 6. IPv4 Addresses
        for match in self.ipv4_pattern.finditer(redacted):
            val = match.group(0)
            if not val.startswith("<"):
                tok = self._get_or_create_token("IP_NODE", val)
                redacted = redacted.replace(val, tok)
                redaction_count += 1

        return redacted, redaction_count

    def redact_dict(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """Recursively traverses JSON/Dict structure and redacts all string values."""
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
        """Restores original values using the local token vault."""
        restored = text
        for token, original in self.reverse_vault.items():
            restored = restored.replace(token, original)
        return restored
